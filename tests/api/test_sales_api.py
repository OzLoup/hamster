from app.models.product import Product
from tests.factories import create_business, create_category, create_product, sale_request_body

BASE_URL = "/api/v1/sales"


def test_create_sale_returns_404_for_product_from_another_business(authenticated_client, db_session):
    # Arrange
    other_business = create_business(db_session, name="Other Business")
    other_category = create_category(db_session, business_id=other_business.id)
    other_product = create_product(db_session, business_id=other_business.id, category_id=other_category.id, sku="OTHER-001")
    request_body = sale_request_body(reference="SALE-CROSS", product_id=other_product.id, quantity=1)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 404


def test_list_sales_returns_empty_list(authenticated_client):
    # Arrange
    url = BASE_URL

    # Act
    response = authenticated_client.get(url)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_create_sale_returns_201_and_decrements_stock(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10, sku="SALE-PRD-101")
    request_body = sale_request_body(reference="SALE-001", product_id=product.id, quantity=2)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["reference"] == "SALE-001"
    assert payload["total_amount"] == "159.98"
    assert len(payload["sale_items"]) == 1
    assert payload["sale_items"][0]["product_id"] == product.id

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 8


def test_list_sales_returns_created_sales(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-102")
    authenticated_client.post(BASE_URL, json=sale_request_body(reference="SALE-010", product_id=product.id, quantity=1))

    # Act
    response = authenticated_client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["reference"] == "SALE-010"


def test_get_sale_by_id_returns_sale(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-103")
    created = authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-020", product_id=product.id, quantity=1),
    ).json()

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{created['id']}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["reference"] == "SALE-020"
    assert len(payload["sale_items"]) == 1


def test_get_sale_by_id_returns_404_when_missing(authenticated_client):
    # Arrange
    missing_id = 9999

    # Act
    response = authenticated_client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Sale {missing_id} was not found."


def test_create_sale_returns_409_for_duplicate_reference(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-104")
    authenticated_client.post(BASE_URL, json=sale_request_body(reference="SALE-030", product_id=product.id, quantity=1))

    # Act
    response = authenticated_client.post(BASE_URL, json=sale_request_body(reference="SALE-030", product_id=product.id, quantity=1))

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_sale_returns_400_for_mismatched_total(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-105")
    invalid_body = sale_request_body(reference="SALE-040", product_id=product.id, quantity=1)
    invalid_body["total_amount"] = "1.00"

    # Act
    response = authenticated_client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 400
    assert "total_amount does not match" in response.json()["detail"]


def test_create_sale_returns_400_for_insufficient_stock(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-106", stock_quantity=1)
    request_body = sale_request_body(reference="SALE-050", product_id=product.id, quantity=2)

    # Act
    response = authenticated_client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_create_sale_returns_422_for_invalid_payload(authenticated_client):
    # Arrange
    invalid_body = {
        "reference": "SALE-060",
        "payment_method": "cash",
        "total_amount": "10.00",
        "sale_items": [
            {
                "product_id": 1,
                "quantity": 0,
                "unit_price": "10.00",
                "subtotal": "0.00",
            }
        ],
    }

    # Act
    response = authenticated_client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_update_sale_returns_200_and_updated_body(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-107")
    created = authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-070", product_id=product.id, quantity=1),
    ).json()
    update_body = {"reference": "SALE-070-UPDATED", "total_amount": "79.99"}

    # Act
    response = authenticated_client.patch(f"{BASE_URL}/{created['id']}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["reference"] == "SALE-070-UPDATED"
    assert payload["total_amount"] == "79.99"


def test_update_sale_returns_404_when_missing(authenticated_client):
    # Arrange
    missing_id = 8888

    # Act
    response = authenticated_client.patch(f"{BASE_URL}/{missing_id}", json={"reference": "SALE-404"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Sale {missing_id} was not found."


def test_update_sale_returns_409_for_duplicate_reference(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    first_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-108")
    second_product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-109")

    first = authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-080", product_id=first_product.id, quantity=1),
    ).json()
    authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-081", product_id=second_product.id, quantity=1),
    )

    # Act
    response = authenticated_client.patch(
        f"{BASE_URL}/{first['id']}",
        json={"reference": "SALE-081"},
    )

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_sale_returns_422_for_invalid_payload(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-110")
    created = authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-090", product_id=product.id, quantity=1),
    ).json()

    # Act
    response = authenticated_client.patch(
        f"{BASE_URL}/{created['id']}",
        json={"total_amount": "-1.00"},
    )

    # Assert
    assert response.status_code == 422
    payload = response.json()
    assert len(payload["detail"]) >= 1


def test_delete_sale_returns_405_method_not_allowed(authenticated_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, sku="SALE-PRD-111")
    created = authenticated_client.post(
        BASE_URL,
        json=sale_request_body(reference="SALE-100", product_id=product.id, quantity=1),
    ).json()

    # Act
    response = authenticated_client.delete(f"{BASE_URL}/{created['id']}")

    # Assert
    assert response.status_code == 405
