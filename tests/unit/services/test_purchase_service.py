from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.product import Product
from app.models.purchase import Purchase
from app.models.supplier import Supplier
from app.schemas.purchase import PurchaseCreate, PurchaseUpdate
from app.schemas.purchase_item import PurchaseItemCreate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.purchase_service import PurchaseService
from tests.factories import create_category, create_product, create_supplier


@pytest.fixture()
def service(db_session):
    return PurchaseService(db_session)


def _build_purchase_create_payload(
    *,
    reference: str,
    supplier_id: int,
    product_id: int,
    quantity: int,
    unit_cost: Decimal,
) -> PurchaseCreate:
    subtotal = (unit_cost * quantity).quantize(Decimal("0.01"))
    return PurchaseCreate(
        reference=reference,
        supplier_id=supplier_id,
        total_amount=subtotal,
        purchase_items=[
            PurchaseItemCreate(
                product_id=product_id,
                quantity=quantity,
                unit_cost=unit_cost,
                subtotal=subtotal,
            )
        ],
    )


def test_create_purchase_success_increments_stock_and_updates_cost(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(
        db_session,
        category_id=category.id,
        sku="PUR-KB-100",
        stock_quantity=10,
        cost=Decimal("40.00"),
    )
    payload = _build_purchase_create_payload(
        reference="PUR-001",
        supplier_id=supplier.id,
        product_id=product.id,
        quantity=5,
        unit_cost=Decimal("35.50"),
    )

    # Act
    created = service.create_purchase(payload)

    # Assert
    assert created.id is not None
    assert created.reference == "PUR-001"
    assert len(created.purchase_items) == 1

    refreshed = db_session.get(Product, product.id)
    assert refreshed.stock_quantity == 15
    assert refreshed.cost == Decimal("35.50")


def test_create_purchase_with_missing_supplier_raises_not_found(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    product = create_product(db_session, category_id=category.id, sku="PUR-KB-101")
    payload = _build_purchase_create_payload(
        reference="PUR-002",
        supplier_id=999,
        product_id=product.id,
        quantity=1,
        unit_cost=Decimal("10.00"),
    )

    # Act / Assert
    with pytest.raises(NotFoundError, match="Supplier 999 was not found"):
        service.create_purchase(payload)


def test_create_purchase_with_inactive_supplier_raises_validation_error(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    service.db.get(Supplier, supplier.id).is_active = False
    db_session.commit()
    product = create_product(db_session, category_id=category.id, sku="PUR-KB-102")
    payload = _build_purchase_create_payload(
        reference="PUR-003",
        supplier_id=supplier.id,
        product_id=product.id,
        quantity=1,
        unit_cost=Decimal("10.00"),
    )

    # Act / Assert
    with pytest.raises(ValidationError, match="inactive and cannot receive new purchases"):
        service.create_purchase(payload)


def test_create_purchase_duplicate_reference_raises_conflict(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-KB-200")
    service.create_purchase(
        _build_purchase_create_payload(
            reference="PUR-004",
            supplier_id=supplier.id,
            product_id=product.id,
            quantity=1,
            unit_cost=Decimal("10.00"),
        )
    )
    duplicate_payload = _build_purchase_create_payload(
        reference="PUR-004",
        supplier_id=supplier.id,
        product_id=product.id,
        quantity=1,
        unit_cost=Decimal("10.00"),
    )

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_purchase(duplicate_payload)


def test_create_purchase_with_invalid_total_raises_validation_error(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-KB-201")
    payload = PurchaseCreate(
        reference="PUR-005",
        supplier_id=supplier.id,
        total_amount=Decimal("999.99"),
        purchase_items=[
            PurchaseItemCreate(
                product_id=product.id,
                quantity=1,
                unit_cost=Decimal("10.00"),
                subtotal=Decimal("10.00"),
            )
        ],
    )

    # Act / Assert
    with pytest.raises(ValidationError, match="total_amount does not match"):
        service.create_purchase(payload)


def test_update_purchase_success(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-KB-300")
    created = service.create_purchase(
        _build_purchase_create_payload(
            reference="PUR-006",
            supplier_id=supplier.id,
            product_id=product.id,
            quantity=1,
            unit_cost=Decimal("10.00"),
        )
    )
    update_payload = PurchaseUpdate(reference="PUR-006-UPDATED", total_amount=Decimal("10.00"))

    # Act
    updated = service.update_purchase(created.id, update_payload)

    # Assert
    assert updated.id == created.id
    assert updated.reference == "PUR-006-UPDATED"


def test_update_purchase_duplicate_reference_raises_conflict(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics", description="Category for purchase tests")
    supplier = create_supplier(db_session, name="Acme Supplies")
    first_product = create_product(db_session, category_id=category.id, sku="PUR-KB-400")
    second_product = create_product(db_session, category_id=category.id, sku="PUR-KB-401")

    first_purchase = service.create_purchase(
        _build_purchase_create_payload(
            reference="PUR-007",
            supplier_id=supplier.id,
            product_id=first_product.id,
            quantity=1,
            unit_cost=Decimal("10.00"),
        )
    )
    service.create_purchase(
        _build_purchase_create_payload(
            reference="PUR-008",
            supplier_id=supplier.id,
            product_id=second_product.id,
            quantity=1,
            unit_cost=Decimal("10.00"),
        )
    )
    duplicate_ref_payload = PurchaseUpdate(reference="PUR-008")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.update_purchase(first_purchase.id, duplicate_ref_payload)


def test_delete_purchase_not_supported_in_service_contract(service):
    # Arrange
    method_name = "delete_purchase"

    # Act
    has_delete_method = hasattr(service, method_name)

    # Assert
    assert has_delete_method is False


def test_create_purchase_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    line = PurchaseItemCreate(
        product_id=1,
        quantity=1,
        unit_cost=Decimal("10.00"),
        subtotal=Decimal("10.00"),
    )
    payload = PurchaseCreate(reference="PUR-009", supplier_id=1, total_amount=Decimal("10.00"), purchase_items=[line])

    supplier = Supplier(id=1, name="Acme Supplies", is_active=True)
    product = Product(
        id=1,
        category_id=1,
        name="Mechanical Keyboard",
        sku="PUR-KB-500",
        stock_quantity=10,
        cost=Decimal("40.00"),
        sale_price=Decimal("79.99"),
    )

    def get_side_effect(model, _id):
        return supplier if model is Supplier else product

    db = MagicMock()
    db.scalar.return_value = None
    db.get.side_effect = get_side_effect
    db.commit.side_effect = SQLAlchemyError("db down")

    def assign_purchase_id(entity):
        if isinstance(entity, Purchase):
            entity.id = 200

    db.add.side_effect = assign_purchase_id

    service = PurchaseService(db)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating purchase"):
        service.create_purchase(payload)
    assert db.rollback.called


def test_update_purchase_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing_purchase = Purchase(id=300, supplier_id=1, reference="PUR-300", total_amount=Decimal("10.00"))

    db = MagicMock()
    db.scalar.side_effect = [existing_purchase, None]
    db.commit.side_effect = SQLAlchemyError("db down")

    service = PurchaseService(db)
    payload = PurchaseUpdate(reference="PUR-300-UPDATED")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating purchase"):
        service.update_purchase(300, payload)
    db.rollback.assert_called_once()
