import asyncio
from app.core.db import init_db
from app.infrastructure.schemas.cita import Cita
from app.infrastructure.repositories.paciente_repo import get_paciente_profile_by_id
from app.infrastructure.repositories.especialista_repo import get_especialista_profile_by_id

async def fix_cita_names():
    await init_db()
    # Busca todas las citas donde los nombres estén vacíos o nulos
    citas = await Cita.find(
        {
            "$or": [
                {"paciente_name": None},
                {"paciente_name": ""},
                {"especialista_name": None},
                {"especialista_name": ""}
            ]
        }
    ).to_list()

    print(f"Total citas a actualizar: {len(citas)}")

    for cita in citas:
        updated = False

        # Actualiza paciente_name si falta
        if not cita.paciente_name:
            paciente = await get_paciente_profile_by_id(str(cita.paciente_id), str(cita.tenant_id))
            if paciente:
                cita.paciente_name = f"{paciente.user.name} {paciente.user.lastname}"
                updated = True

        # Actualiza especialista_name si falta
        if not cita.especialista_name:
            especialista = await get_especialista_profile_by_id(str(cita.especialista_id), str(cita.tenant_id))
            if especialista:
                cita.especialista_name = f"{especialista.user.name} {especialista.user.lastname}"
                updated = True

        if updated:
            await cita.save()
            print(f"Actualizada cita {cita.id}: paciente_name={cita.paciente_name}, especialista_name={cita.especialista_name}")

if __name__ == "__main__":
    asyncio.run(fix_cita_names())