from beanie import PydanticObjectId
from app.core.exceptions import raise_not_found
from app.domain.entities.paciente_entity import PacienteCreate, PacienteOut, PacienteUpdate
from app.infrastructure.schemas.paciente import Paciente
from app.infrastructure.schemas.user import User


async def create_paciente(data: PacienteCreate, user_id: str, tenant_id: str) -> Paciente:
    paciente = Paciente(
        user_id=PydanticObjectId(user_id),
        fecha_nacimiento=data.fecha_nacimiento,
        nombre=data.nombre,
        apellido=data.apellido,
        tipo_sangre=data.tipo_sangre,
        telefono=data.telefono,
        tenant_id=PydanticObjectId(tenant_id)
    )

    created = await paciente.insert()
    return created

async def update_paciente(paciente_id: str, data: PacienteUpdate, tenant_id:str):
    paciente = await Paciente.find(Paciente.tenant_id == PydanticObjectId(tenant_id)).find(Paciente.id == PydanticObjectId(paciente_id)).first_or_none()
    if not paciente:
        raise raise_not_found('Paciente')
    
    paciente.nombre = data.nombre
    paciente.apellido = data.apellido
    paciente.tipo_sangre = data.tipo_sangre
    paciente.fecha_nacimiento = data.fecha_nacimiento
    paciente.telefono = data.telefono

    await paciente.save()
    return paciente


async def get_pacientes_by_tenant(tenant_id: str) -> list[Paciente]:
    return await Paciente.find(Paciente.tenant_id == PydanticObjectId(tenant_id)).to_list()

async def get_paciente_by_user_id(user_id: str, tenant_id: str) -> Paciente | None:
    return await Paciente.find(Paciente.user_id == PydanticObjectId(user_id)).find(Paciente.tenant_id == PydanticObjectId(tenant_id)).first_or_none()

async def delete_paciente(paciente_id: str, tenant_id: str) -> bool:
    paciente = await Paciente.find(Paciente.tenant_id == PydanticObjectId(tenant_id)).find(Paciente.id == PydanticObjectId(paciente_id)).first_or_none()

    if not paciente:
        raise raise_not_found(f'Paciente {paciente_id}')
    
    user = await User.find(User.tenant_id == PydanticObjectId(tenant_id)).find(User.id == paciente.user_id).first_or_none()

    if not user:
        raise raise_not_found(f'Usuario {str(paciente.user_id)}')

    await paciente.delete()
    await user.delete()
    return True

def paciente_to_out(paciente: Paciente) -> PacienteOut:
    dict_paciente = paciente.model_dump()
    dict_paciente['id'] = str(paciente.id)
    dict_paciente['user_id'] = str(paciente.user_id)

    return PacienteOut(**dict_paciente)