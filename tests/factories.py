from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.business import Business
from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User


def create_business(
    db_session: Session,
    *,
    name: str = "Test Business",
    is_active: bool = True,
) -> Business:
    business = Business(name=name, is_active=is_active)
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


def create_user(
    db_session: Session,
    *,
    email: str = "user@example.com",
    password: str = "Password123",
    full_name: str = "Test User",
    role: str | None = "admin",
    business_id: int | None = None,
    is_superuser: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        business_id=business_id,
        is_superuser=is_superuser,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


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


def create_supplier(
    db_session: Session,
    *,
    name: str = "Acme Supplies",
    contact_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> Supplier:
    supplier = Supplier(name=name, contact_name=contact_name, phone=phone, email=email)
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


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
    stock_quantity: int = 20,
    cost: str = "40.00",
    sale_price: str = "79.99",
) -> dict:
    return {
        "category_id": category_id,
        "name": name,
        "stock_quantity": stock_quantity,
        "cost": cost,
        "sale_price": sale_price,
    }


def supplier_request_body(
    *,
    name: str = "Acme Supplies",
    contact_name: str | None = "Jane Doe",
    phone: str | None = "555-0100",
    email: str | None = "jane@acmesupplies.com",
) -> dict:
    return {
        "name": name,
        "contact_name": contact_name,
        "phone": phone,
        "email": email,
    }


def purchase_request_body(
    *,
    reference: str,
    supplier_id: int,
    product_id: int,
    quantity: int = 1,
    unit_cost: str = "40.00",
) -> dict:
    subtotal = (Decimal(unit_cost) * Decimal(quantity)).quantize(Decimal("0.01"))
    return {
        "reference": reference,
        "supplier_id": supplier_id,
        "total_amount": f"{subtotal:.2f}",
        "purchase_items": [
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "subtotal": f"{subtotal:.2f}",
            }
        ],
    }


def open_tab_request_body(*, name: str = "Mesa 1") -> dict:
    return {"name": name}


def open_tab_item_request_body(*, product_id: int, quantity: int = 1) -> dict:
    return {"product_id": product_id, "quantity": quantity}


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
