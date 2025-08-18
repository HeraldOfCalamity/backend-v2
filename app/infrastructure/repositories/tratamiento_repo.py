from beanie import PydanticObjectId
import pymongo
from app.core.exceptions import raise_not_found
from app.domain.entities.tratamiento_entity import TratamientoCreate, TratamientoOut, TratamientoUpdate
from app.infrastructure.schemas.tratamiento import Tratamiento
from beanie.operators import And


async def get_tratamientos_by_tenant(tenant_id: str) -> list[Tratamiento]:
    return await Tratamiento.find(And(
        Tratamiento.tenant_id == PydanticObjectId(tenant_id)
    )).sort([
        (Tratamiento.createdAt, pymongo.DESCENDING)
    ]).to_list()

async def create_tratamiento(data: TratamientoCreate, tenant_id: str) -> Tratamiento:
    tratamiento = Tratamiento(
        nombre=data.nombre,
        descripcion=data.descripcion,
        image=data.image,
        tenant_id=PydanticObjectId(tenant_id)
    )

    created = await tratamiento.insert()

    return created

async def get_tratamiento_by_id(tratamiento_id: str, tenant_id: str) -> Tratamiento :
    return await Tratamiento.find(And(
        Tratamiento.tenant_id == PydanticObjectId(tenant_id),
        Tratamiento.id == PydanticObjectId(tratamiento_id)
    )).first_or_none()

async def update_tratamiento(tratamiento_id: str, data: TratamientoUpdate, tenant_id: str) -> Tratamiento:
    founded_tratamiento = await get_tratamiento_by_id(tratamiento_id, tenant_id);

    if not founded_tratamiento:
        raise raise_not_found('Tratamiento')
    
    founded_tratamiento.nombre=data.nombre
    founded_tratamiento.descripcion=data.descripcion
    founded_tratamiento.image=data.image

    updated = await founded_tratamiento.save()

    return updated

async def delete_tratamiento(tratamiento_id: str, tenant_id: str) -> bool:
    founded = await get_tratamiento_by_id(tratamiento_id, tenant_id)

    if not founded:
        raise raise_not_found('Tratamiento')
    
    await founded.delete()
    return True

def tratamiento_to_out(tratamiento: Tratamiento) -> TratamientoOut:
    tratamiento_dict = tratamiento.model_dump()
    tratamiento_dict['id'] = str(tratamiento.id)
    return TratamientoOut(**tratamiento_dict)