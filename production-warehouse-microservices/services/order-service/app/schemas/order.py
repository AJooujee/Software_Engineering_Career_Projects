from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.models import OrderStatus


class OrderItemCreate(BaseModel):
    """Product and quantity requested by the customer."""

    product_id: UUID
    quantity: int = Field(
        gt=0,
        le=1_000_000,
        description="Number of product units requested.",
    )


class OrderCreate(BaseModel):
    """Payload used to create and reserve inventory for an order."""

    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str = Field(
        min_length=1,
        max_length=150,
    )
    customer_email: EmailStr
    warehouse_id: UUID
    items: list[OrderItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def reject_duplicate_products(self) -> OrderCreate:
        """Require each product to appear only once in an order."""

        product_ids = [item.product_id for item in self.items]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Each product may appear only once per order"
            )

        return self


class OrderItemResponse(BaseModel):
    """Stored order line returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderResponse(BaseModel):
    """Complete order representation including all line items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    customer_name: str
    customer_email: EmailStr
    warehouse_id: UUID
    status: OrderStatus
    total_amount: Decimal
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime