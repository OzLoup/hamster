from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse
from app.schemas.sale import PaymentMethod


class OpenTabCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class OpenTabItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OpenTabItemRead(TimestampedResponse):
    id: int
    tab_id: int
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OpenTabRead(TimestampedResponse):
    id: int
    name: str
    total: Decimal
    items: list[OpenTabItemRead] = Field(default_factory=list)


class OpenTabCloseRequest(BaseModel):
    payment_method: PaymentMethod
