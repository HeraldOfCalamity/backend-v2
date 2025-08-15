from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId
from bson import ObjectId
from pydantic import BaseModel

from app.domain.entities.user_entity import UserBase, UserOut, UserUpdate


class PacienteCreate(BaseModel):    
    fecha_nacimiento: datetime
    tipo_sangre: str

class PacienteAutoCreate(BaseModel):   
    user_id: str 
    fecha_nacimiento: datetime
    tipo_sangre: str

class PacienteUpdate(BaseModel):
    fecha_nacimiento: datetime
    tipo_sangre: str

class PacienteUpdateWithUser(BaseModel):
    user: UserUpdate
    paciente: PacienteUpdate

class PacienteOut(BaseModel):
    id: str
    user_id: str
    fecha_nacimiento: datetime
    tipo_sangre: str
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None

class  PacienteCreateWithUser(BaseModel):
    user: UserBase
    paciente: PacienteCreate

class PacienteProfileOut(BaseModel):
    user: UserOut | None
    paciente: PacienteOut | None
