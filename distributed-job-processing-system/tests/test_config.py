import pytest
from pydantic import ValidationError

from job_system.config import Settings


def test_default_worker_lease_configuration_is_valid() -> None:
    settings = Settings()

    assert settings.worker_heartbeat_interval_seconds == 5.0
    assert settings.worker_lease_duration_seconds == 30.0
    assert settings.worker_heartbeat_interval_seconds < settings.worker_lease_duration_seconds
    assert settings.worker_metrics_port == 9000


def test_heartbeat_interval_must_be_shorter_than_lease() -> None:
    with pytest.raises(
        ValidationError,
        match="worker heartbeat interval must be shorter than worker lease duration",
    ):
        Settings(
            worker_lease_duration_seconds=30.0,
            worker_heartbeat_interval_seconds=30.0,
        )


def test_production_rejects_local_development_password() -> None:
    with pytest.raises(
        ValidationError,
        match="production database URL must not use the local development password",
    ):
        Settings(
            environment="production",
            database_url=(
                "postgresql+asyncpg://job_user:local_dev_password@postgres:5432/job_system"
            ),
        )


def test_production_rejects_database_echo() -> None:
    with pytest.raises(
        ValidationError,
        match="database echo must be disabled in production",
    ):
        Settings(
            environment="production",
            database_url=(
                "postgresql+asyncpg://job_user:secure-production-password@postgres:5432/job_system"
            ),
            database_echo=True,
        )


def test_production_accepts_secure_database_configuration() -> None:
    settings = Settings(
        environment="production",
        database_url=(
            "postgresql+asyncpg://job_user:secure-production-password@postgres:5432/job_system"
        ),
        database_echo=False,
    )

    assert settings.environment == "production"
    assert settings.database_echo is False
