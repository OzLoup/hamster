from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.schemas.product import ProductCreate, ProductListResponse, ProductRead, ProductUpdate
from app.services.dependencies import get_product_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

ProductId = Annotated[int, Path(ge=1, description="Product identifier")]
Page = Annotated[int, Query(ge=1, description="Page number starting at 1")]
PageSize = Annotated[int, Query(ge=1, le=100, description="Page size between 1 and 100")]
Search = Annotated[str | None, Query(min_length=1, max_length=150, description="Search by product name")]
CategoryFilter = Annotated[int | None, Query(ge=1, description="Filter by category id")]
ActiveFilter = Annotated[bool | None, Query(description="Filter by active status")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
def list_products(
    page: Page = 1,
    page_size: PageSize = 20,
    search: Search = None,
    category_id: CategoryFilter = None,
    is_active: ActiveFilter = None,
    service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    try:
        items, total = service.list_products(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            is_active=is_active,
        )
    except ServiceError as exc:
        _raise_http_from_service_error(exc)

    total_pages = ceil(total / page_size) if total else 0
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProductRead, status_code=status.HTTP_200_OK)
def get_product(
    product_id: ProductId,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    try:
        return service.get_product(product_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    try:
        return service.create_product(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.put("/{product_id}", response_model=ProductRead, status_code=status.HTTP_200_OK)
def update_product(
    product_id: ProductId,
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    try:
        update_payload = ProductUpdate(**payload.model_dump())
        return service.update_product(product_id, update_payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{product_id}/deactivate", response_model=ProductRead, status_code=status.HTTP_200_OK)
def deactivate_product(
    product_id: ProductId,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    try:
        return service.set_active_status(product_id, False)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{product_id}/activate", response_model=ProductRead, status_code=status.HTTP_200_OK)
def activate_product(
    product_id: ProductId,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    try:
        return service.set_active_status(product_id, True)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: ProductId,
    service: ProductService = Depends(get_product_service),
) -> Response:
    try:
        service.delete_product(product_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
