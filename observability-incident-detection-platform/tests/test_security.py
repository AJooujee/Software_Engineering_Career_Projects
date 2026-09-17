"""Integration tests for API-key authentication boundaries."""

from collections.abc import Iterator

import pytest
from httpx2 import AsyncClient

from observability_platform.config import Settings, get_settings
from observability_platform.main import app
from observability_platform.security import API_KEY_HEADER_NAME

pytestmark = pytest.mark.asyncio

# Use a deterministic test credential that satisfies the minimum length rule.
TEST_API_KEY = "phase-8-test-api-key-with-32-chars"


@pytest.fixture
def authentication_enabled() -> Iterator[None]:
    """Enable API-key authentication for one isolated test."""

    # Arrange a protected non-production configuration. Dependency overrides
    # avoid changing the developer's real environment or .env file.
    protected_settings = Settings(
        _env_file=None,
        environment="testing",
        api_key_enabled=True,
        api_key=TEST_API_KEY,
    )
    app.dependency_overrides[get_settings] = lambda: protected_settings

    try:
        yield
    finally:
        # Always remove the override so authentication state cannot leak into
        # later tests that expect the normal development configuration.
        app.dependency_overrides.pop(get_settings, None)


async def test_health_endpoint_remains_public(
    api_client: AsyncClient,
    authentication_enabled: None,
) -> None:
    """Liveness checks must work without application credentials."""

    # Act: call the public health endpoint without an API key.
    response = await api_client.get("/health")

    # Assert: infrastructure can still observe application liveness.
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


async def test_protected_endpoint_rejects_missing_api_key(
    api_client: AsyncClient,
    authentication_enabled: None,
) -> None:
    """Business endpoints must reject requests without credentials."""

    # Act: omit the required API-key header.
    response = await api_client.get("/api/v1/services")

    # Assert: the response communicates authentication failure consistently.
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}
    assert response.headers["www-authenticate"] == "ApiKey"


async def test_protected_endpoint_rejects_incorrect_api_key(
    api_client: AsyncClient,
    authentication_enabled: None,
) -> None:
    """Business endpoints must reject incorrect credentials."""

    # Act: provide a credential that differs from the configured secret.
    response = await api_client.get(
        "/api/v1/services",
        headers={API_KEY_HEADER_NAME: "incorrect-api-key"},
    )

    # Assert: the response does not reveal whether the key was close or wrong.
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


async def test_protected_endpoint_accepts_valid_api_key(
    api_client: AsyncClient,
    authentication_enabled: None,
) -> None:
    """A valid credential should allow normal route processing."""

    # Act: provide the configured credential to a protected endpoint.
    response = await api_client.get(
        "/api/v1/services",
        headers={API_KEY_HEADER_NAME: TEST_API_KEY},
    )

    # Assert: authentication succeeds and the empty test database is queried.
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


async def test_authentication_disabled_preserves_local_workflow(
    api_client: AsyncClient,
) -> None:
    """Local development should remain usable when protection is disabled."""

    # Act: use the default settings without an API-key header.
    response = await api_client.get("/api/v1/services")

    # Assert: the existing development behavior remains backward compatible.
    assert response.status_code == 200


async def test_openapi_documents_api_key_security() -> None:
    """OpenAPI must explain how clients authenticate to protected routes."""

    # Arrange: generate the schema from the assembled application.
    schema = app.openapi()

    # Assert: FastAPI exposes the API key as a header-based security scheme.
    security_schemes = schema["components"]["securitySchemes"]
    assert security_schemes["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": API_KEY_HEADER_NAME,
    }

    # Protected operations advertise the scheme to generated API clients.
    protected_operation = schema["paths"]["/api/v1/services"]["get"]
    assert {"APIKeyHeader": []} in protected_operation["security"]

    # Public health operations do not require the API key.
    health_operation = schema["paths"]["/health"]["get"]
    assert "security" not in health_operation
