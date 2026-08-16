from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError
from app.services.supplier_service import SupplierService
from tests.factories import create_business


@pytest.fixture()
def service(db_session, business):
    return SupplierService(db_session, business.id)


def test_create_supplier_success(service):
    # Arrange
    payload = SupplierCreate(name="Acme Supplies", contact_name="Jane Doe", phone="555-0100", email="jane@acmesupplies.com")

    # Act
    created = service.create_supplier(payload)

    # Assert
    assert created.id is not None
    assert created.name == "Acme Supplies"
    assert created.is_active is True


def test_create_supplier_duplicate_name_raises_conflict(service):
    # Arrange
    service.create_supplier(SupplierCreate(name="Acme Supplies"))
    duplicate_payload = SupplierCreate(name="Acme Supplies")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_supplier(duplicate_payload)


def test_update_supplier_success(service):
    # Arrange
    created = service.create_supplier(SupplierCreate(name="Acme Supplies"))
    update_payload = SupplierUpdate(name="Acme Wholesale", phone="555-0199")

    # Act
    updated = service.update_supplier(created.id, update_payload)

    # Assert
    assert updated.id == created.id
    assert updated.name == "Acme Wholesale"
    assert updated.phone == "555-0199"


def test_update_supplier_duplicate_name_raises_conflict(service):
    # Arrange
    first = service.create_supplier(SupplierCreate(name="Acme Supplies"))
    service.create_supplier(SupplierCreate(name="Beta Traders"))
    duplicate_payload = SupplierUpdate(name="Beta Traders")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.update_supplier(first.id, duplicate_payload)


def test_set_active_status_deactivates_and_reactivates_supplier(service):
    # Arrange
    supplier = service.create_supplier(SupplierCreate(name="Acme Supplies"))
    assert supplier.is_active is True

    # Act
    deactivated = service.set_active_status(supplier.id, False)

    # Assert
    assert deactivated.is_active is False

    # Act
    reactivated = service.set_active_status(supplier.id, True)

    # Assert
    assert reactivated.is_active is True


def test_set_active_status_missing_supplier_raises_not_found(service):
    # Act / Assert
    with pytest.raises(NotFoundError, match="Supplier 999 was not found"):
        service.set_active_status(999, False)


def test_get_supplier_from_another_business_raises_not_found(service, db_session):
    # Arrange
    created = service.create_supplier(SupplierCreate(name="Acme Supplies"))
    other_business = create_business(db_session, name="Other Business")
    other_service = SupplierService(db_session, other_business.id)

    # Act / Assert
    with pytest.raises(NotFoundError):
        other_service.get_supplier(created.id)


def test_delete_supplier_success(service, db_session):
    # Arrange
    created = service.create_supplier(SupplierCreate(name="Acme Supplies"))

    # Act
    service.delete_supplier(created.id)

    # Assert
    deleted = db_session.get(Supplier, created.id)
    assert deleted is None


def test_create_supplier_integrity_error_raises_conflict_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.scalar.return_value = None
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception("constraint"))
    service = SupplierService(db, business_id=1)
    payload = SupplierCreate(name="Acme Supplies")

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be created due to a data conflict"):
        service.create_supplier(payload)
    db.rollback.assert_called_once()


def test_create_supplier_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    db = MagicMock()
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")
    service = SupplierService(db, business_id=1)
    payload = SupplierCreate(name="Acme Supplies")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while creating supplier"):
        service.create_supplier(payload)
    db.rollback.assert_called_once()


def test_update_supplier_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Supplier(id=10, business_id=1, name="Acme Supplies", is_active=True)

    db = MagicMock()
    db.get.return_value = existing
    db.scalar.return_value = None
    db.commit.side_effect = SQLAlchemyError("db down")

    service = SupplierService(db, business_id=1)
    payload = SupplierUpdate(name="Acme Wholesale")

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating supplier"):
        service.update_supplier(10, payload)
    db.rollback.assert_called_once()


def test_set_active_status_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Supplier(id=11, business_id=1, name="Acme Supplies", is_active=True)

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = SupplierService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while updating supplier status"):
        service.set_active_status(11, False)
    db.rollback.assert_called_once()


def test_delete_supplier_sqlalchemy_error_raises_service_error_and_rolls_back():
    # Arrange
    existing = Supplier(id=20, business_id=1, name="Acme Supplies", is_active=True)

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = SQLAlchemyError("db down")

    service = SupplierService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ServiceError, match="Unexpected database error while deleting supplier"):
        service.delete_supplier(20)
    db.rollback.assert_called_once()


def test_delete_supplier_integrity_error_raises_conflict_and_rolls_back():
    # Arrange: deleting a supplier still referenced by purchases violates the FK constraint.
    existing = Supplier(id=21, business_id=1, name="Acme Supplies", is_active=True)

    db = MagicMock()
    db.get.return_value = existing
    db.commit.side_effect = IntegrityError("DELETE", {}, Exception("foreign key constraint"))

    service = SupplierService(db, business_id=1)

    # Act / Assert
    with pytest.raises(ConflictError, match="could not be deleted because it has associated purchase records"):
        service.delete_supplier(21)
    db.rollback.assert_called_once()
