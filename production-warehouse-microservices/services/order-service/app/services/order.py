from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, OrderItem, OrderStatus
from app.schemas import OrderCreate
from app.services.external import (
    DownstreamServiceError,
    ServiceClient,
)


MONEY_QUANTUM = Decimal("0.01")


class OrderNotFoundError(LookupError):
    """Raised when an order does not exist."""


class OrderStateConflictError(RuntimeError):
    """Raised when an operation is invalid for the current order state."""


class OrderCompensationError(RuntimeError):
    """Raised when a distributed rollback cannot be completed safely."""


@dataclass(frozen=True)
class ReservationLine:
    """Immutable data used for reservation and compensation calls."""

    product_id: UUID
    quantity: int


def _generate_order_number(order_id: UUID) -> str:
    """Create a unique public reference from the order UUID."""

    return f"ORD-{order_id.hex.upper()}"


def _load_order(
    database: Session,
    order_id: UUID,
    *,
    for_update: bool = False,
) -> Order | None:
    """Load one order and its items, optionally locking its state."""

    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )

    if for_update:
        statement = statement.with_for_update()

    return database.scalar(statement)


def _require_order(
    database: Session,
    order_id: UUID,
    *,
    for_update: bool = False,
) -> Order:
    """Return an order or raise the service-level not-found error."""

    order = _load_order(
        database,
        order_id,
        for_update=for_update,
    )

    if order is None:
        raise OrderNotFoundError(
            f"Order '{order_id}' was not found"
        )

    return order


