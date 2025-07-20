from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.especialista_entity import EspecialistaCreate, EspecialistaCreateWithUser, EspecialistaOut, EspecialistaUpdateWithUser
from app.infrastructure.repositories.especialista_repo import create_especialista, delete_especialista, especialista_to_out, get_especialista_by_user_id, get_especialistas_by_tenant, update_especialista
from app.infrastructure.repositories.user_repo import create_user, update_user


router = APIRouter(prefix='/especialistas', tags=['Especialistas'])

@router.post('/', response_model=EspecialistaOut, dependencies=[Depends(require_permission('create_especialists'))])
async def registrar_especialista(data: EspecialistaCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    created = await create_especialista(data, user_id=str(user.id), tenant_id=tenant_id)
    return especialista_to_out(created)

@router.post('/admin', response_model=EspecialistaOut, dependencies=[
    Depends(require_permission('create_users')),
    Depends(require_permission('create_especialists'))
])
async def admin_crea_especialista(payload: EspecialistaCreateWithUser, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    new_user = await create_user(payload.user, tenant_id)
    created = await create_especialista(payload.especialista, user_id=str(new_user.id), tenant_id=tenant_id)
    return especialista_to_out(created)

@router.get('/{user_id}', response_model=EspecialistaOut, dependencies=[Depends(require_permission('read_especialists'))])
async def obtener_especialista_by_user_id(user_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    especialista = await get_especialista_by_user_id(user_id, tenant_id);
    return especialista_to_out(especialista)

@router.get('/', response_model=list[EspecialistaOut], dependencies=[Depends(require_permission('read_especialists'))])
async def listar_especialistas(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    especialistas = await get_especialistas_by_tenant(tenant_id)
    return [especialista_to_out(e) for e in especialistas]

@router.delete('/{especialista_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[
    Depends(require_permission('delete_users')),
    Depends(require_permission('delete_especialists'))
])
async def eliminar_especialista(especialista_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_especialista(especialista_id, tenant_id)
    return None

@router.put('/admin/{especialista_id}', response_model=EspecialistaOut, dependencies=[
    Depends(require_permission('update_users')),
    Depends(require_permission('update_especialists')),
])
async def admin_edita_especialista(especialista_id: str, payload: EspecialistaUpdateWithUser, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    especialista = await update_especialista(especialista_id, payload.especialista, tenant_id)
    usuario = await update_user(str(especialista.user_id), payload.user,tenant_id)
    return especialista_to_out(especialista)