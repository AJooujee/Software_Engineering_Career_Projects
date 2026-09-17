"""Tests for environment-aware and production-safe configuration."""

import pytest
from pydantic import ValidationError

from observability_platform.config import Settings


def production_settings(**overrides: object) -> Settings:
    """Build a valid production baseline with optional test overrides."""

    # Arrange a secure baseline so individual tests can change only the setting
    # associated with the production rule being exercised.
    values: dict[str, object] = {
        "environment": "production",
        "database_url": (
            "postgresql+asyncpg://observability:secure-password"
            "@postgres:5432/observability"
        ),
        "api_key_enabled": True,
        "api_key": "a" * 32,
        "trusted_hosts": ["api.example.com"],
        "rate_limit_enabled": True,
    }
    values.update(overrides)

    # Disable .env loading so local developer values cannot influence tests.
    return Settings(_env_file=None, **values)


def test_development_defaults_allow_local_startup() -> None:
    """Development should remain usable without production credentials."""

    # Act: construct settings without environment-specific overrides.
    settings = Settings(_env_file=None)

    # Assert: local development does not require API-key authentication.
    assert settings.environment == "development"
    assert settings.api_key_enabled is False
    assert settings.api_key is None
    # Local test traffic should not share production-style request state.
    assert settings.rate_limit_enabled is False
    # Both synchronous and asynchronous integration-client hosts are trusted.
    assert "test" in settings.trusted_hosts
    assert "testserver" in settings.trusted_hosts


def test_api_key_is_masked_when_settings_are_rendered() -> None:
    """Secret values must not appear in settings representations."""

    # Arrange: construct a valid production configuration with a known secret.
    raw_api_key = "super-secret-production-key-123456"
    settings = production_settings(api_key=raw_api_key)

    # Assert: Pydantic's SecretStr masks the credential in diagnostic output.
    assert raw_api_key not in repr(settings)
    assert "**********" in repr(settings.api_key)


def test_production_requires_authentication() -> None:
    """Production must refuse to start when authentication is disabled."""

    # Act and assert: model validation should reject the unsafe configuration.
    with pytest.raises(
        ValidationError,
        match="API-key authentication must be enabled in production",
    ):
        production_settings(api_key_enabled=False)


def test_production_requires_api_key() -> None:
    """Production authentication must include an actual API key."""

    # Act and assert: enabling authentication without a key is invalid.
    with pytest.raises(
        ValidationError,
        match="A production API key is required",
    ):
        production_settings(api_key=None)


def test_production_rejects_wildcard_trusted_host() -> None:
    """Production must not accept every possible Host header."""

    # Act and assert: a wildcard defeats TrustedHostMiddleware protection.
    with pytest.raises(
        ValidationError,
        match="Wildcard trusted hosts are not allowed in production",
    ):
        production_settings(trusted_hosts=["*"])


def test_production_rejects_development_database_credentials() -> None:
    """Production must not reuse credentials from the local Compose stack."""

    # Act and assert: the known local password must fail closed.
    with pytest.raises(
        ValidationError,
        match="development database credentials",
    ):
        production_settings(
            database_url=(
                "postgresql+asyncpg://observability:observability_dev"
                "@postgres:5432/observability"
            )
        )


def test_production_requires_rate_limiting() -> None:
    """Production must keep request throttling enabled."""

    # Act and assert: disabling protection is rejected before startup.
    with pytest.raises(
        ValidationError,
        match="Rate limiting must be enabled in production",
    ):
        production_settings(rate_limit_enabled=False)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("rate_limit_requests", 0),
        ("rate_limit_window_seconds", 0),
    ],
)
def test_rate_limit_values_must_be_positive(
    field_name: str,
    invalid_value: int,
) -> None:
    """Rate-limit settings must describe a usable positive window."""

    # Arrange: pass one invalid numeric setting into an otherwise local config.
    values = {field_name: invalid_value}

    # Act and assert: field-level validation rejects zero and negative values.
    with pytest.raises(ValidationError, match="greater than 0"):
        Settings(_env_file=None, **values)


def test_valid_production_configuration_is_accepted() -> None:
    """Secure production values should pass every hardening rule."""

    # Act: construct the reusable valid production baseline.
    settings = production_settings()

    # Assert: validated values remain available to application startup.
    assert settings.environment == "production"
    assert settings.api_key_enabled is True
    assert settings.trusted_hosts == ["api.example.com"]
    assert settings.rate_limit_requests == 100
    assert settings.rate_limit_window_seconds == 60
