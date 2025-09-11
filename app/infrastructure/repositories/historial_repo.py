import uuid
from beanie import PydanticObjectId
from beanie.operators import And
import boto3
from botocore.config import Config as BotoConfig
from fastapi import HTTPException
from app.core.config import settings
from app.core.db import client

from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RegisterImageReq, UpdateHistorial
from app.infrastructure.schemas.historial import Entrada, HistorialClinico, ImageAsset

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
        antfamiliares=data.antFamiliares,
        antPersonales=data.antPersonales,
        condActual=data.condActual,
        intervencionClinica=data.condActual,
        paciente_id=PydanticObjectId(data.paciente_id),
        tenant_id=PydanticObjectId(tenant_id)
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

    updated = await historial.save()

    return updated



async def add_entrada(historial_id: str, tenant_id: str, data: EntradaAdd) -> HistorialClinico:
    async with await client.start_session() as s:
        async with s.start_transaction():
            hist = await HistorialClinico.get(historial_id, session=s)
            if not hist:
                raise HTTPException(404, "Historial no encontrado")

            entrada = Entrada(
                recursosTerapeuticos=data.recursosTerapeuticos,
                evolucionText=data.evolucionText,
                imagenes=[PydanticObjectId(id) for id in data.imageIds]
            )
            hist.entradas.append(entrada)
            updated = await hist.save(session=s)

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

    if not any(e.id == body.entradaId for e in hist.entradas):
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
    upd = await coll.update_one(
        {
            "_id": hist.id,                           # ObjectId del historial
            "tenant_id": hist.tenant_id,              # seguridad multi-tenant
        },
        {
            # empuja la KEY de la imagen al array 'imagenes' de esa entrada
            "$push": { "entradas.$[e].imagenes": body.key }
        },
        array_filters=[{ "e.id": body.entradaId }],   # condiciona por id de entrada (string)
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

# async def attach_images(historial_id: str, entrtada_id: str, tenant_id: str, body: AttachImages)
#     hist = await get_historial_by_id(historial_id, tenant_id)
#     if not hist:
#         raise raise_not_found('Historial no encontrado')
    
#     target = next((e for e in hist.entradas if e.id))


