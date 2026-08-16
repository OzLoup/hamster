from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class SupplierService:
    """Encapsulates supplier business operations and persistence concerns."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def list_suppliers(self, *, is_active: bool | None = None) -> list[Supplier]:
        """Return suppliers ordered by id, optionally filtered by active status."""
        stmt = select(Supplier).where(Supplier.business_id == self.business_id).order_by(Supplier.id)
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        return list(self.db.scalars(stmt).all())

    def get_supplier(self, supplier_id: int) -> Supplier:
        """Return a supplier or raise a not-found service error."""
        supplier = self.db.get(Supplier, supplier_id)
        if supplier is None or supplier.business_id != self.business_id:
            raise NotFoundError(f"Supplier {supplier_id} was not found.")
        return supplier

    def create_supplier(self, payload: SupplierCreate) -> Supplier:
        """Create a new supplier while enforcing a unique name within this business."""
        self._ensure_unique_name(payload.name)

        supplier = Supplier(**payload.model_dump(), business_id=self.business_id)
        self.db.add(supplier)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Supplier could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating supplier.") from exc

        self.db.refresh(supplier)
        return supplier

    def update_supplier(self, supplier_id: int, payload: SupplierUpdate) -> Supplier:
        """Update mutable supplier fields while preserving uniqueness rules."""
        supplier = self.get_supplier(supplier_id)
        updates = payload.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] != supplier.name:
            self._ensure_unique_name(updates["name"])

        for field, value in updates.items():
            setattr(supplier, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Supplier could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating supplier.") from exc

        self.db.refresh(supplier)
        return supplier

    def set_active_status(self, supplier_id: int, is_active: bool) -> Supplier:
        """Activate or deactivate a supplier without touching its purchase history."""
        supplier = self.get_supplier(supplier_id)
        supplier.is_active = is_active

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating supplier status.") from exc

        self.db.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: int) -> None:
        """Delete an existing supplier."""
        supplier = self.get_supplier(supplier_id)
        self.db.delete(supplier)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                f"Supplier {supplier_id} could not be deleted because it has associated purchase records."
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while deleting supplier.") from exc

    def _ensure_unique_name(self, name: str) -> None:
        existing = self.db.scalar(
            select(Supplier.id).where(Supplier.name == name, Supplier.business_id == self.business_id)
        )
        if existing is not None:
            raise ConflictError(f"Supplier name '{name}' already exists.")
