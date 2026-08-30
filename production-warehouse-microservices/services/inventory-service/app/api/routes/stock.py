from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import InventoryBalance, StockMovement
from app.schemas import (
    InventoryBalanceResponse,
    StockIssueRequest,
    StockMovementResponse,
    StockOperationResponse,
    StockReceiptRequest,
    StockTransferRequest,
    StockTransferResponse,
)
from app.services import (
    InsufficientStockError,
    ProductNotFoundError,
    issue_stock,
    receive_stock,
    transfer_stock,
)


router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
)


@router.post(
    "/receipts",
    response_model=StockOperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_stock_endpoint(
    request: StockReceiptRequest,
    database: Session = Depends(get_db),
) -> dict[str, object]:
    """Receive stock and return the updated balance and audit movement."""

    try:
        result = receive_stock(database, request)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return {
        "balance": result.balance,
        "movement": result.movement,
    }


@router.post(
    "/issues",
    response_model=StockOperationResponse,
)
def issue_stock_endpoint(
    request: StockIssueRequest,
    database: Session = Depends(get_db),
) -> dict[str, object]:
    """Issue available stock without allowing a negative balance."""

    try:
        result = issue_stock(database, request)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InsufficientStockError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(error),
                "available_quantity": error.available_quantity,
                "requested_quantity": error.requested_quantity,
            },
        ) from error

    return {
        "balance": result.balance,
        "movement": result.movement,
    }


@router.post(
    "/transfers",
    response_model=StockTransferResponse,
    status_code=status.HTTP_200_OK,
)
def transfer_stock_endpoint(
    request: StockTransferRequest,
    database: Session = Depends(get_db),
) -> dict[str, object]:
    """Atomically transfer stock between two warehouse balances."""

    try:
        result = transfer_stock(database, request)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InsufficientStockError as error:
        # A rejected transfer leaves both balances and movement history
        # unchanged because the service rolls back the transaction.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(error),
                "available_quantity": error.available_quantity,
                "requested_quantity": error.requested_quantity,
            },
        ) from error

    return {
        "transfer_id": result.transfer_id,
        "source_balance": result.source_balance,
        "destination_balance": result.destination_balance,
        "outbound_movement": result.outbound_movement,
        "inbound_movement": result.inbound_movement,
    }


@router.get(
    "/balances/{warehouse_id}/{product_id}",
    response_model=InventoryBalanceResponse,
)
def get_inventory_balance_endpoint(
    warehouse_id: UUID,
    product_id: UUID,
    database: Session = Depends(get_db),
) -> InventoryBalance:
    """Return one product balance at one warehouse."""

    statement = select(InventoryBalance).where(
        InventoryBalance.product_id == product_id,
        InventoryBalance.warehouse_id == warehouse_id,
    )
    balance = database.scalar(statement)

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory balance was not found",
        )

    return balance


@router.get(
    "/movements",
    response_model=list[StockMovementResponse],
)
def list_stock_movements_endpoint(
    product_id: UUID | None = Query(default=None),
    warehouse_id: UUID | None = Query(default=None),
    transfer_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    database: Session = Depends(get_db),
) -> list[StockMovement]:
    """List movement history using optional audit filters."""

    statement = select(StockMovement)

    if product_id is not None:
        statement = statement.where(
            StockMovement.product_id == product_id,
        )

    if warehouse_id is not None:
        statement = statement.where(
            StockMovement.warehouse_id == warehouse_id,
        )

    if transfer_id is not None:
        # A successful transfer returns exactly one outbound and one inbound
        # movement sharing this identifier.
        statement = statement.where(
            StockMovement.transfer_id == transfer_id,
        )

    statement = (
        statement
        .order_by(StockMovement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())