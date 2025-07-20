from datetime import datetime
from pydantic import BaseModel


class PermissionCreate(BaseModel):
    name: str
    description: str

class PermissionOut(BaseModel):
    id: str
    name: str
    description: str
    createdAt: datetime