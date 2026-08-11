from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.purchase import PurchaseCreate, PurchaseRead, PurchaseUpdate
from app.services.dependencies import get_purchase_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.purchase_service import PurchaseService

router = APIRouter(prefix="/purchases", tags=["purchases"])


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[PurchaseRead])
def list_purchases(service: PurchaseService = Depends(get_purchase_service)) -> list[PurchaseRead]:
    try:
        return service.list_purchases()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_purchase(purchase_id: int, service: PurchaseService = Depends(get_purchase_service)) -> PurchaseRead:
    try:
        return service.get_purchase(purchase_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
def create_purchase(
    payload: PurchaseCreate, service: PurchaseService = Depends(get_purchase_service)
) -> PurchaseRead:
    try:
        return service.create_purchase(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.patch("/{purchase_id}", response_model=PurchaseRead)
def update_purchase(
    purchase_id: int, payload: PurchaseUpdate, service: PurchaseService = Depends(get_purchase_service)
) -> PurchaseRead:
    try:
        return service.update_purchase(purchase_id, payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
