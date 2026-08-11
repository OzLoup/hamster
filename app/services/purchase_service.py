from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.supplier import Supplier
from app.schemas.purchase import PurchaseCreate, PurchaseUpdate
from app.schemas.purchase_item import PurchaseItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError


class PurchaseService:
    """Executes purchase business workflows: growing stock and updating product cost."""

    def __init__(self, db: Session):
        self.db = db

    def list_purchases(self) -> list[Purchase]:
        """Return all purchases including their line items."""
        stmt = select(Purchase).options(selectinload(Purchase.purchase_items)).order_by(Purchase.id)
        return list(self.db.scalars(stmt).all())

    def get_purchase(self, purchase_id: int) -> Purchase:
        """Return a single purchase with line items."""
        stmt = select(Purchase).where(Purchase.id == purchase_id).options(selectinload(Purchase.purchase_items))
        purchase = self.db.scalar(stmt)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} was not found.")
        return purchase

    def create_purchase(self, payload: PurchaseCreate) -> Purchase:
        """Create a purchase transaction, increment stock, update product cost, and persist line items."""
        try:
            if not payload.purchase_items:
                raise ValidationError("A purchase must include at least one purchase item.")

            supplier = self.db.get(Supplier, payload.supplier_id)
            if supplier is None:
                raise NotFoundError(f"Supplier {payload.supplier_id} was not found.")
            if not supplier.is_active:
                raise ValidationError(f"Supplier {payload.supplier_id} is inactive and cannot receive new purchases.")

            existing = self.db.scalar(select(Purchase.id).where(Purchase.reference == payload.reference))
            if existing is not None:
                raise ConflictError(f"Purchase reference '{payload.reference}' already exists.")

            calculated_total = self._calculate_total(payload.purchase_items)
            if payload.total_amount != calculated_total:
                raise ValidationError("Provided total_amount does not match the purchase item totals.")

            purchase = Purchase(
                supplier_id=payload.supplier_id,
                reference=payload.reference,
                total_amount=payload.total_amount,
            )
            self.db.add(purchase)
            self.db.flush()

            for line in payload.purchase_items:
                product = self.db.get(Product, line.product_id)
                if product is None:
                    raise NotFoundError(f"Product {line.product_id} was not found.")

                product.stock_quantity += line.quantity
                product.cost = line.unit_cost

                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                    subtotal=line.subtotal,
                )
                self.db.add(purchase_item)
        except (ConflictError, NotFoundError, ValidationError):
            self.db.rollback()
            raise

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Purchase could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating purchase.") from exc

        self.db.refresh(purchase)
        return self.get_purchase(purchase.id)

    def update_purchase(self, purchase_id: int, payload: PurchaseUpdate) -> Purchase:
        """Update mutable purchase fields without mutating historical line items."""
        purchase = self.get_purchase(purchase_id)
        updates = payload.model_dump(exclude_unset=True)

        if "reference" in updates and updates["reference"] != purchase.reference:
            existing = self.db.scalar(select(Purchase.id).where(Purchase.reference == updates["reference"]))
            if existing is not None:
                raise ConflictError(f"Purchase reference '{updates['reference']}' already exists.")

        for field, value in updates.items():
            setattr(purchase, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Purchase could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating purchase.") from exc

        self.db.refresh(purchase)
        return purchase

    def _calculate_total(self, purchase_items: list[PurchaseItemCreate]) -> Decimal:
        total = Decimal("0.00")
        for line in purchase_items:
            expected_subtotal = line.unit_cost * line.quantity
            if line.subtotal != expected_subtotal:
                raise ValidationError(
                    "Each purchase item subtotal must match quantity multiplied by unit_cost."
                )
            total += line.subtotal
        return total
