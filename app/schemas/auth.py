from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class CurrentUser(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole | None
    is_superuser: bool
    business_id: int | None
    business_name: str | None
