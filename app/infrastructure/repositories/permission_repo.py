from beanie import PydanticObjectId
from app.domain.entities.permission_entity import PermissionOut
from app.infrastructure.schemas.permission import Permission


async def get_permission_by_id_list(ids: list[str], tenant_id: str) -> list[Permission]:
    ids = [PydanticObjectId(id) for id in ids]
    return await Permission.find({
        "tenant_id": PydanticObjectId(tenant_id),
        "_id": {"$in": ids}
    }).to_list()

async def get_permission_by_name_list(names: list[str], tenant_id: str) -> list[Permission]:
    return await Permission.find({
        "tenant_id": PydanticObjectId(tenant_id),
        "name": {"$in": names}
    }).to_list()

async def get_permission_by_tenant(tenant_id: str):
    return await Permission.find(Permission.tenant_id == PydanticObjectId(tenant_id)).to_list()

def permission_to_out(permission: Permission) -> PermissionOut:
    permission_dict = permission.model_dump()
    permission_dict['id'] = str(permission.id)
    return PermissionOut(**permission_dict)
