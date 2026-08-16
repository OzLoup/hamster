from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService
from app.services.exceptions import ConflictError, NotFoundError, ServiceError
from tests.factories import create_business, create_product


@pytest.fixture()
def service(db_session, business):
    return CategoryService(db_session, business.id)


def test_create_category_success(service):
    # Arrange
    payload = CategoryCreate(name="Electronics", description="Devices and accessories")

    # Act
    created = service.create_category(payload)

    # Assert
    assert created.id is not None
    assert created.name == "Electronics"
    assert created.description == "Devices and accessories"


def test_create_category_duplicate_name_raises_conflict(service):
    # Arrange
    service.create_category(CategoryCreate(name="Electronics", description="Original"))
    duplicate_payload = CategoryCreate(name="Electronics", description="Duplicate")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_category(duplicate_payload)


def test_create_category_same_name_allowed_across_different_businesses(service, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_service = CategoryService(db_session, other_business.id)
    service.create_category(CategoryCreate(name="Electronics", description="Business A"))

    # Act
    created = other_service.create_category(CategoryCreate(name="Electronics", description="Business B"))

    # Assert
    assert created.id is not None


def test_update_category_success(service):
    # Arrange
    created = service.create_category(CategoryCreate(name="Electronics", description="Old"))
    update_payload = CategoryUpdate(name="Consumer Electronics", description="Updated")

    # Act
    updated = service.update_category(created.id, update_payload)

    # Assert
    assert updated.id == created.id
    assert updated.name == "Consumer Electronics"
    assert updated.description == "Updated"


def test_update_category_duplicate_name_raises_conflict(service):
    # Arrange
    first = service.create_category(CategoryCreate(name="Electronics", description=None))
    service.create_category(CategoryCreate(name="Office", description=None))
    duplicate_name_payload = CategoryUpdate(name="Office")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.update_category(first.id, duplicate_name_payload)


def test_delete_category_success(service, db_session):
    # Arrange
    created = service.create_category(CategoryCreate(name="Electronics", description="Delete me"))

    # Act
    service.delete_category(created.id)

    # Assert
    deleted = db_session.get(Category, created.id)
    assert deleted is None


def test_delete_category_with_assigned_products_raises_conflict(service, db_session, business):
    # Arrange
    category = service.create_category(CategoryCreate(name="Electronics", description=None))
    create_product(
        db_session,
        business_id=business.id,
        category_id=category.id,
        sku="KB-DELETE-001",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("75.00"),
    )

    # Act / Assert
    with pytest.raises(ConflictError, match="Cannot delete category"):
        service.delete_category(category.id)


def test_get_category_from_another_business_raises_not_found(service, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_service = CategoryService(db_session, other_business.id)
    created = service.create_category(CategoryCreate(name="Electronics", description=None))

    # Act / Assert
    with pytest.raises(NotFoundError):
        other_service.get_category(created.id)


def test_create_category_integrity_error_raises_conflict_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.scalar.return_value = None
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception("constraint"))
    service = CategoryService(db, business_id=1)
    payload = CategoryCreate(name="Electronics", description=None)

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be created due to a data conflict"):
        service.create_category(payload)
    db.rollback.assert_called_once()


def test_create_category_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")
    service = CategoryService(db, business_id=1)
    payload = CategoryCreate(name="Electronics", description=None)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating category"):
        service.create_category(payload)
    db.rollback.assert_called_once()


def test_update_category_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Category(id=10, name="Electronics", description="Old", business_id=1)

    db = MagicMock()
    db.get.return_value = existing
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")

    service = CategoryService(db, business_id=1)
    payload = CategoryUpdate(name="Electronics and Gadgets")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating category"):
        service.update_category(10, payload)
    db.rollback.assert_called_once()


def test_delete_category_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Category(id=20, name="Electronics", description=None, business_id=1)

    db = MagicMock()
    db.get.return_value = existing
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")

    service = CategoryService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while deleting category"):
        service.delete_category(20)
    db.rollback.assert_called_once()
