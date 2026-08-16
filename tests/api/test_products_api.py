from tests.factories import create_business, create_category, create_product, product_request_body

BASE_URL = "/api/v1/products"


def test_get_product_from_another_business_returns_404(authenticated_client, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_category = create_category(db_session, business_id=other_business.id)
    other_product = create_product(db_session, business_id=other_business.id, category_id=other_category.id, sku="OTHER-001")

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{other_product.id}")

    # Assert
    assert response.status_code == 404


def test_create_product_rejects_category_from_another_business(authenticated_client, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_category = create_category(db_session, business_id=other_business.id)
    request_body = product_request_body(category_id=other_category.id)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 404


def test_list_products_returns_empty_payload(authenticated_client):
    # Arrange
    url = BASE_URL

    # Act
    response = authenticated_client.get(url)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 0


def test_list_products_returns_paginated_results(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    first = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-001", name="Keyboard")
    second = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-002", name="Mouse")

    # Act
    response = authenticated_client.get(f"{BASE_URL}?page=1&page_size=1")

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


def test_list_products_supports_search_and_category_filter(authenticated_client, db_session, business):
    # Arrange
    electronics = create_category(db_session, business_id=business.id, name="Electronics")
    office = create_category(db_session, business_id=business.id, name="Office")
    create_product(db_session, business_id=business.id, category_id=electronics.id, sku="PRD-101", name="Gaming Mouse")
    create_product(db_session, business_id=business.id, category_id=office.id, sku="PRD-102", name="Office Chair")

    # Act
    response = authenticated_client.get(f"{BASE_URL}?search=Mouse&category_id={electronics.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "Gaming Mouse"


def test_list_products_returns_422_for_invalid_query_values(authenticated_client):
    # Arrange
    invalid_query = f"{BASE_URL}?page=0&page_size=101"

    # Act
    response = authenticated_client.get(invalid_query)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_get_product_by_id_returns_product(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-200")

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["sku"] == "PRD-200"


def test_get_product_by_id_returns_404_when_missing(authenticated_client):
    # Arrange
    missing_id = 9999

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_create_product_returns_201_and_expected_body(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    request_body = product_request_body(category_id=category.id)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["category_id"] == category.id
    assert payload["sku"] == f"PRD-{payload['id']:06d}"
    assert payload["name"] == "Mechanical Keyboard"


def test_create_product_generates_distinct_skus(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    request_body = product_request_body(category_id=category.id)

    # Act
    first = authenticated_client.post(BASE_URL, json=request_body).json()
    second = authenticated_client.post(BASE_URL, json=request_body).json()

    # Assert
    assert first["sku"] != second["sku"]


def test_create_product_returns_404_for_missing_category(authenticated_client):
    # Arrange
    request_body = product_request_body(category_id=9999)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Category 9999 was not found."


def test_create_product_returns_422_for_invalid_body(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    invalid_body = product_request_body(
        category_id=category.id,
        name="",
        stock_quantity=-1,
        cost="-1.00",
    )

    # Act
    response = authenticated_client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_update_product_returns_200_and_updated_body(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-500")
    update_body = product_request_body(category_id=category.id, name="Gaming Keyboard")

    # Act
    response = authenticated_client.put(f"{BASE_URL}/{product.id}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["name"] == "Gaming Keyboard"
    assert payload["sku"] == "PRD-500"


def test_update_product_returns_404_when_missing(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    update_body = product_request_body(category_id=category.id)

    # Act
    response = authenticated_client.put(f"{BASE_URL}/9999", json=update_body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Product 9999 was not found."


def test_update_product_returns_422_for_invalid_payload(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-800")
    invalid_body = product_request_body(
        category_id=category.id,
        name="",
        sale_price="20.00",
    )

    # Act
    response = authenticated_client.put(f"{BASE_URL}/{product.id}", json=invalid_body)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"][0]["loc"][-1] == "name"


def test_delete_product_returns_204_and_removes_record(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-900")

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 204
    check = authenticated_client.get(f"{BASE_URL}/{product.id}")
    assert check.status_code == 404


def test_delete_product_returns_404_when_missing(authenticated_client):
    # Arrange
    missing_id = 9988

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_create_product_defaults_to_active(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    request_body = product_request_body(category_id=category.id)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    assert response.json()["is_active"] is True


def test_deactivate_product_returns_200_and_flips_is_active(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-951")

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product.id
    assert payload["is_active"] is False

    # A deactivated product is still retrievable, not deleted.
    check = authenticated_client.get(f"{BASE_URL}/{product.id}")
    assert check.status_code == 200
    assert check.json()["is_active"] is False


def test_activate_product_returns_200_and_flips_is_active(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-952")
    authenticated_client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{product.id}/activate")

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_deactivate_product_returns_404_when_missing(authenticated_client):
    # Arrange
    missing_id = 9977

    # Act
    response = authenticated_client.post(f"{BASE_URL}/{missing_id}/deactivate")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Product {missing_id} was not found."


def test_deactivated_product_can_still_be_deleted_when_it_has_no_sales(authenticated_client, db_session, business):
    # Arrange: deactivating is not a prerequisite for deletion; both remain independent actions.
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-953")
    authenticated_client.post(f"{BASE_URL}/{product.id}/deactivate")

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{product.id}")

    # Assert
    assert response.status_code == 204


def test_list_products_filters_by_is_active(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    active_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-960")
    inactive_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="PRD-961")
    authenticated_client.post(f"{BASE_URL}/{inactive_product.id}/deactivate")

    # Act
    active_response = authenticated_client.get(BASE_URL, params={"is_active": "true"})
    inactive_response = authenticated_client.get(BASE_URL, params={"is_active": "false"})

    # Assert
    active_ids = [item["id"] for item in active_response.json()["items"]]
    inactive_ids = [item["id"] for item in inactive_response.json()["items"]]
    assert active_product.id in active_ids
    assert inactive_product.id not in active_ids
    assert inactive_product.id in inactive_ids
    assert active_product.id not in inactive_ids


def test_list_products_filters_by_stock_level(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    create_product(db_session, business_id=business.id, category_id=category.id, sku="STOCK-LOW", name="Low", stock_quantity=3)
    create_product(db_session, business_id=business.id, category_id=category.id, sku="STOCK-MED", name="Medium", stock_quantity=20)
    create_product(db_session, business_id=business.id, category_id=category.id, sku="STOCK-GOOD", name="Good", stock_quantity=200)

    # Act
    low_response = authenticated_client.get(BASE_URL, params={"stock_level": "low"})
    medium_response = authenticated_client.get(BASE_URL, params={"stock_level": "medium"})
    good_response = authenticated_client.get(BASE_URL, params={"stock_level": "good"})

    # Assert
    assert [item["name"] for item in low_response.json()["items"]] == ["Low"]
    assert [item["name"] for item in medium_response.json()["items"]] == ["Medium"]
    assert [item["name"] for item in good_response.json()["items"]] == ["Good"]


def test_list_products_returns_422_for_invalid_stock_level(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL, params={"stock_level": "not-a-level"})

    # Assert
    assert response.status_code == 422


def test_list_products_sorts_by_name_ascending_and_descending(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    create_product(db_session, business_id=business.id, category_id=category.id, sku="SORT-A", name="Alpha")
    create_product(db_session, business_id=business.id, category_id=category.id, sku="SORT-B", name="Bravo")

    # Act
    asc_response = authenticated_client.get(BASE_URL, params={"sort_by": "name", "sort_dir": "asc"})
    desc_response = authenticated_client.get(BASE_URL, params={"sort_by": "name", "sort_dir": "desc"})

    # Assert
    assert [item["name"] for item in asc_response.json()["items"]] == ["Alpha", "Bravo"]
    assert [item["name"] for item in desc_response.json()["items"]] == ["Bravo", "Alpha"]


def test_list_products_returns_422_for_invalid_sort_by(authenticated_client):
    # Act
    response = authenticated_client.get(BASE_URL, params={"sort_by": "not-a-column"})

    # Assert
    assert response.status_code == 422
