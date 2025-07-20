from beanie import PydanticObjectId
from app.core.exceptions import raise_not_found
from app.core.security import get_password_hash
from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate
from app.infrastructure.repositories.role_repo import get_role_by_name
from app.infrastructure.schemas.user import User


async def create_user(data: UserBase, tenant_id: str):
    hashed_pw = get_password_hash(data.password)
    role = await get_role_by_name(data.role, tenant_id)

    if not role:
        raise raise_not_found('Rol no encontrado.')

    user = User(
        name=data.username,
        email=data.email,
        tenant_id=tenant_id,
        password=hashed_pw,
        role=PydanticObjectId(role.id),
        isActive=True,
        isVerified=False
    )

    created = await user.insert()

    return created

async def update_user(user_id: str, data: UserUpdate, tenant_id:str) ->  User:
    user = await User.find(User.tenant_id == PydanticObjectId(tenant_id)).find(User.id == PydanticObjectId(user_id)).first_or_none()
    if not user:
        raise raise_not_found('User')
    
    role = await get_role_by_name(data.role.lower(), tenant_id)
    if not role:
        raise raise_not_found("Role")

    user.name = data.username
    user.email = data.email
    user.role = role.id

    await user.save()
    return user



async def get_users_by_tenant(tenant_id: str):
    admin_role = await get_role_by_name('admin', tenant_id)
    return await User.find(User.tenant_id == PydanticObjectId(tenant_id)).find(User.role != admin_role.id).to_list()

def user_to_out(user: User):
    user_dict = user.model_dump()
    user_dict['id'] = str(user.id)
    user_dict['role'] = str(user.role)
    return UserOut(**user_dict, username=user.name)