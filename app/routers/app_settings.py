from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import require_role
from app.models.business import Business
from app.schemas.app_settings import AppSettingsRead, AppSettingsUpdate
from app.services.app_settings_service import AppSettingsService
from app.services.dependencies import get_app_settings_service
from app.services.exceptions import NotFoundError, ServiceError

router = APIRouter(prefix="/settings", tags=["settings"])


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


def _to_app_settings_read(business: Business) -> AppSettingsRead:
    return AppSettingsRead(
        id=business.id,
        business_name=business.name,
        created_at=business.created_at,
        updated_at=business.updated_at,
    )


@router.get(
    "", response_model=AppSettingsRead, dependencies=[Depends(require_role("admin", "coordinator", "seller"))]
)
def get_settings(service: AppSettingsService = Depends(get_app_settings_service)) -> AppSettingsRead:
    try:
        return _to_app_settings_read(service.get_settings())
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.put("", response_model=AppSettingsRead, dependencies=[Depends(require_role("admin"))])
def update_settings(
    payload: AppSettingsUpdate, service: AppSettingsService = Depends(get_app_settings_service)
) -> AppSettingsRead:
    try:
        return _to_app_settings_read(service.update_settings(payload))
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
