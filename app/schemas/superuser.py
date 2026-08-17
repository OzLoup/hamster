from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedResponse


class SuperuserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)


class SuperuserRead(TimestampedResponse):
    id: int
    email: str
    full_name: str
    is_active: bool
