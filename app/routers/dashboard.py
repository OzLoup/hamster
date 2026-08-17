from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import require_role
from app.schemas.dashboard import DashboardSummary, LowStockProduct
from app.services.dashboard_service import DashboardService
from app.services.dependencies import get_dashboard_service

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_role("admin", "coordinator"))]
)

TimezoneParam = Annotated[
    str | None, Query(max_length=64, description="IANA timezone name, e.g. America/Bogota")
]


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    tz: TimezoneParam = None,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return service.get_summary(tz)


@router.get("/low-stock-products", response_model=list[LowStockProduct])
def list_low_stock_products(
    service: DashboardService = Depends(get_dashboard_service),
) -> list[LowStockProduct]:
    return service.list_low_stock_products()
