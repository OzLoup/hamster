from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedResponse


class BusinessRead(TimestampedResponse):
    id: int
    name: str
    is_active: bool


class BusinessCreateWithAdmin(BaseModel):
    business_name: str = Field(min_length=1, max_length=150)
    admin_email: EmailStr
    admin_full_name: str = Field(min_length=1, max_length=150)
    admin_password: str = Field(min_length=8, max_length=255)
