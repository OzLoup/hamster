from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.open_tab import OpenTab
from app.models.product import Product
from app.schemas.open_tab import OpenTabCloseRequest, OpenTabCreate, OpenTabItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.open_tab_service import OpenTabService
from tests.factories import create_business, create_category, create_product


@pytest.fixture()
def service(db_session, business):
    return OpenTabService(db_session, business.id)


def test_create_tab_success(service):
    # Act
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Assert
    assert tab.id is not None
    assert tab.name == "Mesa 1"
    assert tab.total == Decimal("0.00")
    assert tab.items == []


def test_create_tab_duplicate_name_raises_conflict(service):
    # Arrange
    service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_tab(OpenTabCreate(name="Mesa 1"))


def test_get_tab_missing_raises_not_found(service):
    # Act / Assert
    with pytest.raises(NotFoundError, match="Open tab 999 was not found"):
        service.get_tab(999)


def test_add_item_decrements_stock_and_creates_item(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10, sale_price=Decimal("5.00"))
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act
    updated = service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=3))

    # Assert
    assert len(updated.items) == 1
    item = updated.items[0]
    assert item.quantity == 3
    assert item.unit_price == Decimal("5.00")
    assert item.subtotal == Decimal("15.00")
    assert updated.total == Decimal("15.00")

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 7


def test_add_item_accumulates_existing_line(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10, sale_price=Decimal("5.00"))
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))
    service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=2))

    # Act
    updated = service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=1))

    # Assert
    assert len(updated.items) == 1
    assert updated.items[0].quantity == 3
    assert updated.items[0].subtotal == Decimal("15.00")

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 7


def test_add_item_missing_product_raises_not_found(service):
    # Arrange
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(NotFoundError, match="Product 999 was not found"):
        service.add_item(tab.id, OpenTabItemCreate(product_id=999, quantity=1))


def test_add_item_rejects_product_from_another_business(service, db_session):
    # Arrange
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))
    other_business = create_business(db_session, name="Other Business")
    other_category = create_category(db_session, business_id=other_business.id)
    other_product = create_product(db_session, business_id=other_business.id, category_id=other_category.id)

    # Act / Assert
    with pytest.raises(NotFoundError, match=f"Product {other_product.id} was not found"):
        service.add_item(tab.id, OpenTabItemCreate(product_id=other_product.id, quantity=1))


def test_create_tab_same_name_allowed_across_different_businesses(service, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_service = OpenTabService(db_session, other_business.id)
    service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act
    created = other_service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Assert
    assert created.id is not None


def test_add_item_inactive_product_raises_validation_error(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10)
    product.is_active = False
    db_session.commit()
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(ValidationError, match="inactive"):
        service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=1))


def test_add_item_insufficient_stock_raises_validation_error(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=2)
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(ValidationError, match="Insufficient stock"):
        service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=5))


def test_remove_item_restores_stock(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10)
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))
    added = service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=4))
    item_id = added.items[0].id

    # Act
    updated = service.remove_item(tab.id, item_id)

    # Assert
    assert updated.items == []
    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 10


def test_remove_item_missing_raises_not_found(service):
    # Arrange
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(NotFoundError, match="Item 999 was not found"):
        service.remove_item(tab.id, 999)


def test_close_tab_creates_sale_and_empties_items(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10, sale_price=Decimal("5.00"))
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))
    service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=3))

    # Act
    sale = service.close_tab(tab.id, OpenTabCloseRequest(payment_method="cash"))

    # Assert
    assert sale.id is not None
    assert sale.total_amount == Decimal("15.00")
    assert len(sale.sale_items) == 1
    assert sale.sale_items[0].product_id == product.id
    assert sale.sale_items[0].quantity == 3

    refreshed_tab = service.get_tab(tab.id)
    assert refreshed_tab.items == []

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 7


def test_close_tab_with_no_items_raises_validation_error(service):
    # Arrange
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))

    # Act / Assert
    with pytest.raises(ValidationError, match="Cannot close an open tab with no items"):
        service.close_tab(tab.id, OpenTabCloseRequest(payment_method="cash"))


def test_delete_tab_with_items_restores_stock(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10)
    tab = service.create_tab(OpenTabCreate(name="Mesa 1"))
    service.add_item(tab.id, OpenTabItemCreate(product_id=product.id, quantity=4))

    # Act
    service.delete_tab(tab.id)

    # Assert
    with pytest.raises(NotFoundError):
        service.get_tab(tab.id)
    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 10


def test_delete_tab_missing_raises_not_found(service):
    # Act / Assert
    with pytest.raises(NotFoundError, match="Open tab 999 was not found"):
        service.delete_tab(999)


def test_create_tab_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")

    service = OpenTabService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating open tab"):
        service.create_tab(OpenTabCreate(name="Mesa 1"))
    assert db.rollback.called


def test_add_item_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    tab = OpenTab(id=1, business_id=1, name="Mesa 1")
    product = Product(
        id=1,
        business_id=1,
        category_id=1,
        name="Producto",
        sku="PRD-000001",
        stock_quantity=10,
        cost=Decimal("1.00"),
        sale_price=Decimal("5.00"),
        is_active=True,
    )

    db = MagicMock()

    def scalar_side_effect(stmt):
        return tab

    db.scalar.side_effect = scalar_side_effect
    db.get.return_value = product
    db.commit.side_effect = SQLAlchemyError("db down")

    service = OpenTabService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while adding item to open tab"):
        service.add_item(1, OpenTabItemCreate(product_id=1, quantity=1))
    assert db.rollback.called
