from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.sale import SaleCreate, SaleUpdate
from app.schemas.sale_item import SaleItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError


class SaleService:
    """Executes sale business workflows and keeps routes free from data-access logic."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def list_sales(self) -> list[Sale]:
        """Return all sales for this business including their line items."""
        stmt = (
            select(Sale)
            .where(Sale.business_id == self.business_id)
            .options(selectinload(Sale.sale_items))
            .order_by(Sale.id)
        )
        return list(self.db.scalars(stmt).all())

    def get_sale(self, sale_id: int) -> Sale:
        """Return a single sale with line items."""
        stmt = (
            select(Sale)
            .where(Sale.id == sale_id, Sale.business_id == self.business_id)
            .options(selectinload(Sale.sale_items))
        )
        sale = self.db.scalar(stmt)
        if sale is None:
            raise NotFoundError(f"Sale {sale_id} was not found.")
        return sale

    def create_sale(self, payload: SaleCreate) -> Sale:
        """Create a sale transaction, decrement stock, and persist sale items atomically."""
        try:
            if not payload.sale_items:
                raise ValidationError("A sale must include at least one sale item.")

            existing = self.db.scalar(
                select(Sale.id).where(Sale.reference == payload.reference, Sale.business_id == self.business_id)
            )
            if existing is not None:
                raise ConflictError(f"Sale reference '{payload.reference}' already exists.")

            calculated_total = self._calculate_total(payload.sale_items)
            if payload.total_amount != calculated_total:
                raise ValidationError("Provided total_amount does not match the sale item totals.")

            sale = Sale(
                business_id=self.business_id,
                reference=payload.reference,
                payment_method=payload.payment_method,
                total_amount=payload.total_amount,
            )
            self.db.add(sale)
            self.db.flush()

            for line in payload.sale_items:
                product = self.db.get(Product, line.product_id)
                if product is None or product.business_id != self.business_id:
                    raise NotFoundError(f"Product {line.product_id} was not found.")
                if product.stock_quantity < line.quantity:
                    raise ValidationError(
                        f"Insufficient stock for product {line.product_id}. Requested={line.quantity}."
                    )

                product.stock_quantity -= line.quantity

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    subtotal=line.subtotal,
                )
                self.db.add(sale_item)
        except (ConflictError, NotFoundError, ValidationError):
            self.db.rollback()
            raise

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Sale could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating sale.") from exc

        self.db.refresh(sale)
        return self.get_sale(sale.id)

    def update_sale(self, sale_id: int, payload: SaleUpdate) -> Sale:
        """Update mutable sale fields without mutating historical line items."""
        sale = self.get_sale(sale_id)
        updates = payload.model_dump(exclude_unset=True)

        if "reference" in updates and updates["reference"] != sale.reference:
            existing = self.db.scalar(
                select(Sale.id).where(
                    Sale.reference == updates["reference"], Sale.business_id == self.business_id
                )
            )
            if existing is not None:
                raise ConflictError(f"Sale reference '{updates['reference']}' already exists.")

        for field, value in updates.items():
            setattr(sale, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Sale could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating sale.") from exc

        self.db.refresh(sale)
        return self.get_sale(sale.id)

    def _calculate_total(self, sale_items: list[SaleItemCreate]) -> Decimal:
        total = Decimal("0.00")
        for line in sale_items:
            expected_subtotal = line.unit_price * line.quantity
            if line.subtotal != expected_subtotal:
                raise ValidationError(
                    "Each sale item subtotal must match quantity multiplied by unit_price."
                )
            total += line.subtotal
        return total
