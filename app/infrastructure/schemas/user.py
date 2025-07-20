from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import EmailStr, Field

from app.shared.utils import get_utc_now


class User(Document):
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    role: PydanticObjectId = Field(...)
    tenant_id: PydanticObjectId = Field(...)
    isActive: bool = Field(default=True)
    isVerified: bool = Field(default=False)
    createdAt: datetime = Field(default_factory=get_utc_now)
    updatedAt: datetime = Field(default_factory=get_utc_now)
    deletedAt: datetime | None = None

    class Settings:
        name = 'users'
        