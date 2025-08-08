from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class EspecialidadCreate(BaseModel):
    nombre: str
    descripcion: str
    image: Optional[str]

class EspecialidadUpdate(BaseModel):
    nombre: str
    descripcion: str
    image: Optional[str]

class EspecialidadOut(BaseModel):
    id: str
    nombre: str
    image: Optional[str]
    descripcion: str
    createdAt: datetime