from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.models.sale import Sale
from app.services.dashboard_service import DEFAULT_TIMEZONE, DashboardService
from tests.factories import create_category, create_product

BOGOTA = ZoneInfo(DEFAULT_TIMEZONE)


@pytest.fixture()
def service(db_session):
    return DashboardService(db_session)


def _create_sale(db_session, *, reference: str, total_amount: Decimal, created_at: datetime) -> Sale:
    sale = Sale(
        reference=reference,
        payment_method="cash",
        total_amount=total_amount,
        created_at=created_at,
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


def test_get_summary_with_no_data_returns_zeros_and_neutral_labels(service):
    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.total_products == 0
    assert summary.total_categories == 0
    assert summary.sales_this_month == 0
    assert summary.sales_today == 0
    assert summary.revenue_today == Decimal("0.00")
    assert summary.revenue_change_pct is None
    assert summary.low_stock_products == 0
    assert summary.catalog_health.level == "neutral"
    assert summary.category_balance.level == "neutral"
    assert summary.sales_trend.level == "neutral"


def test_get_summary_counts_only_active_products(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-001")
    inactive = create_product(db_session, category_id=category.id, sku="DASH-002")
    inactive.is_active = False
    db_session.commit()

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.total_products == 1


def test_get_summary_counts_categories_regardless_of_products(service, db_session):
    # Arrange
    create_category(db_session, name="Electronics")
    create_category(db_session, name="Office")

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.total_categories == 2


def test_get_summary_counts_low_stock_active_products_only(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-010", stock_quantity=5)
    create_product(db_session, category_id=category.id, sku="DASH-011", stock_quantity=50)
    low_stock_inactive = create_product(db_session, category_id=category.id, sku="DASH-012", stock_quantity=2)
    low_stock_inactive.is_active = False
    db_session.commit()

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.low_stock_products == 1
    assert summary.low_stock_threshold == 10


def test_list_low_stock_products_returns_only_active_low_stock_items(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    low_stock = create_product(
        db_session, category_id=category.id, sku="DASH-LOW-001", name="Low Stock Item", stock_quantity=3
    )
    create_product(db_session, category_id=category.id, sku="DASH-LOW-002", name="Well Stocked", stock_quantity=50)
    low_stock_inactive = create_product(
        db_session, category_id=category.id, sku="DASH-LOW-003", name="Inactive Low", stock_quantity=1
    )
    low_stock_inactive.is_active = False
    db_session.commit()

    # Act
    items = service.list_low_stock_products()

    # Assert
    assert len(items) == 1
    assert items[0].id == low_stock.id
    assert items[0].name == "Low Stock Item"
    assert items[0].sku == "DASH-LOW-001"
    assert items[0].stock_quantity == 3
    assert items[0].category_name == "Electronics"


def test_list_low_stock_products_orders_by_lowest_stock_first(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-LOW-010", name="Medium Low", stock_quantity=8)
    create_product(db_session, category_id=category.id, sku="DASH-LOW-011", name="Very Low", stock_quantity=1)

    # Act
    items = service.list_low_stock_products()

    # Assert
    assert [item.name for item in items] == ["Very Low", "Medium Low"]


def test_list_low_stock_products_returns_empty_list_when_none_are_low(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    create_product(db_session, category_id=category.id, sku="DASH-LOW-020", stock_quantity=100)

    # Act
    items = service.list_low_stock_products()

    # Assert
    assert items == []


@pytest.mark.parametrize(
    ("low_stock_count", "total", "expected_level"),
    [
        (0, 10, "positive"),
        (2, 10, "warning"),
        (5, 10, "critical"),
    ],
)
def test_catalog_health_levels(service, db_session, low_stock_count, total, expected_level):
    # Arrange
    category = create_category(db_session, name="Electronics")
    for index in range(total):
        stock = 2 if index < low_stock_count else 50
        create_product(db_session, category_id=category.id, sku=f"DASH-HEALTH-{index}", stock_quantity=stock)

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.catalog_health.level == expected_level


def test_category_balance_dominant_when_one_category_has_all_products(service, db_session):
    # Arrange
    category = create_category(db_session, name="Electronics")
    for index in range(5):
        create_product(db_session, category_id=category.id, sku=f"DASH-BAL-{index}")

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.category_balance.level == "critical"


def test_category_balance_balanced_when_evenly_spread(service, db_session):
    # Arrange
    categories = [create_category(db_session, name=f"Category {i}") for i in range(5)]
    for index, category in enumerate(categories):
        create_product(db_session, category_id=category.id, sku=f"DASH-BAL-EVEN-{index}")

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.category_balance.level == "positive"


def test_get_summary_sales_this_month_and_today(service, db_session):
    # Arrange
    now = datetime.now(BOGOTA)
    today_start = now.replace(hour=10, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    last_month = month_start - timedelta(days=2)

    _create_sale(db_session, reference="DASH-SALE-TODAY", total_amount=Decimal("50.00"), created_at=today_start)
    _create_sale(db_session, reference="DASH-SALE-LAST-MONTH", total_amount=Decimal("20.00"), created_at=last_month)

    # A day earlier in the current month only exists when today isn't the 1st.
    expected_month_count = 1
    if today_start.day > 1:
        earlier_this_month = month_start.replace(hour=2)
        _create_sale(
            db_session, reference="DASH-SALE-MONTH", total_amount=Decimal("30.00"), created_at=earlier_this_month
        )
        expected_month_count = 2

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.sales_today == 1
    assert summary.sales_this_month == expected_month_count


def test_get_summary_revenue_today_and_change_pct(service, db_session):
    # Arrange
    now = datetime.now(BOGOTA)
    today = now.replace(hour=9, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    _create_sale(db_session, reference="DASH-REV-TODAY", total_amount=Decimal("150.00"), created_at=today)
    _create_sale(db_session, reference="DASH-REV-YESTERDAY", total_amount=Decimal("100.00"), created_at=yesterday)

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.revenue_today == Decimal("150.00")
    assert summary.revenue_change_pct == Decimal("50.0")


def test_get_summary_revenue_change_pct_is_none_without_prior_day_data(service, db_session):
    # Arrange
    today = datetime.now(BOGOTA).replace(hour=9, minute=0, second=0, microsecond=0)
    _create_sale(db_session, reference="DASH-REV-ONLY-TODAY", total_amount=Decimal("75.00"), created_at=today)

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.revenue_change_pct is None


def test_get_summary_sales_trend_stable_within_band(service, db_session):
    # Arrange
    now = datetime.now(BOGOTA)
    this_week = now - timedelta(days=1)
    last_week = now - timedelta(days=8)

    for index in range(10):
        _create_sale(
            db_session, reference=f"DASH-TREND-CUR-{index}", total_amount=Decimal("10.00"), created_at=this_week
        )
    for index in range(10):
        _create_sale(
            db_session, reference=f"DASH-TREND-PRIOR-{index}", total_amount=Decimal("10.00"), created_at=last_week
        )

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.sales_trend.level == "positive"
    assert summary.sales_trend.label == "Flujo estable"


def test_get_summary_sales_trend_declining_below_band(service, db_session):
    # Arrange
    now = datetime.now(BOGOTA)
    this_week = now - timedelta(days=1)
    last_week = now - timedelta(days=8)

    for index in range(2):
        _create_sale(
            db_session, reference=f"DASH-TREND-DOWN-CUR-{index}", total_amount=Decimal("10.00"), created_at=this_week
        )
    for index in range(10):
        _create_sale(
            db_session,
            reference=f"DASH-TREND-DOWN-PRIOR-{index}",
            total_amount=Decimal("10.00"),
            created_at=last_week,
        )

    # Act
    summary = service.get_summary(None)

    # Assert
    assert summary.sales_trend.level == "warning"
    assert summary.sales_trend.label == "En descenso"


def test_get_summary_falls_back_to_default_timezone_for_invalid_tz(service):
    # Act
    summary = service.get_summary("Not/A_Real_Zone")

    # Assert
    assert summary.total_products == 0
