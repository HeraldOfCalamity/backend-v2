import uuid
from beanie import PydanticObjectId
from beanie.operators import And
import boto3
from botocore.config import Config as BotoConfig
from fastapi import HTTPException
from app.application.services.ner_service import extract_ner_spans, spans_to_models
from app.core.config import settings
from app.core.db import client

from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RegisterImageReq, TratamientoAdd, UpdateHistorial
from app.infrastructure.schemas.historial import Entrada, HistorialClinico, ImageAsset, NerSpan, SectionNer, Tratamiento

s3 = boto3.client(
    's3',
    region_name=settings.S3_REGION,
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    config=BotoConfig(
        signature_version='s3v4',
        s3={"addressing_style": "path"}
    )
)

async def get_historial_by_paciente_id(paciente_id: str, tenant_id: str) -> HistorialClinico:
    return await HistorialClinico.find(And(
        HistorialClinico.tenant_id == PydanticObjectId(tenant_id),
        HistorialClinico.paciente_id == PydanticObjectId(paciente_id)
    )).first_or_none()

async def get_historial_by_id(historial_id: str, tenant_id: str) -> HistorialClinico:
    return await HistorialClinico.find(And(
        HistorialClinico.tenant_id == PydanticObjectId(tenant_id),
        HistorialClinico.id == PydanticObjectId(historial_id)
    )).first_or_none()

async def create_historial(data: HistorialCreate, tenant_id: str) -> HistorialClinico:
    historial = await get_historial_by_paciente_id(data.paciente_id, tenant_id)

    if historial:
        raise raise_duplicate_entity('Ya existe un historial para el paciente')

    new_historial = HistorialClinico(
        paciente_id=PydanticObjectId(data.paciente_id),
        tenant_id=PydanticObjectId(tenant_id),
        tratamientos=[]
    )

    created = await new_historial.insert()

    return created

async def update_historial_anamnesis(updateData: UpdateHistorial, tenant_id: str, historial_id: str) -> HistorialClinico:
    historial = await get_historial_by_id(historial_id, tenant_id);
    if not historial:
        raise raise_not_found('Historial no encontrado')
    
    historial.condActual = updateData.condActual
    historial.intervencionClinica = updateData.intervencionClinica
    if updateData.antFamiliares:
        historial.antfamiliares = updateData.antFamiliares
    
    if updateData.antPersonales:
        historial.antPersonales = updateData.antPersonales

    cond_spans = spans_to_models(extract_ner_spans(updateData.condActual))
    intv_spans = spans_to_models(extract_ner_spans(updateData.intervencionClinica))
    if updateData.antFamiliares:
        antf_spans = spans_to_models(extract_ner_spans(updateData.antFamiliares))
    
    if updateData.antPersonales:
        antp_spans = spans_to_models(extract_ner_spans(updateData.antPersonales))

    historial.ner_sections = [
        SectionNer(section="condActual", ents=cond_spans),
        SectionNer(section="intervencionClinica", ents=intv_spans)
    ]

    if updateData.antFamiliares:
        historial.ner_sections.append(SectionNer(
            section='antfamiliares',
            ents=antf_spans
        ))
    
    if updateData.antPersonales:
        historial.ner_sections.append(SectionNer(
            section='antPersonales',
            ents=antp_spans
        ))

    updated = await historial.save()

    return updated



