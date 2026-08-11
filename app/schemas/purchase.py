from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse
from app.schemas.purchase_item import PurchaseItemCreate, PurchaseItemRead


class PurchaseCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=64)
    total_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    purchase_items: list[PurchaseItemCreate] = Field(default_factory=list)


class PurchaseUpdate(BaseModel):
    reference: str | None = Field(default=None, min_length=1, max_length=64)
    total_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class PurchaseRead(TimestampedResponse):
    id: int
    supplier_id: int
    reference: str
    total_amount: Decimal
    purchase_items: list[PurchaseItemRead] = Field(default_factory=list)
