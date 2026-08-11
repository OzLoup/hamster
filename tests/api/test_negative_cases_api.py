from tests.factories import create_category, create_product


CATEGORIES_URL = "/api/v1/categories"
PRODUCTS_URL = "/api/v1/products"
SALES_URL = "/api/v1/sales"


def test_missing_required_fields_category_post_returns_422(client):
    # Arrange
    invalid_body = {"description": "Missing name"}

    # Act
    response = client.post(CATEGORIES_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_missing_required_fields_product_post_returns_422(client):
    # Arrange
    invalid_body = {
        "name": "Keyboard",
        "sku": "NEG-MISSING-001",
        "stock_quantity": 10,
    }

    # Act
    response = client.post(PRODUCTS_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_missing_required_fields_sale_post_returns_422(client):
    # Arrange
    invalid_body = {
        "sale_items": [
            {
                "product_id": 1,
                "quantity": 1,
                "unit_price": "10.00",
                "subtotal": "10.00",
            }
        ]
    }

    # Act
    response = client.post(SALES_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_invalid_ids_in_path_return_422(client):
    # Arrange
    invalid_category_id = 0
    invalid_product_id = 0

    # Act
    category_response = client.get(f"{CATEGORIES_URL}/{invalid_category_id}")
    product_response = client.get(f"{PRODUCTS_URL}/{invalid_product_id}")

    # Assert
    assert category_response.status_code == 422
    assert product_response.status_code == 422


def test_invalid_related_ids_return_not_found(client):
    # Arrange
    invalid_product_body = {
        "category_id": 9999,
        "name": "Invalid Category Product",
        "sku": "NEG-INVALID-ID-001",
        "stock_quantity": 5,
        "cost": "10.00",
        "sale_price": "20.00",
    }

    sale_body = {
        "reference": "NEG-SALE-404",
        "payment_method": "cash",
        "total_amount": "10.00",
        "sale_items": [
            {
                "product_id": 9999,
                "quantity": 1,
                "unit_price": "10.00",
                "subtotal": "10.00",
            }
        ],
    }

    # Act
    product_response = client.post(PRODUCTS_URL, json=invalid_product_body)
    sale_response = client.post(SALES_URL, json=sale_body)

    # Assert
    assert product_response.status_code == 404
    assert sale_response.status_code == 404


def test_negative_stock_returns_422(client, db_session):
    # Arrange
    category = create_category(db_session)
    invalid_body = {
        "category_id": category.id,
        "name": "Negative Stock Product",
        "sku": "NEG-STOCK-001",
        "stock_quantity": -1,
        "cost": "10.00",
        "sale_price": "20.00",
    }

    # Act
    response = client.post(PRODUCTS_URL, json=invalid_body)

    # Assert
    assert response.status_code == 422


def test_duplicated_categories_return_409(client, db_session):
    # Arrange
    create_category(db_session, name="Office")
    duplicate_body = {"name": "Office", "description": "Duplicate category"}

    # Act
    response = client.post(CATEGORIES_URL, json=duplicate_body)

    # Assert
    assert response.status_code == 409


def test_large_strings_return_422(client, db_session):
    # Arrange
    category = create_category(db_session)
    oversized_category_name = "x" * 121
    oversized_product_sku = "S" * 65

    category_body = {
        "name": oversized_category_name,
        "description": "Valid description",
    }
    product_body = {
        "category_id": category.id,
        "name": "Valid Name",
        "sku": oversized_product_sku,
        "stock_quantity": 10,
        "cost": "10.00",
        "sale_price": "20.00",
    }

    # Act
    category_response = client.post(CATEGORIES_URL, json=category_body)
    product_response = client.post(PRODUCTS_URL, json=product_body)

    # Assert
    assert category_response.status_code == 422
    assert product_response.status_code == 422


def test_invalid_prices_return_422(client, db_session):
    # Arrange
    category = create_category(db_session)
    invalid_product_prices = {
        "category_id": category.id,
        "name": "Invalid Price Product",
        "sku": "NEG-PRICE-001",
        "stock_quantity": 5,
        "cost": "-1.00",
        "sale_price": "-5.00",
    }
    invalid_sale_total = {
        "reference": "NEG-PRICE-SALE",
        "payment_method": "cash",
        "total_amount": "-1.00",
        "sale_items": [
            {
                "product_id": 1,
                "quantity": 1,
                "unit_price": "10.00",
                "subtotal": "10.00",
            }
        ],
    }

    # Act
    product_response = client.post(PRODUCTS_URL, json=invalid_product_prices)
    sale_response = client.post(SALES_URL, json=invalid_sale_total)

    # Assert
    assert product_response.status_code == 422
    assert sale_response.status_code == 422


def test_unexpected_values_return_400_or_422(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, sku="NEG-UNEXPECTED-001")

    unexpected_type_payload = {
        "category_id": category.id,
        "name": "Bad Type Product",
        "sku": "NEG-UNEXPECTED-002",
        "stock_quantity": "not-a-number",
        "cost": "10.00",
        "sale_price": "20.00",
    }

    business_invalid_sale = {
        "reference": "NEG-UNEXPECTED-SALE",
        "payment_method": "cash",
        "total_amount": "0.00",
        "sale_items": [],
    }

    invalid_sale_item_payload = {
        "reference": "NEG-UNEXPECTED-SALE-2",
        "payment_method": "cash",
        "total_amount": "10.00",
        "sale_items": [
            {
                "product_id": product.id,
                "quantity": 0,
                "unit_price": "10.00",
                "subtotal": "0.00",
            }
        ],
    }

    # Act
    unexpected_type_response = client.post(PRODUCTS_URL, json=unexpected_type_payload)
    business_rule_response = client.post(SALES_URL, json=business_invalid_sale)
    invalid_sale_item_response = client.post(SALES_URL, json=invalid_sale_item_payload)

    # Assert
    assert unexpected_type_response.status_code == 422
    assert business_rule_response.status_code == 400
    assert invalid_sale_item_response.status_code == 422
