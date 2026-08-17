from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.dependencies import require_superuser
from app.schemas.superuser import SuperuserCreate, SuperuserRead
from app.services.dependencies import get_superuser_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.superuser_service import SuperuserService

router = APIRouter(
    prefix="/admin/superusers", tags=["admin-superusers"], dependencies=[Depends(require_superuser)]
)

SuperuserId = Annotated[int, Path(ge=1, description="Superuser identifier")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[SuperuserRead])
def list_superusers(service: SuperuserService = Depends(get_superuser_service)) -> list[SuperuserRead]:
    try:
        return service.list_superusers()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=SuperuserRead, status_code=status.HTTP_201_CREATED)
def create_superuser(
    payload: SuperuserCreate, service: SuperuserService = Depends(get_superuser_service)
) -> SuperuserRead:
    try:
        return service.create_superuser(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{user_id}/deactivate", response_model=SuperuserRead)
def deactivate_superuser(
    user_id: SuperuserId, service: SuperuserService = Depends(get_superuser_service)
) -> SuperuserRead:
    try:
        return service.set_active_status(user_id, False)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{user_id}/activate", response_model=SuperuserRead)
def activate_superuser(
    user_id: SuperuserId, service: SuperuserService = Depends(get_superuser_service)
) -> SuperuserRead:
    try:
        return service.set_active_status(user_id, True)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
