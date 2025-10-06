from datetime import datetime
from typing import Any, List, Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING, DESCENDING
from pydantic import BaseModel, Field, field_validator, model_validator, validator

from app.infrastructure.schemas.estadoCita import ESTADOS_CITA
    

class Cita(Document):
    tenant_id: PydanticObjectId
    paciente_id: PydanticObjectId
    paciente_name: Optional[str] = Field(default=None)
    especialista_name: Optional[str] = Field(default=None)
    especialista_id: PydanticObjectId
    especialidad_id: PydanticObjectId
    fecha_inicio: datetime
    fecha_fin: datetime
    duration_minutes: int = Field(..., ge=1, le=24 * 60)
    estado_id: int = Field(default=0)
    motivo: Optional[str] = Field(default=None, max_length=500)
    canceledBy: Optional[PydanticObjectId] = Field(default=None)
    reminders_sent_marks: List[int] = Field(default_factory=list)
    last_reminder_sent_at: Optional[datetime] = Field(default=None)
    auto_canceled_at: Optional[datetime] = Field(default=None)
    motivo_cancelacion: Optional[str] = Field(default=None, max_length=250)

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
            IndexModel(
                [("tenant_id", ASCENDING), ("especialista_id", ASCENDING), ("fecha_inicio", ASCENDING), ("fecha_fin", ASCENDING)],
                name="uniq_slot_active",
                unique=True,
                partialFilterExpression={
                    "estado_id": {
                        "$in": [
                            ESTADOS_CITA.pendiente.value,
                            ESTADOS_CITA.confirmada.value,
                            ESTADOS_CITA.atendida.value,
                        ]
                    }
                },  # 👈 solo aplica a NO canceladas
            ),
        ]

    @model_validator(mode="before")
    @classmethod
    def end_must_be_after_start(cls, data: Any) -> Any:
        start = data.get("fecha_inicio")
        end = data.get("fecha_fin")

        if start and end and end <= start:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return data
