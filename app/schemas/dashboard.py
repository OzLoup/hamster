from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

InsightLevel = Literal["positive", "neutral", "warning", "critical"]


class MetricInsight(BaseModel):
    level: InsightLevel
    label: str


class LowStockProduct(BaseModel):
    id: int
    name: str
    sku: str
    stock_quantity: int
    category_name: str


class DashboardSummary(BaseModel):
    total_products: int
    total_categories: int
    sales_this_month: int
    sales_today: int
    revenue_today: Decimal
    revenue_change_pct: Decimal | None
    low_stock_products: int
    low_stock_threshold: int
    catalog_health: MetricInsight
    category_balance: MetricInsight
    sales_trend: MetricInsight
