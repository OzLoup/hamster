from tests.factories import create_category, create_product, product_request_body

BASE_URL = "/api/v1/products"


def test_list_products_returns_empty_payload(client):
    # Arrange
    url = BASE_URL

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 0


def test_list_products_returns_paginated_results(client, db_session):
    # Arrange
    category = create_category(db_session)
    first = create_product(db_session, category_id=category.id, sku="PRD-001", name="Keyboard")
    second = create_product(db_session, category_id=category.id, sku="PRD-002", name="Mouse")

    # Act
    response = client.get(f"{BASE_URL}?page=1&page_size=1")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["total_pages"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == first.id
    assert second.id != payload["items"][0]["id"]


def test_list_products_supports_search_and_category_filter(client, db_session):
    # Arrange
    electronics = create_category(db_session, name="Electronics")
    office = create_category(db_session, name="Office")
    create_product(db_session, category_id=electronics.id, sku="PRD-101", name="Gaming Mouse")
    create_product(db_session, category_id=office.id, sku="PRD-102", name="Office Chair")

    # Act
    response = client.get(f"{BASE_URL}?search=Mouse&category_id={electronics.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "Gaming Mouse"


def test_list_products_returns_422_for_invalid_query_values(client):
    # Arrange
    invalid_query = f"{BASE_URL}?page=0&page_size=101"

    # Act
    response = client.get(invalid_query)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_get_product_by_id_returns_product(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-200")

    # Act
    response = client.get(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["sku"] == "PRD-200"


def test_get_product_by_id_returns_404_when_missing(client):
    # Arrange
    missing_id = 9999

    # Act
    response = client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_create_product_returns_201_and_expected_body(client, db_session):
    # Arrange
    category = create_category(db_session)
    request_body = product_request_body(category_id=category.id, sku="PRD-300")

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["category_id"] == category.id
    assert payload["sku"] == "PRD-300"
    assert payload["name"] == "Mechanical Keyboard"


def test_create_product_returns_409_for_duplicate_sku(client, db_session):
    # Arrange
    category = create_category(db_session)
    create_product(db_session, category_id=category.id, sku="PRD-DUP")
    duplicate_body = product_request_body(category_id=category.id, sku="PRD-DUP")

    # Act
    response = client.post(BASE_URL, json=duplicate_body)

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_product_returns_404_for_missing_category(client):
    # Arrange
    request_body = product_request_body(category_id=9999, sku="PRD-404")

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Category 9999 was not found."


def test_create_product_returns_422_for_invalid_body(client, db_session):
    # Arrange
    category = create_category(db_session)
    invalid_body = product_request_body(
        category_id=category.id,
        name="",
        sku="PRD-422",
        stock_quantity=-1,
        cost="-1.00",
    )

    # Act
    response = client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_update_product_returns_200_and_updated_body(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-500")
    update_body = product_request_body(category_id=category.id, sku="PRD-500", name="Gaming Keyboard")

    # Act
    response = client.put(f"{BASE_URL}/{product.id}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["name"] == "Gaming Keyboard"
    assert payload["sku"] == "PRD-500"


def test_update_product_returns_404_when_missing(client, db_session):
    # Arrange
    category = create_category(db_session)
    update_body = product_request_body(category_id=category.id, sku="PRD-501")

    # Act
    response = client.put(f"{BASE_URL}/9999", json=update_body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Product 9999 was not found."


def test_update_product_returns_409_for_duplicate_sku(client, db_session):
    # Arrange
    category = create_category(db_session)
    first = create_product(db_session, category_id=category.id, sku="PRD-700")
    create_product(db_session, category_id=category.id, sku="PRD-701")
    update_body = product_request_body(
        category_id=category.id,
        sku="PRD-701",
        name="Duplicate SKU Product",
    )

    # Act
    response = client.put(f"{BASE_URL}/{first.id}", json=update_body)

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_product_returns_422_for_invalid_payload(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-800")
    invalid_body = product_request_body(
        category_id=category.id,
        name="",
        sku="PRD-800",
        sale_price="20.00",
    )

    # Act
    response = client.put(f"{BASE_URL}/{product.id}", json=invalid_body)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"][0]["loc"][-1] == "name"


def test_delete_product_returns_204_and_removes_record(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-900")

    # Act
    response = client.delete(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 204
    check = client.get(f"{BASE_URL}/{product.id}")
    assert check.status_code == 404


def test_delete_product_returns_404_when_missing(client):
    # Arrange
    missing_id = 9988

    # Act
    response = client.delete(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_create_product_defaults_to_active(client, db_session):
    # Arrange
    category = create_category(db_session)
    request_body = product_request_body(category_id=category.id, sku="PRD-950")

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    assert response.json()["is_active"] is True


def test_deactivate_product_returns_200_and_flips_is_active(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-951")

    # Act
    response = client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["is_active"] is False

    # A deactivated product is still retrievable, not deleted.
    check = client.get(f"{BASE_URL}/{product.id}")
    assert check.status_code == 200
    assert check.json()["is_active"] is False


def test_activate_product_returns_200_and_flips_is_active(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-952")
    client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Act
    response = client.post(f"{BASE_URL}/{product.id}/activate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_deactivate_product_returns_404_when_missing(client):
    # Arrange
    missing_id = 9977

    # Act
    response = client.post(f"{BASE_URL}/{missing_id}/deactivate")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_deactivated_product_can_still_be_deleted_when_it_has_no_sales(client, db_session):
    # Arrange: deactivating is not a prerequisite for deletion; both remain independent actions.
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PRD-953")
    client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Act
    response = client.delete(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 204


def test_list_products_filters_by_is_active(client, db_session):
    # Arrange
    category = create_category(db_session)
    active_product = create_product(db_session, category_id=category.id, sku="PRD-960")
    inactive_product = create_product(db_session, category_id=category.id, sku="PRD-961")
    client.post(f"{BASE_URL}/{inactive_product.id}/deactivate")

    # Act
    active_response = client.get(BASE_URL, params={"is_active": "true"})
    inactive_response = client.get(BASE_URL, params={"is_active": "false"})

    # Assert
    active_ids = [item["id"] for item in active_response.json()["items"]]
    inactive_ids = [item["id"] for item in inactive_response.json()["items"]]
    assert active_product.id in active_ids
    assert inactive_product.id not in active_ids
    assert inactive_product.id in inactive_ids
    assert active_product.id not in inactive_ids
