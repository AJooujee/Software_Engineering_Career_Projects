"""Per-client fixed-window rate limiting for protected API traffic.

This implementation stores request timestamps in application memory. It is
appropriate for one application process and local portfolio deployment. A
multi-instance production deployment should replace the in-memory store with a
shared backend such as Redis while preserving the same HTTP contract.
"""

from asyncio import Lock
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from math import ceil
from time import monotonic

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Documentation paths are exact matches. Every route under /health is exempt so
# new infrastructure checks cannot accidentally become throttled later.
RATE_LIMIT_EXEMPT_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests from each client inside a fixed time window."""

    def __init__(
        self,
        app: object,
        *,
        enabled: bool,
        request_limit: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        """Initialize rate-limit policy and isolated in-memory state."""

        super().__init__(app)

        # Settings validation already enforces positive values. Defensive checks
        # also protect direct middleware use in small test applications.
        if request_limit <= 0:
            raise ValueError("request_limit must be greater than zero")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        self._enabled = enabled
        self._request_limit = request_limit
        self._window_seconds = window_seconds
        self._clock = clock

        # Each client receives its own chronological queue of request times.
        self._request_times: dict[str, deque[float]] = defaultdict(deque)

        # Concurrent asynchronous requests must update queues atomically.
        self._lock = Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Allow, describe, or reject one request under the configured policy."""

        # Health checks remain available to orchestrators even after a client
        # exhausts its business-API request allowance.
        if (
            not self._enabled
            or request.url.path.startswith("/health")
            or request.url.path in RATE_LIMIT_EXEMPT_PATHS
        ):
            return await call_next(request)

        client_key = self._client_key(request)
        now = self._clock()

        # Only queue inspection and mutation require the lock. Route processing
        # happens after releasing it so slow handlers do not block other clients.
        async with self._lock:
            request_times = self._request_times[client_key]
            window_started_at = now - self._window_seconds

            # Remove timestamps that no longer belong to the active window.
            while request_times and request_times[0] <= window_started_at:
                request_times.popleft()

            # A full queue means the client must wait until its oldest request
            # leaves the current window.
            if len(request_times) >= self._request_limit:
                retry_after = max(
                    1,
                    ceil(request_times[0] + self._window_seconds - now),
                )

                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self._request_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(retry_after),
                    },
                )

            # Record the accepted request and calculate the remaining allowance.
            request_times.append(now)
            remaining = self._request_limit - len(request_times)
            reset_after = max(
                1,
                ceil(request_times[0] + self._window_seconds - now),
            )

        response = await call_next(request)

        # Expose standard policy information without overwriting a stricter
        # value that a downstream gateway may have already provided.
        response.headers.setdefault(
            "X-RateLimit-Limit",
            str(self._request_limit),
        )
        response.headers.setdefault(
            "X-RateLimit-Remaining",
            str(remaining),
        )
        response.headers.setdefault(
            "X-RateLimit-Reset",
            str(reset_after),
        )

        return response

    @staticmethod
    def _client_key(request: Request) -> str:
        """Return a stable client identity without trusting forwarded headers."""

        # X-Forwarded-For is intentionally ignored because an untrusted caller
        # can spoof it unless a known reverse proxy sanitizes that header.
        if request.client is None:
            return "unknown"

        return request.client.host
