import asyncio
from app.core.db import init_db
from app.infrastructure.schemas.office import Office

OFFICE_DATA = {
    "name": "Benedetta Bellezza",
    "email": "benedetta.email@gmail.com"
}

async def seed_office():
    await init_db()
    exists = await Office.find_one({"email": OFFICE_DATA["email"]})
    if not exists:
        office = Office(**OFFICE_DATA)
        await office.insert()
        print(f'Oficina creada: {office.name} ({office.email})')
    else:
        print(f'Ya existe la oficina con email: {OFFICE_DATA["email"]}')

if __name__ == "__main__":
    asyncio.run(seed_office())