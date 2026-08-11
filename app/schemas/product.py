from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class ProductBase(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    sku: str = Field(min_length=1, max_length=64)
    stock_quantity: int = Field(ge=0)
    cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    sale_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    stock_quantity: int | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)


class ProductRead(TimestampedResponse):
    id: int
    category_id: int
    name: str
    sku: str
    stock_quantity: int
    is_active: bool
    cost: Decimal
    sale_price: Decimal


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
