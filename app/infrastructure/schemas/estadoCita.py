from enum import Enum
from beanie import Document, PydanticObjectId
from pydantic import Field

class ESTADOS_CITA(Enum):
    pendiente=0
    confirmada=1
    cancelada=2
    atendida=3

class EstadoCita(Document):
    estado_id: int = Field(..., unique=True)
    nombre: str
    descripcion: str
    tenant_id: PydanticObjectId = Field(...)

    class Settings:
        name = 'cita_estados'