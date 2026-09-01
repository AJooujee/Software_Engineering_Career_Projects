from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


BASE_URL = os.getenv(
    "GATEWAY_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def require(condition: bool, message: str) -> None:
    """Raise a readable test failure when a requirement is not met."""

    if not condition:
        raise AssertionError(message)


def api_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    expected_statuses: tuple[int, ...] = (200,),
    request_id: str | None = None,
) -> tuple[int, Any, Any]:
    """Send one JSON request through the API Gateway."""

    request_data = None
    headers = {
        "Accept": "application/json",
    }

    if request_id is not None:
        headers["X-Request-ID"] = request_id

    if payload is not None:
        request_data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url=f"{BASE_URL}{path}",
        data=request_data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=15) as response:
            status_code = response.status
            response_text = response.read().decode("utf-8")
            response_headers = response.headers
    except HTTPError as error:
        error_body = error.read().decode("utf-8")

        raise AssertionError(
            f"{method} {path} returned {error.code}: {error_body}"
        ) from error

    require(
        status_code in expected_statuses,
        (
            f"{method} {path} returned {status_code}; "
            f"expected {expected_statuses}"
        ),
    )

    response_body = (
        json.loads(response_text)
        if response_text
        else None
    )

    return status_code, response_body, response_headers


def wait_for_gateway() -> None:
    """Wait until Docker exposes a healthy Gateway endpoint."""

    last_error: Exception | None = None

    for _ in range(60):
        try:
            api_request("GET", "/health")
            return
        except Exception as error:
            last_error = error
            time.sleep(2)

    raise RuntimeError(
        f"API Gateway did not become ready: {last_error}"
    )


def run_smoke_test() -> None:
    """Exercise an order reservation lifecycle through port 8000."""

    wait_for_gateway()

    unique_suffix = uuid4().hex[:12].upper()
    request_id = f"e2e-{unique_suffix.lower()}"

    _, health, health_headers = api_request(
        "GET",
        "/health/services",
        request_id=request_id,
    )

    require(
        health["status"] == "healthy",
        f"Downstream services are not healthy: {health}",
    )
    require(
        health_headers.get("X-Request-ID") == request_id,
        "Gateway did not preserve the request ID",
    )

    _, warehouse, _ = api_request(
        "POST",
        "/warehouses",
        payload={
            "code": f"CI-{unique_suffix}",
            "name": "CI Integration Warehouse",
            "address_line_1": "100 Integration Way",
            "city": "Lowell",
            "state": "MA",
            "postal_code": "01852",
            "country_code": "US",
        },
        expected_statuses=(200, 201),
        request_id=request_id,
    )

    _, product, _ = api_request(
        "POST",
        "/products",
        payload={
            "sku": f"CI-{unique_suffix}",
            "name": "CI Barcode Scanner",
            "description": "Temporary product for automated E2E testing.",
            "unit_price": 25.50,
            "reorder_level": 5,
        },
        expected_statuses=(200, 201),
        request_id=request_id,
    )

    warehouse_id = warehouse["id"]
    product_id = product["id"]

    api_request(
        "POST",
        "/stock/receipts",
        payload={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": 20,
            "reference_id": f"CI-RECEIPT-{unique_suffix}",
            "reason": "Seed stock for the automated E2E test",
        },
        expected_statuses=(200, 201),
        request_id=request_id,
    )

    _, created_order, _ = api_request(
        "POST",
        "/orders",
        payload={
            "customer_name": "CI Gateway Test",
            "customer_email": (
                f"ci-{unique_suffix.lower()}@example.com"
            ),
            "warehouse_id": warehouse_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 3,
                }
            ],
        },
        expected_statuses=(200, 201),
        request_id=request_id,
    )

    require(
        created_order["status"] == "RESERVED",
        f"Expected RESERVED order: {created_order}",
    )

    _, reserved_balance, _ = api_request(
        "GET",
        f"/stock/balances/{warehouse_id}/{product_id}",
        request_id=request_id,
    )

    require(
        reserved_balance["quantity_on_hand"] == 20,
        "Unexpected on-hand balance after reservation",
    )
    require(
        reserved_balance["quantity_reserved"] == 3,
        "Order did not reserve three units",
    )
    require(
        reserved_balance["available_quantity"] == 17,
        "Unexpected available balance after reservation",
    )

    order_id = created_order["id"]

    _, cancelled_order, _ = api_request(
        "POST",
        f"/orders/{order_id}/cancel",
        request_id=request_id,
    )

    require(
        cancelled_order["status"] == "CANCELLED",
        f"Expected CANCELLED order: {cancelled_order}",
    )

    _, final_balance, _ = api_request(
        "GET",
        f"/stock/balances/{warehouse_id}/{product_id}",
        request_id=request_id,
    )

    require(
        final_balance["quantity_reserved"] == 0,
        "Cancellation did not release reserved stock",
    )
    require(
        final_balance["available_quantity"] == 20,
        "Available stock was not restored after cancellation",
    )

    print(
        json.dumps(
            {
                "request_id": request_id,
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "order_id": order_id,
                "order_status": cancelled_order["status"],
                "quantity_on_hand": final_balance[
                    "quantity_on_hand"
                ],
                "quantity_reserved": final_balance[
                    "quantity_reserved"
                ],
                "available_quantity": final_balance[
                    "available_quantity"
                ],
            },
            indent=2,
        )
    )
    print("PRODUCTION WAREHOUSE E2E SMOKE TEST PASSED")


if __name__ == "__main__":
    run_smoke_test()