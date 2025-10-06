from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel


class HistorialCreate(BaseModel):    
    paciente_id: str

class TratamientoAdd(BaseModel):
    motivo: str
    antFamiliares: str
    antPersonales: str
    condActual: str
    intervencionClinica: str
    diagnostico: str
    
class EntradaAdd(BaseModel):
    recursosTerapeuticos: str
    evolucionText: str
    imageIds: List[str] = []

class PresignReq(BaseModel):
    paciente_id: str
    historial_id: str
    entrada_id: str
    filename: str
    content_type: str

class UpdateHistorial(BaseModel):
    antPersonales: Optional[str] = None
    antFamiliares: Optional[str] = None
    condActual: str
    intervencionClinica: str

class RegisterImageReq(BaseModel):
    tratamientoId: str
    pacienteId: str
    historialId: Optional[str]
    entradaId: Optional[str]
    key: str
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    originalName: Optional[str] = None
    originalType: Optional[str] = None
    aesKeyB64: Optional[str] = None
    ivB64: Optional[str] = None
    previewDataUrl: Optional[str] = None

class RecomendacionesUpdate(BaseModel):
    recomendaciones: str




