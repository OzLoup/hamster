from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.app_settings_service import AppSettingsService
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.dashboard_service import DashboardService
from app.services.open_tab_service import OpenTabService
from app.services.product_service import ProductService
from app.services.purchase_service import PurchaseService
from app.services.sale_service import SaleService
from app.services.supplier_service import SupplierService


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Dependency provider for category service."""
    return CategoryService(db)


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Dependency provider for product service."""
    return ProductService(db)


def get_sale_service(db: Session = Depends(get_db)) -> SaleService:
    """Dependency provider for sale service."""
    return SaleService(db)


def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    """Dependency provider for supplier service."""
    return SupplierService(db)


def get_purchase_service(db: Session = Depends(get_db)) -> PurchaseService:
    """Dependency provider for purchase service."""
    return PurchaseService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency provider for dashboard service."""
    return DashboardService(db)


def get_app_settings_service(db: Session = Depends(get_db)) -> AppSettingsService:
    """Dependency provider for app settings service."""
    return AppSettingsService(db)


def get_open_tab_service(db: Session = Depends(get_db)) -> OpenTabService:
    """Dependency provider for open tab service."""
    return OpenTabService(db)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency provider for auth service."""
    return AuthService(db)
