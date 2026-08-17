import pytest

from app.schemas.user import UserCreate, UserUpdate
from app.services.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.services.user_service import UserService
from tests.factories import create_business, create_user


@pytest.fixture()
def admin_service(db_session, business):
    admin = create_user(db_session, email="admin@biz.com", business_id=business.id, role="admin")
    return UserService(db_session, business.id, admin.id, "admin"), admin


@pytest.fixture()
def coordinator_service(db_session, business):
    coordinator = create_user(db_session, email="coordinator@biz.com", business_id=business.id, role="coordinator")
    return UserService(db_session, business.id, coordinator.id, "coordinator"), coordinator


def test_create_user_success_as_admin(admin_service):
    service, _ = admin_service
    payload = UserCreate(email="new@biz.com", password="Password123", full_name="New User", role="seller")

    # Act
    created = service.create_user(payload)

    # Assert
    assert created.id is not None
    assert created.role == "seller"
    assert created.is_active is True
    assert created.is_superuser is False


def test_create_user_coordinator_can_create_seller(coordinator_service):
    service, _ = coordinator_service
    payload = UserCreate(email="seller@biz.com", password="Password123", full_name="Seller", role="seller")

    # Act
    created = service.create_user(payload)

    # Assert
    assert created.role == "seller"


def test_create_user_coordinator_cannot_create_admin(coordinator_service):
    service, _ = coordinator_service
    payload = UserCreate(email="wannabe-admin@biz.com", password="Password123", full_name="Wannabe", role="admin")

    # Act / Assert
    with pytest.raises(AuthorizationError, match="Only an administrator"):
        service.create_user(payload)


def test_create_user_duplicate_email_raises_conflict(admin_service, db_session, business):
    service, _ = admin_service
    create_user(db_session, email="taken@biz.com", business_id=business.id, role="seller")
    payload = UserCreate(email="taken@biz.com", password="Password123", full_name="Dup", role="seller")

    # Act / Assert
    with pytest.raises(ConflictError, match="already exists"):
        service.create_user(payload)


def test_get_user_from_another_business_raises_not_found(admin_service, db_session):
    service, _ = admin_service
    other_business = create_business(db_session, name="Other Business")
    other_user = create_user(db_session, email="other@biz.com", business_id=other_business.id, role="admin")

    # Act / Assert
    with pytest.raises(NotFoundError):
        service.get_user(other_user.id)


def test_update_user_coordinator_cannot_edit_admin(coordinator_service, db_session, business):
    service, _ = coordinator_service
    admin = create_user(db_session, email="theadmin@biz.com", business_id=business.id, role="admin")

    # Act / Assert
    with pytest.raises(AuthorizationError, match="Only an administrator can manage"):
        service.update_user(admin.id, UserUpdate(full_name="Renamed"))


def test_update_user_coordinator_cannot_promote_to_admin(coordinator_service, db_session, business):
    service, _ = coordinator_service
    seller = create_user(db_session, email="theseller@biz.com", business_id=business.id, role="seller")

    # Act / Assert
    with pytest.raises(AuthorizationError, match="Only an administrator can promote"):
        service.update_user(seller.id, UserUpdate(role="admin"))


def test_update_user_admin_can_edit_admin(admin_service, db_session, business):
    service, _ = admin_service
    other_admin = create_user(db_session, email="otheradmin@biz.com", business_id=business.id, role="admin")

    # Act
    updated = service.update_user(other_admin.id, UserUpdate(full_name="Renamed Admin"))

    # Assert
    assert updated.full_name == "Renamed Admin"


def test_update_user_changes_password(admin_service, db_session, business):
    from app.core.security import verify_password

    service, _ = admin_service
    seller = create_user(db_session, email="pwtest@biz.com", business_id=business.id, role="seller", password="OldPass123")

    # Act
    updated = service.update_user(seller.id, UserUpdate(password="NewPass123"))

    # Assert
    assert verify_password("NewPass123", updated.hashed_password) is True


def test_set_active_status_cannot_deactivate_self(admin_service):
    service, admin = admin_service

    # Act / Assert
    with pytest.raises(ValidationError, match="cannot deactivate your own account"):
        service.set_active_status(admin.id, False)


def test_set_active_status_coordinator_cannot_deactivate_admin(coordinator_service, db_session, business):
    service, _ = coordinator_service
    admin = create_user(db_session, email="theadmin2@biz.com", business_id=business.id, role="admin")

    # Act / Assert
    with pytest.raises(AuthorizationError, match="Only an administrator can manage"):
        service.set_active_status(admin.id, False)


def test_set_active_status_coordinator_can_deactivate_seller(coordinator_service, db_session, business):
    service, _ = coordinator_service
    seller = create_user(db_session, email="theseller2@biz.com", business_id=business.id, role="seller")

    # Act
    deactivated = service.set_active_status(seller.id, False)

    # Assert
    assert deactivated.is_active is False


def test_list_users_only_includes_this_business(admin_service, db_session):
    service, admin = admin_service
    other_business = create_business(db_session, name="Other Business")
    create_user(db_session, email="notmine@biz.com", business_id=other_business.id, role="admin")

    # Act
    users = service.list_users()

    # Assert
    assert [u.id for u in users] == [admin.id]
