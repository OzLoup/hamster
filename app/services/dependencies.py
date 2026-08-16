from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_business_id, get_db
from app.services.app_settings_service import AppSettingsService
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.dashboard_service import DashboardService
from app.services.open_tab_service import OpenTabService
from app.services.product_service import ProductService
from app.services.purchase_service import PurchaseService
from app.services.sale_service import SaleService
from app.services.supplier_service import SupplierService


def get_category_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> CategoryService:
    """Dependency provider for category service."""
    return CategoryService(db, business_id)


def get_product_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> ProductService:
    """Dependency provider for product service."""
    return ProductService(db, business_id)


def get_sale_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> SaleService:
    """Dependency provider for sale service."""
    return SaleService(db, business_id)


def get_supplier_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> SupplierService:
    """Dependency provider for supplier service."""
    return SupplierService(db, business_id)


def get_purchase_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> PurchaseService:
    """Dependency provider for purchase service."""
    return PurchaseService(db, business_id)


def get_dashboard_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> DashboardService:
    """Dependency provider for dashboard service."""
    return DashboardService(db, business_id)


def get_app_settings_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> AppSettingsService:
    """Dependency provider for app settings service."""
    return AppSettingsService(db, business_id)


def get_open_tab_service(
    db: Session = Depends(get_db), business_id: int = Depends(get_current_business_id)
) -> OpenTabService:
    """Dependency provider for open tab service."""
    return OpenTabService(db, business_id)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency provider for auth service."""
    return AuthService(db)
