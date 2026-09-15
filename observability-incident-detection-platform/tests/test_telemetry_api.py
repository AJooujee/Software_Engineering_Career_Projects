from datetime import datetime

from fastapi.testclient import TestClient

from observability_platform.main import app

client = TestClient(app)


def test_ingest_mixed_telemetry_batch() -> None:
    response = client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": 72.5,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                    "level": "error",
                    "message": "Payment provider timed out",
                },
                {
                    "type": "event",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                    "name": "service_restart",
                    "severity": "warning",
                    "description": "Instance restarted",
                },
            ]
        },
    )

    payload = response.json()

    assert response.status_code == 202
    assert payload["accepted_count"] == 3
    assert len(payload["telemetry_ids"]) == 3
    assert len(set(payload["telemetry_ids"])) == 3
    assert datetime.fromisoformat(payload["received_at"]).tzinfo is not None
    assert "X-Request-ID" in response.headers


def test_ingest_rejects_empty_batch() -> None:
    response = client.post(
        "/api/v1/telemetry",
        json={"items": []},
    )

    assert response.status_code == 422


def test_ingest_rejects_unknown_telemetry_type() -> None:
    response = client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "trace",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_ingest_rejects_invalid_metric_value() -> None:
    response = client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": "not-a-number",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_openapi_schema_contains_telemetry_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/telemetry" in response.json()["paths"]
    assert "post" in response.json()["paths"]["/api/v1/telemetry"]
