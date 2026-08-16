from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class CategoryService:
    """Encapsulates category business operations and persistence concerns."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def list_categories(self) -> list[Category]:
        """Return all categories for this business ordered by id."""
        stmt = select(Category).where(Category.business_id == self.business_id).order_by(Category.id)
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int) -> Category:
        """Return a category or raise a not-found service error."""
        category = self.db.get(Category, category_id)
        if category is None or category.business_id != self.business_id:
            raise NotFoundError(f"Category {category_id} was not found.")
        return category

    def create_category(self, payload: CategoryCreate) -> Category:
        """Create a new category while enforcing unique category names within this business."""
        self._ensure_unique_name(payload.name)

        category = Category(name=payload.name, description=payload.description, business_id=self.business_id)
        self.db.add(category)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Category could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating category.") from exc

        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, payload: CategoryUpdate) -> Category:
        """Update mutable category fields while preserving uniqueness rules."""
        category = self.get_category(category_id)
        updates = payload.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] != category.name:
            self._ensure_unique_name(updates["name"])

        for field, value in updates.items():
            setattr(category, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Category could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating category.") from exc

        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        """Delete a category when no products reference it."""
        category = self.get_category(category_id)
        products_count = self.db.scalar(
            select(Product.id)
            .where(Product.category_id == category_id, Product.business_id == self.business_id)
            .limit(1)
        )
        if products_count is not None:
            raise ConflictError("Cannot delete category while products are still assigned.")

        self.db.delete(category)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while deleting category.") from exc

    def _ensure_unique_name(self, name: str) -> None:
        existing = self.db.scalar(
            select(Category.id).where(Category.name == name, Category.business_id == self.business_id)
        )
        if existing is not None:
            raise ConflictError(f"Category name '{name}' already exists.")
