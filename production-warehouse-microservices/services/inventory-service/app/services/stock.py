from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import InventoryBalance, Product, StockMovement
from app.schemas.stock import (
    StockIssueRequest,
    StockReceiptRequest,
    StockReleaseRequest,
    StockReservationRequest,
    StockTransferRequest,
)


class ProductNotFoundError(Exception):
    """Raised when a stock operation references an unknown product."""

    def __init__(self, product_id: UUID) -> None:
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' was not found")


class InsufficientStockError(Exception):
    """Raised when available stock is below the requested quantity."""

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


class ReservationAlreadyExistsError(Exception):
    """Raised when an order attempts to reserve the same stock twice."""

    def __init__(
        self,
        reference_id: str,
        reserved_quantity: int,
    ) -> None:
        self.reference_id = reference_id
        self.reserved_quantity = reserved_quantity
        super().__init__(
            f"Reservation '{reference_id}' already has "
            f"{reserved_quantity} reserved"
        )


class InsufficientReservedStockError(Exception):
    """Raised when an order attempts to release too much stock."""

    def __init__(
        self,
        reserved_quantity: int,
        requested_quantity: int,
        reference_id: str,
    ) -> None:
        self.reserved_quantity = reserved_quantity
        self.requested_quantity = requested_quantity
        self.reference_id = reference_id
        super().__init__(
            "Insufficient reserved stock: "
            f"{reserved_quantity} reserved for '{reference_id}', "
            f"{requested_quantity} requested"
        )


@dataclass(frozen=True)
class StockOperationResult:
    """Result returned by a receipt or issue operation."""

    balance: InventoryBalance
    movement: StockMovement


@dataclass(frozen=True)
class StockTransferResult:
    """Result returned after both sides of a transfer are committed."""

    transfer_id: UUID
    source_balance: InventoryBalance
    destination_balance: InventoryBalance
    outbound_movement: StockMovement
    inbound_movement: StockMovement


def _ensure_product_exists(
    database: Session,
    product_id: UUID,
) -> None:
    """Verify that the product exists before changing inventory."""

    product = database.get(Product, product_id)

    if product is None:
        raise ProductNotFoundError(product_id)

def _get_reference_reserved_quantity(
    database: Session,
    product_id: UUID,
    warehouse_id: UUID,
    reference_id: str,
) -> int:
    """Return the remaining reservation owned by one order reference."""

    statement = select(
        func.coalesce(
            func.sum(StockMovement.reserved_delta),
            0,
        )
    ).where(
        StockMovement.product_id == product_id,
        StockMovement.warehouse_id == warehouse_id,
        StockMovement.reference_id == reference_id,
        StockMovement.movement_type.in_(
            [
                "RESERVATION",
                "RELEASE",
            ]
        ),
    )

    return int(database.scalar(statement) or 0)


def _insert_empty_balance_if_missing(
    database: Session,
    product_id: UUID,
    warehouse_id: UUID,
) -> None:
    """Create an empty balance without failing on concurrent inserts."""

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


def _get_balance_for_update(
    database: Session,
    product_id: UUID,
    warehouse_id: UUID,
) -> InventoryBalance | None:
    """Load and lock one balance until the transaction finishes."""

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
    """Create the balance when necessary and return it row-locked."""

    _insert_empty_balance_if_missing(
        database,
        product_id,
        warehouse_id,
    )

    balance = _get_balance_for_update(
        database,
        product_id,
        warehouse_id,
    )

    if balance is None:
        raise RuntimeError("Inventory balance could not be created")

    return balance


def _get_transfer_balances_for_update(
    database: Session,
    product_id: UUID,
    source_warehouse_id: UUID,
    destination_warehouse_id: UUID,
) -> tuple[InventoryBalance | None, InventoryBalance]:
    """Lock both transfer balances using a deterministic lock order."""

    # A destination is allowed to receive a product for the first time.
    _insert_empty_balance_if_missing(
        database,
        product_id,
        destination_warehouse_id,
    )

    # Ordering by warehouse UUID ensures concurrent opposite-direction
    # transfers request locks in the same order, reducing deadlock risk.
    statement = (
        select(InventoryBalance)
        .where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.warehouse_id.in_(
                [
                    source_warehouse_id,
                    destination_warehouse_id,
                ]
            ),
        )
        .order_by(InventoryBalance.warehouse_id)
        .with_for_update()
    )

    balances = {
        balance.warehouse_id: balance
        for balance in database.scalars(statement).all()
    }

    source_balance = balances.get(source_warehouse_id)
    destination_balance = balances.get(destination_warehouse_id)

    if destination_balance is None:
        raise RuntimeError(
            "Destination inventory balance could not be created"
        )

    return source_balance, destination_balance


def receive_stock(
    database: Session,
    request: StockReceiptRequest,
) -> StockOperationResult:
    """Increase on-hand stock and create its audit movement."""

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
            transfer_id=None,
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
        # No partial balance or movement may remain after a failed operation.
        database.rollback()
        raise


