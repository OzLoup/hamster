from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale
from app.schemas.dashboard import DashboardSummary, LowStockProduct, MetricInsight

DEFAULT_TIMEZONE = "America/Bogota"
LOW_STOCK_THRESHOLD = 10
STABLE_TREND_BAND = 0.15
BALANCED_CATEGORY_RATIO = 0.40
CONCENTRATED_CATEGORY_RATIO = 0.60
HEALTHY_STOCK_RATIO = 0.15
WARNING_STOCK_RATIO = 0.30


def _resolve_timezone(tz_name: str | None) -> ZoneInfo:
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError, KeyError):
            pass
    return ZoneInfo(DEFAULT_TIMEZONE)


class DashboardService:
    """Aggregates real inventory and sales data for the home dashboard."""

    def __init__(self, db: Session, business_id: int):
        self.db = db
        self.business_id = business_id

    def get_summary(self, tz_name: str | None) -> DashboardSummary:
        tz = _resolve_timezone(tz_name)
        now_local = datetime.now(tz)
        today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)
        month_start = today_start.replace(day=1)
        week_start = today_start - timedelta(days=6)
        prior_week_start = today_start - timedelta(days=13)

        total_products = self._count_active_products()
        total_categories = int(
            self.db.scalar(select(func.count(Category.id)).where(Category.business_id == self.business_id)) or 0
        )
        low_stock_products = self._count_low_stock_products()

        sales_this_month = self._count_sales(start=month_start, end=None)
        sales_today = self._count_sales(start=today_start, end=tomorrow_start)
        revenue_today = self._sum_revenue(start=today_start, end=tomorrow_start)
        revenue_yesterday = self._sum_revenue(start=yesterday_start, end=today_start)

        sales_this_week = self._count_sales(start=week_start, end=None)
        sales_prior_week = self._count_sales(start=prior_week_start, end=week_start)

        return DashboardSummary(
            total_products=total_products,
            total_categories=total_categories,
            sales_this_month=sales_this_month,
            sales_today=sales_today,
            revenue_today=revenue_today,
            revenue_change_pct=self._percent_change(revenue_today, revenue_yesterday),
            low_stock_products=low_stock_products,
            low_stock_threshold=LOW_STOCK_THRESHOLD,
            catalog_health=self._catalog_health(low_stock_products, total_products),
            category_balance=self._category_balance(total_products),
            sales_trend=self._sales_trend(sales_this_week, sales_prior_week),
        )

    def list_low_stock_products(self) -> list[LowStockProduct]:
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.sku,
                Product.stock_quantity,
                Category.name.label("category_name"),
            )
            .join(Category, Category.id == Product.category_id)
            .where(
                Product.business_id == self.business_id,
                Product.is_active == True,  # noqa: E712
                Product.stock_quantity <= LOW_STOCK_THRESHOLD,
            )
            .order_by(Product.stock_quantity.asc(), Product.name.asc())
        )
        rows = self.db.execute(stmt).all()
        return [
            LowStockProduct(
                id=row.id,
                name=row.name,
                sku=row.sku,
                stock_quantity=row.stock_quantity,
                category_name=row.category_name,
            )
            for row in rows
        ]

    def _count_active_products(self) -> int:
        stmt = select(func.count(Product.id)).where(
            Product.business_id == self.business_id, Product.is_active == True  # noqa: E712
        )
        return int(self.db.scalar(stmt) or 0)

    def _count_low_stock_products(self) -> int:
        stmt = select(func.count(Product.id)).where(
            Product.business_id == self.business_id,
            Product.is_active == True,  # noqa: E712
            Product.stock_quantity <= LOW_STOCK_THRESHOLD,
        )
        return int(self.db.scalar(stmt) or 0)

    def _count_sales(self, *, start: datetime, end: datetime | None) -> int:
        stmt = select(func.count(Sale.id)).where(Sale.business_id == self.business_id, Sale.created_at >= start)
        if end is not None:
            stmt = stmt.where(Sale.created_at < end)
        return int(self.db.scalar(stmt) or 0)

    def _sum_revenue(self, *, start: datetime, end: datetime) -> Decimal:
        stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
            Sale.business_id == self.business_id, Sale.created_at >= start, Sale.created_at < end
        )
        total = self.db.scalar(stmt) or Decimal("0.00")
        return Decimal(total).quantize(Decimal("0.01"))

    def _percent_change(self, current: Decimal, previous: Decimal) -> Decimal | None:
        if previous == 0:
            return None
        return ((current - previous) / previous * 100).quantize(Decimal("0.1"))

    def _catalog_health(self, low_stock_count: int, total: int) -> MetricInsight:
        if total == 0:
            return MetricInsight(level="neutral", label="Sin productos activos")
        ratio = low_stock_count / total
        if ratio < HEALTHY_STOCK_RATIO:
            return MetricInsight(level="positive", label="Catálogo saludable")
        if ratio <= WARNING_STOCK_RATIO:
            return MetricInsight(level="warning", label="Revisión recomendada")
        return MetricInsight(level="critical", label="Stock crítico")

    def _category_balance(self, total_products: int) -> MetricInsight:
        if total_products == 0:
            return MetricInsight(level="neutral", label="Sin datos")

        stmt = (
            select(func.count(Product.id))
            .where(Product.business_id == self.business_id, Product.is_active == True)  # noqa: E712
            .group_by(Product.category_id)
            .order_by(func.count(Product.id).desc())
            .limit(1)
        )
        top_category_count = int(self.db.scalar(stmt) or 0)
        ratio = top_category_count / total_products
        if ratio < BALANCED_CATEGORY_RATIO:
            return MetricInsight(level="positive", label="Agrupación equilibrada")
        if ratio <= CONCENTRATED_CATEGORY_RATIO:
            return MetricInsight(level="warning", label="Agrupación concentrada")
        return MetricInsight(level="critical", label="Categoría dominante")

    def _sales_trend(self, current_week: int, prior_week: int) -> MetricInsight:
        if prior_week == 0:
            if current_week == 0:
                return MetricInsight(level="neutral", label="Sin ventas recientes")
            return MetricInsight(level="positive", label="En crecimiento")

        change = (current_week - prior_week) / prior_week
        if -STABLE_TREND_BAND <= change <= STABLE_TREND_BAND:
            return MetricInsight(level="positive", label="Flujo estable")
        if change > STABLE_TREND_BAND:
            return MetricInsight(level="positive", label="En crecimiento")
        return MetricInsight(level="warning", label="En descenso")
