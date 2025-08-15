from re import M
from beanie import PydanticObjectId
from beanie.operators import And
import pymongo
from app.core.exceptions import raise_not_found
from app.domain.entities.especialidad_entity import EspecialidadCreate, EspecialidadOut, EspecialidadUpdate
from app.infrastructure.schemas.especialidad import Especialidad


async def create_especialidad(data: EspecialidadCreate, tenant_id: str) -> Especialidad:
    especialidad = Especialidad(**data.model_dump(), tenant_id= tenant_id)
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
    especialidad.image = data.image
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
    return EspecialidadOut(**especialidad_dict)