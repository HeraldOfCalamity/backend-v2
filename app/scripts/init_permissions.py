import asyncio
# from pathlib import Path
# import sys
from beanie import PydanticObjectId

# sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.db import init_db
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.schemas.permission import Permission


PERMISSIONS = [
    {"name": "create_users", "description": "Crear nuevos usuarios"},
    {"name": "update_users", "description": "Actualizar usuarios usuarios"},
    {"name": "read_users", "description": "Listar usuarios"},
    {"name": "delete_users", "description": "Eliminar usuarios"},

    {"name": "create_patients", "description": "Crear nuevos pacientes"},
    {"name": "update_patients", "description": "Actualizar pacientes"},
    {"name": "read_patients", "description": "Listar pacientes"},
    {"name": "delete_patients", "description": "Eliminar pacientes"},

    {"name": "read_roles", "description": "Asignar roles"},
    {"name": "update_roles", "description": "Asignar roles"},
    {"name": "create_roles", "description": "Crear roles"},
    {"name": "delete_roles", "description": "Eliminar roles"},

    {"name": "create_specialties", "description": "Crear especialidades"},
    {"name": "update_specialties", "description": "Editar especialidades"},
    {"name": "read_specialties", "description": "Listar especialidades"},
    {"name": "delete_specialties", "description": "Eliminar especialidades"},
    
    {"name": "create_especialist", "description": "Crear especialidades"},
    {"name": "update_especialist", "description": "Editar especialidades"},
    {"name": "read_especialists", "description": "Listar especialidades"},
    {"name": "delete_especialists", "description": "Eliminar especialidades"},

    {"name": "read_permissions", "description": "Listar permisos"},

    {"name": "read_office_config", "description": "Listar permisos"},
    {"name": "update_office_config", "description": "Actualizar parametros"},

    {"name": "create_appointments", "description": "Crear citas"},
    {"name": "read_appointments", "description": "Listar citas"},
    {"name": "cancel_appointments", "description": "Cancelar citas"},
    {"name": "confirm_appointments", "description": "Confirmar citas"},

    {"name": "create_tratamientos", "description": "Crear Tratamientos"},
    {"name": "update_tratamientos", "description": "Editar Tratamientos"},
    {"name": "delete_tratamientos", "description": "Eliminar Tratamientos"},


]
async def get_tennant_id() -> PydanticObjectId:
    office = await get_benedetta_office()
    return office.id


async def seed_permissions():
    await init_db()
    tenant_id = await get_tennant_id()

    for p in PERMISSIONS:
        exists = await Permission.find_one({
            "name": p["name"],
            "tenant_id": tenant_id
        })

        if not exists:
            perm = Permission(**p, tenant_id=tenant_id)
            inserted = await perm.insert()
            print(f'Insertado permiso {inserted.name}')
        else:
            print(f'Ya esiste el permiso {exists.name}')

if __name__ == "__main__":
    asyncio.run(seed_permissions())