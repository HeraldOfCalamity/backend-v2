from beanie import PydanticObjectId
from beanie.operators import And
from app.core.exceptions import raise_not_found
from app.domain.entities.especialista_entity import EspecialistaCreate, EspecialistaOut, EspecialistaUpdate
from app.infrastructure.schemas.especialista import Especialista
from app.infrastructure.schemas.user import User

async def create_especialista(data: EspecialistaCreate, user_id: str, tenant_id: str) -> Especialista:
    especialista = Especialista(
        user_id=PydanticObjectId(user_id),
        nombre=data.nombre,
        apellido=data.apellido,
        especialidades=[PydanticObjectId(eid) for eid in data.especialidad_ids],
        matricula_profesional=data.matricula_profesional,
        telefono=data.telefono,
        disponibilidades=[disp.model_dump() for disp in data.disponibilidades],
        tenant_id=tenant_id
    )

    created = await especialista.insert()
    return created

async def update_especialista(especialista_id: str, data: EspecialistaUpdate, tenant_id:str):
    especialista = await Especialista.find(Especialista.tenant_id == PydanticObjectId(tenant_id)).find(Especialista.id == PydanticObjectId(especialista_id)).first_or_none()
    if not especialista:
        raise raise_not_found('Especialista')
    
    especialista.nombre = data.nombre
    especialista.apellido = data.apellido
    especialista.matricula_profesional = data.matricula_profesional
    especialista.telefono = data.telefono
    especialista.especialidades = [PydanticObjectId(eId) for eId in data.especialidad_ids]
    especialista.disponibilidades = [disp.model_dump() for disp in data.disponibilidades]

    await especialista.save()
    return especialista

async def get_especialistas_by_tenant(tenant_id: str) -> list[Especialista]:
    return await Especialista.find(Especialista.tenant_id == PydanticObjectId(tenant_id)).to_list()

async def get_especialista_by_user_id(user_id: str, tenant_id: str) -> Especialista:
    return await Especialista.find(Especialista.user_id == PydanticObjectId(user_id)).find(Especialista.tenant_id == PydanticObjectId(tenant_id)).first_or_none()

async def delete_especialista(especialista_id: str, tenant_id: str) -> bool:
    especialista = await Especialista.find(Especialista.tenant_id == PydanticObjectId(tenant_id)).find(Especialista.id == PydanticObjectId(especialista_id)).first_or_none()

    if not especialista:
        raise raise_not_found(f'Paciente {especialista_id}')
    
    user = await User.find(User.tenant_id == PydanticObjectId(tenant_id)).find(User.id == especialista.user_id).first_or_none()

    if not user:
        raise raise_not_found(f'Usuario {str(especialista.user_id)}')

    await especialista.delete()
    await user.delete()
    return True

async def get_especialista_by_especialidad_id(especialidad_id: str, tenant_id: str) -> list[Especialista]:
    especialistas = await Especialista.find({
        "tenant_id": PydanticObjectId(tenant_id),
        "especialidades": PydanticObjectId(especialidad_id)
    }).to_list()
    return especialistas

async def get_especialista_by_id(especialista_id: str, tenant_id: str) -> Especialista:
    return await Especialista.find(And(
        Especialista.tenant_id == PydanticObjectId(tenant_id),
        Especialista.id == PydanticObjectId(especialista_id)
    )).first_or_none()

def especialista_to_out(especialista: Especialista):
    especialista_dict = especialista.model_dump()
    especialista_dict['user_id'] = str(especialista.user_id)
    especialista_dict['id'] = str(especialista.id)
    especialista_dict['especialidad_ids'] = [str(eId) for eId in especialista.especialidades]
    
    return EspecialistaOut(**especialista_dict)