def _build_order(
    request: OrderCreate,
    service_client: ServiceClient,
) -> tuple[Order, list[ReservationLine]]:
    """Validate external references and build an uncommitted order."""

    service_client.verify_warehouse(request.warehouse_id)

    order_id = uuid4()
    order_items: list[OrderItem] = []
    reservation_lines: list[ReservationLine] = []
    total_amount = Decimal("0.00")

    for requested_item in request.items:
        product = service_client.get_product(
            requested_item.product_id
        )

        if product.unit_price < 0:
            raise DownstreamServiceError(
                "Inventory Service returned a negative product price"
            )

        unit_price = product.unit_price.quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        line_total = (
            unit_price * requested_item.quantity
        ).quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

        order_items.append(
            OrderItem(
                product_id=requested_item.product_id,
                quantity=requested_item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
        reservation_lines.append(
            ReservationLine(
                product_id=requested_item.product_id,
                quantity=requested_item.quantity,
            )
        )
        total_amount += line_total

    order = Order(
        id=order_id,
        order_number=_generate_order_number(order_id),
        customer_name=request.customer_name,
        customer_email=str(request.customer_email),
        warehouse_id=request.warehouse_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount.quantize(MONEY_QUANTUM),
        items=order_items,
    )

    return order, reservation_lines


def _release_lines(
    service_client: ServiceClient,
    lines: list[ReservationLine],
    *,
    warehouse_id: UUID,
    reference_id: str,
) -> list[str]:
    """Best-effort release used to compensate failed order creation."""

    failures: list[str] = []

    # Reverse order mirrors the successful reservation sequence.
    for line in reversed(lines):
        try:
            service_client.release_stock(
                product_id=line.product_id,
                warehouse_id=warehouse_id,
                quantity=line.quantity,
                reference_id=reference_id,
            )
        except Exception as error:
            # Continue so every successful reservation gets a release attempt.
            failures.append(
                f"{line.product_id}: {error}"
            )

    return failures


def _reserve_lines(
    service_client: ServiceClient,
    lines: list[ReservationLine],
    *,
    warehouse_id: UUID,
    reference_id: str,
) -> list[str]:
    """Best-effort re-reservation used to compensate failed cancellation."""

    failures: list[str] = []

    for line in lines:
        try:
            service_client.reserve_stock(
                product_id=line.product_id,
                warehouse_id=warehouse_id,
                quantity=line.quantity,
                reference_id=reference_id,
            )
        except Exception as error:
            # Continue to report every line requiring manual reconciliation.
            failures.append(
                f"{line.product_id}: {error}"
            )

    return failures


def _create_order(
    database: Session,
    request: OrderCreate,
    service_client: ServiceClient,
) -> Order:
    """Create an order and reserve every line as one logical operation."""

    order, reservation_lines = _build_order(
        request,
        service_client,
    )
    reserved_lines: list[ReservationLine] = []

    database.add(order)

    try:
        database.flush()

        for line in reservation_lines:
            service_client.reserve_stock(
                product_id=line.product_id,
                warehouse_id=order.warehouse_id,
                quantity=line.quantity,
                reference_id=order.order_number,
            )
            reserved_lines.append(line)

        order.status = OrderStatus.RESERVED
        database.commit()

    except Exception as error:
        database.rollback()

        # PostgreSQL and Inventory Service cannot share one transaction.
        # Release all successful reservations when local creation fails.
        compensation_failures = _release_lines(
            service_client,
            reserved_lines,
            warehouse_id=order.warehouse_id,
            reference_id=order.order_number,
        )

        if compensation_failures:
            raise OrderCompensationError(
                "Order creation failed and some reservations could not "
                "be released: "
                + "; ".join(compensation_failures)
            ) from error

        raise

    return _require_order(database, order.id)


def create_order(
    database: Session,
    request: OrderCreate,
    service_client: ServiceClient | None = None,
) -> Order:
    """Create an order using an injected or internally managed client."""

    if service_client is not None:
        return _create_order(
            database,
            request,
            service_client,
        )

    with ServiceClient() as managed_client:
        return _create_order(
            database,
            request,
            managed_client,
        )


def get_order(
    database: Session,
    order_id: UUID,
) -> Order:
    """Return one order with all line items."""

    return _require_order(database, order_id)


def list_orders(
    database: Session,
    *,
    status_filter: OrderStatus | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Order]:
    """Return orders using an optional lifecycle-status filter."""

    statement = select(Order).options(
        selectinload(Order.items)
    )

    if status_filter is not None:
        statement = statement.where(
            Order.status == status_filter
        )

    statement = (
        statement
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())


def confirm_order(
    database: Session,
    order_id: UUID,
) -> Order:
    """Move a successfully reserved order to CONFIRMED."""

    order = _require_order(
        database,
        order_id,
        for_update=True,
    )

    if order.status == OrderStatus.CONFIRMED:
        return order

    if order.status != OrderStatus.RESERVED:
        raise OrderStateConflictError(
            f"Order '{order_id}' cannot be confirmed from "
            f"status '{order.status.value}'"
        )

    order.status = OrderStatus.CONFIRMED

    try:
        database.commit()
    except Exception:
        database.rollback()
        raise

    return _require_order(database, order_id)


def _cancel_order(
    database: Session,
    order_id: UUID,
    service_client: ServiceClient,
) -> Order:
    """Cancel one reserved order and release all owned inventory."""

    order = _require_order(
        database,
        order_id,
        for_update=True,
    )

    # Cancellation is idempotent so retries do not release stock twice.
    if order.status == OrderStatus.CANCELLED:
        return order

    if order.status != OrderStatus.RESERVED:
        raise OrderStateConflictError(
            f"Order '{order_id}' cannot be cancelled from "
            f"status '{order.status.value}'"
        )

    warehouse_id = order.warehouse_id
    reference_id = order.order_number
    reservation_lines = [
        ReservationLine(
            product_id=item.product_id,
            quantity=item.quantity,
        )
        for item in order.items
    ]
    released_lines: list[ReservationLine] = []

    try:
        for line in reservation_lines:
            service_client.release_stock(
                product_id=line.product_id,
                warehouse_id=warehouse_id,
                quantity=line.quantity,
                reference_id=reference_id,
            )
            released_lines.append(line)

        order.status = OrderStatus.CANCELLED
        database.commit()

    except Exception as error:
        database.rollback()

        # If cancellation only partially released inventory, recreate the
        # released reservations so the external state matches the order.
        compensation_failures = _reserve_lines(
            service_client,
            released_lines,
            warehouse_id=warehouse_id,
            reference_id=reference_id,
        )

        if compensation_failures:
            raise OrderCompensationError(
                "Order cancellation failed and some released inventory "
                "could not be re-reserved: "
                + "; ".join(compensation_failures)
            ) from error

        raise

    return _require_order(database, order_id)


def cancel_order(
    database: Session,
    order_id: UUID,
    service_client: ServiceClient | None = None,
) -> Order:
    """Cancel an order using an injected or internally managed client."""

    if service_client is not None:
        return _cancel_order(
            database,
            order_id,
            service_client,
        )

    with ServiceClient() as managed_client:
        return _cancel_order(
            database,
            order_id,
            managed_client,
        )