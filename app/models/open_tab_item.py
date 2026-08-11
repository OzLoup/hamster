from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OpenTabItem(Base):
    __tablename__ = "open_tab_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tab_id: Mapped[int] = mapped_column(ForeignKey("open_tabs.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)

    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tab: Mapped["OpenTab"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="open_tab_items")

    @property
    def product_name(self) -> str:
        return self.product.name

    @property
    def product_sku(self) -> str:
        return self.product.sku
