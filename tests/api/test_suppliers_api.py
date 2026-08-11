from tests.factories import create_supplier, supplier_request_body

BASE_URL = "/api/v1/suppliers"


def test_list_suppliers_returns_empty_list(client):
    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_list_suppliers_returns_created_suppliers(client, db_session):
    # Arrange
    first = create_supplier(db_session, name="Acme Supplies")
    second = create_supplier(db_session, name="Beta Traders")

    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["id"] == first.id
    assert payload[1]["id"] == second.id


def test_get_supplier_by_id_returns_supplier(client, db_session):
    # Arrange
    supplier = create_supplier(db_session, name="Acme Supplies", contact_name="Jane Doe")

    # Act
    response = client.get(f"{BASE_URL}/{supplier.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == supplier.id
    assert payload["name"] == "Acme Supplies"
    assert payload["contact_name"] == "Jane Doe"
    assert payload["is_active"] is True


def test_get_supplier_by_id_returns_404_when_not_found(client):
    # Arrange
    missing_id = 9999

    # Act
    response = client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Supplier {missing_id} was not found."


def test_create_supplier_returns_201_with_expected_body(client):
    # Arrange
    request_body = supplier_request_body(name="Acme Supplies")

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["name"] == "Acme Supplies"
    assert payload["is_active"] is True


def test_create_supplier_returns_409_for_duplicate_name(client, db_session):
    # Arrange
    create_supplier(db_session, name="Acme Supplies")
    duplicate_body = supplier_request_body(name="Acme Supplies")

    # Act
    response = client.post(BASE_URL, json=duplicate_body)

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_supplier_returns_422_for_invalid_payload(client):
    # Arrange
    invalid_body = {"name": ""}

    # Act
    response = client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_update_supplier_returns_200_and_updated_body(client, db_session):
    # Arrange
    supplier = create_supplier(db_session, name="Acme Supplies")
    update_body = supplier_request_body(name="Acme Wholesale", phone="555-0199")

    # Act
    response = client.put(f"{BASE_URL}/{supplier.id}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == supplier.id
    assert payload["name"] == "Acme Wholesale"
    assert payload["phone"] == "555-0199"


def test_update_supplier_returns_404_when_not_found(client):
    # Arrange
    missing_id = 4321
    update_body = supplier_request_body(name="Acme Wholesale")

    # Act
    response = client.put(f"{BASE_URL}/{missing_id}", json=update_body)

    # Assert
    assert response.status_code == 404


def test_deactivate_supplier_returns_200_and_flips_is_active(client, db_session):
    # Arrange
    supplier = create_supplier(db_session, name="Acme Supplies")

    # Act
    response = client.post(f"{BASE_URL}/{supplier.id}/deactivate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_supplier_returns_200_and_flips_is_active(client, db_session):
    # Arrange
    supplier = create_supplier(db_session, name="Acme Supplies")
    client.post(f"{BASE_URL}/{supplier.id}/deactivate")

    # Act
    response = client.post(f"{BASE_URL}/{supplier.id}/activate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_list_suppliers_filters_by_is_active(client, db_session):
    # Arrange
    active_supplier = create_supplier(db_session, name="Acme Supplies")
    inactive_supplier = create_supplier(db_session, name="Beta Traders")
    client.post(f"{BASE_URL}/{inactive_supplier.id}/deactivate")

    # Act
    active_response = client.get(BASE_URL, params={"is_active": "true"})
    inactive_response = client.get(BASE_URL, params={"is_active": "false"})

    # Assert
    active_ids = [item["id"] for item in active_response.json()]
    inactive_ids = [item["id"] for item in inactive_response.json()]
    assert active_supplier.id in active_ids
    assert inactive_supplier.id not in active_ids
    assert inactive_supplier.id in inactive_ids


def test_delete_supplier_returns_204_and_removes_record(client, db_session):
    # Arrange
    supplier = create_supplier(db_session, name="Acme Supplies")

    # Act
    response = client.delete(f"{BASE_URL}/{supplier.id}")

    # Assert
    assert response.status_code == 204
    check = client.get(f"{BASE_URL}/{supplier.id}")
    assert check.status_code == 404


def test_delete_supplier_returns_404_when_not_found(client):
    # Arrange
    missing_id = 5432

    # Act
    response = client.delete(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
