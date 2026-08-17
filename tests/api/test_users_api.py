from app.models.user import User
from tests.factories import create_business, create_user

BASE_URL = "/api/v1/users"


def test_list_users_returns_the_acting_admin(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["email"] == "admin@test-business.com"


def test_create_user_returns_201(authenticated_client):
    # Arrange
    request_body = {
        "email": "vendedor@test-business.com",
        "password": "Password123",
        "full_name": "Vendedor Uno",
        "role": "seller",
    }

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "vendedor@test-business.com"
    assert payload["role"] == "seller"
    assert payload["is_active"] is True
    assert "password" not in payload
    assert "hashed_password" not in payload


def test_create_user_returns_409_for_duplicate_email(authenticated_client):
    # Arrange
    request_body = {
        "email": "admin@test-business.com",
        "password": "Password123",
        "full_name": "Duplicate",
        "role": "seller",
    }

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 409


def test_create_user_returns_422_for_invalid_payload(authenticated_client):
    # Act
    response = authenticated_client.post(BASE_URL, json={"email": "not-an-email", "password": "short"})

    # Assert
    assert response.status_code == 422


def test_update_user_returns_200(authenticated_client, db_session, business):
    # Arrange
    target = create_user(db_session, email="editme@test-business.com", business_id=business.id, role="seller")

    # Act
    response = authenticated_client.patch(f"{BASE_URL}/{target.id}", json={"full_name": "Nuevo Nombre"})

    # Assert
    assert response.status_code == 200
    assert response.json()["full_name"] == "Nuevo Nombre"


def test_deactivate_and_activate_user(authenticated_client, db_session, business):
    # Arrange
    target = create_user(db_session, email="toggleme@test-business.com", business_id=business.id, role="seller")

    # Act
    deactivate_response = authenticated_client.post(f"{BASE_URL}/{target.id}/deactivate")

    # Assert
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    # Act
    activate_response = authenticated_client.post(f"{BASE_URL}/{target.id}/activate")

    # Assert
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_deactivate_self_returns_400(authenticated_client, db_session):
    # Arrange
    self_user = db_session.query(User).filter_by(email="admin@test-business.com").first()

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{self_user.id}/deactivate")

    # Assert
    assert response.status_code == 400


def test_get_user_from_another_business_returns_404(authenticated_client, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_user = create_user(db_session, email="other-biz-user@nope.com", business_id=other_business.id, role="admin")

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{other_user.id}")

    # Assert
    assert response.status_code == 404


def test_users_endpoints_require_admin_or_coordinator_role(seller_client):
    # Act
    response = seller_client.get(BASE_URL)

    # Assert
    assert response.status_code == 403


def test_coordinator_cannot_create_admin_user(coordinator_client):
    # Arrange
    request_body = {
        "email": "sneaky-admin@test-business.com",
        "password": "Password123",
        "full_name": "Sneaky",
        "role": "admin",
    }

    # Act
    response = coordinator_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 403


def test_coordinator_can_create_seller_user(coordinator_client):
    # Arrange
    request_body = {
        "email": "coordinator-made-seller@test-business.com",
        "password": "Password123",
        "full_name": "Made By Coordinator",
        "role": "seller",
    }

    # Act
    response = coordinator_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
