from tests.factories import create_user

BASE_URL = "/api/v1/admin/superusers"


def test_list_superusers_returns_the_acting_superuser(superuser_client):
    # Act
    response = superuser_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["email"] == "superuser@hamster.com"


def test_create_superuser_returns_201(superuser_client):
    # Arrange
    request_body = {
        "email": "second-root@hamster.com",
        "password": "Password123",
        "full_name": "Second Root",
    }

    # Act
    response = superuser_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "second-root@hamster.com"
    assert payload["is_active"] is True
    assert "password" not in payload
    assert "hashed_password" not in payload


def test_create_superuser_returns_409_for_duplicate_email(superuser_client):
    # Arrange
    request_body = {
        "email": "superuser@hamster.com",
        "password": "Password123",
        "full_name": "Duplicate",
    }

    # Act
    response = superuser_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 409


def test_create_superuser_returns_422_for_invalid_payload(superuser_client):
    # Act
    response = superuser_client.post(BASE_URL, json={"email": "not-an-email", "password": "short"})

    # Assert
    assert response.status_code == 422


def test_deactivate_and_activate_superuser(superuser_client, db_session):
    # Arrange
    target = create_user(
        db_session, email="toggleme@hamster.com", role=None, business_id=None, is_superuser=True
    )

    # Act
    deactivate_response = superuser_client.post(f"{BASE_URL}/{target.id}/deactivate")

    # Assert
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    # Act
    activate_response = superuser_client.post(f"{BASE_URL}/{target.id}/activate")

    # Assert
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_deactivate_self_returns_400(superuser_client, db_session):
    # Arrange
    from app.models.user import User

    self_user = db_session.query(User).filter_by(email="superuser@hamster.com").first()

    # Act
    response = superuser_client.post(f"{BASE_URL}/{self_user.id}/deactivate")

    # Assert
    assert response.status_code == 400


def test_superuser_endpoints_require_superuser(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 403


def test_superuser_endpoints_forbidden_for_seller(seller_client):
    # Act
    response = seller_client.get(BASE_URL)

    # Assert
    assert response.status_code == 403
