import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.role import Role

async def get_tenant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id

async def seed_especialista_role():
    await init_db()
    tenant_id = await get_tenant_id()

    existing = await Role.find_one({
        "name": "especialista",
        "tenant_id": tenant_id
    })

    if existing:
        print('Rol especialista ya existe, eliminando...')
        await existing.delete()

    especialista_role = Role(
        name='especialista',
        description='Rol para especialistas, sin permisos iniciales',
        tenant_id=tenant_id,
        permissions=[]
    )

    inserted = await especialista_role.insert()
    print(f'Rol {inserted.name} creado sin permisos.')

if __name__ == "__main__":
    asyncio.run(seed_especialista_role())