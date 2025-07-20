from beanie import PydanticObjectId
from app.core.exceptions import raise_not_found
from app.domain.entities.role_entity import RoleCreate, RoleOut, RoleUpdate
from app.infrastructure.repositories.permission_repo import get_permission_by_name_list, get_permission_by_id_list
from app.infrastructure.schemas.role import Role
from app.domain.entities.permission_entity import PermissionOut



async def get_role_by_name(name: str, tenant_id: str) -> Role:
    return await Role.find_one(Role.name == name).find_one(Role.tenant_id == PydanticObjectId(tenant_id))

async def create_role(data: RoleCreate, tenant_id: str) -> Role:
    permissions = await get_permission_by_id_list(data.permissions, tenant_id)
    if len(permissions) == 0 or len(permissions) != len(data.permissions):
        raise raise_not_found(f'Rol con id {[p for p in data.permissions if p not in [per.name for per in permissions]]}')
    
    permission_ids = [PydanticObjectId(p.id) for p in permissions]
    role = Role(
        name=data.name,
        description=data.description,
        tenant_id=tenant_id,
        permissions=permission_ids
    )

    created = await role.insert()
    return created;

async def get_roles_by_tenant(tenant_id: str) -> list[Role]:
    admin_role = await get_role_by_name('admin', tenant_id)
    return await Role.find(Role.tenant_id == PydanticObjectId(tenant_id)).find(Role.id != admin_role.id).to_list()
    
async def update_role(role_id: str, data: RoleUpdate, tennant_id: str) -> Role:
    role = await Role.find(Role.tenant_id == PydanticObjectId(tennant_id)).find(Role.id == PydanticObjectId(role_id)).first_or_none()
    if not role:
        raise raise_not_found('Role')
    
    role.name = data.name
    role.description = data.description
    role.permissions = [PydanticObjectId(p) for p in data.permissions]
    await role.save()
    return role

async def delete_role(role_id: str, tenant_id: str) -> bool:
    role = await Role.find(Role.tenant_id == PydanticObjectId(tenant_id)).find(Role.id == PydanticObjectId(role_id)).first_or_none()
    if not role:
        raise raise_not_found(f'Rol {role_id}')
    
    await role.delete()
    return True

async def role_to_out(role: Role) -> RoleOut:
    role_dict = role.model_dump()
    role_dict['id'] = str(role.id)
    role_dict['permissions'] = [str(p) for p in role.permissions]

    # permissions = await get_permission_by_id_list(role.permissions, str(role.tenant_id))
    # permission_dicts = [p.model_dump() for p in permissions]
    # for i in range(len(permission_dicts)):
    #     permission_dicts[i]['id'] = str(permissions[i].id)

    # role_dict['permissions'] = [PermissionOut(**p) for p in permission_dicts]
    return RoleOut(**role_dict)