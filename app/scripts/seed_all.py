# app/scripts/seed_all.py
import asyncio
import logging

# Usa el logger de uvicorn para que aparezca en consola incluso con --log-level info
LOGGER = logging.getLogger("uvicorn.error")

# IMPORTA TUS SEEDS
# Ajusta las rutas si tus archivos init_* están en otra carpeta.
# Aquí asumo que están en app/ a la par de main.py (como mostraste).
from app.scripts.init_office import seed_office
from app.scripts.init_permissions import seed_permissions
from app.scripts.init_admin_role import seed_admin_role
from app.scripts.init_paciente_role import seed_paciente_role
from app.scripts.init_especialista_role import seed_especialista_role
from app.scripts.init_office_config import seed_office_config
from app.scripts.init_estados_cita import seed_estados_cita
from app.scripts.init_admin_user import seed_admin_user


async def seed_all() -> None:
    print("=== [SEED] Iniciando siembra de datos base ===")
    LOGGER.info("=== [SEED] Iniciando siembra de datos base ===")

    steps = [
        ("Office", seed_office),
        ("Permissions", seed_permissions),
        ("Admin role", seed_admin_role),
        ("Paciente role", seed_paciente_role),
        ("Especialista role", seed_especialista_role),
        ("Office config", seed_office_config),
        ("Estados cita", seed_estados_cita),
        ("Admin user", seed_admin_user),
    ]

    for name, fn in steps:
        try:
            print(f"[SEED] → {name}")
            LOGGER.info("[SEED] → %s", name)
            await fn()
            print(f"[SEED] ✓ OK: {name}")
            LOGGER.info("[SEED] ✓ OK: %s", name)
        except Exception as e:
            # Loguea y sigue con los demás pasos
            print(f"[SEED] ✗ Falló {name}: {e!r}")
            LOGGER.exception("[SEED] ✗ Falló %s: %s", name, e)

    print("=== [SEED] Finalizado ===")
    LOGGER.info("=== [SEED] Finalizado ===")


if __name__ == "__main__":
    asyncio.run(seed_all())
