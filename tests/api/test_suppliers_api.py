from tests.factories import create_supplier, supplier_request_body

BASE_URL = "/api/v1/suppliers"


def test_list_suppliers_returns_empty_list(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_list_suppliers_returns_created_suppliers(authenticated_client, db_session, business):
    # Arrange
    first = create_supplier(db_session, business_id=business.id, name="Acme Supplies")
    second = create_supplier(db_session, business_id=business.id, name="Beta Traders")

    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["id"] == first.id
    assert payload[1]["id"] == second.id


def test_get_supplier_by_id_returns_supplier(authenticated_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies", contact_name="Jane Doe")

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{supplier.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == supplier.id
    assert payload["name"] == "Acme Supplies"
    assert payload["contact_name"] == "Jane Doe"
    assert payload["is_active"] is True


def test_get_supplier_by_id_returns_404_when_not_found(authenticated_client):
    # Arrange
    missing_id = 9999

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Supplier {missing_id} was not found."


def test_create_supplier_returns_201_with_expected_body(authenticated_client):
    # Arrange
    request_body = supplier_request_body(name="Acme Supplies")

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["name"] == "Acme Supplies"
    assert payload["is_active"] is True


def test_create_supplier_returns_409_for_duplicate_name(authenticated_client, db_session, business):
    # Arrange
    create_supplier(db_session, business_id=business.id, name="Acme Supplies")
    duplicate_body = supplier_request_body(name="Acme Supplies")

    # Act
    response = authenticated_client.post(BASE_URL, json=duplicate_body)

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_supplier_returns_422_for_invalid_payload(authenticated_client):
    # Arrange
    invalid_body = {"name": ""}

    # Act
    response = authenticated_client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_update_supplier_returns_200_and_updated_body(authenticated_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies")
    update_body = supplier_request_body(name="Acme Wholesale", phone="555-0199")

    # Act
    response = authenticated_client.put(f"{BASE_URL}/{supplier.id}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == supplier.id
    assert payload["name"] == "Acme Wholesale"
    assert payload["phone"] == "555-0199"


def test_update_supplier_returns_404_when_not_found(authenticated_client):
    # Arrange
    missing_id = 4321
    update_body = supplier_request_body(name="Acme Wholesale")

    # Act
    response = authenticated_client.put(f"{BASE_URL}/{missing_id}", json=update_body)

    # Assert
    assert response.status_code == 404


def test_deactivate_supplier_returns_200_and_flips_is_active(authenticated_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies")

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{supplier.id}/deactivate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_supplier_returns_200_and_flips_is_active(authenticated_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies")
    authenticated_client.post(f"{BASE_URL}/{supplier.id}/deactivate")

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{supplier.id}/activate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_list_suppliers_filters_by_is_active(authenticated_client, db_session, business):
    # Arrange
    active_supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies")
    inactive_supplier = create_supplier(db_session, business_id=business.id, name="Beta Traders")
    authenticated_client.post(f"{BASE_URL}/{inactive_supplier.id}/deactivate")

    # Act
    active_response = authenticated_client.get(BASE_URL, params={"is_active": "true"})
    inactive_response = authenticated_client.get(BASE_URL, params={"is_active": "false"})

    # Assert
    active_ids = [item["id"] for item in active_response.json()]
    inactive_ids = [item["id"] for item in inactive_response.json()]
    assert active_supplier.id in active_ids
    assert inactive_supplier.id not in active_ids
    assert inactive_supplier.id in inactive_ids


def test_delete_supplier_returns_204_and_removes_record(authenticated_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id, name="Acme Supplies")

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{supplier.id}")

    # Assert
    assert response.status_code == 204
    check = authenticated_client.get(f"{BASE_URL}/{supplier.id}")
    assert check.status_code == 404


def test_delete_supplier_returns_404_when_not_found(authenticated_client):
    # Arrange
    missing_id = 5432

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
