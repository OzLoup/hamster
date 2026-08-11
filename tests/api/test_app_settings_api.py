from app.core.config import settings as app_config

BASE_URL = "/api/v1/settings"


def test_get_settings_returns_default_business_name(client):
    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["business_name"] == app_config.app_name


def test_update_settings_returns_200_and_updated_business_name(client):
    # Arrange
    update_body = {"business_name": "Ferretería El Tornillo"}

    # Act
    response = client.put(BASE_URL, json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["business_name"] == "Ferretería El Tornillo"

    follow_up = client.get(BASE_URL)
    assert follow_up.json()["business_name"] == "Ferretería El Tornillo"


def test_update_settings_returns_422_for_empty_business_name(client):
    # Act
    response = client.put(BASE_URL, json={"business_name": ""})

    # Assert
    assert response.status_code == 422


def test_update_settings_returns_422_for_missing_business_name(client):
    # Act
    response = client.put(BASE_URL, json={})

    # Assert
    assert response.status_code == 422
