import asyncio
from typing import Any

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import Response

from app.core.config import Settings


# These headers describe one HTTP connection and must not be forwarded
# between the client, Gateway, and downstream services.
HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class DownstreamService:
    """Describe one internal service that can receive Gateway requests."""

    def __init__(self, name: str, base_url: str) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")


class ProxyClient:
    """Forward HTTP requests and inspect downstream service health."""

    def __init__(self, settings: Settings) -> None:
        self.timeout_seconds = settings.service_request_timeout_seconds

        self.services = {
            "inventory": DownstreamService(
                name="inventory-service",
                base_url=settings.inventory_service_url,
            ),
            "warehouse": DownstreamService(
                name="warehouse-service",
                base_url=settings.warehouse_service_url,
            ),
            "order": DownstreamService(
                name="order-service",
                base_url=settings.order_service_url,
            ),
        }

    async def forward(
        self,
        request: Request,
        service_key: str,
        downstream_path: str,
    ) -> Response:
        """Forward one incoming HTTP request to its owning service."""

        service = self.services[service_key]
        target_url = f"{service.base_url}/{downstream_path.lstrip('/')}"

        forwarded_headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() not in HOP_BY_HOP_HEADERS
        }

        request_body = await request.body()

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
            ) as client:
                downstream_response = await client.request(
                    method=request.method,
                    url=target_url,
                    params=list(request.query_params.multi_items()),
                    headers=forwarded_headers,
                    content=request_body or None,
                )

        except httpx.TimeoutException as error:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "message": "The downstream service timed out",
                    "service": service.name,
                },
            ) from error

        except httpx.RequestError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": "The downstream service is unavailable",
                    "service": service.name,
                },
            ) from error

        # Only forward response headers that remain meaningful to the client.
        response_headers = {
            name: downstream_response.headers[name]
            for name in ("content-type", "location", "x-request-id")
            if name in downstream_response.headers
        }

        return Response(
            content=downstream_response.content,
            status_code=downstream_response.status_code,
            headers=response_headers,
        )

    async def check_health(self) -> dict[str, dict[str, Any]]:
        """Check all downstream health endpoints concurrently."""

        services = list(self.services.values())

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=False,
        ) as client:
            results = await asyncio.gather(
                *(
                    self._check_one_service(client, service)
                    for service in services
                )
            )

        return {
            service.name: result
            for service, result in zip(services, results, strict=True)
        }

    async def _check_one_service(
        self,
        client: httpx.AsyncClient,
        service: DownstreamService,
    ) -> dict[str, Any]:
        """Return a normalized health result for one service."""

        try:
            response = await client.get(f"{service.base_url}/health")

        except httpx.TimeoutException:
            return {
                "status": "unhealthy",
                "error": "timeout",
            }

        except httpx.RequestError:
            return {
                "status": "unhealthy",
                "error": "unavailable",
            }

        if response.status_code == status.HTTP_200_OK:
            return {
                "status": "healthy",
                "status_code": response.status_code,
            }

        return {
            "status": "unhealthy",
            "status_code": response.status_code,
        }