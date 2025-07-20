from datetime import datetime
from typing import List
from pydantic import BaseModel

from app.domain.entities.permission_entity import PermissionOut


class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: List[str]

class RoleUpdate(BaseModel):
    name: str
    description: str
    permissions: List[str]

class RoleOut(BaseModel):
    id: str
    name: str
    description: str
    permissions: List[str]
    createdAt: datetime