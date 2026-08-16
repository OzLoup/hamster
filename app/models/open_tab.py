from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OpenTab(Base):
    """A named running order (table, customer-on-credit tab, etc.) awaiting checkout."""

    __tablename__ = "open_tabs"
    __table_args__ = (UniqueConstraint("business_id", "name", name="uq_open_tabs_business_id_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    items: Mapped[list["OpenTabItem"]] = relationship(
        back_populates="tab", cascade="all, delete-orphan", order_by="OpenTabItem.id"
    )

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0.00"))
