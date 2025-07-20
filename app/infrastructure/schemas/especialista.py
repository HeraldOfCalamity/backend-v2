from datetime import datetime, time
from typing import List
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from app.shared.utils import get_utc_now

class Disponibilidad(BaseModel):
    dia: int
    desde: str
    hasta: str

class Especialista(Document):
    user_id: PydanticObjectId = Field(...)
    nombre: str
    apellido: str
    especialidades: List[PydanticObjectId] = Field(default_factory=list)
    disponibilidades: List[Disponibilidad] = Field(default_factory=list)
    matricula_profesional: str
    telefono: str
    tenant_id: PydanticObjectId = Field(...)
    createdAt: datetime = Field(default_factory=get_utc_now)
    updatedAt: datetime = Field(default_factory=get_utc_now)
    deletedAt: datetime | None = None

    class Settings:
        name = 'especialistas'