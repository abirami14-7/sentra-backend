from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmergencyContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=3, max_length=32)
    relationship: Optional[str] = Field(None, max_length=64)
    priority: int = 1


class EmergencyContactCreate(EmergencyContactBase):
    pass


class EmergencyContactOut(EmergencyContactBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithContacts(UserOut):
    contacts: List[EmergencyContactOut] = []
