import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.routes.gateway import get_proxy_client
from app.main import app


client = TestClient(app)


class FakeProxyClient:
    """Record routed requests without calling real downstream services."""

    def __init__(self) -> None:
        self.health_results: dict[str, dict[str, Any]] = {
            "inventory-service": {
                "status": "healthy",
                "status_code": 200,
            },
            "warehouse-service": {
                "status": "healthy",
                "status_code": 200,
            },
            "order-service": {
                "status": "healthy",
                "status_code": 200,
            },
        }

    async def forward(
        self,
        request: Request,
        service_key: str,
        downstream_path: str,
    ) -> JSONResponse:
        """Return the routing decision so tests can inspect it."""

        raw_body = await request.body()
        parsed_body = (
            json.loads(raw_body)
            if raw_body
            else None
        )

        response_status = (
            201
            if request.method == "POST"
            else 200
        )

        return JSONResponse(
            status_code=response_status,
            content={
                "service_key": service_key,
                "downstream_path": downstream_path,
                "method": request.method,
                "query": request.url.query,
                "body": parsed_body,
            },
        )

    async def check_health(self) -> dict[str, dict[str, Any]]:
        """Return configurable downstream health results."""

        return self.health_results


@pytest.fixture
def fake_proxy_client() -> Iterator[FakeProxyClient]:
    """Override the real Gateway client for one isolated test."""

    fake_client = FakeProxyClient()

    app.dependency_overrides[get_proxy_client] = (
        lambda: fake_client
    )

    yield fake_client

    app.dependency_overrides.clear()


def test_products_route_targets_inventory(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Verify product paths and query parameters are preserved."""

    response = client.get(
        "/products/abc-123",
        params={
            "include_inactive": "true",
            "limit": 25,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "service_key": "inventory",
        "downstream_path": "/products/abc-123",
        "method": "GET",
        "query": "include_inactive=true&limit=25",
        "body": None,
    }


def test_stock_nested_route_targets_inventory(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Verify nested stock paths are preserved."""

    response = client.get(
        "/stock/balances/warehouse-1/product-1",
    )

    assert response.status_code == 200
    assert response.json()["service_key"] == "inventory"
    assert response.json()["downstream_path"] == (
        "/stock/balances/warehouse-1/product-1"
    )


def test_order_post_preserves_json_and_status(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Verify POST bodies and downstream status codes are preserved."""

    payload = {
        "customer_name": "Gateway Test",
        "items": [
            {
                "product_id": "product-1",
                "quantity": 2,
            }
        ],
    }

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 201
    assert response.json() == {
        "service_key": "order",
        "downstream_path": "/orders",
        "method": "POST",
        "query": "",
        "body": payload,
    }


def test_warehouse_route_targets_warehouse_service(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Verify warehouse routes use the Warehouse Service."""

    response = client.patch(
        "/warehouses/warehouse-1",
        json={"name": "Updated Warehouse"},
    )

    assert response.status_code == 200
    assert response.json()["service_key"] == "warehouse"
    assert response.json()["downstream_path"] == (
        "/warehouses/warehouse-1"
    )


def test_downstream_health_is_healthy(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Return 200 when all downstream services are healthy."""

    response = client.get("/health/services")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert len(response.json()["services"]) == 3


def test_downstream_health_is_degraded(
    fake_proxy_client: FakeProxyClient,
) -> None:
    """Return 503 when any downstream service is unavailable."""

    fake_proxy_client.health_results["inventory-service"] = {
        "status": "unhealthy",
        "error": "unavailable",
    }

    response = client.get("/health/services")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert (
        response.json()["services"]["inventory-service"]["status"]
        == "unhealthy"
    )