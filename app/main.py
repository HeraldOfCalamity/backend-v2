# app/main.py
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.db import init_db
from app.core.exceptions import internal_errror_handler
from app.core.config import settings
from app.presentation.api.v1 import (
    auth_routes,
    cita_routes,
    especialidad_routes,
    especialista_routes,
    historial_routes,
    officeConfig_routes,
    paciente_routes,
    permission_routes,
    role_routes,
    tratamiento_routes,
    user_routes,
    reportes_citas_routes,
)
from app.application.websockets.routes import ws_router

# 👇 importante: orquestador del seed
from app.scripts.seed_all import seed_all

# Asegura que INFO se imprima (uvicorn maneja logger propio,
# pero así nos garantizamos ver los logger.info/exception del seed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: conecta DB y levanta rutas
    await init_db()
    print("\nConectando a la base de datos\n")

    # Entrega el control a FastAPI (para health check OK)
    yield

    # Post-startup: programa el seed en segundo plano
    try:
        seed_on = settings.SEED_ON_START == "1"
        seed_disabled = settings.DISABLE_SEED_ON_START == "1"
        print('entra aqui')
        print('seedon',seed_on)
        print('entra aqui',seed_disabled)
        if seed_on and not seed_disabled:
            print('entra aqui')
            logger.info("Programando seed_all() en segundo plano…")
            asyncio.create_task(seed_all())
        else:
            logger.info(
                "Seed deshabilitado (SEED_ON_START=%s, DISABLE_SEED_ON_START=%s)",
                os.getenv("SEED_ON_START", "1"),
                os.getenv("DISABLE_SEED_ON_START", "0"),
            )
    except Exception as e:
        logger.exception("No se pudo programar seed_all(): %s", e)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, internal_errror_handler)

# Routers
app.include_router(auth_routes.router)
app.include_router(especialidad_routes.router)
app.include_router(especialista_routes.router)
app.include_router(paciente_routes.router)
app.include_router(role_routes.router)
app.include_router(permission_routes.router)
app.include_router(user_routes.router)
app.include_router(officeConfig_routes.router)
app.include_router(cita_routes.router)
app.include_router(tratamiento_routes.router)
app.include_router(historial_routes.router)
app.include_router(ws_router)
app.include_router(reportes_citas_routes.router)

# Static
app.mount("/static", StaticFiles(directory="static"))
