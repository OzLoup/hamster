from app.models.product import Product
from tests.factories import create_category, create_product, create_supplier, purchase_request_body

BASE_URL = "/api/v1/purchases"


def test_list_purchases_returns_empty_list(client):
    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_create_purchase_returns_201_and_increments_stock_and_cost(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(
        db_session, category_id=category.id, stock_quantity=10, cost="40.00", sku="PUR-PRD-101"
    )
    request_body = purchase_request_body(
        reference="PUR-001", supplier_id=supplier.id, product_id=product.id, quantity=5, unit_cost="35.50"
    )

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["reference"] == "PUR-001"
    assert payload["total_amount"] == "177.50"
    assert len(payload["purchase_items"]) == 1
    assert payload["purchase_items"][0]["product_id"] == product.id

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 15
    assert str(refreshed_product.cost) == "35.50"


def test_list_purchases_returns_created_purchases(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-102")
    client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-010", supplier_id=supplier.id, product_id=product.id, quantity=1),
    )

    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["reference"] == "PUR-010"


def test_get_purchase_by_id_returns_purchase(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-103")
    created = client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-020", supplier_id=supplier.id, product_id=product.id, quantity=1),
    ).json()

    # Act
    response = client.get(f"{BASE_URL}/{created['id']}")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["reference"] == "PUR-020"
    assert len(payload["purchase_items"]) == 1


def test_get_purchase_by_id_returns_404_when_missing(client):
    # Arrange
    missing_id = 9999

    # Act
    response = client.get(f"{BASE_URL}/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Purchase {missing_id} was not found."


def test_create_purchase_returns_404_for_missing_supplier(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-104")
    request_body = purchase_request_body(reference="PUR-030", supplier_id=9999, product_id=product.id, quantity=1)

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Supplier 9999 was not found."


def test_create_purchase_returns_400_for_inactive_supplier(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    client.post(f"/api/v1/suppliers/{supplier.id}/deactivate")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-105")
    request_body = purchase_request_body(reference="PUR-031", supplier_id=supplier.id, product_id=product.id, quantity=1)

    # Act
    response = client.post(BASE_URL, json=request_body)

    # Assert
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"]


def test_create_purchase_returns_409_for_duplicate_reference(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-106")
    client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-040", supplier_id=supplier.id, product_id=product.id, quantity=1),
    )

    # Act
    response = client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-040", supplier_id=supplier.id, product_id=product.id, quantity=1),
    )

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_purchase_returns_400_for_mismatched_total(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-107")
    invalid_body = purchase_request_body(
        reference="PUR-050", supplier_id=supplier.id, product_id=product.id, quantity=1
    )
    invalid_body["total_amount"] = "1.00"

    # Act
    response = client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 400
    assert "total_amount does not match" in response.json()["detail"]


def test_create_purchase_returns_422_for_invalid_payload(client):
    # Arrange
    invalid_body = {
        "reference": "PUR-060",
        "supplier_id": 1,
        "total_amount": "10.00",
        "purchase_items": [
            {
                "product_id": 1,
                "quantity": 0,
                "unit_cost": "10.00",
                "subtotal": "0.00",
            }
        ],
    }

    # Act
    response = client.post(BASE_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_update_purchase_returns_200_and_updated_body(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-108")
    created = client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-070", supplier_id=supplier.id, product_id=product.id, quantity=1),
    ).json()
    update_body = {"reference": "PUR-070-UPDATED"}

    # Act
    response = client.patch(f"{BASE_URL}/{created['id']}", json=update_body)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["reference"] == "PUR-070-UPDATED"


def test_update_purchase_returns_404_when_missing(client):
    # Arrange
    missing_id = 8888

    # Act
    response = client.patch(f"{BASE_URL}/{missing_id}", json={"reference": "PUR-404"})

    # Assert
    assert response.status_code == 404


def test_delete_purchase_returns_405_method_not_allowed(client, db_session):
    # Arrange
    category = create_category(db_session)
    supplier = create_supplier(db_session, name="Acme Supplies")
    product = create_product(db_session, category_id=category.id, sku="PUR-PRD-109")
    created = client.post(
        BASE_URL,
        json=purchase_request_body(reference="PUR-080", supplier_id=supplier.id, product_id=product.id, quantity=1),
    ).json()

    # Act
    response = client.delete(f"{BASE_URL}/{created['id']}")

    # Assert
    assert response.status_code == 405
