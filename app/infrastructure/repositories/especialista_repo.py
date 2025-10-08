import base64
from datetime import datetime, timezone
import os
import uuid
from beanie import PydanticObjectId
from beanie.operators import And
import pymongo
import boto3
from botocore.config import Config as BotoConfig
from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.core.config import settings
from app.domain.entities.especialista_entity import EspecialistaCreate, EspecialistaCreateWithUser, EspecialistaOut, EspecialistaProfileOut, EspecialistaUpdate, InactividadPayload
from app.infrastructure.repositories.officeConfig_repo import get_office_timezone
from app.infrastructure.repositories.user_repo import get_user_by_email, get_user_by_id, user_to_out
from app.infrastructure.schemas.especialista import Especialista
from app.shared.utils import save_base_64_image_local

def _upload_base64_to_r2(base64_image: str, prefix: str = "especialistas") -> str:
    """
    Sube una imagen base64 a R2 y devuelve la KEY (p.ej. 'especialistas/<uuid>.webp').
    """
    # Detectar extensión por el header dataURL
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

async def create_especialista(data: EspecialistaCreate, user_id: str, tenant_id: str) -> Especialista:    
    image_key = None
    if data.image:
        # Antes: save_base_64_image_local(..., 'especialistas')  -> archivo local
        # Ahora: subimos a R2 y guardamos la KEY
        if data.image.startswith("data:") or "," in data.image:
            image_key = _upload_base64_to_r2(data.image)
        elif data.image.startswith("especialistas/"):
            # por si envías ya una key
            image_key = data.image
        else:
            image_key = None

    especialista = Especialista(
        user_id=PydanticObjectId(user_id),
        especialidades=[PydanticObjectId(eid) for eid in data.especialidad_ids],
        informacion=data.informacion if data.informacion else None,
        image=image_key if image_key else None,
        disponibilidades=[disp.model_dump() for disp in data.disponibilidades],
        tenant_id=tenant_id,
    )
    created = await especialista.insert()    
    return created

async def update_especialista(especialista_id: str, data: EspecialistaUpdate, tenant_id:str):
    especialista = await Especialista.find(
        Especialista.tenant_id == PydanticObjectId(tenant_id)
    ).find(
        Especialista.id == PydanticObjectId(especialista_id)
    ).first_or_none()
    if not especialista:
        raise raise_not_found('Especialista')
    
    especialista.especialidades = [PydanticObjectId(eId) for eId in data.especialidad_ids]
    especialista.disponibilidades = [disp.model_dump() for disp in data.disponibilidades]

    if data.image is None or data.image == "":
        especialista.image = None
    elif data.image.startswith("data:") or "," in data.image:
        especialista.image = _upload_base64_to_r2(data.image)
    elif data.image.startswith("especialistas/"):
        especialista.image = data.image
    elif data.image.startswith("http") or data.image.startswith("/static/"):
        # Antes intentabas traducir '/static/...' a ruta local y re-guardar; eso falla tras redeploy. No tocar.
        pass
    else:
        # Valor desconocido -> no tocar imagen existente
        pass

    especialista.informacion = data.informacion if data.informacion else None

    await especialista.save()
    return especialista

async def get_especialistas_by_tenant(tenant_id: str) -> list[Especialista]:
    return await Especialista.find(
        Especialista.tenant_id == PydanticObjectId(tenant_id)
    ).sort([
        (Especialista.createdAt, pymongo.DESCENDING)
    ]).to_list()

async def get_especialista_by_user_id(user_id: str, tenant_id: str) -> Especialista:
    return await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id),
        Especialista.user_id == PydanticObjectId(user_id))
    ).first_or_none()

async def delete_especialista(especialista_id: str, tenant_id: str) -> bool:
    especialista = await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id)),
        Especialista.id == PydanticObjectId(especialista_id)
    ).first_or_none()

    if not especialista:
        raise raise_not_found(f'Especialista {especialista_id}')
    
    user = await get_user_by_id(str(especialista.user_id), tenant_id)

    if not user:
        raise raise_not_found(f'Usuario {str(especialista.user_id)}')

    if not user.isActive:
        raise raise_duplicate_entity('El especialista ya se encuentra inactivo.')

    user.isActive = False
    await user.save()
    return True

async def get_especialista_by_especialidad_id(especialidad_id: str, tenant_id: str) -> list[EspecialistaProfileOut]:
    especialistas = await get_especialistas_with_user(tenant_id);
    filtered = []
    for e in especialistas:
        if especialidad_id in e.especialista.especialidad_ids and e.user.isActive:
            filtered.append(e)


    return filtered

async def get_especialista_by_id(especialista_id: str, tenant_id: str) -> Especialista | None:
    return await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id),
        Especialista.id == PydanticObjectId(especialista_id)
    )).first_or_none()

async def get_especialista_profile_by_id(especialista_id: str, tenant_id: str) -> EspecialistaProfileOut:
    especialista = await get_especialista_by_id(especialista_id, tenant_id)
    user = await get_user_by_id(str(especialista.user_id), tenant_id)

    if not especialista or not user:
        raise raise_not_found('Especialista y usuario')

    return EspecialistaProfileOut(
        especialista=especialista_to_out(especialista),
        user=user_to_out(user)
    )