async def add_entrada(historial_id: str, tratamiento_id: str, tenant_id: str, data: EntradaAdd) -> HistorialClinico:
    async with await client.start_session() as s:
        async with s.start_transaction():
            hist = await HistorialClinico.get(historial_id, session=s)
            if not hist or str(hist.tenant_id) != tenant_id:
                raise HTTPException(404, "Historial no encontrado")

            # 1) Texto base para NER (puedes separar por campo si quieres ner por subcampo)
            txt_rec = (data.recursosTerapeuticos or "").strip()
            txt_evo = (data.evolucionText or "").strip()
            ner_spans_dicts = extract_ner_spans(f"{txt_rec}\n{txt_evo}".strip())

            # 2) Construimos la entrada con NER
            entrada = Entrada(
                recursosTerapeuticos=txt_rec,
                evolucionText=txt_evo,
                imagenes=[PydanticObjectId(id) for id in data.imageIds],   # si cambiaste a keys, ajusta aquí
                ner=[NerSpan(
                    label=s["label"],
                    text=s["text"],
                    start=int(s["start"]),
                    end=int(s["end"]),
                    norm=s.get("norm"),
                    source="rules",
                    confidence=None
                ) for s in ner_spans_dicts]
            )

            # 3) Guardar en el historial
            if not hist.tratamientos:
                raise HTTPException(400, 'No hay tratamientos en el historial. Crea uno primero.')
            
            found_tratamiento = None
            for tratamiento in hist.tratamientos:
                if tratamiento.id == tratamiento_id:
                    found_tratamiento = tratamiento
                    break;
            
            if not found_tratamiento:
                raise HTTPException(400, 'No se encontro ningun tratamiento asociado')

            tratamiento.entradas.append(entrada)
            updated = await hist.save(session=s)

            # 4) Si te pasan imageIds (ids de ImageAsset), vincúlalas a esta entrada
            if data.imageIds:
                await ImageAsset.find(ImageAsset.id.in_(data.imageIds)).update(
                    {"$set": {"historial_id": hist.id, "entrada_id": entrada.id}},
                    session=s
                )

    return updated

def presign_upload(body: PresignReq):
    # Usa la extensión correcta
    ext = '.bin' if body.content_type == 'application/octet-stream' else '.webp'
    key = (
        f"pacientes/{body.paciente_id}/"
        f"{body.historial_id or 'no-hist'}/"
        f"{body.entrada_id or 'no-entry'}/"
        f"{uuid.uuid4().hex}{ext}"
    )

    try:
        url = s3.generate_presigned_url(
            ClientMethod='put_object',                     
            Params={
                'Bucket': settings.S3_BUCKET,
                'Key': key,                                
                'ContentType': body.content_type,          
            },
            ExpiresIn=60,
            HttpMethod='PUT'
        )
        return {'url': url, 'key': key, 'expiresIn': 60}
    except Exception as e:
        raise HTTPException(500, f'presigned error: {e}')


    
from beanie import PydanticObjectId
from beanie.operators import And, ElemMatch
from fastapi import HTTPException
from app.core.db import client
from app.core.config import settings
from app.core.exceptions import raise_not_found
from app.infrastructure.schemas.historial import HistorialClinico, ImageAsset

async def register_image(body: RegisterImageReq, tenant_id: str):
    # 1) Cargar historial y validar entrada
    hist = await HistorialClinico.find_one(
        HistorialClinico.id == PydanticObjectId(body.historialId),
        HistorialClinico.tenant_id == PydanticObjectId(tenant_id)
    )
    if not hist:
        raise HTTPException(404, "Historial no encontrado")

    entrada_encontrada = None
    tratamiento_encontrado = None
    for tratamiento in hist.tratamientos:
        for entrada in tratamiento.entradas:
            if entrada.id == body.entradaId:
                entrada_encontrada = entrada
                tratamiento_encontrado = tratamiento
                break
        if entrada_encontrada:
            break

    if not entrada_encontrada:
        raise HTTPException(404, "Entrada no encontrada")

    # 2) Insertar metadata de la imagen
    img = ImageAsset(
        tenant_id=PydanticObjectId(tenant_id),
        paciente_id=PydanticObjectId(body.pacienteId),
        historial_id=PydanticObjectId(body.historialId),
        entrada_id=body.entradaId,               # <-- string, coincide con Entrada.id
        bucket=settings.S3_BUCKET,
        key=body.key,                            # <-- GUARDAS LA KEY
        content_type=body.originalType or ('application/octet-stream' if body.aesKeyB64 else 'image/webp'),
        size=body.size or 0,
        width=body.width,
        height=body.height,
        preview_data_url=body.previewDataUrl,
        crypto=None if not (body.aesKeyB64 and body.ivB64) else {'key_b64': body.aesKeyB64, 'iv_b64': body.ivB64},
    )
    await img.insert()

    # 3) $push posicional en la entrada que coincide (arrayFilters)
    coll = HistorialClinico.get_motor_collection()
    t_id = getattr(body, 'tratamientoId', None) or (tratamiento_encontrado.id if tratamiento_encontrado else None)
    if not t_id:
        raise HTTPException(400, 'tratamientoId requerido o no se pudo inferir desde la entrada')
    upd = await coll.update_one(
        {
            "_id": hist.id,                           # ObjectId del historial
            "tenant_id": hist.tenant_id,              # seguridad multi-tenant
        },
        {
            # empuja la KEY de la imagen al array 'imagenes' de esa entrada
            "$push": { "tratamientos.$[t].entradas.$[e].imagenes": body.key }
        },
        array_filters=[
            { "t.id": t_id },
            { "e.id": body.entradaId }
        ],   # condiciona por id de entrada (string)
    )

    # 4) NUNCA devuelvas UpdateResult; devuelve JSON o el doc actualizado
    #    Opción A: doc actualizado (Pydantic -> JSON ok)
    # updated = await HistorialClinico.get(hist.id)
    return {
        "ok": True,
        "key": body.key,
        "imageId": str(img.id),
        "matched": upd.matched_count,
        "modified": upd.modified_count,
        # "historial": updated,  # <- El Document de Beanie es Pydantic; FastAPI lo serializa
    }


