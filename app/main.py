# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.application.services.reminder_service import reminder_scheduler_loop
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
    reminders_task = asyncio.create_task(reminder_scheduler_loop())
    try:
        yield
    finally:
        reminders_task.cancel()
        try:
            await reminders_task
        except asyncio.CancelledError:
            pass
    

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
