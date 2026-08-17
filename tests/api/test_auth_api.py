from app.core.security import SESSION_COOKIE_NAME
from tests.factories import create_business, create_user

BASE_URL = "/api/v1/auth"


def test_login_success_returns_current_user_and_sets_session_cookie(client, db_session):
    # Arrange
    business = create_business(db_session, name="Acme")
    create_user(
        db_session,
        email="admin@acme.com",
        password="Password123",
        full_name="Admin Acme",
        role="admin",
        business_id=business.id,
    )

    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@acme.com"
    assert payload["full_name"] == "Admin Acme"
    assert payload["role"] == "admin"
    assert payload["is_superuser"] is False
    assert payload["business_id"] == business.id
    assert payload["business_name"] == "Acme"
    assert SESSION_COOKIE_NAME in response.cookies


def test_login_returns_business_name_none_for_superuser(client, db_session):
    # Arrange
    create_user(
        db_session,
        email="root@hamster.com",
        password="Password123",
        full_name="Root",
        role=None,
        business_id=None,
        is_superuser=True,
    )

    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "root@hamster.com", "password": "Password123"})

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_superuser"] is True
    assert payload["business_id"] is None
    assert payload["business_name"] is None


def test_login_returns_401_for_wrong_password(client, db_session):
    # Arrange
    create_user(db_session, email="admin@acme.com", password="Password123")

    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "WrongPassword"})

    # Assert
    assert response.status_code == 401


def test_login_returns_401_for_unknown_email(client):
    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "nobody@acme.com", "password": "Password123"})

    # Assert
    assert response.status_code == 401


def test_login_returns_401_for_inactive_user(client, db_session):
    # Arrange
    create_user(db_session, email="admin@acme.com", password="Password123", is_active=False)

    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})

    # Assert
    assert response.status_code == 401


def test_login_returns_422_for_invalid_payload(client):
    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "not-an-email", "password": "short"})

    # Assert
    assert response.status_code == 422


def test_me_returns_401_without_session_cookie(client):
    # Act
    response = client.get(f"{BASE_URL}/me")

    # Assert
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_session(client, db_session):
    # Arrange
    business = create_business(db_session, name="Acme")
    create_user(db_session, email="admin@acme.com", password="Password123", business_id=business.id)
    client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})

    # Act
    response = client.get(f"{BASE_URL}/me")

    # Assert
    assert response.status_code == 200
    assert response.json()["email"] == "admin@acme.com"


def test_login_returns_401_for_deactivated_business(client, db_session):
    # Arrange
    business = create_business(db_session, name="Acme", is_active=False)
    create_user(db_session, email="admin@acme.com", password="Password123", business_id=business.id)

    # Act
    response = client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})

    # Assert
    assert response.status_code == 401


def test_deactivating_business_locks_out_already_logged_in_user(client, db_session):
    # Arrange
    business = create_business(db_session, name="Acme")
    create_user(db_session, email="admin@acme.com", password="Password123", business_id=business.id)
    client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})
    assert client.get(f"{BASE_URL}/me").status_code == 200

    # Act
    business.is_active = False
    db_session.commit()

    # Assert
    assert client.get(f"{BASE_URL}/me").status_code == 401


def test_logout_clears_session_so_me_requires_login_again(client, db_session):
    # Arrange
    create_user(db_session, email="admin@acme.com", password="Password123")
    client.post(f"{BASE_URL}/login", json={"email": "admin@acme.com", "password": "Password123"})
    assert client.get(f"{BASE_URL}/me").status_code == 200

    # Act
    logout_response = client.post(f"{BASE_URL}/logout")

    # Assert
    assert logout_response.status_code == 200
    assert client.get(f"{BASE_URL}/me").status_code == 401
