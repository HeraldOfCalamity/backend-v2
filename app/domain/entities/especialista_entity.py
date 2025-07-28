from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel

from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate

class Disponibilidad(BaseModel):
    dia: int
    desde: str
    hasta: str

class EspecialistaCreate(BaseModel):
    especialidad_ids: List[str]
    nombre: str
    apellido: str
    matricula_profesional: str
    telefono: str
    disponibilidades: List[Disponibilidad]
    
class EspecialistaUpdate(BaseModel):
    especialidad_ids: List[str]
    nombre: str
    apellido: str
    matricula_profesional: str
    telefono: str
    disponibilidades: List[Disponibilidad]

class EspecialistaOut(BaseModel):
    id: str
    user_id: str
    especialidad_ids: List[str]
    disponibilidades: List[Disponibilidad]
    matricula_profesional: str
    nombre: str
    apellido: str
    telefono: str
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None

class EspecialistaCreateWithUser(BaseModel):
    user: UserBase
    especialista: EspecialistaCreate

class EspecialistaUpdateWithUser(BaseModel):
    user: UserUpdate
    especialista: EspecialistaUpdate

class EspecialistaProfileOut(BaseModel):
    user: UserOut
    especialista: EspecialistaOut | None