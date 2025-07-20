from datetime import datetime
from typing import Annotated
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from app.shared.utils import get_utc_now


class Permission(Document):
    name: Annotated[str, Indexed(unique=True)]
    description: str
    tenant_id: PydanticObjectId
    createdAt: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = 'permissions'