from datetime import datetime
from beanie import Document
from pydantic import EmailStr, Field

from app.shared.utils import get_utc_now



class Office(Document):
    name: str
    email: EmailStr
    createdAt: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = 'offices'