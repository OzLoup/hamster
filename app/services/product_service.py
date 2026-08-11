from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError


class ProductService:
    """Handles product and inventory business operations independent from API routes."""

    def __init__(self, db: Session):
        self.db = db

    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Product], int]:
        """Return paginated products with optional name search, category, and active-status filtering."""
        if page < 1:
            raise ValidationError("Page must be greater than or equal to 1.")
        if page_size < 1 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")

        conditions = []
        if search:
            conditions.append(Product.name.ilike(f"%{search.strip()}%"))
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if is_active is not None:
            conditions.append(Product.is_active == is_active)

        items_stmt = select(Product)
        count_stmt = select(func.count(Product.id))
        if conditions:
            items_stmt = items_stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        items_stmt = items_stmt.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
        products = list(self.db.scalars(items_stmt).all())
        total = int(self.db.scalar(count_stmt) or 0)
        return products, total

    def get_product(self, product_id: int) -> Product:
        """Return one product or raise a not-found service error."""
        product = self.db.get(Product, product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} was not found.")
        return product

    def create_product(self, payload: ProductCreate) -> Product:
        """Create a product after validating category and SKU uniqueness."""
        self._ensure_category_exists(payload.category_id)
        self._ensure_unique_sku(payload.sku)

        product = Product(**payload.model_dump())
        self.db.add(product)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Product could not be created due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while creating product.") from exc

        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        """Apply partial updates while enforcing business constraints."""
        product = self.get_product(product_id)
        updates = payload.model_dump(exclude_unset=True)

        if "category_id" in updates:
            self._ensure_category_exists(updates["category_id"])
        if "sku" in updates and updates["sku"] != product.sku:
            self._ensure_unique_sku(updates["sku"])
        if "stock_quantity" in updates and updates["stock_quantity"] < 0:
            raise ValidationError("Stock quantity cannot be negative.")

        for field, value in updates.items():
            setattr(product, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Product could not be updated due to a data conflict.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating product.") from exc

        self.db.refresh(product)
        return product

    def delete_product(self, product_id: int) -> None:
        """Delete an existing product."""
        product = self.get_product(product_id)
        self.db.delete(product)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                f"Product {product_id} could not be deleted because it has associated sale records."
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while deleting product.") from exc

    def set_active_status(self, product_id: int, is_active: bool) -> Product:
        """Activate or deactivate a product without touching its sale history."""
        product = self.get_product(product_id)
        product.is_active = is_active

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ServiceError("Unexpected database error while updating product status.") from exc

        self.db.refresh(product)
        return product

    def _ensure_category_exists(self, category_id: int) -> None:
        exists = self.db.scalar(select(Category.id).where(Category.id == category_id))
        if exists is None:
            raise NotFoundError(f"Category {category_id} was not found.")

    def _ensure_unique_sku(self, sku: str) -> None:
        existing = self.db.scalar(select(Product.id).where(Product.sku == sku))
        if existing is not None:
            raise ConflictError(f"Product SKU '{sku}' already exists.")
