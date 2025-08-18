from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TratamientoCreate(BaseModel):
    nombre: str
    descripcion: str
    image: Optional[str]

class TratamientoUpdate(BaseModel):
    nombre: str
    descripcion: str
    image: Optional[str]

class TratamientoOut(BaseModel):
    id: str
    nombre: str
    image: Optional[str]
    descripcion: str
    createdAt: datetime