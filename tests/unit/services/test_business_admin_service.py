import pytest

from app.schemas.business import BusinessCreateWithAdmin
from app.services.business_admin_service import BusinessAdminService
from app.services.exceptions import ConflictError, NotFoundError
from tests.factories import create_business, create_user


@pytest.fixture()
def service(db_session):
    return BusinessAdminService(db_session)


def test_create_business_creates_business_and_first_admin(service, db_session):
    payload = BusinessCreateWithAdmin(
        business_name="Papelería El Trébol",
        admin_email="juan@trebol.com",
        admin_full_name="Juan Pérez",
        admin_password="Password123",
    )

    # Act
    business = service.create_business(payload)

    # Assert
    assert business.id is not None
    assert business.name == "Papelería El Trébol"
    assert business.is_active is True

    from app.models.user import User

    admin = db_session.query(User).filter_by(email="juan@trebol.com").first()
    assert admin is not None
    assert admin.business_id == business.id
    assert admin.role == "admin"
    assert admin.is_superuser is False


def test_create_business_duplicate_admin_email_raises_conflict(service, db_session, business):
    create_user(db_session, email="taken@biz.com", business_id=business.id, role="admin")
    payload = BusinessCreateWithAdmin(
        business_name="Another Business",
        admin_email="taken@biz.com",
        admin_full_name="Someone",
        admin_password="Password123",
    )

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_business(payload)


def test_get_business_not_found_raises(service):
    with pytest.raises(NotFoundError):
        service.get_business(999999)


def test_list_businesses_returns_all(service, db_session):
    create_business(db_session, name="Business A")
    create_business(db_session, name="Business B")

    # Act
    businesses = service.list_businesses()

    # Assert
    assert {b.name for b in businesses} == {"Business A", "Business B"}


def test_set_active_status_deactivates_and_reactivates(service, db_session):
    business = create_business(db_session, name="Toggle Me")

    # Act
    deactivated = service.set_active_status(business.id, False)

    # Assert
    assert deactivated.is_active is False

    # Act
    reactivated = service.set_active_status(business.id, True)

    # Assert
    assert reactivated.is_active is True
