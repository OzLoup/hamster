from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.open_tab import OpenTab
from app.models.open_tab_item import OpenTabItem
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.open_tab import OpenTabCloseRequest, OpenTabCreate, OpenTabItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError


class OpenTabService:
    """Manages open tabs (tables, customer-on-credit accounts) that later become real sales."""

    def __init__(self, db: Session):
        self.db = db

    def list_tabs(self) -> list[OpenTab]:
        stmt = (
            select(OpenTab)
            .options(selectinload(OpenTab.items).selectinload(OpenTabItem.product))
            .order_by(OpenTab.name)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_tab(self, tab_id: int) -> OpenTab:
        stmt = (
            select(OpenTab)
            .where(OpenTab.id == tab_id)
            .options(selectinload(OpenTab.items).selectinload(OpenTabItem.product))
        )
        tab = self.db.scalar(stmt)
        if tab is None:
            raise NotFoundError(f"Open tab {tab_id} was not found.")
        return tab

    def create_tab(self, payload: OpenTabCreate) -> OpenTab:
        self._ensure_unique_name(payload.name)

        tab = OpenTab(name=payload.name)
        self.db.add(tab)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Open tab could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating open tab.") from exc

        return self.get_tab(tab.id)

    def add_item(self, tab_id: int, payload: OpenTabItemCreate) -> OpenTab:
        tab = self.get_tab(tab_id)
        product = self.db.get(Product, payload.product_id)
        if product is None:
            raise NotFoundError(f"Product {payload.product_id} was not found.")
        if not product.is_active:
            raise ValidationError(f"Product {payload.product_id} is inactive and cannot be added to a tab.")
        if product.stock_quantity < payload.quantity:
            raise ValidationError(
                f"Insufficient stock for product {payload.product_id}. Requested={payload.quantity}."
            )

        existing_item = next((item for item in tab.items if item.product_id == payload.product_id), None)
        unit_price = product.sale_price
        product.stock_quantity -= payload.quantity

        if existing_item is not None:
            existing_item.quantity += payload.quantity
            existing_item.unit_price = unit_price
            existing_item.subtotal = (unit_price * existing_item.quantity).quantize(Decimal("0.01"))
        else:
            self.db.add(
                OpenTabItem(
                    tab_id=tab.id,
                    product_id=payload.product_id,
                    quantity=payload.quantity,
                    unit_price=unit_price,
                    subtotal=(unit_price * payload.quantity).quantize(Decimal("0.01")),
                )
            )

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while adding item to open tab.") from exc

        return self.get_tab(tab_id)

    def remove_item(self, tab_id: int, item_id: int) -> OpenTab:
        tab = self.get_tab(tab_id)
        item = next((candidate for candidate in tab.items if candidate.id == item_id), None)
        if item is None:
            raise NotFoundError(f"Item {item_id} was not found in open tab {tab_id}.")

        product = self.db.get(Product, item.product_id)
        if product is not None:
            product.stock_quantity += item.quantity

        self.db.delete(item)

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while removing item from open tab.") from exc

        return self.get_tab(tab_id)

    def close_tab(self, tab_id: int, payload: OpenTabCloseRequest) -> Sale:
        """Convert the tab's current items into a real sale. Stock was already deducted on add."""
        tab = self.get_tab(tab_id)
        if not tab.items:
            raise ValidationError("Cannot close an open tab with no items.")

        total = sum((item.subtotal for item in tab.items), Decimal("0.00"))
        reference = self._generate_sale_reference(tab)

        sale = Sale(reference=reference, payment_method=payload.payment_method, total_amount=total)
        self.db.add(sale)
        self.db.flush()

        for item in list(tab.items):
            self.db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )
            self.db.delete(item)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Open tab could not be closed due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while closing open tab.") from exc

        stmt = select(Sale).where(Sale.id == sale.id).options(selectinload(Sale.sale_items))
        return self.db.scalar(stmt)

    def delete_tab(self, tab_id: int) -> None:
        """Delete a tab, restoring stock for any items still sitting in it unpaid."""
        tab = self.get_tab(tab_id)

        for item in tab.items:
            product = self.db.get(Product, item.product_id)
            if product is not None:
                product.stock_quantity += item.quantity

        self.db.delete(tab)

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while deleting open tab.") from exc

    def _ensure_unique_name(self, name: str) -> None:
        existing = self.db.scalar(select(OpenTab.id).where(OpenTab.name == name))
        if existing is not None:
            raise ConflictError(f"Open tab name '{name}' already exists.")

    def _generate_sale_reference(self, tab: OpenTab) -> str:
        stamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        return f"TAB-{tab.id}-{stamp}"
