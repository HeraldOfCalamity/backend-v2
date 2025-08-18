from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.infrastructure.schemas.cita import Cita
from app.infrastructure.schemas.especialidad import Especialidad
from app.infrastructure.schemas.especialista import Especialista
from app.infrastructure.schemas.estadoCita import EstadoCita
from app.infrastructure.schemas.office import Office
from app.infrastructure.schemas.officeConfig import OfficeConfig
from app.infrastructure.schemas.paciente import Paciente
from app.infrastructure.schemas.permission import Permission
from app.infrastructure.schemas.role import Role
from app.infrastructure.schemas.tratamiento import Tratamiento
from app.infrastructure.schemas.user import User

client = AsyncIOMotorClient(settings.MONGO_URI)
database = client[settings.DB_NAME]

async def init_db():
    await init_beanie(
        database=database,
        document_models=[
            Office,
            Permission,
            Role,
            User,
            Paciente,
            Especialidad,
            Especialista,
            EstadoCita,
            Cita,
            OfficeConfig,
            Tratamiento
        ]
    )