from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Warehouse
from app.schemas import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.services import (
    WarehouseCodeConflictError,
    WarehouseNotFoundError,
    create_warehouse,
    deactivate_warehouse,
    get_warehouse,
    list_warehouses,
    update_warehouse,
)


router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"],
)


@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse_endpoint(
    request: WarehouseCreate,
    database: Session = Depends(get_db),
) -> Warehouse:
    """Create a warehouse with a globally unique business code."""
    try:
        return create_warehouse(database, request)
    except WarehouseCodeConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[WarehouseResponse],
)
def list_warehouses_endpoint(
    include_inactive: bool = Query(default=False),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    database: Session = Depends(get_db),
) -> list[Warehouse]:
    """List active warehouses unless inactive records are requested."""
    return list_warehouses(
        database,
        include_inactive=include_inactive,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def get_warehouse_endpoint(
    warehouse_id: UUID,
    database: Session = Depends(get_db),
) -> Warehouse:
    """Return a warehouse by its UUID."""
    try:
        return get_warehouse(database, warehouse_id)
    except WarehouseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def update_warehouse_endpoint(
    warehouse_id: UUID,
    request: WarehouseUpdate,
    database: Session = Depends(get_db),
) -> Warehouse:
    """Partially update a warehouse using only supplied fields."""
    try:
        return update_warehouse(
            database,
            warehouse_id,
            request,
        )
    except WarehouseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except WarehouseCodeConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_warehouse_endpoint(
    warehouse_id: UUID,
    database: Session = Depends(get_db),
) -> Response:
    """Deactivate a warehouse while preserving historical references."""
    try:
        deactivate_warehouse(database, warehouse_id)
    except WarehouseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    # HTTP 204 responses intentionally contain no JSON response body.
    return Response(status_code=status.HTTP_204_NO_CONTENT)