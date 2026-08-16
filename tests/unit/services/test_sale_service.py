from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.product import Product
from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleUpdate
from app.schemas.sale_item import SaleItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.sale_service import SaleService
from tests.factories import create_business, create_category, create_product


@pytest.fixture()
def service(db_session, business):
    return SaleService(db_session, business.id)


def _build_sale_create_payload(
    *,
    reference: str,
    product_id: int,
    quantity: int,
    unit_price: Decimal,
    payment_method: str = "cash",
) -> SaleCreate:
    subtotal = (unit_price * quantity).quantize(Decimal("0.01"))
    return SaleCreate(
        reference=reference,
        payment_method=payment_method,
        total_amount=subtotal,
        sale_items=[
            SaleItemCreate(
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
        ],
    )


def test_create_sale_success_and_decrements_stock(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id, name="Electronics", description="Category for sale tests")
    product = create_product(
        db_session,
        business_id=business.id,
        category_id=category.id,
        sku="SALE-KB-100",
        stock_quantity=10,
        sale_price=Decimal("79.99"),
    )
    payload = _build_sale_create_payload(
        reference="SALE-001",
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("79.99"),
    )

    # Act
    created = service.create_sale(payload)

    # Assert
    assert created.id is not None
    assert created.reference == "SALE-001"
    assert len(created.sale_items) == 1

    refreshed = db_session.get(Product, product.id)
    assert refreshed.stock_quantity == 8


def test_create_sale_duplicate_reference_raises_conflict(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id, name="Electronics", description="Category for sale tests")
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-KB-200")
    service.create_sale(
        _build_sale_create_payload(
            reference="SALE-001",
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("79.99"),
        )
    )
    duplicate_payload = _build_sale_create_payload(
        reference="SALE-001",
        product_id=product.id,
        quantity=1,
        unit_price=Decimal("79.99"),
    )

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_sale(duplicate_payload)


def test_create_sale_with_invalid_total_raises_validation_error(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id, name="Electronics", description="Category for sale tests")
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-KB-201")
    payload = SaleCreate(
        reference="SALE-002",
        payment_method="cash",
        total_amount=Decimal("999.99"),
        sale_items=[
            SaleItemCreate(
                product_id=product.id,
                quantity=1,
                unit_price=Decimal("79.99"),
                subtotal=Decimal("79.99"),
            )
        ],
    )

    # Act / Assert
    with pytest.raises(ValidationError, match="total_amount does not match"):
        service.create_sale(payload)


def test_update_sale_success(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id, name="Electronics", description="Category for sale tests")
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-KB-300")
    created = service.create_sale(
        _build_sale_create_payload(
            reference="SALE-003",
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("79.99"),
        )
    )
    update_payload = SaleUpdate(reference="SALE-003-UPDATED", total_amount=Decimal("79.99"))

    # Act
    updated = service.update_sale(created.id, update_payload)

    # Assert
    assert updated.id == created.id
    assert updated.reference == "SALE-003-UPDATED"
    assert updated.total_amount == Decimal("79.99")


def test_update_sale_duplicate_reference_raises_conflict(service, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id, name="Electronics", description="Category for sale tests")
    first_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-KB-400")
    second_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-KB-401")

    first_sale = service.create_sale(
        _build_sale_create_payload(
            reference="SALE-004",
            product_id=first_product.id,
            quantity=1,
            unit_price=Decimal("79.99"),
        )
    )
    service.create_sale(
        _build_sale_create_payload(
            reference="SALE-005",
            product_id=second_product.id,
            quantity=1,
            unit_price=Decimal("79.99"),
        )
    )
    duplicate_ref_payload = SaleUpdate(reference="SALE-005")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.update_sale(first_sale.id, duplicate_ref_payload)


def test_create_sale_rejects_product_from_another_business(service, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_category = create_category(db_session, business_id=other_business.id, name="Electronics")
    other_product = create_product(db_session, business_id=other_business.id, category_id=other_category.id, sku="OTHER-001")
    payload = _build_sale_create_payload(
        reference="SALE-CROSS-TENANT",
        product_id=other_product.id,
        quantity=1,
        unit_price=Decimal("79.99"),
    )

    # Act / Assert
    with pytest.raises(NotFoundError, match=f"Product {other_product.id} was not found"):
        service.create_sale(payload)


def test_delete_sale_not_supported_in_service_contract(service):
    # Arrange
    method_name = "delete_sale"

    # Act
    has_delete_method = hasattr(service, method_name)

    # Assert
    assert has_delete_method is False


def test_create_sale_integrity_error_raises_conflict_and_rolls_back():
    # Arrange
    line = SaleItemCreate(
        product_id=1,
        quantity=1,
        unit_price=Decimal("79.99"),
        subtotal=Decimal("79.99"),
    )
    payload = SaleCreate(
        reference="SALE-006", payment_method="cash", total_amount=Decimal("79.99"), sale_items=[line]
    )

    product = Product(
        id=1,
        business_id=1,
        category_id=1,
        name="Mechanical Keyboard",
        sku="SALE-KB-500",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.scalar.return_value = None
    db.get.return_value = product
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception("constraint"))

    created_sale = Sale(id=123, reference="SALE-006", payment_method="cash", total_amount=Decimal("79.99"))

    def assign_sale_id(entity):
        if isinstance(entity, Sale):
            entity.id = created_sale.id

    db.add.side_effect = assign_sale_id

    service = SaleService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be created due to a data conflict"):
        service.create_sale(payload)
    assert db.rollback.called


def test_create_sale_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    line = SaleItemCreate(
        product_id=1,
        quantity=1,
        unit_price=Decimal("79.99"),
        subtotal=Decimal("79.99"),
    )
    payload = SaleCreate(
        reference="SALE-007", payment_method="cash", total_amount=Decimal("79.99"), sale_items=[line]
    )

    product = Product(
        id=1,
        business_id=1,
        category_id=1,
        name="Mechanical Keyboard",
        sku="SALE-KB-501",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    db = MagicMock()
    db.scalar.return_value = None
    db.get.return_value = product
    db.commit.side_effect = SQLAlchemyError("db down")

    def assign_sale_id(entity):
        if isinstance(entity, Sale):
            entity.id = 124

    db.add.side_effect = assign_sale_id

    service = SaleService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating sale"):
        service.create_sale(payload)
    assert db.rollback.called


def test_update_sale_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing_sale = Sale(id=300, reference="SALE-300", payment_method="cash", total_amount=Decimal("79.99"))

    db = MagicMock()
    db.scalar.side_effect = [existing_sale, None]
    db.commit.side_effect = SQLAlchemyError("db down")

    service = SaleService(db, business_id=1)
    payload = SaleUpdate(reference="SALE-300-UPDATED")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating sale"):
        service.update_sale(300, payload)
    db.rollback.assert_called_once()
