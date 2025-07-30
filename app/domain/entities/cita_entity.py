from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.domain.entities.especialidad_entity import EspecialidadOut
from app.domain.entities.especialista_entity import EspecialistaOut
from app.domain.entities.estadoCita_entity import EstadoCitaOut
from app.domain.entities.paciente_entity import PacienteOut


class CitaCreate(BaseModel):
    paciente_id: str
    especialista_id: str
    especialidad_id: str
    fecha_inicio: datetime
    motivo: str


class CitaOut(BaseModel):
    id: str
    paciente: PacienteOut
    especialista: EspecialistaOut
    especialidad: EspecialidadOut
    fecha_inicio: datetime
    fecha_fin: datetime
    duration_minutes: int
    estado: EstadoCitaOut
    motivo: Optional[str]