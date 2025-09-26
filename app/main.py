from fastapi.staticfiles import StaticFiles
from app.application.websockets.routes import ws_router
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.db import init_db
from app.core.exceptions import internal_errror_handler
from app.presentation.api.v1 import auth_routes, cita_routes, especialidad_routes, especialista_routes, historial_routes, officeConfig_routes, paciente_routes, permission_routes, role_routes, tratamiento_routes, user_routes, reportes_citas_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print('\nConectando a la base de datos\n')
    yield
    print('\nApp detenida\n')

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.add_exception_handler(Exception, internal_errror_handler)

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

app.mount('/static', StaticFiles(directory='static'))