from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class EspecialidadCreate(BaseModel):
    nombre: str
    descripcion: str
    tratamientos: List[str]
    image: Optional[str]

class EspecialidadUpdate(BaseModel):
    nombre: str
    descripcion: str
    tratamientos: List[str]
    image: Optional[str]

class EspecialidadOut(BaseModel):
    id: str
    nombre: str
    image: Optional[str]
    tratamientos: List[str]
    descripcion: str
    createdAt: datetime


class PresignEspecialidadReq(BaseModel):
    content_type: Optional[str] = "image/webp"

class RegisterEspecialidadImageReq(BaseModel):
    especialidadId: str
    key: str
    originalType: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    previewDataUrl: Optional[str] = None