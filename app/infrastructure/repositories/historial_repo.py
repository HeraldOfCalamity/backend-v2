import uuid
from beanie import PydanticObjectId
from beanie.operators import And
import boto3
from botocore.config import Config as BotoConfig
from fastapi import HTTPException
from app.core.config import settings
from app.core.db import client

from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RegisterImageReq
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
        HistorialClinico.id == HistorialClinico(historial_id)
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

    )

    created = await new_historial.insert()

    return created

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
    ext = '.bin' if body.content_type == 'application/octet-stream' else '.webp'
    key = f"pacientes/{body.paciente_id}/{body.historial_id or 'no-hist'}/{body.entrada_id or 'no-entry'}/{uuid.uuid4().hex}{ext}"
    try:
        url = s3.generate_presigned_url(
            'put object',
            Params={
                'Bucket': settings.S3_BUCKET,
                'key': key,
                'ContentType': body.content_type
            },
            ExpiresIn=60,
            HttpMethod='PUT'
        )
        return {'url': url, 'key':key, 'expiresIn': 60}
    except Exception as e:
        raise HTTPException(500, f'presigned error: {e}')
    
async def register_image(body: RegisterImageReq, tenant_id: str):
    img = ImageAsset(
        tenant_id=PydanticObjectId(tenant_id),
        paciente_id=PydanticObjectId(body.pacienteId),
        historial_id=PydanticObjectId(body.historialId),
        entrada_id=PydanticObjectId(body.entradaId),
        bucket=settings.S3_BUCKET,
        key=body.key,
        content_type=body.originalType or ('application/octet-stream' if body.aesKeyB64 else 'image/webp'),
        size=body.size or 0,
        width=body.width,
        height=body.height,
        preview_data_url=body.previewDataUrl,
        crypto=None if not (body.aesKeyB64 and body.ivB64) else {'key_b64':body.aesKeyB64, 'iv_b64': body.ivB64}
    )

    await img.insert()
    return {'ok':True, 'imgeId': str(img.id), 'key': img.key}

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


