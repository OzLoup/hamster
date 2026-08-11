from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.app_settings import AppSettingsRead, AppSettingsUpdate
from app.services.app_settings_service import AppSettingsService
from app.services.dependencies import get_app_settings_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/settings", tags=["settings"])


def _raise_http_from_service_error(exc: Exception) -> None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=AppSettingsRead)
def get_settings(service: AppSettingsService = Depends(get_app_settings_service)) -> AppSettingsRead:
    try:
        return service.get_settings()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.put("", response_model=AppSettingsRead)
def update_settings(
    payload: AppSettingsUpdate, service: AppSettingsService = Depends(get_app_settings_service)
) -> AppSettingsRead:
    try:
        return service.update_settings(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
