from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.core.dependencies import require_role
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.dependencies import get_user_service
from app.services.exceptions import AuthorizationError, ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_role("admin", "coordinator"))]
)

UserId = Annotated[int, Path(ge=1, description="User identifier")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, AuthorizationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[UserRead])
def list_users(service: UserService = Depends(get_user_service)) -> list[UserRead]:
    try:
        return service.list_users()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UserId, service: UserService = Depends(get_user_service)) -> UserRead:
    try:
        return service.get_user(user_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)) -> UserRead:
    try:
        return service.create_user(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UserId, payload: UserUpdate, service: UserService = Depends(get_user_service)
) -> UserRead:
    try:
        return service.update_user(user_id, payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: UserId, service: UserService = Depends(get_user_service)) -> UserRead:
    try:
        return service.set_active_status(user_id, False)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{user_id}/activate", response_model=UserRead)
def activate_user(user_id: UserId, service: UserService = Depends(get_user_service)) -> UserRead:
    try:
        return service.set_active_status(user_id, True)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
