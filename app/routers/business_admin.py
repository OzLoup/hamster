from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.dependencies import require_superuser
from app.schemas.business import BusinessCreateWithAdmin, BusinessRead
from app.services.business_admin_service import BusinessAdminService
from app.services.dependencies import get_business_admin_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError

router = APIRouter(
    prefix="/admin/businesses", tags=["admin-businesses"], dependencies=[Depends(require_superuser)]
)

BusinessId = Annotated[int, Path(ge=1, description="Business identifier")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[BusinessRead])
def list_businesses(service: BusinessAdminService = Depends(get_business_admin_service)) -> list[BusinessRead]:
    try:
        return service.list_businesses()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get("/{business_id}", response_model=BusinessRead)
def get_business(
    business_id: BusinessId, service: BusinessAdminService = Depends(get_business_admin_service)
) -> BusinessRead:
    try:
        return service.get_business(business_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=BusinessRead, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreateWithAdmin, service: BusinessAdminService = Depends(get_business_admin_service)
) -> BusinessRead:
    try:
        return service.create_business(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{business_id}/deactivate", response_model=BusinessRead)
def deactivate_business(
    business_id: BusinessId, service: BusinessAdminService = Depends(get_business_admin_service)
) -> BusinessRead:
    try:
        return service.set_active_status(business_id, False)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{business_id}/activate", response_model=BusinessRead)
def activate_business(
    business_id: BusinessId, service: BusinessAdminService = Depends(get_business_admin_service)
) -> BusinessRead:
    try:
        return service.set_active_status(business_id, True)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
