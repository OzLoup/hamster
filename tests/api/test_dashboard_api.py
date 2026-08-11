from tests.factories import create_category, create_product

BASE_URL = "/api/v1/dashboard/summary"
LOW_STOCK_URL = "/api/v1/dashboard/low-stock-products"


def test_get_dashboard_summary_returns_zeros_when_empty(client):
    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_products"] == 0
    assert payload["total_categories"] == 0
    assert payload["sales_this_month"] == 0
    assert payload["sales_today"] == 0
    assert payload["revenue_today"] == "0.00"
    assert payload["revenue_change_pct"] is None
    assert payload["low_stock_products"] == 0
    assert payload["low_stock_threshold"] == 10
    assert payload["catalog_health"]["level"] == "neutral"
    assert payload["category_balance"]["level"] == "neutral"
    assert payload["sales_trend"]["level"] == "neutral"


def test_get_dashboard_summary_reflects_real_catalog_data(client, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-API-001", stock_quantity=5)
    create_product(db_session, category_id=category.id, sku="DASH-API-002", stock_quantity=50)

    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_products"] == 2
    assert payload["total_categories"] == 1
    assert payload["low_stock_products"] == 1


def test_get_dashboard_summary_accepts_timezone_query_param(client, db_session):
    # Act
    response = client.get(BASE_URL, params={"tz": "America/Bogota"})

    # Assert
    assert response.status_code == 200


def test_get_dashboard_summary_falls_back_for_invalid_timezone(client):
    # Act
    response = client.get(BASE_URL, params={"tz": "Not/A_Real_Zone"})

    # Assert
    assert response.status_code == 200
    assert response.json()["total_products"] == 0


def test_list_low_stock_products_returns_empty_list_when_none(client):
    # Act
    response = client.get(LOW_STOCK_URL)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_list_low_stock_products_returns_matching_products(client, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-API-LOW-001", name="Low Stock", stock_quantity=2)
    create_product(db_session, category_id=category.id, sku="DASH-API-LOW-002", name="Plenty", stock_quantity=80)

    # Act
    response = client.get(LOW_STOCK_URL)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Low Stock"
    assert payload[0]["sku"] == "DASH-API-LOW-001"
    assert payload[0]["stock_quantity"] == 2
    assert payload[0]["category_name"] == "Electronics"
