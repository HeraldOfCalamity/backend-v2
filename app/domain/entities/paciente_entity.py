from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId
from bson import ObjectId
from pydantic import BaseModel

from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate


class PacienteCreate(BaseModel):    
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    tipo_sangre: str
    telefono: str

class PacienteAutoCreate(BaseModel):   
    user_id: str 
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    tipo_sangre: str
    telefono: str

class PacienteUpdate(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    tipo_sangre: str
    telefono: str

class PacienteUpdateWithUser(BaseModel):
    user: UserUpdate
    paciente: PacienteUpdate

class PacienteOut(BaseModel):
    id: str
    user_id: str
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    tipo_sangre: str
    telefono: str
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None

class  PacienteCreateWithUser(BaseModel):
    user: UserBase
    paciente: PacienteCreate

class PacienteProfileOut(BaseModel):
    user: UserOut
    paciente: PacienteOut | None