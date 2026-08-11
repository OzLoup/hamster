from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


def create_category(
    db_session: Session,
    *,
    name: str = "Electronics",
    description: str | None = None,
) -> Category:
    category = Category(name=name, description=description)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


def create_product(
    db_session: Session,
    *,
    category_id: int,
    name: str = "Mechanical Keyboard",
    sku: str = "PRD-001",
    stock_quantity: int = 20,
    cost: Decimal = Decimal("40.00"),
    sale_price: Decimal = Decimal("79.99"),
) -> Product:
    product = Product(
        category_id=category_id,
        name=name,
        sku=sku,
        stock_quantity=stock_quantity,
        cost=cost,
        sale_price=sale_price,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def category_request_body(
    *,
    name: str = "Electronics",
    description: str | None = "Devices and accessories",
) -> dict:
    return {
        "name": name,
        "description": description,
    }


def product_request_body(
    *,
    category_id: int,
    name: str = "Mechanical Keyboard",
    sku: str = "PRD-100",
    stock_quantity: int = 20,
    cost: str = "40.00",
    sale_price: str = "79.99",
) -> dict:
    return {
        "category_id": category_id,
        "name": name,
        "sku": sku,
        "stock_quantity": stock_quantity,
        "cost": cost,
        "sale_price": sale_price,
    }


def sale_request_body(
    *,
    reference: str,
    product_id: int,
    quantity: int = 1,
    unit_price: str = "79.99",
    payment_method: str = "cash",
) -> dict:
    subtotal = (Decimal(unit_price) * Decimal(quantity)).quantize(Decimal("0.01"))
    return {
        "reference": reference,
        "payment_method": payment_method,
        "total_amount": f"{subtotal:.2f}",
        "sale_items": [
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": f"{subtotal:.2f}",
            }
        ],
    }
