from pydantic import BaseModel


class EstadoCitaOut(BaseModel):
    id: str
    estado_id: str
    nombre: str
    descripcion: str