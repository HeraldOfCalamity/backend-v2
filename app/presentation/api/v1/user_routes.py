from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.repositories.user_repo import create_user, delete_user, get_users_by_tenant, update_user, user_to_out


router = APIRouter(prefix='/users', tags=['Usuarios'])

@router.get('/', response_model=list[UserOut], dependencies=[Depends(require_permission('read_users'))])
async def listar_usuarios(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    usuarios = await get_users_by_tenant(tenant_id)
    return [user_to_out(u) for u in usuarios]

@router.post('/', response_model=UserOut)
async def crear_usuario(payload: UserBase):
    office = await get_benedetta_office()
    user = await create_user(payload, str(office.id))
    return user_to_out(user)

@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission('delete_users'))])
async def eliminar_usuario(user_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_user(user_id, tenant_id);
    return None

@router.put('/{user_id}', response_model=UserOut, dependencies=[Depends(require_permission('update_users'))])
async def actualizar_usuario(user_id: str, payload: UserUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    updated = await update_user(user_id, payload, tenant_id)
    return user_to_out(updated)


