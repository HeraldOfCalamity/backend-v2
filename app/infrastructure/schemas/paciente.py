from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field

from app.shared.utils import get_utc_now


class Paciente(Document):
    user_id: PydanticObjectId = Field(...)
    fecha_nacimiento: datetime
    tipo_sangre: str
    tenant_id: PydanticObjectId = Field(...)
    createdAt: datetime = Field(default_factory=get_utc_now)
    updatedAt: datetime = Field(default_factory=get_utc_now)
    deletedAt: datetime | None = None

    class Settings:
        name = 'pacientes'
