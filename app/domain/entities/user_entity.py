from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = 'paciente'

# class UserCreate(BaseModel):
#     username: str
#     email: EmailStr
#     password: str
#     role: str

class UserUpdate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    isActive: bool
    isVerified: bool


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str
    isActive: bool
    isVerified: bool
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None