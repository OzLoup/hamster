from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedResponse


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None


class SupplierRead(TimestampedResponse):
    id: int
    name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    is_active: bool
