from datetime import datetime
from typing import Annotated
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from app.shared.utils import get_utc_now


class Especialidad(Document):
    nombre: Annotated[str, Indexed(unique=True)] = Field(...)
    descripcion: str
    tenant_id: PydanticObjectId = Field(...)
    createdAt: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = 'especialidades'
        