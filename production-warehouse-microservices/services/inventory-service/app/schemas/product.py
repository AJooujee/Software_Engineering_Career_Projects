from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    reorder_level: int = Field(default=0, ge=0)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        normalized_value = value.strip().upper()

        if not normalized_value:
            raise ValueError("SKU cannot be empty")

        return normalized_value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Product name cannot be empty")

        return normalized_value


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    unit_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)