from datetime import datetime
from typing import List
from beanie import Document, PydanticObjectId
from pydantic import Field

from app.shared.utils import get_utc_now


class Role(Document):
    name: str
    description: str
    tenant_id: PydanticObjectId
    permissions: List[PydanticObjectId] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = 'roles'