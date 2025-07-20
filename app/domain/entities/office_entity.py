from datetime import datetime
from pydantic import BaseModel, EmailStr


class OfficeOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    createdAt: datetime