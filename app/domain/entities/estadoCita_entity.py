from pydantic import BaseModel


class EstadoCitaOut(BaseModel):
    id: str
    name: str
    description: str