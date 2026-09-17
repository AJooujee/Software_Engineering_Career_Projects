"""Integration tests for request tracing and HTTP response hardening."""

from uuid import UUID

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from observability_platform.main import app
from observability_platform.middleware import SecurityHeadersMiddleware

# The default TestClient host is ``testserver``, which is explicitly allowed by
# the application configuration.
client = TestClient(app)


def test_response_contains_generated_request_id() -> None:
    """Requests without an identifier should receive a generated UUID."""

    # Act: send a request without X-Request-ID.
    response = client.get("/health")

    # Assert: middleware returns a valid version-four UUID.
    request_id = response.headers["X-Request-ID"]
    assert response.status_code == 200
    assert UUID(request_id).version == 4


def test_existing_request_id_is_preserved() -> None:
    """Caller-provided identifiers should survive the request pipeline."""

    # Arrange: use a deterministic upstream correlation identifier.
    request_id = "test-request-123"

    # Act: forward the identifier through the health endpoint.
    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    # Assert: downstream clients receive the same identifier.
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_response_contains_security_headers() -> None:
    """Every response should contain baseline browser protections."""

    # Act: request a public endpoint.
    response = client.get("/health")

    # Assert: each defensive policy is visible to clients and proxies.
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), geolocation=(), microphone=()"
    )
    assert response.headers["Cache-Control"] == "no-store"


def test_development_response_does_not_enable_hsts() -> None:
    """Local HTTP development should not advertise an HTTPS-only policy."""

    # Act: request the health endpoint under default development settings.
    response = client.get("/health")

    # Assert: HSTS is reserved for production application assembly.
    assert "Strict-Transport-Security" not in response.headers


def test_untrusted_host_is_rejected() -> None:
    """Requests with unknown Host headers must fail before route handling."""

    # Arrange: create a client whose base URL supplies an untrusted hostname.
    untrusted_client = TestClient(
        app,
        base_url="http://attacker.example",
    )

    # Act: attempt to reach an otherwise public endpoint.
    response = untrusted_client.get("/health")

    # Assert: TrustedHostMiddleware rejects the request consistently.
    assert response.status_code == 400
    assert response.text == "Invalid host header"

    # Outer middleware still adds traceability and defensive headers to errors.
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_security_middleware_preserves_stricter_route_header() -> None:
    """Middleware should not overwrite a header selected by a route."""

    # Arrange: assemble a minimal app whose route chooses its own frame policy.
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/custom")
    async def custom_header_response(response: Response) -> dict[str, str]:
        """Return a response with an explicitly selected security header."""

        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return {"status": "ok"}

    # Act: process the response through SecurityHeadersMiddleware.
    response = TestClient(test_app).get("/custom")

    # Assert: setdefault preserves the route's intentional value.
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