async def get_especialistas_with_user(tenant_id: str) -> list[EspecialistaProfileOut]:
    especialistas = await get_especialistas_by_tenant(tenant_id)
    result = []

    for e in especialistas:
        usuario = await get_user_by_id(str(e.user_id), tenant_id)
        result.append(EspecialistaProfileOut(
            especialista=especialista_to_out(e),
            user=user_to_out(usuario) if usuario else None
        ))

    return result
   
async def create_especialista_profile(data: EspecialistaCreateWithUser, tenant_id: str) -> EspecialistaProfileOut:
    found_user = await get_user_by_email(data.user.email, tenant_id)
    
    if found_user:
        raise raise_duplicate_entity('Ya existe un usuario registrado con ese correo');

    

def especialista_to_out(especialista: Especialista) -> EspecialistaOut:
    especialista_dict = especialista.model_dump()
    especialista_dict['user_id'] = str(especialista.user_id)
    especialista_dict['id'] = str(especialista.id)
    especialista_dict['especialidad_ids'] = [str(eId) for eId in especialista.especialidades]
    
    key = especialista.image
    if key:
        s3 = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        especialista_dict['image'] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=60,
            HttpMethod="GET",
        )
    else:
        especialista_dict['image'] = None

    return EspecialistaOut(**especialista_dict)


async def agregar_inactividad_y_verificar(especialista_id: str, payload: InactividadPayload, cancelar: bool, tenant_id: str) -> dict:
    from app.infrastructure.repositories.cita_repo import cancelar_citas, find_citas_de_especialista_entre
    esp = await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id),
        Especialista.id == PydanticObjectId(especialista_id)
    )).first_or_none()

    if not esp:
        raise raise_not_found('Especialista')
    
    ini_utc = _to_utc_naive(payload.desde)
    fin_utc = _to_utc_naive(payload.hasta)
    
    inicio = min(ini_utc, fin_utc)
    fin = max(ini_utc, fin_utc)

    citas = await find_citas_de_especialista_entre(especialista_id, inicio, fin, tenant_id)

    canceladas = 0
    if cancelar and citas:
        ids = [str(c.id) for c in citas]
        canceladas = await cancelar_citas(ids, payload.motivo or 'Sin horarios disponibles', tenant_id)
    
    nuevo = {'desde': inicio, 'hasta': fin, 'motivo': payload.motivo}
    new_mot = (payload.motivo or '').lower()
    ya_existe = any(
        getattr(ia, "desde", None) == inicio and
        getattr(ia, "hasta", None) == fin and
        (getattr(ia, "motivo", "") or "").lower() == new_mot
        for ia in (esp.inactividades or [])
    )


    if not ya_existe:
        esp.inactividades.append(nuevo)
        await esp.save()

    return{
        'inactividad': nuevo,
        'citas_en_rango': len(citas),
        'citas_canceladas': canceladas
    }

async def re_verificar_inactividad(
        especialista_id: str,
        desde: datetime,
        hasta: datetime,
        tenant_id: str
    ) -> dict:
    from app.infrastructure.repositories.cita_repo import find_citas_de_especialista_entre
    inicio = min(desde, hasta)
    fin = max(desde, hasta)
    citas = await find_citas_de_especialista_entre(especialista_id, inicio, fin, tenant_id)
    return {
        'citas_en_rango': len(citas)
    }

async def eliminar_inactividad(especialista_id: str, desde: datetime, hasta: datetime, tenant_id: str) -> dict:
    esp = await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id),
        Especialista.id == PydanticObjectId(especialista_id)
    )).first_or_none()
    if not esp:
        raise raise_not_found('Especialista')

    # Variante A: UTC naive (recomendada y la que usamos ahora)
    a_ini = _to_utc_naive(desde)
    a_fin = _to_utc_naive(hasta)

    # Variante B: naive "tal cual vino"
    b_ini = desde.replace(tzinfo=None)
    b_fin = hasta.replace(tzinfo=None)

    # Variante C: hora local de oficina -> naive (compat con datos guardados localmente)
    tz = await get_office_timezone(tenant_id)
    if desde.tzinfo is not None:
        c_ini = desde.astimezone(tz).replace(tzinfo=None)
        c_fin = hasta.astimezone(tz).replace(tzinfo=None)
    else:
        # si llegó naive, no tenemos su tz de origen: asumimos que ya es local
        c_ini = b_ini
        c_fin = b_fin

    def _match(ia) -> bool:
        d = getattr(ia, "desde", None)
        h = getattr(ia, "hasta", None)
        return (
            (d == a_ini and h == a_fin) or
            (d == b_ini and h == b_fin) or
            (d == c_ini and h == c_fin)
        )

    before = len(esp.inactividades or [])
    esp.inactividades = [ia for ia in (esp.inactividades or []) if not _match(ia)]
    removed = before - len(esp.inactividades or [])
    if removed > 0:
        await esp.save()

    return {"removed": removed}



def _to_utc_naive(dt: datetime) -> datetime:
    """Convierte cualquier datetime a UTC naive (tz=UTC y luego sin tz)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Interpretamos naïve entrante como UTC (compatibilidad)
        return dt.replace(tzinfo=None)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
