from tests.factories import (
    category_request_body,
    create_category,
    create_product,
    create_supplier,
    product_request_body,
)


def test_seller_can_read_products(seller_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    create_product(db_session, business_id=business.id, category_id=category.id)

    # Act
    response = seller_client.get("/api/v1/products")

    # Assert
    assert response.status_code == 200


def test_seller_cannot_create_product(seller_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    request_body = product_request_body(category_id=category.id)

    # Act
    response = seller_client.post("/api/v1/products", json=request_body)

    # Assert
    assert response.status_code == 403


def test_seller_cannot_create_category(seller_client):
    # Act
    response = seller_client.post("/api/v1/categories", json=category_request_body())

    # Assert
    assert response.status_code == 403


def test_coordinator_can_create_product(coordinator_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    request_body = product_request_body(category_id=category.id)

    # Act
    response = coordinator_client.post("/api/v1/products", json=request_body)

    # Assert
    assert response.status_code == 201


def test_seller_cannot_access_suppliers(seller_client):
    # Act
    response = seller_client.get("/api/v1/suppliers")

    # Assert
    assert response.status_code == 403


def test_coordinator_can_access_suppliers(coordinator_client):
    # Act
    response = coordinator_client.get("/api/v1/suppliers")

    # Assert
    assert response.status_code == 200


def test_seller_cannot_access_purchases(seller_client):
    # Act
    response = seller_client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == 403


def test_seller_cannot_access_dashboard(seller_client):
    # Act
    response = seller_client.get("/api/v1/dashboard/summary")

    # Assert
    assert response.status_code == 403


def test_coordinator_can_access_dashboard(coordinator_client):
    # Act
    response = coordinator_client.get("/api/v1/dashboard/summary")

    # Assert
    assert response.status_code == 200


def test_seller_can_create_sale(seller_client, db_session, business):
    # Arrange
    category = create_category(db_session, business_id=business.id)
    product = create_product(db_session, business_id=business.id, category_id=category.id, stock_quantity=10)

    # Act
    response = seller_client.post(
        "/api/v1/sales",
        json={
            "reference": "SELLER-SALE-1",
            "payment_method": "cash",
            "total_amount": "79.99",
            "sale_items": [
                {"product_id": product.id, "quantity": 1, "unit_price": "79.99", "subtotal": "79.99"}
            ],
        },
    )

    # Assert
    assert response.status_code == 201


def test_seller_can_use_open_tabs(seller_client):
    # Act
    response = seller_client.post("/api/v1/open-tabs", json={"name": "Mesa 1"})

    # Assert
    assert response.status_code == 201


def test_seller_can_read_settings(seller_client):
    # Sellers need the business name for their own report exports (CSV/PDF headers).
    # Act
    response = seller_client.get("/api/v1/settings")

    # Assert
    assert response.status_code == 200


def test_seller_cannot_update_settings(seller_client):
    # Act
    response = seller_client.put("/api/v1/settings", json={"business_name": "Hacked"})

    # Assert
    assert response.status_code == 403


def test_coordinator_can_read_settings_but_not_update(coordinator_client):
    # Act
    read_response = coordinator_client.get("/api/v1/settings")
    write_response = coordinator_client.put("/api/v1/settings", json={"business_name": "Hacked"})

    # Assert
    assert read_response.status_code == 200
    assert write_response.status_code == 403


def test_admin_can_update_settings(authenticated_client):
    # Act
    response = authenticated_client.put("/api/v1/settings", json={"business_name": "Renamed Business"})

    # Assert
    assert response.status_code == 200
    assert response.json()["business_name"] == "Renamed Business"


def test_seller_cannot_deactivate_supplier(seller_client, db_session, business):
    # Arrange
    supplier = create_supplier(db_session, business_id=business.id)

    # Act
    response = seller_client.post(f"/api/v1/suppliers/{supplier.id}/deactivate")

    # Assert
    assert response.status_code == 403
