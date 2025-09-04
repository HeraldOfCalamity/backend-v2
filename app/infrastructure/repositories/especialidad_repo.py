import os
from re import M
from beanie import PydanticObjectId
from beanie.operators import And
import pymongo
from app.core.exceptions import raise_not_found
from app.domain.entities.especialidad_entity import EspecialidadCreate, EspecialidadOut, EspecialidadUpdate
from app.infrastructure.schemas.especialidad import Especialidad
from app.shared.utils import save_base_64_image_local


async def create_especialidad(data: EspecialidadCreate, tenant_id: str) -> Especialidad:
    image_path=None
    if data.image:
        image_path = save_base_64_image_local(data.image, 'especialidades')
    especialidad_dict = data.model_dump()
    especialidad_dict['image'] = image_path
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
    especialidad = await Especialidad.find(Especialidad.tenant_id == PydanticObjectId(tenant_id)).find(Especialidad.id == PydanticObjectId(especialidad_id)).first_or_none()
    if not especialidad:
        raise raise_not_found('Especialidad')

    especialidad.nombre =data.nombre
    especialidad.descripcion = data.descripcion
    if data.image:
        especialidad.image = save_base_64_image_local(data.image, 'especialidades')
    else:
        especialidad.image = None
    especialidad.tratamientos=data.tratamientos
    
    await especialidad.save()
    return especialidad


async def get_especialidad_by_id(especialidad_id: str, tenant_id: str) -> Especialidad:
    return await Especialidad.find(And(
        Especialidad.tenant_id == PydanticObjectId(tenant_id),
        Especialidad.id == PydanticObjectId(especialidad_id)
    )).first_or_none()


def especialidad_to_out(especialidad: Especialidad) -> EspecialidadOut:
    especialidad_dict = especialidad.model_dump()
    especialidad_dict['id'] = str(especialidad.id)
    especialidad_dict['tratamientos'] = [str(t) for t in especialidad.tratamientos]
    image_path = especialidad.image
    if image_path and os.path.exists(image_path):
        url_path = image_path.replace('\\', '/')
        especialidad_dict['image'] = f"/static/{url_path.split('static/', 1)[-1]}"
    else:
        especialidad_dict['image'] = None
    return EspecialidadOut(**especialidad_dict)