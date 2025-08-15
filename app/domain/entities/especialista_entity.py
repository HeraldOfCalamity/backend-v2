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
    image: Optional[str] = ''
    informacion: Optional[str] = ''
    disponibilidades: List[Disponibilidad]
    
class EspecialistaUpdate(BaseModel):
    especialidad_ids: List[str]
    image: Optional[str] = None
    informacion: Optional[str] = None
    disponibilidades: List[Disponibilidad]

class EspecialistaOut(BaseModel):
    id: str
    user_id: str
    especialidad_ids: List[str]
    disponibilidades: List[Disponibilidad]
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
    user: UserOut | None
    especialista: EspecialistaOut | None