def issue_stock(
    database: Session,
    request: StockIssueRequest,
) -> StockOperationResult:
    """Decrease available stock without allowing a negative balance."""

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
            transfer_id=None,
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

def reserve_stock(
    database: Session,
    request: StockReservationRequest,
) -> StockOperationResult:
    """Reserve available stock for one order reference."""

    try:
        _ensure_product_exists(database, request.product_id)

        balance = _get_balance_for_update(
            database,
            request.product_id,
            request.warehouse_id,
        )

        reserved_for_reference = _get_reference_reserved_quantity(
            database=database,
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            reference_id=request.reference_id,
        )

        # Repeated requests must not reserve the same order twice.
        if reserved_for_reference > 0:
            raise ReservationAlreadyExistsError(
                reference_id=request.reference_id,
                reserved_quantity=reserved_for_reference,
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

        balance.quantity_reserved += request.quantity

        movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            movement_type="RESERVATION",
            on_hand_delta=0,
            reserved_delta=request.quantity,
            on_hand_balance_after=balance.quantity_on_hand,
            reserved_balance_after=balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
            transfer_id=None,
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
        # A failed reservation must not consume any available quantity.
        database.rollback()
        raise


def release_stock(
    database: Session,
    request: StockReleaseRequest,
) -> StockOperationResult:
    """Release stock owned by one order reference."""

    try:
        _ensure_product_exists(database, request.product_id)

        balance = _get_balance_for_update(
            database,
            request.product_id,
            request.warehouse_id,
        )

        reserved_for_reference = _get_reference_reserved_quantity(
            database=database,
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            reference_id=request.reference_id,
        )

        releasable_quantity = 0

        if balance is not None:
            # This defensive minimum protects the aggregate balance even if
            # its audit history becomes inconsistent.
            releasable_quantity = min(
                reserved_for_reference,
                balance.quantity_reserved,
            )

        if (
            balance is None
            or request.quantity > releasable_quantity
        ):
            raise InsufficientReservedStockError(
                reserved_quantity=releasable_quantity,
                requested_quantity=request.quantity,
                reference_id=request.reference_id,
            )

        balance.quantity_reserved -= request.quantity

        movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            movement_type="RELEASE",
            on_hand_delta=0,
            reserved_delta=-request.quantity,
            on_hand_balance_after=balance.quantity_on_hand,
            reserved_balance_after=balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
            transfer_id=None,
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
        # Rollback keeps the order reservation unchanged after any error.
        database.rollback()
        raise


def transfer_stock(
    database: Session,
    request: StockTransferRequest,
) -> StockTransferResult:
    """Atomically move available stock between two warehouses."""

    try:
        _ensure_product_exists(database, request.product_id)

        source_balance, destination_balance = (
            _get_transfer_balances_for_update(
                database=database,
                product_id=request.product_id,
                source_warehouse_id=request.source_warehouse_id,
                destination_warehouse_id=request.destination_warehouse_id,
            )
        )

        available_quantity = 0

        if source_balance is not None:
            available_quantity = (
                source_balance.quantity_on_hand
                - source_balance.quantity_reserved
            )

        if (
            source_balance is None
            or request.quantity > available_quantity
        ):
            raise InsufficientStockError(
                available_quantity=available_quantity,
                requested_quantity=request.quantity,
            )

        transfer_id = uuid4()

        # Both balance changes occur before one commit, so PostgreSQL either
        # saves the complete transfer or rolls back both sides.
        source_balance.quantity_on_hand -= request.quantity
        destination_balance.quantity_on_hand += request.quantity

        outbound_movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.source_warehouse_id,
            movement_type="TRANSFER_OUT",
            on_hand_delta=-request.quantity,
            reserved_delta=0,
            on_hand_balance_after=source_balance.quantity_on_hand,
            reserved_balance_after=source_balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
            transfer_id=transfer_id,
        )
        inbound_movement = StockMovement(
            product_id=request.product_id,
            warehouse_id=request.destination_warehouse_id,
            movement_type="TRANSFER_IN",
            on_hand_delta=request.quantity,
            reserved_delta=0,
            on_hand_balance_after=destination_balance.quantity_on_hand,
            reserved_balance_after=destination_balance.quantity_reserved,
            reference_id=request.reference_id,
            reason=request.reason,
            transfer_id=transfer_id,
        )

        database.add_all(
            [
                outbound_movement,
                inbound_movement,
            ]
        )
        database.commit()

        database.refresh(source_balance)
        database.refresh(destination_balance)
        database.refresh(outbound_movement)
        database.refresh(inbound_movement)

        return StockTransferResult(
            transfer_id=transfer_id,
            source_balance=source_balance,
            destination_balance=destination_balance,
            outbound_movement=outbound_movement,
            inbound_movement=inbound_movement,
        )
    except Exception:
        # A failure must restore both warehouses and discard both movements.
        database.rollback()
        raise