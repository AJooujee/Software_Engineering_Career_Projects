"""HTTP middleware for request tracing, logging, and response hardening."""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Use a dedicated logger so request lifecycle events can be filtered and routed
# independently from application-domain logs.
logger = logging.getLogger("observability.requests")

# These headers reduce browser-side attack surface for API responses. They are
# applied with setdefault so a route may intentionally provide a stricter value.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
}

# HSTS tells browsers to use HTTPS for future requests. It is enabled only in
# production because local development serves ordinary HTTP.
HSTS_HEADER_VALUE = "max-age=31536000; includeSubDomains"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a correlation identifier and log each request lifecycle."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process one request and record its identifier and duration."""

        # Preserve a caller-provided identifier so requests can be traced across
        # service boundaries. Generate a UUID when the caller does not send one.
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        started_at = perf_counter()

        try:
            # Forward the request to the remaining middleware and route handler.
            response = await call_next(request)
        except Exception:
            # Failed requests still need latency and correlation information.
            duration_ms = round((perf_counter() - started_at) * 1000, 2)

            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        # Return the identifier to the caller and record the completed request.
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply defensive response headers to every HTTP response."""

    def __init__(
        self,
        app: object,
        *,
        enable_hsts: bool = False,
    ) -> None:
        """Configure whether production-only HSTS should be emitted."""

        super().__init__(app)
        self._enable_hsts = enable_hsts

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Add security and cache-control headers after route processing."""

        # Let the application produce its response before adding headers. This
        # also lets setdefault preserve any stricter value selected by a route.
        response = await call_next(request)

        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers.setdefault(header_name, header_value)

        # Operational and business API responses may contain live system state.
        # Prevent shared clients and intermediaries from caching those results.
        if request.url.path == "/health" or request.url.path.startswith(
            ("/health/", "/api/")
        ):
            response.headers.setdefault("Cache-Control", "no-store")

        # HSTS is meaningful only for production deployments served over HTTPS.
        if self._enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security",
                HSTS_HEADER_VALUE,
            )

        return response
