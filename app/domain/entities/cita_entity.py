from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.domain.entities.especialidad_entity import EspecialidadOut
from app.domain.entities.especialista_entity import EspecialistaOut
from app.domain.entities.estadoCita_entity import EstadoCitaOut
from app.domain.entities.paciente_entity import PacienteOut, PacienteProfileOut
from app.domain.entities.user_entity import UserOut


class CitaCreate(BaseModel):
    paciente_id: str
    especialista_id: str
    especialidad_id: str
    fecha_inicio: datetime
    motivo: str


class CitaOut(BaseModel):
    id: str
    paciente: str
    pacienteName: str
    especialista: str
    especialidad: str
    fecha_inicio: datetime
    fecha_fin: datetime
    canceledBy: UserOut | None
    duration_minutes: int
    estado: EstadoCitaOut
    motivo: Optional[str]