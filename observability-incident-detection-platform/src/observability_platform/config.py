"""Centralized and environment-aware application configuration.

Settings are loaded from environment variables prefixed with
``OBSERVABILITY_``. Development keeps convenient defaults, while production
configuration is validated against unsafe credentials and security settings.
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Restrict environments and log levels to explicitly supported values.
Environment = Literal["development", "testing", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Values commonly copied from examples must never be accepted as production
# credentials. Keeping this list centralized makes the safety rule auditable.
UNSAFE_API_KEYS = {
    "change-me",
    "development-only",
    "replace-with-a-secure-api-key",
}


class Settings(BaseSettings):
    """Validated runtime configuration for the observability platform."""

    # Application metadata is exposed through health and OpenAPI responses.
    app_name: str = "Observability & Incident Detection Platform"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    log_level: LogLevel = "INFO"

    # Local development uses the PostgreSQL container exposed on port 5433.
    # Production validation rejects this development credential combination.
    database_url: str = (
        "postgresql+asyncpg://observability:observability_dev"
        "@localhost:5433/observability"
    )

    # Authentication is optional during local development so existing examples
    # remain easy to run. Production must explicitly enable it and supply a
    # strong secret through OBSERVABILITY_API_KEY.
    api_key_enabled: bool = False
    api_key: SecretStr | None = Field(
        default=None,
        min_length=32,
    )

    # Trusted hosts protect the application from invalid Host headers. Both
    # test hostnames support the synchronous and asynchronous test clients.
    # A wildcard is convenient but intentionally forbidden in production.
    trusted_hosts: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "test",
            "testserver",
        ]
    )

    # Local development and the integration suite remain unrestricted by
    # default. Production validation below requires explicit enforcement.
    rate_limit_enabled: bool = False
    rate_limit_requests: int = Field(default=100, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)

    # Pydantic Settings reads .env locally and environment variables in every
    # environment. Unknown variables are ignored to keep shared files usable.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVABILITY_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        """Reject unsafe settings before a production process can start."""

        # Development and tests retain convenient defaults. Production receives
        # stricter checks because it is exposed to real clients and data.
        if self.environment != "production":
            return self

        # Production endpoints must never start without authentication.
        if not self.api_key_enabled:
            raise ValueError("API-key authentication must be enabled in production")

        # SecretStr prevents accidental display, while get_secret_value is used
        # only inside validation to inspect the actual configured credential.
        if self.api_key is None:
            raise ValueError("A production API key is required")

        normalized_api_key = self.api_key.get_secret_value().strip()
        if normalized_api_key.lower() in UNSAFE_API_KEYS:
            raise ValueError("The production API key cannot use a placeholder value")

        # Wildcard hosts would defeat Host-header validation.
        if "*" in self.trusted_hosts:
            raise ValueError("Wildcard trusted hosts are not allowed in production")

        # The password shipped for local Docker development must not reach a
        # production database configuration.
        if "observability:observability_dev@" in self.database_url.lower():
            raise ValueError(
                "The development database credentials are not allowed in production"
            )

        # Rate limiting is a required protection for production API traffic.
        if not self.rate_limit_enabled:
            raise ValueError("Rate limiting must be enabled in production")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance for the process lifetime."""

    # Caching avoids reparsing environment variables on every dependency call.
    return Settings()
