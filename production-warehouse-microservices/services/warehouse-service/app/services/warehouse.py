from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Warehouse
from app.schemas import WarehouseCreate, WarehouseUpdate


class WarehouseNotFoundError(Exception):
    """Raised when a requested warehouse does not exist."""

    def __init__(self, warehouse_id: UUID) -> None:
        self.warehouse_id = warehouse_id
        super().__init__(f"Warehouse '{warehouse_id}' was not found")


class WarehouseCodeConflictError(Exception):
    """Raised when a warehouse code is already in use."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Warehouse code '{code}' already exists")


def _find_warehouse_by_code(
    database: Session,
    code: str,
) -> Warehouse | None:
    """Find a warehouse by its normalized business code."""
    statement = select(Warehouse).where(Warehouse.code == code)

    return database.scalar(statement)


def get_warehouse(
    database: Session,
    warehouse_id: UUID,
) -> Warehouse:
    """Return one warehouse or raise a domain-specific error."""
    warehouse = database.get(Warehouse, warehouse_id)

    if warehouse is None:
        raise WarehouseNotFoundError(warehouse_id)

    return warehouse


def list_warehouses(
    database: Session,
    *,
    include_inactive: bool,
    offset: int,
    limit: int,
) -> list[Warehouse]:
    """Return warehouses using deterministic pagination."""
    statement = select(Warehouse)

    # Inactive locations are hidden from normal operational queries.
    if not include_inactive:
        statement = statement.where(Warehouse.is_active.is_(True))

    statement = (
        statement
        .order_by(Warehouse.code)
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())


def create_warehouse(
    database: Session,
    request: WarehouseCreate,
) -> Warehouse:
    """Create a warehouse while enforcing unique business codes."""
    if _find_warehouse_by_code(database, request.code) is not None:
        raise WarehouseCodeConflictError(request.code)

    warehouse = Warehouse(**request.model_dump())
    database.add(warehouse)

    try:
        database.commit()
        database.refresh(warehouse)
    except IntegrityError as error:
        # The database constraint also protects against concurrent requests
        # that attempt to create the same code at nearly the same time.
        database.rollback()
        raise WarehouseCodeConflictError(request.code) from error
    except Exception:
        database.rollback()
        raise

    return warehouse


def update_warehouse(
    database: Session,
    warehouse_id: UUID,
    request: WarehouseUpdate,
) -> Warehouse:
    """Apply only fields explicitly supplied by the client."""
    warehouse = get_warehouse(database, warehouse_id)
    update_values = request.model_dump(exclude_unset=True)

    new_code = update_values.get("code")

    if new_code is not None and new_code != warehouse.code:
        conflicting_warehouse = _find_warehouse_by_code(
            database,
            new_code,
        )

        if conflicting_warehouse is not None:
            raise WarehouseCodeConflictError(new_code)

    # exclude_unset=True allows PATCH semantics and also permits explicitly
    # clearing nullable fields such as address_line_2.
    for field_name, value in update_values.items():
        setattr(warehouse, field_name, value)

    try:
        database.commit()
        database.refresh(warehouse)
    except IntegrityError as error:
        database.rollback()

        conflict_code = new_code or warehouse.code
        raise WarehouseCodeConflictError(conflict_code) from error
    except Exception:
        database.rollback()
        raise

    return warehouse


def deactivate_warehouse(
    database: Session,
    warehouse_id: UUID,
) -> None:
    """Soft-delete a warehouse so historical records remain valid."""
    warehouse = get_warehouse(database, warehouse_id)

    # A soft delete preserves the location for future transfer history.
    warehouse.is_active = False

    try:
        database.commit()
    except Exception:
        database.rollback()
        raise