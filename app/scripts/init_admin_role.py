import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.permission import Permission
from app.infrastructure.schemas.role import Role


async def get_tenant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id

async def seed_admin_role():
    await init_db()
    tenant_id = await get_tenant_id()

    existing = await Role.find_one({
        "name": "admin",
        "tenant_id": tenant_id
    })

    if existing:
        print('Rol admin ya existe, eliminando...')
        await existing.delete()        
    
    permissions = await Permission.find(Permission.tenant_id == tenant_id).to_list()
    permission_ids = [p.id for p in permissions]

    admin_role = Role(
        name='admin',
        description='Rol con todos los permisos del sistema',
        tenant_id=tenant_id,
        permissions=permission_ids
    )

    inserted = await admin_role.insert()
    print(f'Rol {inserted.name} creado con {len(inserted.permissions)} permisos.')

if __name__ == "__main__":
    asyncio.run(seed_admin_role())