def signed_get(key: str):
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=60,
            HttpMethod="GET",
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(500, f'signed-get error: {e}')

async def add_tratamiento(historial_id: str, tenant_id: str, body: TratamientoAdd) -> HistorialClinico:
    hist = await get_historial_by_id(historial_id, tenant_id)
    if not hist:
        raise raise_not_found('Historial no encontrado')
    
    cond_spans = spans_to_models(extract_ner_spans(body.condActual or ''))
    intv_spans = spans_to_models(extract_ner_spans(body.intervencionClinica or ''))
    antf_spans = spans_to_models(extract_ner_spans(body.antFamiliares or ''))
    antp_spans = spans_to_models(extract_ner_spans(body.antPersonales or ''))

    sections = [
        SectionNer(section='condActual', ents=cond_spans),
        SectionNer(section='intervencionClinica', ents=intv_spans),
        SectionNer(section='antfamiliares', ents=antf_spans),
        SectionNer(section='antPersonales', ents=antp_spans),
    ]

    tratamiento = Tratamiento(
        motivo=body.motivo or '',
        antfamiliares=body.antFamiliares or '',
        antPersonales=body.antPersonales or '',
        condActual=body.condActual or '',
        intervencionClinica=body.intervencionClinica or '',
        ner_sections=sections,
        entradas=[]
    )

    hist.tratamientos.append(tratamiento)
    return await hist.save()

async def set_anamnesis_once(historial_id: str, tratamiento_id: str, tenant_id: str, body: TratamientoAdd) -> HistorialClinico:
    hist = await get_historial_by_id(historial_id, tenant_id)
    if not hist:
        raise raise_not_found('Historial no encontrado')
    
    tr = None
    for t in hist.tratamientos:
        if t.id == tratamiento_id:
            tr = t
            break
    
    if tr is None:
        raise raise_not_found('Tratamiento no encontrado')
    
    already = any([
        (tr.antPersonales or '').strip(),
        (tr.antfamiliares or '').strip(),
        (tr.condActual or '').strip(),
        (tr.intervencionClinica or '').strip(),
    ])

    if already:
        raise HTTPException(status_code=409, detail='La anamnesis ya fue guardada para este tratamiento')
    tr.antPersonales = body.antPersonales or ''
    tr.antfamiliares = body.antFamiliares or ''
    tr.condActual = body.condActual or ''
    tr.intervencionClinica = body.intervencionClinica or ''

    sections = [
        SectionNer(section="antPersonales",     ents=spans_to_models(extract_ner_spans(tr.antPersonales))),
        SectionNer(section="antfamiliares",     ents=spans_to_models(extract_ner_spans(tr.antfamiliares))),
        SectionNer(section="condActual",        ents=spans_to_models(extract_ner_spans(tr.condActual))),
        SectionNer(section="intervencionClinica", ents=spans_to_models(extract_ner_spans(tr.intervencionClinica))),
    ]

    tr.ner_sections = sections

    return await hist.save()
        