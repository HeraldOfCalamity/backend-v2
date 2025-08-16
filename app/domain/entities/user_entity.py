from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    lastname: str 
    ci: str 
    phone:str 
    name: str
    email: EmailStr
    password: str
    isVerified: Optional[bool] = False
    role: Optional[str] = 'paciente'

# class UserCreate(BaseModel):
#     username: str
#     email: EmailStr
#     password: str
#     role: str

class UserUpdate(BaseModel):
    lastname: str 
    ci: str 
    phone:str
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str
    isActive: bool
    isVerified: Optional[bool] = False


class UserOut(BaseModel):
    id: str
    lastname: str 
    ci: str 
    phone:str 
    name: str
    email: EmailStr
    role: str
    isActive: bool
    isVerified: bool
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None