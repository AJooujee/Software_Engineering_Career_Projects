from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)


# Movement types form the immutable audit history for every stock change.
MovementType = Literal[
    "RECEIPT",
    "ISSUE",
    "ADJUSTMENT",
    "RESERVATION",
    "RELEASE",
    "TRANSFER_OUT",
    "TRANSFER_IN",
]


class StockChangeRequest(BaseModel):
    """Common request fields for receipt and issue operations."""

    product_id: UUID
    warehouse_id: UUID
    quantity: int = Field(gt=0)
    reference_id: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=500)


class StockReceiptRequest(StockChangeRequest):
    """Request to increase on-hand inventory."""

    pass


class StockIssueRequest(StockChangeRequest):
    """Request to decrease available on-hand inventory."""

    pass

class StockReservationRequest(StockChangeRequest):
    """Request to reserve available inventory for an order."""

    # Every reservation must identify its owning order.
    reference_id: str = Field(min_length=1, max_length=100)


class StockReleaseRequest(StockChangeRequest):
    """Request to release inventory reserved by a specific order."""

    # Release operations must use the same order reference as reservation.
    reference_id: str = Field(min_length=1, max_length=100)


class StockTransferRequest(BaseModel):
    """Request to move stock between two different warehouses."""

    product_id: UUID
    source_warehouse_id: UUID
    destination_warehouse_id: UUID
    quantity: int = Field(gt=0)
    reference_id: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_different_warehouses(self) -> Self:
        # Moving stock to the same warehouse has no business meaning and
        # would produce misleading audit movements.
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError(
                "Source and destination warehouses must be different"
            )

        return self


class InventoryBalanceResponse(BaseModel):
    """Current inventory balance for one product and warehouse."""

    id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity_on_hand: int
    quantity_reserved: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def available_quantity(self) -> int:
        """Return stock that is not currently reserved."""

        return self.quantity_on_hand - self.quantity_reserved


class StockMovementResponse(BaseModel):
    """Immutable audit record for a stock quantity change."""

    id: UUID
    product_id: UUID
    warehouse_id: UUID
    movement_type: MovementType
    on_hand_delta: int
    reserved_delta: int
    on_hand_balance_after: int
    reserved_balance_after: int
    reference_id: str | None
    reason: str | None
    transfer_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockOperationResponse(BaseModel):
    """Response returned by a receipt or issue operation."""

    balance: InventoryBalanceResponse
    movement: StockMovementResponse


class StockTransferResponse(BaseModel):
    """Completed transfer with both balances and audit movements."""

    transfer_id: UUID
    source_balance: InventoryBalanceResponse
    destination_balance: InventoryBalanceResponse
    outbound_movement: StockMovementResponse
    inbound_movement: StockMovementResponse