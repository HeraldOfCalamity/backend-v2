from fastapi import APIRouter, Depends

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.user_entity import UserBase, UserOut
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.repositories.user_repo import create_user, get_users_by_tenant, user_to_out


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

