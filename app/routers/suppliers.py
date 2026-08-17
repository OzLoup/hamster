from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.core.dependencies import require_role
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services.dependencies import get_supplier_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.supplier_service import SupplierService

router = APIRouter(
    prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_role("admin", "coordinator"))]
)

SupplierId = Annotated[int, Path(ge=1, description="Supplier identifier")]
ActiveFilter = Annotated[bool | None, Query(description="Filter by active status")]


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[SupplierRead], status_code=status.HTTP_200_OK)
def list_suppliers(
    is_active: ActiveFilter = None,
    service: SupplierService = Depends(get_supplier_service),
) -> list[SupplierRead]:
    try:
        return service.list_suppliers(is_active=is_active)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get("/{supplier_id}", response_model=SupplierRead, status_code=status.HTTP_200_OK)
def get_supplier(
    supplier_id: SupplierId, service: SupplierService = Depends(get_supplier_service)
) -> SupplierRead:
    try:
        return service.get_supplier(supplier_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate, service: SupplierService = Depends(get_supplier_service)
) -> SupplierRead:
    try:
        return service.create_supplier(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.put("/{supplier_id}", response_model=SupplierRead, status_code=status.HTTP_200_OK)
def update_supplier(
    supplier_id: SupplierId,
    payload: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    try:
        update_payload = SupplierUpdate(**payload.model_dump())
        return service.update_supplier(supplier_id, update_payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{supplier_id}/deactivate", response_model=SupplierRead, status_code=status.HTTP_200_OK)
def deactivate_supplier(
    supplier_id: SupplierId, service: SupplierService = Depends(get_supplier_service)
) -> SupplierRead:
    try:
        return service.set_active_status(supplier_id, False)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{supplier_id}/activate", response_model=SupplierRead, status_code=status.HTTP_200_OK)
def activate_supplier(
    supplier_id: SupplierId, service: SupplierService = Depends(get_supplier_service)
) -> SupplierRead:
    try:
        return service.set_active_status(supplier_id, True)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: SupplierId, service: SupplierService = Depends(get_supplier_service)
) -> Response:
    try:
        service.delete_supplier(supplier_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
