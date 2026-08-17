from tests.factories import create_business

BASE_URL = "/api/v1/admin/businesses"


def test_list_businesses_returns_all(superuser_client, db_session):
    # Arrange
    create_business(db_session, name="Business A")
    create_business(db_session, name="Business B")

    # Act
    response = superuser_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    names = {b["name"] for b in response.json()}
    assert {"Business A", "Business B"}.issubset(names)


def test_create_business_returns_201(superuser_client):
    # Arrange
    request_body = {
        "business_name": "Papelería El Trébol",
        "admin_email": "juan@trebol.com",
        "admin_full_name": "Juan Pérez",
        "admin_password": "Password123",
    }

    # Act
    response = superuser_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Papelería El Trébol"
    assert payload["is_active"] is True


def test_create_business_returns_409_for_duplicate_admin_email(superuser_client, db_session, business):
    from tests.factories import create_user

    create_user(db_session, email="taken@biz.com", business_id=business.id, role="admin")
    request_body = {
        "business_name": "Another Business",
        "admin_email": "taken@biz.com",
        "admin_full_name": "Someone",
        "admin_password": "Password123",
    }

    # Act
    response = superuser_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 409


def test_create_business_returns_422_for_invalid_payload(superuser_client):
    # Act
    response = superuser_client.post(BASE_URL, json={"business_name": "", "admin_email": "not-an-email"})

    # Assert
    assert response.status_code == 422


def test_deactivate_and_activate_business(superuser_client, db_session):
    # Arrange
    target = create_business(db_session, name="Toggle Me")

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


def test_get_business_returns_404_for_unknown_id(superuser_client):
    # Act
    response = superuser_client.get(f"{BASE_URL}/999999")

    # Assert
    assert response.status_code == 404


def test_business_admin_endpoints_require_superuser(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 403


def test_business_admin_endpoints_forbidden_for_coordinator(coordinator_client):
    # Act
    response = coordinator_client.get(BASE_URL)

    # Assert
    assert response.status_code == 403
