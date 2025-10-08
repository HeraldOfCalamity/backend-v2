import base64
import uuid
from beanie import PydanticObjectId
from beanie.operators import And
import boto3
from botocore.config import Config as BotoConfig
import pymongo
from app.core.exceptions import raise_not_found
from app.core.config import settings
from app.domain.entities.especialidad_entity import EspecialidadCreate, EspecialidadOut, EspecialidadUpdate
from app.infrastructure.schemas.especialidad import Especialidad

def _upload_base64_to_r2(base64_image: str, prefix: str = "especialidades") -> str:
    """
    Sube una imagen base64 a R2 y devuelve la KEY (p.ej. 'especialidades/uuid.webp').
    """
    # detectar extension por el header dataURL
    if "," in base64_image:
        header, data = base64_image.split(",", 1)
        if "image/" in header:
            ext = header.split("/")[1].split(";")[0]
        else:
            ext = "png"
    else:
        data = base64_image
        ext = "png"

    key = f"{prefix}/{uuid.uuid4().hex}.{ext}"

    s3 = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=base64.b64decode(data),
        ContentType=f"image/{ext}",
    )
    return key


async def create_especialidad(data: EspecialidadCreate, tenant_id: str) -> Especialidad:
    image_key = None
    if data.image:
        if data.image.startswith('data:') or ',' in data.image:
            image_key = _upload_base64_to_r2(data.image)
        elif data.image.startswith('especialidades/'):
            image_key = data.image
        else:
            image_key=None

    especialidad_dict = data.model_dump()
    especialidad_dict['image'] = image_key
    especialidad = Especialidad(**especialidad_dict, tenant_id= tenant_id)
    created = await especialidad.insert()
    return created

async def get_especialidades_by_tenant(tenant_id: str) -> list[Especialidad]:
    return await Especialidad.find(
        Especialidad.tenant_id == PydanticObjectId(tenant_id)
    ).sort([
        (Especialidad.createdAt, pymongo.DESCENDING)
    ]).to_list()

async def delete_especialidad(especialidad_id: str, tenant_id: str) -> bool:
    especialidad = await Especialidad.find(Especialidad.id == PydanticObjectId(especialidad_id)).find(Especialidad.tenant_id == PydanticObjectId(tenant_id)).first_or_none()
    
    if not especialidad:
        raise raise_not_found(f'Especialidad {especialidad_id}');

    await especialidad.delete()
    return True
    

async def update_especialidad(especialidad_id: str, data: EspecialidadUpdate, tenant_id: str) -> Especialidad:
    especialidad = await Especialidad.find(
        Especialidad.tenant_id == PydanticObjectId(tenant_id)
    ).find(
        Especialidad.id == PydanticObjectId(especialidad_id)
    ).first_or_none()

    if not especialidad:
        raise raise_not_found('Especialidad')

    especialidad.nombre =data.nombre
    especialidad.descripcion = data.descripcion
    if data.image is None or data.image == "":
        especialidad.image = None
    elif data.image.startswith("data:") or "," in data.image:
        especialidad.image = _upload_base64_to_r2(data.image)
    elif data.image.startswith("especialidades/"):
        especialidad.image = data.image
    elif data.image.startswith("http") or data.image.startswith("/static/"):
        # El form suele reenviar lo que ve en el preview. Si no es Base64 ni KEY, asumimos "sin cambios".
        # (antes intentabas reconstruir ruta local desde '/static/...'; eso rompía tras redeploy) :contentReference[oaicite:5]{index=5}
        pass
    else:
        # Si llega algo raro, mejor no tocar la imagen existente
        pass

    especialidad.tratamientos=data.tratamientos
    
    await especialidad.save()
    return especialidad


async def get_especialidad_by_id(especialidad_id: str, tenant_id: str) -> Especialidad:
    return await Especialidad.find(And(
        Especialidad.tenant_id == PydanticObjectId(tenant_id),
        Especialidad.id == PydanticObjectId(especialidad_id)
    )).first_or_none()


def especialidad_to_out(especialidad: Especialidad) -> EspecialidadOut:
    d = especialidad.model_dump()
    d['id'] = str(especialidad.id)
    d['tratamientos'] = [str(t) for t in especialidad.tratamientos]
    
    if especialidad.image:
        s3 = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        d["image"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": especialidad.image},
            ExpiresIn=60,
            HttpMethod="GET",
        )
    else:
        d['image'] = None
    
    return EspecialidadOut(**d)