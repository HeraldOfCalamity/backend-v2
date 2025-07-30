from beanie import Document, PydanticObjectId
from pydantic import Field


class EstadoCita(Document):
    estado_id: int
    nombre: str
    descripcion: str
    tenant_id: PydanticObjectId = Field(...)

    class Settings:
        name = 'cita_estados'