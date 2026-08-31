from collections.abc import Generator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Order, OrderStatus
from app.schemas import OrderCreate, OrderResponse
from app.services import (
    DownstreamServiceError,
    OrderCompensationError,
    OrderNotFoundError,
    OrderStateConflictError,
    ProductUnavailableError,
    ServiceClient,
    StockReleaseError,
    StockReservationError,
    WarehouseUnavailableError,
    cancel_order,
    confirm_order,
    create_order,
    get_order,
    list_orders,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def get_service_client() -> Generator[ServiceClient, None, None]:
    """Provide one downstream-service client per API request."""

    with ServiceClient() as service_client:
        yield service_client


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_endpoint(
    request: OrderCreate,
    database: Session = Depends(get_db),
    service_client: ServiceClient = Depends(get_service_client),
) -> Order:
    """Create an order and reserve every requested product."""

    try:
        return create_order(
            database,
            request,
            service_client,
        )
    except (
        ProductUnavailableError,
        WarehouseUnavailableError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except StockReservationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except OrderCompensationError as error:
        # Manual reconciliation may be required when compensation fails.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except DownstreamServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[OrderResponse],
)
def list_orders_endpoint(
    order_status: OrderStatus | None = Query(
        default=None,
        alias="status",
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    database: Session = Depends(get_db),
) -> list[Order]:
    """List orders with optional lifecycle-status filtering."""

    return list_orders(
        database,
        status_filter=order_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order_endpoint(
    order_id: UUID,
    database: Session = Depends(get_db),
) -> Order:
    """Return one order and all of its line items."""

    try:
        return get_order(database, order_id)
    except OrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
)
def confirm_order_endpoint(
    order_id: UUID,
    database: Session = Depends(get_db),
) -> Order:
    """Confirm an order whose inventory is already reserved."""

    try:
        return confirm_order(database, order_id)
    except OrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except OrderStateConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order_endpoint(
    order_id: UUID,
    database: Session = Depends(get_db),
    service_client: ServiceClient = Depends(get_service_client),
) -> Order:
    """Cancel a reserved order and release its inventory."""

    try:
        return cancel_order(
            database,
            order_id,
            service_client,
        )
    except OrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except OrderStateConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except StockReleaseError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except OrderCompensationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except DownstreamServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error