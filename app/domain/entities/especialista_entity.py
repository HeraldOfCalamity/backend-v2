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
    telefono: str
    ci: str
    image: Optional[str] = ''
    informacion: Optional[str] = ''
    disponibilidades: List[Disponibilidad]
    
class EspecialistaUpdate(BaseModel):
    especialidad_ids: List[str]
    nombre: str
    apellido: str
    ci: str
    telefono: str
    image: Optional[str] = None
    informacion: Optional[str] = None
    disponibilidades: List[Disponibilidad]

class EspecialistaOut(BaseModel):
    id: str
    user_id: str
    ci: str
    especialidad_ids: List[str]
    disponibilidades: List[Disponibilidad]
    nombre: str
    apellido: str
    telefono: str
    createdAt: datetime
    updatedAt: datetime
    image: Optional[str] = None
    informacion: Optional[str] = None
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