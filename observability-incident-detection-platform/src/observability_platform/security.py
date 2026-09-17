"""Authentication dependencies shared by protected API routes.

The platform uses an API key for service-to-service access. FastAPI's
``APIKeyHeader`` integrates the credential with OpenAPI while ``compare_digest``
avoids ordinary string comparison for security-sensitive values.
"""

from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from observability_platform.config import Settings, get_settings

# Keep the header name in one place so runtime validation and OpenAPI
# documentation always describe the same authentication contract.
API_KEY_HEADER_NAME = "X-API-Key"

# auto_error=False lets this module return the same controlled response for
# missing and incorrect credentials without revealing which condition occurred.
api_key_header = APIKeyHeader(
    name=API_KEY_HEADER_NAME,
    auto_error=False,
)

# Settings remain dependency-injected so tests can safely provide isolated
# configurations without modifying process-wide environment variables.
SettingsDependency = Annotated[Settings, Depends(get_settings)]
PresentedAPIKey = Annotated[str | None, Depends(api_key_header)]


async def require_api_key(
    settings: SettingsDependency,
    presented_api_key: PresentedAPIKey,
) -> None:
    """Authorize a request when API-key protection is enabled."""

    # Development and testing may disable authentication for convenient local
    # workflows. Production configuration requires this setting to be enabled.
    if not settings.api_key_enabled:
        return

    # Production validation already prevents this state. The runtime guard also
    # protects development deployments that enable authentication incorrectly.
    if settings.api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    configured_api_key = settings.api_key.get_secret_value()

    # Constant-time comparison reduces timing differences that could otherwise
    # disclose information about the configured credential.
    if presented_api_key is None or not compare_digest(
        presented_api_key,
        configured_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
