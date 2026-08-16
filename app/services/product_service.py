import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError

LOW_STOCK_MAX = 10
MEDIUM_STOCK_MAX = 30

SORTABLE_COLUMNS = {
    "name": Product.name,
    "category": Category.name,
    "stock_quantity": Product.stock_quantity,
    "cost": Product.cost,
    "sale_price": Product.sale_price,
}


class ProductService:
    """Handles product and inventory business operations independent from API routes."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        stock_level: str | None = None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> tuple[list[Product], int]:
        """Return paginated products with optional filtering and sorting."""
        if page < 1:
            raise ValidationError("Page must be greater than or equal to 1.")
        if page_size < 1 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")

        conditions = [Product.business_id == self.business_id]
        if search:
            conditions.append(Product.name.ilike(f"%{search.strip()}%"))
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if is_active is not None:
            conditions.append(Product.is_active == is_active)
        if stock_level == "low":
            conditions.append(Product.stock_quantity <= LOW_STOCK_MAX)
        elif stock_level == "medium":
            conditions.append(Product.stock_quantity.between(LOW_STOCK_MAX + 1, MEDIUM_STOCK_MAX))
        elif stock_level == "good":
            conditions.append(Product.stock_quantity > MEDIUM_STOCK_MAX)

        items_stmt = select(Product).where(*conditions)
        count_stmt = select(func.count(Product.id)).where(*conditions)

        order_column = SORTABLE_COLUMNS.get(sort_by)
        if order_column is not None:
            if sort_by == "category":
                items_stmt = items_stmt.join(Category, Category.id == Product.category_id)
            order_clauses = [order_column.desc() if sort_dir == "desc" else order_column.asc(), Product.id.asc()]
        else:
            order_clauses = [Product.id.asc()]

        items_stmt = items_stmt.order_by(*order_clauses).offset((page - 1) * page_size).limit(page_size)
        products = list(self.db.scalars(items_stmt).all())
        total = int(self.db.scalar(count_stmt) or 0)
        return products, total

    def get_product(self, product_id: int) -> Product:
        """Return one product or raise a not-found service error."""
        product = self.db.get(Product, product_id)
        if product is None or product.business_id != self.business_id:
            raise NotFoundError(f"Product {product_id} was not found.")
        return product

    def create_product(self, payload: ProductCreate) -> Product:
        """Create a product after validating its category; the SKU is generated automatically."""
        self._ensure_category_exists(payload.category_id)

        # Temporary placeholder so the NOT NULL/unique sku column accepts the insert;
        # it is replaced with the real, id-based SKU right after the row gets its id.
        product = Product(**payload.model_dump(), sku=f"TMP-{uuid.uuid4().hex}", business_id=self.business_id)
        self.db.add(product)

        try:
            self.db.flush()
            product.sku = self._generate_sku(product.id)
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
        exists = self.db.scalar(
            select(Category.id).where(Category.id == category_id, Category.business_id == self.business_id)
        )
        if exists is None:
            raise NotFoundError(f"Category {category_id} was not found.")

    def _generate_sku(self, product_id: int) -> str:
        return f"PRD-{product_id:06d}"
