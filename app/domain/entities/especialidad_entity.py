from pydantic import BaseModel
from datetime import datetime

class EspecialidadCreate(BaseModel):
    nombre: str
    descripcion: str

class EspecialidadUpdate(BaseModel):
    nombre: str
    descripcion: str

class EspecialidadOut(BaseModel):
    id: str
    nombre: str
    descripcion: str
    createdAt: datetime