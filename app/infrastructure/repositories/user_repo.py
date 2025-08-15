from ast import And
from beanie import PydanticObjectId
from beanie.operators import And
import pymongo
from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.core.security import get_password_hash
from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate
from app.infrastructure.repositories.role_repo import get_role_by_id, get_role_by_name
from app.infrastructure.schemas.especialista import Especialista
from app.infrastructure.schemas.paciente import Paciente
from app.infrastructure.schemas.user import User


async def create_user(data: UserBase, tenant_id: str):
    hashed_pw = get_password_hash(data.password)
    role = await get_role_by_name(data.role, tenant_id)

    if not role:
        raise raise_not_found('Rol no encontrado.')
    
    founded_user = None

    founded_user = await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id),
        User.email == data.email
    )).first_or_none()

    if founded_user:
        raise raise_duplicate_entity(f"Usuario con email: {data.email} ya existe")
    
    founded_user = await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id),
        User.ci == data.ci
    )).first_or_none()

    if founded_user:
        raise raise_duplicate_entity(f"Usuario con ci: {data.ci} ya existe")

    founded_user = await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id),
        User.phone == data.phone
    )).first_or_none()

    if founded_user:
        raise raise_duplicate_entity(f"Usuario con telefono: {data.phone} ya existe")


    user = User(
        name=data.name,
        ci=data.ci,
        phone=data.phone,
        lastname=data.lastname,
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
    role_by_id = await get_role_by_id(data.role, tenant_id)

    if not role and not role_by_id:
        raise raise_not_found("Role")

    user.name=data.name
    user.ci=data.ci
    user.phone=data.phone
    user.lastname=data.lastname
    user.email = data.email
    user.role = role.id if role else role_by_id.id
    user.isActive = data.isActive
    user.isVerified = data.isVerified

    await user.save()
    return user

async def delete_user(user_id: str, tenant_id: str) -> bool:
    user = await User.find(User.tenant_id == PydanticObjectId(tenant_id)).find(User.id == PydanticObjectId(user_id)).first_or_none()
    if not user:
        raise raise_not_found('User')
    
    role = await get_role_by_id(user.role, tenant_id)
    
    if not role:
        raise raise_not_found('Rol no encontrado')
    
    user.isActive=False
    await user.save()
    # await user.delete()
    # await perfil.delete()

    return True


async def get_users_by_tenant(tenant_id: str):
    admin_role = await get_role_by_name('admin', tenant_id)
    return await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id)),
        User.role != admin_role.id
    ).sort([
        (User.createdAt, pymongo.DESCENDING)
    ]).to_list()

async def get_user_by_id(user_id: str, tenant_id: str) -> User | None:
    user = await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id),
        User.id == PydanticObjectId(user_id)
    )).first_or_none()

    return user

async def get_admin_user(tenant_id: str) -> User:
    admin_role = await get_role_by_name('admin', tenant_id)
    return await User.find(And(
        User.tenant_id == PydanticObjectId(tenant_id),
        User.role == admin_role.id
    )).first_or_none()


def user_to_out(user: User):
    user_dict = user.model_dump()
    user_dict['id'] = str(user.id)
    user_dict['role'] = str(user.role)
    return UserOut(**user_dict)