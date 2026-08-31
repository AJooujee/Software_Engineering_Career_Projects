from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, Response

from app.core.config import get_settings
from app.services import ProxyClient


router = APIRouter()

PROXY_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
    "HEAD",
]


def get_proxy_client() -> ProxyClient:
    """Create a Gateway client using the current runtime settings."""

    return ProxyClient(get_settings())


ProxyClientDependency = Annotated[
    ProxyClient,
    Depends(get_proxy_client),
]


def build_downstream_path(root_path: str, remaining_path: str) -> str:
    """Join a public route root with its optional nested path."""

    if not remaining_path:
        return root_path

    return f"{root_path}/{remaining_path}"


@router.get(
    "/health/services",
    tags=["System"],
)
async def downstream_health_check(
    proxy_client: ProxyClientDependency,
) -> JSONResponse:
    """Report the combined health of all internal services."""

    service_results = await proxy_client.check_health()

    all_services_healthy = all(
        result["status"] == "healthy"
        for result in service_results.values()
    )

    overall_status = (
        "healthy"
        if all_services_healthy
        else "degraded"
    )

    response_status = (
        status.HTTP_200_OK
        if all_services_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=response_status,
        content={
            "status": overall_status,
            "services": service_results,
        },
    )


@router.api_route(
    "/products",
    methods=PROXY_METHODS,
    tags=["Inventory"],
    include_in_schema=False,
)
@router.api_route(
    "/products/{remaining_path:path}",
    methods=PROXY_METHODS,
    tags=["Inventory"],
    include_in_schema=False,
)
async def proxy_products(
    request: Request,
    proxy_client: ProxyClientDependency,
    remaining_path: str = "",
) -> Response:
    """Forward product requests to the Inventory Service."""

    return await proxy_client.forward(
        request=request,
        service_key="inventory",
        downstream_path=build_downstream_path(
            "/products",
            remaining_path,
        ),
    )


@router.api_route(
    "/stock",
    methods=PROXY_METHODS,
    tags=["Inventory"],
    include_in_schema=False,
)
@router.api_route(
    "/stock/{remaining_path:path}",
    methods=PROXY_METHODS,
    tags=["Inventory"],
    include_in_schema=False,
)
async def proxy_stock(
    request: Request,
    proxy_client: ProxyClientDependency,
    remaining_path: str = "",
) -> Response:
    """Forward stock requests to the Inventory Service."""

    return await proxy_client.forward(
        request=request,
        service_key="inventory",
        downstream_path=build_downstream_path(
            "/stock",
            remaining_path,
        ),
    )


@router.api_route(
    "/warehouses",
    methods=PROXY_METHODS,
    tags=["Warehouses"],
    include_in_schema=False,
)
@router.api_route(
    "/warehouses/{remaining_path:path}",
    methods=PROXY_METHODS,
    tags=["Warehouses"],
    include_in_schema=False,
)
async def proxy_warehouses(
    request: Request,
    proxy_client: ProxyClientDependency,
    remaining_path: str = "",
) -> Response:
    """Forward warehouse requests to the Warehouse Service."""

    return await proxy_client.forward(
        request=request,
        service_key="warehouse",
        downstream_path=build_downstream_path(
            "/warehouses",
            remaining_path,
        ),
    )


@router.api_route(
    "/orders",
    methods=PROXY_METHODS,
    tags=["Orders"],
    include_in_schema=False,
)
@router.api_route(
    "/orders/{remaining_path:path}",
    methods=PROXY_METHODS,
    tags=["Orders"],
    include_in_schema=False,
)
async def proxy_orders(
    request: Request,
    proxy_client: ProxyClientDependency,
    remaining_path: str = "",
) -> Response:
    """Forward order requests to the Order Service."""

    return await proxy_client.forward(
        request=request,
        service_key="order",
        downstream_path=build_downstream_path(
            "/orders",
            remaining_path,
        ),
    )