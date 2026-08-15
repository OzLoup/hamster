import pytest

from app.services.auth_service import AuthService
from app.services.exceptions import AuthenticationError
from tests.factories import create_business, create_user


@pytest.fixture()
def service(db_session):
    return AuthService(db_session)


def test_authenticate_success_returns_user(service, db_session):
    # Arrange
    business = create_business(db_session, name="Acme")
    create_user(db_session, email="admin@acme.com", password="Password123", business_id=business.id)

    # Act
    user = service.authenticate("admin@acme.com", "Password123")

    # Assert
    assert user.email == "admin@acme.com"
    assert user.business_id == business.id


def test_authenticate_wrong_password_raises_authentication_error(service, db_session):
    # Arrange
    create_user(db_session, email="admin@acme.com", password="Password123")

    # Act / Assert
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        service.authenticate("admin@acme.com", "WrongPassword")


def test_authenticate_unknown_email_raises_authentication_error(service):
    # Act / Assert
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        service.authenticate("nobody@acme.com", "Password123")


def test_authenticate_inactive_user_raises_authentication_error(service, db_session):
    # Arrange
    create_user(db_session, email="admin@acme.com", password="Password123", is_active=False)

    # Act / Assert
    with pytest.raises(AuthenticationError, match="deactivated"):
        service.authenticate("admin@acme.com", "Password123")
