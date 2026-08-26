from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


MovementType = Literal[
    "RECEIPT",
    "ISSUE",
    "ADJUSTMENT",
    "RESERVATION",
    "RELEASE",
]


class StockChangeRequest(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: int = Field(gt=0)
    reference_id: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=500)


class StockReceiptRequest(StockChangeRequest):
    pass


class StockIssueRequest(StockChangeRequest):
    pass


class InventoryBalanceResponse(BaseModel):
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
        return self.quantity_on_hand - self.quantity_reserved


class StockMovementResponse(BaseModel):
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockOperationResponse(BaseModel):
    balance: InventoryBalanceResponse
    movement: StockMovementResponse