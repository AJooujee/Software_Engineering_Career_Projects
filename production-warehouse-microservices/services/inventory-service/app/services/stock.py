from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import InventoryBalance, Product, StockMovement
from app.schemas import StockIssueRequest, StockReceiptRequest


class ProductNotFoundError(Exception):
    def __init__(self, product_id: UUID) -> None:
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' was not found")


class InsufficientStockError(Exception):
    def __init__(
        self,
        available_quantity: int,
        requested_quantity: int,
    ) -> None:
        self.available_quantity = available_quantity
        self.requested_quantity = requested_quantity
        super().__init__(
            "Insufficient stock: "
            f"{available_quantity} available, "
            f"{requested_quantity} requested"
        )


@dataclass(frozen=True)
class StockOperationResult:
    balance: InventoryBalance
    movement: StockMovement


def _ensure_product_exists(
    database: Session,
    product_id: UUID,
) -> None:
    product = database.get(Product, product_id)

    if product is None:
        raise ProductNotFoundError(product_id)


def _get_balance_for_update(
    database: Session,
    product_id: UUID,
    warehouse_id: UUID,
) -> InventoryBalance | None:
    statement = (
        select(InventoryBalance)
        .where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.warehouse_id == warehouse_id,
        )
        .with_for_update()
    )

    return database.scalar(statement)


def _get_or_create_balance_for_update(
    database: Session,
    product_id: UUID,
    warehouse_id: UUID,
) -> InventoryBalance:
    create_statement = (
        insert(InventoryBalance)
        .values(
            id=uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=0,
            quantity_reserved=0,
        )
        .on_conflict_do_nothing(
            index_elements=["product_id", "warehouse_id"],
        )
    )

    database.execute(create_statement)

    balance = _get_balance_for_update(
        database,
        product_id,
        warehouse_id,
    )

    if balance is None:
        raise RuntimeError("Inventory balance could not be created")

    return balance


def receive_stock(
    database: Session,
    request: StockReceiptRequest,
) -> StockOperationResult:
    try:
        _ensure_product_exists(database, request.product_id)

        balance = _get_or_create_balance_for_update(
            database,
            request.product_id,
            request.warehouse_id,
        )

        balance.quantity_on_hand += request.quantity

        movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            movement_type="RECEIPT",
            on_hand_delta=request.quantity,
            reserved_delta=0,
            on_hand_balance_after=balance.quantity_on_hand,
            reserved_balance_after=balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
        )

        database.add(movement)
        database.commit()
        database.refresh(balance)
        database.refresh(movement)

        return StockOperationResult(
            balance=balance,
            movement=movement,
        )
    except Exception:
        database.rollback()
        raise


def issue_stock(
    database: Session,
    request: StockIssueRequest,
) -> StockOperationResult:
    try:
        _ensure_product_exists(database, request.product_id)

        balance = _get_balance_for_update(
            database,
            request.product_id,
            request.warehouse_id,
        )

        available_quantity = 0

        if balance is not None:
            available_quantity = (
                balance.quantity_on_hand
                - balance.quantity_reserved
            )

        if balance is None or request.quantity > available_quantity:
            raise InsufficientStockError(
                available_quantity=available_quantity,
                requested_quantity=request.quantity,
            )

        balance.quantity_on_hand -= request.quantity

        movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            movement_type="ISSUE",
            on_hand_delta=-request.quantity,
            reserved_delta=0,
            on_hand_balance_after=balance.quantity_on_hand,
            reserved_balance_after=balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
        )

        database.add(movement)
        database.commit()
        database.refresh(balance)
        database.refresh(movement)

        return StockOperationResult(
            balance=balance,
            movement=movement,
        )
    except Exception:
        database.rollback()
        raise