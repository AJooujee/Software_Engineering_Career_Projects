from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WarehouseBase(BaseModel):
    """Fields shared by warehouse create and response schemas."""

    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    address_line_1: str = Field(min_length=2, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=2, max_length=20)
    country_code: str = Field(default="US", min_length=2, max_length=2)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("code", "country_code")
    @classmethod
    def normalize_uppercase_fields(cls, value: str) -> str:
        """Store business codes consistently for reliable comparisons."""
        return value.upper()


class WarehouseCreate(WarehouseBase):
    """Payload used to create a warehouse."""


class WarehouseUpdate(BaseModel):
    """Optional fields supported by a partial warehouse update."""

    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address_line_1: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )
    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
    )
    is_active: bool | None = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("code", "country_code")
    @classmethod
    def normalize_optional_uppercase_fields(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize optional codes only when the client supplies them."""
        if value is None:
            return None

        return value.upper()


class WarehouseResponse(WarehouseBase):
    """Warehouse representation returned by the API."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )