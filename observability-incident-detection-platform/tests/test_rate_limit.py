"""Tests for deterministic per-client request rate limiting."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from observability_platform.rate_limit import RateLimitMiddleware


class ControllableClock:
    """Provide deterministic time without sleeping during tests."""

    def __init__(self) -> None:
        """Start the synthetic monotonic clock at zero seconds."""

        self.current_time = 0.0

    def __call__(self) -> float:
        """Return the current synthetic timestamp."""

        return self.current_time

    def advance(self, seconds: float) -> None:
        """Move the synthetic clock forward by a controlled amount."""

        self.current_time += seconds


def build_test_client(
    *,
    enabled: bool = True,
    request_limit: int = 2,
    window_seconds: int = 60,
    clock: ControllableClock | None = None,
) -> TestClient:
    """Build an isolated application with fresh rate-limit state."""

    # Each test receives a new app and middleware instance so request history
    # cannot leak between tests.
    test_app = FastAPI()
    selected_clock = clock or ControllableClock()

    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=enabled,
        request_limit=request_limit,
        window_seconds=window_seconds,
        clock=selected_clock,
    )

    @test_app.get("/api/data")
    async def protected_data() -> dict[str, str]:
        """Represent a business endpoint subject to request limiting."""

        return {"status": "ok"}

    @test_app.get("/health")
    async def health() -> dict[str, str]:
        """Represent an infrastructure endpoint exempt from limiting."""

        return {"status": "healthy"}

    return TestClient(test_app)


def test_requests_within_limit_include_policy_headers() -> None:
    """Accepted requests should report limit, remaining, and reset values."""

    # Arrange: allow two requests during a sixty-second window.
    client = build_test_client()

    # Act: consume the first allowance.
    response = client.get("/api/data")

    # Assert: the response describes the remaining client allowance.
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"
    assert response.headers["X-RateLimit-Reset"] == "60"


def test_request_exceeding_limit_returns_too_many_requests() -> None:
    """A client exceeding its allowance should receive HTTP 429."""

    # Arrange: consume both requests in the active window.
    client = build_test_client()
    assert client.get("/api/data").status_code == 200
    assert client.get("/api/data").status_code == 200

    # Act: attempt one additional request without advancing time.
    response = client.get("/api/data")

    # Assert: the API provides a machine-readable retry contract.
    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded"}
    assert response.headers["Retry-After"] == "60"
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Reset"] == "60"


def test_allowance_recovers_after_window_expires() -> None:
    """Expired request timestamps should release client capacity."""

    # Arrange: reach the limit under a controllable clock.
    clock = ControllableClock()
    client = build_test_client(clock=clock)
    assert client.get("/api/data").status_code == 200
    assert client.get("/api/data").status_code == 200
    assert client.get("/api/data").status_code == 429

    # Act: move beyond the complete rate-limit window.
    clock.advance(61)
    response = client.get("/api/data")

    # Assert: the old timestamps were removed and the request is accepted.
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == "1"


def test_health_endpoint_is_exempt_from_rate_limit() -> None:
    """Infrastructure health checks must remain continuously available."""

    # Arrange: exhaust the business-endpoint allowance.
    client = build_test_client(request_limit=1)
    assert client.get("/api/data").status_code == 200
    assert client.get("/api/data").status_code == 429

    # Act: call health repeatedly from the same client.
    responses = [client.get("/health") for _ in range(3)]

    # Assert: orchestration checks are never throttled.
    assert all(response.status_code == 200 for response in responses)
    assert all("X-RateLimit-Limit" not in response.headers for response in responses)


def test_disabled_rate_limit_preserves_unrestricted_local_behavior() -> None:
    """Disabling the feature should bypass request tracking entirely."""

    # Arrange: configure a nominal one-request limit but disable enforcement.
    client = build_test_client(
        enabled=False,
        request_limit=1,
    )

    # Act: send more requests than the configured allowance.
    responses = [client.get("/api/data") for _ in range(3)]

    # Assert: all requests pass and no policy headers are emitted.
    assert all(response.status_code == 200 for response in responses)
    assert all("X-RateLimit-Limit" not in response.headers for response in responses)
