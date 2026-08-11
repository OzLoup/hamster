from collections.abc import Generator
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401
from app.core.dependencies import get_db
from app.database.database import Base
from app.main import app as main_app
from app.models.category import Category
from app.models.product import Product


@pytest.fixture(scope="session")
def sqlite_db_url(tmp_path_factory) -> str:
    """Create a temporary SQLite database path for the test session."""
    db_dir = tmp_path_factory.mktemp("pytest-db")
    return f"sqlite+pysqlite:///{db_dir / 'test.sqlite3'}"


@pytest.fixture(scope="session")
def engine(sqlite_db_url: str):
    """Build a shared SQLite engine that points to the temporary test database."""
    test_engine = create_engine(sqlite_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def session_factory(engine):
    """Return a reusable SQLAlchemy session factory bound to the test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session(session_factory) -> Generator[Session, None, None]:
    """Provide a clean SQLAlchemy session per test and remove persisted rows on teardown."""
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        # Some tests call commit() multiple times; explicit table cleanup keeps isolation deterministic.
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def dependency_overrides(db_session: Session) -> Generator[dict, None, None]:
    """Attach default and custom dependency overrides for the app lifecycle."""

    def _get_test_db() -> Generator[Session, None, None]:
        yield db_session

    main_app.dependency_overrides[get_db] = _get_test_db
    try:
        yield main_app.dependency_overrides
    finally:
        main_app.dependency_overrides.clear()


@pytest.fixture()
def override_dependency(dependency_overrides: dict):
    """Helper fixture to override any FastAPI dependency during a test."""

    def _override(source_dependency, override_callable) -> None:
        dependency_overrides[source_dependency] = override_callable

    return _override


@pytest.fixture()
def app(dependency_overrides: dict) -> Generator[FastAPI, None, None]:
    """Return FastAPI app with dependency overrides already applied."""
    yield main_app


@pytest.fixture()
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Synchronous API client for route tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture()
async def async_client(app: FastAPI) -> Generator[AsyncClient, None, None]:
    """Asynchronous API client for async endpoint testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture()
def category_payload() -> dict:
    """Return a baseline category payload for API and service tests."""
    return {
        "name": "Electronics",
        "description": "Devices and accessories",
    }


@pytest.fixture()
def product_payload() -> dict:
    """Return a baseline product payload for API and service tests."""
    return {
        "category_id": 1,
        "name": "Mechanical Keyboard",
        "sku": "KB-100",
        "stock_quantity": 25,
        "cost": "45.50",
        "sale_price": "79.99",
    }


@pytest.fixture()
def sale_payload_factory():
    """Build valid sale payloads using the provided product id and quantities."""

    def _factory(
        *,
        product_id: int,
        quantity: int = 2,
        unit_price: str = "79.99",
        reference: str = "SALE-001",
        payment_method: str = "cash",
    ) -> dict:
        unit = Decimal(unit_price)
        subtotal = (unit * Decimal(quantity)).quantize(Decimal("0.01"))
        return {
            "reference": reference,
            "payment_method": payment_method,
            "total_amount": f"{subtotal:.2f}",
            "sale_items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": f"{unit:.2f}",
                    "subtotal": f"{subtotal:.2f}",
                }
            ],
        }

    return _factory


@pytest.fixture()
def sample_category(db_session: Session, category_payload: dict) -> Category:
    """Create and persist a reusable category entity."""
    category = Category(**category_payload)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture()
def sample_product(db_session: Session, sample_category: Category) -> Product:
    """Create and persist a reusable product entity linked to sample_category."""
    product = Product(
        category_id=sample_category.id,
        name="Mechanical Keyboard",
        sku="KB-100",
        stock_quantity=25,
        cost=Decimal("45.50"),
        sale_price=Decimal("79.99"),
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product
