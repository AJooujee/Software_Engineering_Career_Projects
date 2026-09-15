from uuid import uuid4

import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_service(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "payment-service",
            "environment": "development",
            "description": "Processes customer payments",
        },
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["name"] == "payment-service"
    assert payload["environment"] == "development"
    assert payload["description"] == "Processes customer payments"
    assert payload["id"]
    assert payload["created_at"]
    assert payload["updated_at"]


async def test_register_service_rejects_duplicate_identity(
    api_client: AsyncClient,
) -> None:
    service = {
        "name": "payment-service",
        "environment": "production",
    }

    first_response = await api_client.post(
        "/api/v1/services",
        json=service,
    )
    duplicate_response = await api_client.post(
        "/api/v1/services",
        json=service,
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == (
        "A service with this name and environment already exists"
    )


async def test_list_services_supports_pagination(
    api_client: AsyncClient,
) -> None:
    await api_client.post(
        "/api/v1/services",
        json={"name": "orders-service"},
    )
    await api_client.post(
        "/api/v1/services",
        json={"name": "payment-service"},
    )

    response = await api_client.get(
        "/api/v1/services",
        params={"offset": 1, "limit": 1},
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "payment-service"


async def test_get_service_by_id(api_client: AsyncClient) -> None:
    create_response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "inventory-service",
            "environment": "staging",
        },
    )
    service_id = create_response.json()["id"]

    response = await api_client.get(
        f"/api/v1/services/{service_id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == service_id
    assert response.json()["name"] == "inventory-service"
    assert response.json()["environment"] == "staging"


async def test_get_unknown_service_returns_not_found(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get(
        f"/api/v1/services/{uuid4()}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Monitored service was not found"


async def test_register_service_rejects_invalid_environment(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "payment-service",
            "environment": "unknown",
        },
    )

    assert response.status_code == 422
