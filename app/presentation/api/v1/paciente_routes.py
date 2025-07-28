from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.exceptions import raise_not_found
from app.core.security import get_current_user, require_permission
from app.domain.entities.paciente_entity import PacienteAutoCreate, PacienteCreate, PacienteCreateWithUser, PacienteOut, PacienteProfileOut, PacienteUpdate, PacienteUpdateWithUser
from app.infrastructure.repositories.paciente_repo import create_paciente, delete_paciente, get_paciente_by_user_id, get_pacientes_by_tenant, paciente_to_out, update_paciente
from app.infrastructure.repositories.user_repo import create_user, update_user, user_to_out
from app.infrastructure.schemas.user import User


router = APIRouter(prefix='/pacientes', tags=['Pacientes'])

# region PERFIL
@router.post('/perfil', response_model=PacienteOut, dependencies=[
    Depends(require_permission('create_patients')),
    Depends(require_permission('create_users')),
])
async def crear_perfil_paciente(payload: PacienteCreateWithUser, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    new_user = await create_user(payload.user, tenant_id)
    created = await create_paciente(payload.paciente, user_id=str(new_user.id), tenant_id=tenant_id)
    return paciente_to_out(created)

@router.put('/perfil/{paciente_id}', response_model=PacienteOut, dependencies=[
    Depends(require_permission('update_users')),
    Depends(require_permission('update_patients')),
])
async def editar_perfil_paciente(paciente_id: str, payload: PacienteUpdateWithUser, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    paciente = await update_paciente(paciente_id, payload.paciente, tenant_id)
    usuario = await update_user(str(paciente.user_id), payload.user,tenant_id)
    return paciente_to_out(paciente)
        
@router.get('/perfil', response_model=PacienteProfileOut, dependencies=[Depends(require_permission('read_patients'))])
async def obtener_paciente_perfil(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    paciente = await get_paciente_by_user_id(str(user.id), tenant_id)
    return PacienteProfileOut(
        paciente=paciente_to_out(paciente) if paciente else None,
        user=user_to_out(user)
    )
# endregion

@router.post('/', response_model=PacienteOut, dependencies=[Depends(require_permission('create_patients'))])
async def registrar_paciente(data: PacienteAutoCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    created = await create_paciente(data, user_id=str(data.user_id), tenant_id=tenant_id)
    return paciente_to_out(created)

@router.put('/{paciente_id}', response_model=PacienteOut, dependencies=[Depends(require_permission('update_patients'))])
async def editar_paciente(paciente_id: str, payload: PacienteUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    updated = await update_paciente(paciente_id, payload, tenant_id)
    return paciente_to_out(updated)

@router.get('/', response_model=list[PacienteOut], dependencies=[Depends(require_permission('read_patients'))])
async def listar_pacientes(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    pacientes = await get_pacientes_by_tenant(tenant_id)
    return [paciente_to_out(p) for p in pacientes]


@router.get('/{user_id}', response_model=PacienteOut, dependencies=[Depends(require_permission('read_patients'))])
async def obtener_paciente_by_user_id(user_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    paciente = await get_paciente_by_user_id(user_id, tenant_id)
    if not paciente:
        # return None
        raise raise_not_found(f'Paciente con id de usuario: {user_id}')
    return paciente_to_out(paciente)

@router.delete('/{paciente_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[
    Depends(require_permission('delete_users')),
    Depends(require_permission('delete_patients'))])
async def eliminar_paciente(paciente_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_paciente(paciente_id, tenant_id)
    return None