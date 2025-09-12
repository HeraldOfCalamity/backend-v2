from datetime import datetime
from typing import Annotated, Literal, Optional, List
from uuid import uuid4
from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field

from app.shared.utils import get_utc_now

NerLabel = Literal[
    "SYMPTOM","PAIN_QUALITY","PAIN_INTENSITY","BODY_PART","MOVEMENT",
    "FUNCTIONAL_LIMITATION","DIAGNOSIS","TREATMENT","EXERCISE","FREQUENCY",
    "SCALE","MEASURE","DURATION","ROM","LATERALITY","TEST"
]

class NerSpan(BaseModel):
    label: NerLabel | str
    text: str
    start: int
    end: int
    norm: Optional[str] = None
    source: Literal["rules","ml"] = "rules"
    confidence: Optional[float] = None

class SectionNer(BaseModel):
    # secciones de Anamnesis
    section: Literal["antPersonales","antfamiliares","condActual","intervencionClinica"]
    ents: List[NerSpan] = Field(default_factory=list)

class CryptoMeta(BaseModel):
    alg: Literal['AES-GCM'] = 'AES-GCM'
    key_b64: Optional[str] = None
    iv_b64: Optional[str] = None

class ImageAsset(Document):
    # Ubicación en R2
    bucket: str = Field(default_factory=lambda: "historiales")
    key: str                                  # p. ej. patients/<paciente>/<entrada>/<uuid>.webp | .bin
    content_type: str                         # image/webp o application/octet-stream (si cifrada)
    size: int
    width: Optional[int] = None
    height: Optional[int] = None

    # Contexto
    tenant_id: PydanticObjectId
    paciente_id: PydanticObjectId            # referencia al paciente dueño
    historial_id: Optional[PydanticObjectId] = None  # opcional: link al historial
    entrada_id: Optional[str] = None         # opcional: id (string) de la entrada embebida

    # UX
    preview_data_url: Optional[str] = None   # miniatura ligera opcional

    # Seguridad
    crypto: Optional[CryptoMeta] = None

    createdAt: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = "images"
        indexes = [
            "tenant_id",
            "paciente_id",
            "historial_id",
            "entrada_id",
            [("createdAt", -1)],
        ]

class Entrada(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)  # identificador estable dentro del historial
    createdAt: datetime = Field(default_factory=get_utc_now)

    # Texto clínico
    recursosTerapeuticos: str
    evolucionText: str

    # Referencias a imágenes (ids de ImageAsset)
    imagenes: List[str] = Field(default_factory=list)
    ner: List[NerSpan] = Field(default_factory=list)

class HistorialClinico(Document):
    paciente_id: PydanticObjectId
    tenant_id: PydanticObjectId
    antfamiliares: str
    antPersonales: str
    condActual: str
    intervencionClinica: str
    entradas: List[Entrada] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=get_utc_now)
    ner_sections: List[SectionNer] = Field(default_factory=list)

    class Settings:
        name = 'historiales'