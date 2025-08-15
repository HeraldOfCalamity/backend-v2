from beanie import PydanticObjectId
from beanie.operators import And, RegEx
import pymongo
from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.paciente_entity import PacienteCreate, PacienteOut, PacienteProfileOut, PacienteUpdate
from app.infrastructure.repositories.user_repo import delete_user, get_user_by_id, user_to_out
from app.infrastructure.schemas.paciente import Paciente
from app.infrastructure.schemas.user import User


async def create_paciente(data: PacienteCreate, user_id: str, tenant_id: str) -> Paciente:
    paciente = Paciente.find(Paciente.tenant_id == PydanticObjectId(tenant_id))


    paciente = Paciente(
        user_id=PydanticObjectId(user_id),
        fecha_nacimiento=data.fecha_nacimiento,
        tipo_sangre=data.tipo_sangre,
        tenant_id=PydanticObjectId(tenant_id)
    )

    created = await paciente.insert()
    return created

async def update_paciente(paciente_id: str, data: PacienteUpdate, tenant_id:str):
    paciente = await Paciente.find(And(
        Paciente.tenant_id == PydanticObjectId(tenant_id),
        Paciente.id == PydanticObjectId(paciente_id)
    )).first_or_none()

    if not paciente:
        raise raise_not_found('Paciente')
    
    paciente.tipo_sangre = data.tipo_sangre
    paciente.fecha_nacimiento = data.fecha_nacimiento

    await paciente.save()
    return paciente


async def get_pacientes_by_tenant(tenant_id: str) -> list[Paciente]:
    return await Paciente.find(
        Paciente.tenant_id == PydanticObjectId(tenant_id)
    ).sort([
        (Paciente.createdAt, pymongo.DESCENDING)
    ]).to_list()

async def get_paciente_by_user_id(user_id: str, tenant_id: str) -> Paciente | None:
    return await Paciente.find(And(
        Paciente.tenant_id == PydanticObjectId(tenant_id),
        Paciente.user_id == PydanticObjectId(user_id),
    )).first_or_none()

async def delete_paciente(paciente_id: str, tenant_id: str) -> bool:
    paciente = await Paciente.find(And(
        Paciente.tenant_id == PydanticObjectId(tenant_id),
        Paciente.id == PydanticObjectId(paciente_id)
    )).first_or_none()

    if not paciente:
        raise raise_not_found(f'Paciente {paciente_id}')
    
    user = await get_user_by_id(str(paciente.user_id), tenant_id)

    if not user:
        raise raise_not_found(f'Usuario {str(paciente.user_id)}')

    # await paciente.delete()
    await delete_user(str(user.id), tenant_id)

    return True

async def get_paciente_by_id(paciente_id: str, tenant_id: str) -> Paciente:
    return await Paciente.find(And(
        Paciente.tenant_id == PydanticObjectId(tenant_id),
        Paciente.id == PydanticObjectId(paciente_id)
    )).first_or_none()

# async def filter_paciente_by(criteria: FilterPaciente, tenant_id: str) -> list[Paciente]:
#     query = Paciente.find(Paciente.tenant_id == PydanticObjectId(tenant_id))

#     if criteria.ci and criteria.ci.strip():
#         query = query.find(RegEx(Paciente.ci, f'^{criteria.ci.strip()}',options='i'))

#     if criteria.nombre and criteria.nombre.strip():
#         query = query.find(RegEx(Paciente.nombre, f'^{criteria.nombre.strip()}',options='i'))

#     if criteria.apellido and criteria.apellido.strip():
#         query = query.find(RegEx(Paciente.apellido, f'^{criteria.apellido.strip()}',options='i'))        

#     query = query.find(Paciente.deletedAt == None)
#     return await query.to_list()


async def get_pacientes_with_user(tenant_id: str) -> list[PacienteProfileOut]:
    pacientes = await get_pacientes_by_tenant(tenant_id)
    result = []

    for p in pacientes:
        usuario = await get_user_by_id(str(p.user_id), tenant_id)
        result.append(PacienteProfileOut(
            paciente=paciente_to_out(p),
            user=user_to_out(usuario) if usuario else None
        ))

    return result

def paciente_to_out(paciente: Paciente) -> PacienteOut:
    dict_paciente = paciente.model_dump()
    dict_paciente['id'] = str(paciente.id)
    dict_paciente['user_id'] = str(paciente.user_id)

    return PacienteOut(**dict_paciente)