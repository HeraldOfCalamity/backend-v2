from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.role_entity import RoleCreate, RoleOut, RoleUpdate
from app.infrastructure.repositories.role_repo import create_role, delete_role, get_roles_by_tenant, role_to_out, update_role


router = APIRouter(prefix='/roles', tags=['Roles'])

@router.post('/', response_model=RoleOut, dependencies=[Depends(require_permission('create_roles'))])
async def crear_rol(data:RoleCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    created = await create_role(data, tenant_id)
    return await role_to_out(created)

@router.get('/', response_model=list[RoleOut], dependencies=[Depends(require_permission('read_roles'))])
async def listar_roles(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    roles = await get_roles_by_tenant(tenant_id)
    return [await role_to_out(r) for r in roles]

@router.delete('/{role_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission('delete_roles'))])
async def eliminar_rol(role_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_role(role_id, tenant_id)
    return None

@router.put('/{role_id}', response_model=RoleOut, dependencies=[Depends(require_permission('update_roles'))])
async def editar_rol(role_id: str, data: RoleUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    role = await update_role(role_id, data, tenant_id)
    return await role_to_out(role)