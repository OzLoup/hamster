from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.product_service import ProductService
from tests.factories import create_category, create_product


@pytest.fixture()
def service(db_session):
    return ProductService(db_session)


def _build_product_create_payload(category_id):
    return ProductCreate(
        category_id=category_id,
        name="Mechanical Keyboard",
        stock_quantity=30,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )


def test_create_product_success(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")
    payload = _build_product_create_payload(category.id)

    # Act
    created = service.create_product(payload)

    # Assert
    assert created.id is not None
    assert created.category_id == category.id
    assert created.sku == f"PRD-{created.id:06d}"


def test_create_product_generates_unique_sku_per_product(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")

    # Act
    first = service.create_product(_build_product_create_payload(category.id))
    second = service.create_product(_build_product_create_payload(category.id))

    # Assert
    assert first.sku != second.sku


def test_create_product_with_missing_category_raises_not_found(service):
    # Arrange
    payload = _build_product_create_payload(category_id=999)

    # Act / Assert
    with pytest.raises(NotFoundError, match="Category 999 was not found"):
        service.create_product(payload)


def test_update_product_success(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")
    product = service.create_product(_build_product_create_payload(category.id))
    update_payload = ProductUpdate(name="Gaming Keyboard", stock_quantity=45)

    # Act
    updated = service.update_product(product.id, update_payload)

    # Assert
    assert updated.id == product.id
    assert updated.name == "Gaming Keyboard"
    assert updated.stock_quantity == 45


def test_update_product_schema_rejects_negative_stock_value():
    # Arrange
    invalid_stock = -1

    # Act / Assert
    with pytest.raises(PydanticValidationError):
        ProductUpdate(stock_quantity=invalid_stock)


def test_update_product_with_model_construct_negative_stock_raises_validation_error(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")
    product = service.create_product(_build_product_create_payload(category.id))
    invalid_payload = ProductUpdate.model_construct(stock_quantity=-1)

    # Act / Assert
    with pytest.raises(ValidationError, match="cannot be negative"):
        service.update_product(product.id, invalid_payload)


def test_delete_product_success(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")
    product = service.create_product(_build_product_create_payload(category.id))

    # Act
    service.delete_product(product.id)

    # Assert
    deleted = db_session.get(Product, product.id)
    assert deleted is None


def test_create_product_integrity_error_raises_conflict_and_rolls_back():
    # Arrange
    db = MagicMock()

    def scalar_side_effect(stmt):
        text = str(stmt)
        if "FROM categories" in text:
            return 1
        if "FROM products" in text:
            return None
        return None

    db.scalar.side_effect = scalar_side_effect
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception("constraint"))

    def assign_product_id(entity):
        if isinstance(entity, Product):
            entity.id = 501

    db.add.side_effect = assign_product_id

    service = ProductService(db)
    payload = ProductCreate(
        category_id=1,
        name="Mechanical Keyboard",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be created due to a data conflict"):
        service.create_product(payload)
    db.rollback.assert_called_once()


def test_create_product_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    db = MagicMock()

    def scalar_side_effect(stmt):
        text = str(stmt)
        if "FROM categories" in text:
            return 1
        if "FROM products" in text:
            return None
        return None

    db.scalar.side_effect = scalar_side_effect
    db.commit.side_effect = SQLAlchemyError("db down")

    def assign_product_id(entity):
        if isinstance(entity, Product):
            entity.id = 502

    db.add.side_effect = assign_product_id

    service = ProductService(db)
    payload = ProductCreate(
        category_id=1,
        name="Mechanical Keyboard",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating product"):
        service.create_product(payload)
    db.rollback.assert_called_once()


def test_update_product_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Product(
        id=10,
        category_id=1,
        name="Mechanical Keyboard",
        sku="KB-100",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = ProductService(db)
    payload = ProductUpdate(name="Updated Name")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating product"):
        service.update_product(10, payload)
    db.rollback.assert_called_once()


def test_delete_product_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Product(
        id=20,
        category_id=1,
        name="Mechanical Keyboard",
        sku="KB-100",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = ProductService(db)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while deleting product"):
        service.delete_product(20)
    db.rollback.assert_called_once()


def test_set_active_status_deactivates_and_reactivates_product(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for product tests")
    product = service.create_product(_build_product_create_payload(category.id))
    assert product.is_active is True

    # Act
    deactivated = service.set_active_status(product.id, False)

    # Assert
    assert deactivated.is_active is False

    # Act
    reactivated = service.set_active_status(product.id, True)

    # Assert
    assert reactivated.is_active is True


def test_set_active_status_missing_product_raises_not_found(service):
    # Act / Assert
    with pytest.raises(NotFoundError, match="Product 999 was not found"):
        service.set_active_status(999, False)


def test_set_active_status_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Product(
        id=22,
        category_id=1,
        name="Mechanical Keyboard",
        sku="KB-102",
        stock_quantity=10,
        is_active=True,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = ProductService(db)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating product status"):
        service.set_active_status(22, False)
    db.rollback.assert_called_once()


def test_delete_product_integrity_error_raises_conflict_and_rolls_back():
    # Arrange: deleting a product still referenced by sale_items violates the FK constraint.
    existing = Product(
        id=21,
        category_id=1,
        name="Mechanical Keyboard",
        sku="KB-101",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = IntegrityError("DELETE", {}, Exception("foreign key constraint"))

    service = ProductService(db)

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be deleted because it has associated sale records"):
        service.delete_product(21)
    db.rollback.assert_called_once()


@pytest.mark.parametrize(
    ("stock_level", "expected_names"),
    [
        ("low", ["Low Stock"]),
        ("medium", ["Medium Stock"]),
        ("good", ["Good Stock"]),
        (None, ["Low Stock", "Medium Stock", "Good Stock"]),
    ],
)
def test_list_products_filters_by_stock_level(service, db_session, stock_level, expected_names):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="SORT-001", name="Low Stock", stock_quantity=5)
    create_product(db_session, category_id=category.id, sku="SORT-002", name="Medium Stock", stock_quantity=20)
    create_product(db_session, category_id=category.id, sku="SORT-003", name="Good Stock", stock_quantity=100)

    # Act
    products, total = service.list_products(stock_level=stock_level)

    # Assert
    assert total == len(expected_names)
    assert sorted(p.name for p in products) == sorted(expected_names)


@pytest.mark.parametrize(
    ("sort_by", "sort_dir", "expected_order"),
    [
        ("name", "asc", ["Alpha", "Bravo", "Charlie"]),
        ("name", "desc", ["Charlie", "Bravo", "Alpha"]),
        ("stock_quantity", "asc", ["Bravo", "Charlie", "Alpha"]),
        ("stock_quantity", "desc", ["Alpha", "Charlie", "Bravo"]),
        ("cost", "asc", ["Charlie", "Alpha", "Bravo"]),
        ("sale_price", "desc", ["Bravo", "Alpha", "Charlie"]),
        (None, "asc", ["Alpha", "Bravo", "Charlie"]),
    ],
)
def test_list_products_sorts_by_requested_column(service, db_session, sort_by, sort_dir, expected_order):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(
        db_session,
        category_id=category.id,
        sku="SORT-ALPHA",
        name="Alpha",
        stock_quantity=50,
        cost=Decimal("20.00"),
        sale_price=Decimal("90.00"),
    )
    create_product(
        db_session,
        category_id=category.id,
        sku="SORT-BRAVO",
        name="Bravo",
        stock_quantity=5,
        cost=Decimal("30.00"),
        sale_price=Decimal("100.00"),
    )
    create_product(
        db_session,
        category_id=category.id,
        sku="SORT-CHARLIE",
        name="Charlie",
        stock_quantity=15,
        cost=Decimal("10.00"),
        sale_price=Decimal("50.00"),
    )

    # Act
    products, _ = service.list_products(sort_by=sort_by, sort_dir=sort_dir)

    # Assert
    assert [p.name for p in products] == expected_order


def test_list_products_sorts_by_category_name(service, db_session):
    # Arrange
    zeta_category = create_category(db_session, name="Zeta Category")
    alpha_category = create_category(db_session, name="Alpha Category")
    create_product(db_session, category_id=zeta_category.id, sku="SORT-CAT-1", name="In Zeta")
    create_product(db_session, category_id=alpha_category.id, sku="SORT-CAT-2", name="In Alpha")

    # Act
    products, _ = service.list_products(sort_by="category", sort_dir="asc")

    # Assert
    assert [p.name for p in products] == ["In Alpha", "In Zeta"]
