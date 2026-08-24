"""Integration tests for the sensor platform REST API."""

import pytest
from fastapi.testclient import TestClient

from sensor_platform.api import create_app


@pytest.fixture
def client(tmp_path):
    """Create an API client with an isolated SQLite database."""

    application = create_app(tmp_path / "api_test.db")

    with TestClient(application) as test_client:
        yield test_client


def test_health_endpoint(client) -> None:
    """The API should expose a basic service health check."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_simulation_stores_and_returns_readings(client) -> None:
    """Generated readings should be saved and returned through the API."""

    response = client.post(
        "/api/v1/simulations",
        json={
            "count": 2,
            "warning_rate": 0,
            "fault_rate": 0,
            "seed": 42,
        },
    )

    assert response.status_code == 201
    assert response.json()["generated_count"] == 8

    stored_response = client.get("/api/v1/readings")
    stored_readings = stored_response.json()

    assert stored_response.status_code == 200
    assert len(stored_readings) == 8
    assert all(
        reading["status"] == "normal"
        for reading in stored_readings
    )


def test_summary_reports_stored_faults(client) -> None:
    """The summary endpoint should reflect persisted fault data."""

    client.post(
        "/api/v1/simulations",
        json={
            "count": 1,
            "warning_rate": 0,
            "fault_rate": 1,
        },
    )

    summary = client.get("/api/v1/summary").json()

    assert summary["total_readings"] == 4
    assert summary["fault_count"] == 4
    assert summary["health_score"] == 0.0


def test_simulation_rejects_invalid_combined_rates(client) -> None:
    """Warning and fault probabilities cannot exceed 100 percent."""

    response = client.post(
        "/api/v1/simulations",
        json={
            "count": 5,
            "warning_rate": 0.6,
            "fault_rate": 0.5,
        },
    )

    assert response.status_code == 422


def test_hardware_test_endpoint_returns_pass_and_fail(client) -> None:
    """The API should distinguish healthy and faulty hardware tests."""

    passing = client.post(
        "/api/v1/hardware-tests",
        json={"count": 5},
    ).json()

    failing = client.post(
        "/api/v1/hardware-tests",
        json={"count": 5, "fault_rate": 1},
    ).json()

    assert passing["overall_outcome"] == "pass"
    assert passing["passed_sensors"] == 4
    assert failing["overall_outcome"] == "fail"
    assert failing["failed_sensors"] == 4
