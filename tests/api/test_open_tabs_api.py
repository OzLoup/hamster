from app.models.product import Product
from tests.factories import create_category, create_product, open_tab_item_request_body, open_tab_request_body

BASE_URL = "/api/v1/open-tabs"


def test_list_open_tabs_returns_empty_list(client):
    # Act
    response = client.get(BASE_URL)

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_create_open_tab_returns_201(client):
    # Act
    response = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1"))

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["name"] == "Mesa 1"
    assert payload["total"] == "0.00"
    assert payload["items"] == []


def test_create_open_tab_returns_409_for_duplicate_name(client):
    # Arrange
    client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1"))

    # Act
    response = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1"))

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_get_open_tab_returns_404_when_missing(client):
    # Act
    response = client.get(f"{BASE_URL}/9999")

    # Assert
    assert response.status_code == 404


def test_add_item_returns_201_and_decrements_stock(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, stock_quantity=10, sale_price="5.00")
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()

    # Act
    response = client.post(
        f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=product.id, quantity=3)
    )

    # Assert
    assert response.status_code == 201
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["quantity"] == 3
    assert payload["total"] == "15.00"

    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 7


def test_add_item_returns_400_for_insufficient_stock(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, stock_quantity=2)
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()

    # Act
    response = client.post(
        f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=product.id, quantity=5)
    )

    # Assert
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_add_item_returns_404_for_missing_product(client):
    # Arrange
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()

    # Act
    response = client.post(f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=9999))

    # Assert
    assert response.status_code == 404


def test_remove_item_returns_204_and_restores_stock(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, stock_quantity=10)
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()
    added = client.post(
        f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=product.id, quantity=4)
    ).json()
    item_id = added["items"][0]["id"]

    # Act
    response = client.delete(f"{BASE_URL}/{tab['id']}/items/{item_id}")

    # Assert
    assert response.status_code == 204
    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 10


def test_close_open_tab_returns_201_with_sale_and_empties_tab(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, stock_quantity=10, sale_price="5.00")
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()
    client.post(f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=product.id, quantity=3))

    # Act
    response = client.post(f"{BASE_URL}/{tab['id']}/close", json={"payment_method": "cash"})

    # Assert
    assert response.status_code == 201
    sale_payload = response.json()
    assert sale_payload["total_amount"] == "15.00"
    assert len(sale_payload["sale_items"]) == 1

    reopened_tab = client.get(f"{BASE_URL}/{tab['id']}").json()
    assert reopened_tab["items"] == []
    assert reopened_tab["total"] == "0.00"


def test_close_open_tab_returns_400_when_no_items(client):
    # Arrange
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()

    # Act
    response = client.post(f"{BASE_URL}/{tab['id']}/close", json={"payment_method": "cash"})

    # Assert
    assert response.status_code == 400


def test_delete_open_tab_with_items_returns_204_and_restores_stock(client, db_session):
    # Arrange
    category = create_category(db_session)
    product = create_product(db_session, category_id=category.id, stock_quantity=10)
    tab = client.post(BASE_URL, json=open_tab_request_body(name="Mesa 1")).json()
    client.post(f"{BASE_URL}/{tab['id']}/items", json=open_tab_item_request_body(product_id=product.id, quantity=4))

    # Act
    response = client.delete(f"{BASE_URL}/{tab['id']}")

    # Assert
    assert response.status_code == 204
    assert client.get(f"{BASE_URL}/{tab['id']}").status_code == 404
    refreshed_product = db_session.get(Product, product.id)
    assert refreshed_product.stock_quantity == 10


def test_delete_open_tab_returns_404_when_missing(client):
    # Act
    response = client.delete(f"{BASE_URL}/9999")

    # Assert
    assert response.status_code == 404
