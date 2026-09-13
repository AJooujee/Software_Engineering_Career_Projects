import pytest
from pydantic import ValidationError

from job_system.config import Settings


def test_default_worker_lease_configuration_is_valid() -> None:
    settings = Settings()

    assert settings.worker_heartbeat_interval_seconds == 5.0
    assert settings.worker_lease_duration_seconds == 30.0
    assert settings.worker_heartbeat_interval_seconds < settings.worker_lease_duration_seconds


def test_heartbeat_interval_must_be_shorter_than_lease() -> None:
    with pytest.raises(
        ValidationError,
        match="worker heartbeat interval must be shorter than worker lease duration",
    ):
        Settings(
            worker_lease_duration_seconds=30.0,
            worker_heartbeat_interval_seconds=30.0,
        )
