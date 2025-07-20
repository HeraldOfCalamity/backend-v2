
from fastapi import APIRouter, Depends

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.permission_entity import PermissionOut
from app.infrastructure.repositories.permission_repo import get_permission_by_tenant, permission_to_out


router = APIRouter(prefix='/permisos', tags=['Permisos'])

@router.get('/', response_model=list[PermissionOut], dependencies=[Depends(require_permission('read_permissions'))])
async def listar_permisos(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    permisos = await get_permission_by_tenant(tenant_id)
    return [permission_to_out(p) for p in permisos]