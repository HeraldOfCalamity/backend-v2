import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.core.security import get_password_hash
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.role import Role
from app.infrastructure.schemas.user import User


ADMIN_NAME = 'administrador'
ADMIN_EMAIL = 'leguinov_cb@est.emi.edu.bo'
ADMIN_PASSWORD = 'admin123'

async def get_tenant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id

async def seed_admin_user():
    await init_db()
    tenant_id = await get_tenant_id()

    existing = await User.find_one({
        "email": ADMIN_EMAIL,
        "tenant_id": tenant_id
    })

    if existing:
        print('Ya existe un usuario admin para este tenant, eliminando ...')
        await existing.delete()
    
    role = await Role.find(Role.name == 'admin').find(Role.tenant_id == tenant_id).first_or_none()
    if not role:
        print('Rol "admin" no encontrado')
        return
    
    hashed_password = get_password_hash(ADMIN_PASSWORD)
    admin_user = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password=hashed_password,
        role=role.id,
        tenant_id=tenant_id,
        isActive=True,
        isVerified=True
    )

    inserted = await admin_user.insert()
    print(f'Usuario administrador creado {inserted.email}')

if __name__ == '__main__':
    asyncio.run(seed_admin_user())