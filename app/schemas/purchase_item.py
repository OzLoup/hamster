from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class PurchaseItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    subtotal: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class PurchaseItemRead(TimestampedResponse):
    id: int
    purchase_id: int
    product_id: int
    quantity: int
    unit_cost: Decimal
    subtotal: Decimal
