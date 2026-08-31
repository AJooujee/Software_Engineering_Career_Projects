from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import TracebackType
from typing import Self
from uuid import UUID

import httpx

from app.core.config import get_settings


class DownstreamServiceError(RuntimeError):
    """Base error for failed communication with another service."""


class ProductUnavailableError(DownstreamServiceError):
    """Raised when a requested product cannot be used in an order."""


class WarehouseUnavailableError(DownstreamServiceError):
    """Raised when a warehouse is missing or inactive."""


class StockReservationError(DownstreamServiceError):
    """Raised when Inventory Service rejects a reservation."""


class StockReleaseError(DownstreamServiceError):
    """Raised when Inventory Service rejects reservation release."""


@dataclass(frozen=True)
class ProductSnapshot:
    """Product data needed to calculate one order line."""

    product_id: UUID
    unit_price: Decimal


def _response_detail(response: httpx.Response) -> str:
    """Extract a readable error message from a downstream response."""

    try:
        payload = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"

    if isinstance(payload, dict) and "detail" in payload:
        return str(payload["detail"])

    return str(payload)


class ServiceClient:
    """Synchronous client for Order Service dependencies."""

    def __init__(
        self,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()

        self._settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=settings.service_request_timeout_seconds,
        )

    def __enter__(self) -> Self:
        """Support safe use through a context manager."""

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close only clients created internally by this class."""

        if self._owns_client:
            self._client.close()

    def _request(
        self,
        method: str,
        url: str,
        service_name: str,
        **kwargs: object,
    ) -> httpx.Response:
        """Convert network failures into one application-level error."""

        try:
            return self._client.request(
                method,
                url,
                **kwargs,
            )
        except httpx.RequestError as error:
            raise DownstreamServiceError(
                f"{service_name} is unavailable"
            ) from error

    def get_product(self, product_id: UUID) -> ProductSnapshot:
        """Fetch the authoritative product price from Inventory Service."""

        response = self._request(
            "GET",
            (
                f"{self._settings.inventory_service_url}"
                f"/products/{product_id}"
            ),
            "Inventory Service",
        )

        if response.status_code == 404:
            raise ProductUnavailableError(
                f"Product '{product_id}' was not found"
            )

        if not response.is_success:
            raise DownstreamServiceError(
                "Inventory Service product lookup failed: "
                f"{_response_detail(response)}"
            )

        payload = response.json()

        if not payload.get("is_active", True):
            raise ProductUnavailableError(
                f"Product '{product_id}' is inactive"
            )

        try:
            unit_price = Decimal(str(payload["unit_price"]))
        except (KeyError, InvalidOperation, TypeError) as error:
            raise DownstreamServiceError(
                "Inventory Service returned an invalid product price"
            ) from error

        return ProductSnapshot(
            product_id=product_id,
            unit_price=unit_price,
        )

    def verify_warehouse(self, warehouse_id: UUID) -> None:
        """Require the fulfillment warehouse to exist and be active."""

        response = self._request(
            "GET",
            (
                f"{self._settings.warehouse_service_url}"
                f"/warehouses/{warehouse_id}"
            ),
            "Warehouse Service",
        )

        if response.status_code == 404:
            raise WarehouseUnavailableError(
                f"Warehouse '{warehouse_id}' was not found"
            )

        if not response.is_success:
            raise DownstreamServiceError(
                "Warehouse Service lookup failed: "
                f"{_response_detail(response)}"
            )

        payload = response.json()

        if not payload.get("is_active", False):
            raise WarehouseUnavailableError(
                f"Warehouse '{warehouse_id}' is inactive"
            )

    def reserve_stock(
        self,
        *,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: int,
        reference_id: str,
    ) -> None:
        """Reserve one order line in Inventory Service."""

        response = self._request(
            "POST",
            (
                f"{self._settings.inventory_service_url}"
                "/stock/reservations"
            ),
            "Inventory Service",
            json={
                "product_id": str(product_id),
                "warehouse_id": str(warehouse_id),
                "quantity": quantity,
                "reference_id": reference_id,
                "reason": "Order inventory reservation",
            },
        )

        if not response.is_success:
            raise StockReservationError(
                "Stock reservation failed: "
                f"{_response_detail(response)}"
            )

    def release_stock(
        self,
        *,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: int,
        reference_id: str,
    ) -> None:
        """Release one order-owned inventory reservation."""

        response = self._request(
            "POST",
            (
                f"{self._settings.inventory_service_url}"
                "/stock/releases"
            ),
            "Inventory Service",
            json={
                "product_id": str(product_id),
                "warehouse_id": str(warehouse_id),
                "quantity": quantity,
                "reference_id": reference_id,
                "reason": "Order inventory reservation release",
            },
        )

        if not response.is_success:
            raise StockReleaseError(
                "Stock release failed: "
                f"{_response_detail(response)}"
            )