from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING, DESCENDING
from pydantic import Field, field_validator, validator


class Cita(Document):
    tenant_id: PydanticObjectId
    paciente_id: PydanticObjectId
    especialista_id: PydanticObjectId
    fecha_inicio: datetime
    fecha_fin: datetime
    duration_minutes: int = Field(..., ge=1, le=24 * 60)
    estado_id: int = Field(default=0)
    motivo: Optional[str] = Field(default=None, max_length=500)

    class Settings:
        name = "citas"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("especialista_id", ASCENDING), ("fecha_inicio", ASCENDING)],
                name="idx_tenant_especialista_fecha",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("paciente_id", ASCENDING), ("fecha_inicio", DESCENDING)],
                name="idx_tenant_paciente_fecha_desc",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("especialista_id", ASCENDING),
                    ("fecha_inicio", ASCENDING),
                    ("fecha_fin", ASCENDING),
                ],
                name="idx_unique_slot_like",
            ),
        ]

    @field_validator("fecha_fin")
    def end_must_be_after_start(cls, v, values):
        start = values.get("fecha_inicio")
        if start and v <= start:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return v
