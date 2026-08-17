from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.core.dependencies import require_role
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService
from app.services.dependencies import get_category_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError

router = APIRouter(prefix="/categories", tags=["categories"])
WriteAccess = Depends(require_role("admin", "coordinator"))

CategoryId = Annotated[int, Path(ge=1, description="Category identifier")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[CategoryRead],
    status_code=status.HTTP_200_OK,
    summary="List categories",
)
def list_categories(service: CategoryService = Depends(get_category_service)) -> list[CategoryRead]:
    try:
        return service.list_categories()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Get category by id",
)
def get_category(category_id: CategoryId, service: CategoryService = Depends(get_category_service)) -> CategoryRead:
    try:
        return service.get_category(category_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    dependencies=[WriteAccess],
)
def create_category(
    payload: CategoryCreate, service: CategoryService = Depends(get_category_service)
) -> CategoryRead:
    try:
        return service.create_category(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Replace category",
    dependencies=[WriteAccess],
)
def update_category(
    category_id: CategoryId,
    payload: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    try:
        update_payload = CategoryUpdate(name=payload.name, description=payload.description)
        return service.update_category(category_id, update_payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    dependencies=[WriteAccess],
)
def delete_category(
    category_id: CategoryId, service: CategoryService = Depends(get_category_service)
) -> Response:
    try:
        service.delete_category(category_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
