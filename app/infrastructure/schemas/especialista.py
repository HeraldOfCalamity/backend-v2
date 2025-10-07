from datetime import datetime, time
from typing import List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from app.shared.utils import get_utc_now

class Disponibilidad(BaseModel):
    dia: int
    desde: str
    hasta: str

class Inactividad(BaseModel):
    desde: datetime
    hasta: datetime
    motivo: Optional[str] = None

class Especialista(Document):
    user_id: PydanticObjectId = Field(...)
    especialidades: List[PydanticObjectId] = Field(default_factory=list)
    disponibilidades: List[Disponibilidad] = Field(default_factory=list)
    inactividades: List[Inactividad] = Field(default_factory=list)
    informacion: Optional[str] = Field(default=None, max_length=500)
    image: Optional[str] = Field(default=None)
    tenant_id: PydanticObjectId = Field(...)
    createdAt: datetime = Field(default_factory=get_utc_now)
    updatedAt: datetime = Field(default_factory=get_utc_now)
    deletedAt: datetime | None = None

    class Settings:
        name = 'especialistas'