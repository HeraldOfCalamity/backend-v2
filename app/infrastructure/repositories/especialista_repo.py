from re import M
from beanie import PydanticObjectId
from beanie.operators import And
import pymongo
from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.especialista_entity import EspecialistaCreate, EspecialistaOut, EspecialistaProfileOut, EspecialistaUpdate
from app.infrastructure.repositories.user_repo import get_user_by_id, user_to_out
from app.infrastructure.schemas.especialista import Especialista
from app.infrastructure.schemas.user import User

async def create_especialista(data: EspecialistaCreate, user_id: str, tenant_id: str) -> Especialista:    
    especialista = Especialista(
        user_id=PydanticObjectId(user_id),
        especialidades=[PydanticObjectId(eid) for eid in data.especialidad_ids],
        informacion=data.informacion if data.informacion else None,
        image=data.image if data.image else None,
        disponibilidades=[disp.model_dump() for disp in data.disponibilidades],
        tenant_id=tenant_id,
    )
    created = await especialista.insert()    
    return created

async def update_especialista(especialista_id: str, data: EspecialistaUpdate, tenant_id:str):
    especialista = await Especialista.find(Especialista.tenant_id == PydanticObjectId(tenant_id)).find(Especialista.id == PydanticObjectId(especialista_id)).first_or_none()
    if not especialista:
        raise raise_not_found('Especialista')
    
    especialista.especialidades = [PydanticObjectId(eId) for eId in data.especialidad_ids]
    especialista.disponibilidades = [disp.model_dump() for disp in data.disponibilidades]
    especialista.image = data.image if data.image else None
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
   


def especialista_to_out(especialista: Especialista) -> EspecialistaOut:
    especialista_dict = especialista.model_dump()
    especialista_dict['user_id'] = str(especialista.user_id)
    especialista_dict['id'] = str(especialista.id)
    especialista_dict['especialidad_ids'] = [str(eId) for eId in especialista.especialidades]
    
    return EspecialistaOut(**especialista_dict)