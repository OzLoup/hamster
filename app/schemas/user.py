from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedResponse

UserRole = Literal["admin", "coordinator", "seller"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    role: UserRole


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    role: UserRole | None = None


class UserRead(TimestampedResponse):
    id: int
    business_id: int | None
    email: EmailStr
    full_name: str
    role: UserRole | None
    is_superuser: bool
    is_active: bool
