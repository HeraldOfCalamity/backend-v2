import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.role import Role

async def get_tenant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id

async def seed_paciente_role():
    await init_db()
    tenant_id = await get_tenant_id()

    existing = await Role.find_one({
        "name": "paciente",
        "tenant_id": tenant_id
    })

    if existing:
        print('Rol paciente ya existe, eliminando...')
        await existing.delete()

    paciente_role = Role(
        name='paciente',
        description='Rol para pacientes, sin permisos iniciales',
        tenant_id=tenant_id,
        permissions=[]
    )

    inserted = await paciente_role.insert()
    print(f'Rol {inserted.name} creado sin permisos.')

if __name__ == "__main__":
    asyncio.run(seed_paciente_role())