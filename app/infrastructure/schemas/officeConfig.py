from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel
from typing import Literal


class OfficeConfig(Document):
    tenant_id: PydanticObjectId = Field(...)
    name: str = Field(..., unique=True)
    value: str = Field(...)

    class Settings:
        name = "office_configs"
