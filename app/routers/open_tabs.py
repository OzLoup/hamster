from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.schemas.open_tab import (
    OpenTabCloseRequest,
    OpenTabCreate,
    OpenTabItemCreate,
    OpenTabRead,
)
from app.schemas.sale import SaleRead
from app.services.dependencies import get_open_tab_service
from app.services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from app.services.open_tab_service import OpenTabService

router = APIRouter(prefix="/open-tabs", tags=["open-tabs"])


def _raise_http_from_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[OpenTabRead])
def list_open_tabs(service: OpenTabService = Depends(get_open_tab_service)) -> list[OpenTabRead]:
    try:
        return service.list_tabs()
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.get("/{tab_id}", response_model=OpenTabRead)
def get_open_tab(tab_id: int, service: OpenTabService = Depends(get_open_tab_service)) -> OpenTabRead:
    try:
        return service.get_tab(tab_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("", response_model=OpenTabRead, status_code=status.HTTP_201_CREATED)
def create_open_tab(
    payload: OpenTabCreate, service: OpenTabService = Depends(get_open_tab_service)
) -> OpenTabRead:
    try:
        return service.create_tab(payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.post("/{tab_id}/items", response_model=OpenTabRead, status_code=status.HTTP_201_CREATED)
def add_open_tab_item(
    tab_id: int, payload: OpenTabItemCreate, service: OpenTabService = Depends(get_open_tab_service)
) -> OpenTabRead:
    try:
        return service.add_item(tab_id, payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.delete("/{tab_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_open_tab_item(
    tab_id: int, item_id: int, service: OpenTabService = Depends(get_open_tab_service)
) -> Response:
    try:
        service.remove_item(tab_id, item_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{tab_id}/close", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def close_open_tab(
    tab_id: int, payload: OpenTabCloseRequest, service: OpenTabService = Depends(get_open_tab_service)
) -> SaleRead:
    try:
        return service.close_tab(tab_id, payload)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)


@router.delete("/{tab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_open_tab(tab_id: int, service: OpenTabService = Depends(get_open_tab_service)) -> Response:
    try:
        service.delete_tab(tab_id)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
