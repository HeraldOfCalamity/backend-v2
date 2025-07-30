import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.estadoCita import EstadoCita

ESTADOS = [
    { "estado_id": 0, "nombre": "pendiente", "descripcion": "Esperando confirmación" },
    { "estado_id": 1, "nombre": "confirmada", "descripcion": "Confirmada por el especialista" },
    { "estado_id": 2, "nombre": "cancelada", "descripcion": "Cancelada por paciente o especialista" },
    { "estado_id": 3, "nombre": "rechazada", "descripcion": "Rechazada por el especialista" },
    { "estado_id": 4, "nombre": "finalizada", "descripcion": "La cita ya se atendió" }
]
async def get_tennant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id


async def seed_estados_cita():
    await init_db()
    tenant_id = await get_tennant_id()

    for e in ESTADOS:
        exists = await EstadoCita.find_one({
            "nombre": e["nombre"],
            "tenant_id": tenant_id
        })

        if not exists:
            estado = EstadoCita(**e, tenant_id=tenant_id)
            inserted = await estado.insert()
            print(f'Insertado estado {inserted.nombre}')
        else:
            print(f'Ya esiste el estado {exists.nombre}')

if __name__ == "__main__":
    asyncio.run(seed_estados_cita())