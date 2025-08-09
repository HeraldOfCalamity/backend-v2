import asyncio
from beanie import PydanticObjectId

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.officeConfig import OfficeConfig

OFFICE_CONFIGS = [
    {"name":"duracion_cita_minutos", "value":'45'},
    {"name":"confirmacion_automatica", "value":'0'},
    {"name":"confirmacion_automatica_admin", "value":'1'},
]

async def get_tenant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id

async def seed_office_config():
    await init_db()
    tenant_id = await get_tenant_id()


    for oc in OFFICE_CONFIGS:
        
        existing = await OfficeConfig.find_one({        
            "tenant_id": tenant_id,
            "name": oc['name']
        })

        if existing:
            print(f'Ya existe la configuracion {existing.name} en este tenant...')
            await existing.delete()
        
        config = OfficeConfig(**oc, tenant_id=tenant_id);

        inserted = await config.insert()
        print(f'Configuracion {inserted.name} creada.')

if __name__ == "__main__":
    asyncio.run(seed_office_config())