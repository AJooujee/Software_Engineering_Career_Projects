# Rule-Based Anomaly Detection

## Overview

The platform evaluates telemetry during ingestion using deterministic rules.
Detected anomalies are persisted in the same database transaction as their
source telemetry records.

If anomaly persistence fails, the telemetry ingestion transaction is rolled
back.

## Detection Rules

| Rule ID | Condition | Severity |
| --- | --- | --- |
| `metric.cpu_usage.high` | CPU usage is at least 90 percent | Critical |
| `metric.memory_usage.high` | Memory usage is at least 90 percent | Critical |
| `metric.response_latency.high` | Response latency is at least 500 milliseconds | Warning |
| `metric.error_rate.high` | Error rate is at least 5 percent | Critical |
| `log.level.error` | Log level is error | Warning |
| `log.level.critical` | Log level is critical | Critical |
| `event.severity.error` | Event severity is error | Warning |
| `event.severity.critical` | Event severity is critical | Critical |

Metric rules require the expected metric name and unit.

## Ingestion Response

`POST /api/v1/telemetry` returns telemetry and anomaly identifiers:

```json
{
  "accepted_count": 2,
  "telemetry_ids": [
    "f15b2f24-3e7d-4091-ad92-37e0dc4f9160",
    "b98c0d48-0209-41e8-bb44-70b322a416e9"
  ],
  "received_at": "2026-09-15T22:26:29.051241Z",
  "detected_anomaly_count": 2,
  "anomaly_ids": [
    "d0b304a3-e4b4-4bd3-b639-b28de17de1b0",
    "3986ce44-f6ed-4cd5-9fb4-eede13ac96a6"
  ]
}
```

## Query Endpoint

```text
GET /api/v1/anomalies
```

Supported query parameters:

| Parameter | Description |
| --- | --- |
| `service` | Filter by monitored service name |
| `environment` | Filter by service environment |
| `category` | Filter by anomaly category |
| `severity` | Filter by warning or critical severity |
| `rule_id` | Filter by exact detection rule |
| `detected_from` | Include anomalies detected at or after this time |
| `detected_to` | Include anomalies detected at or before this time |
| `limit` | Maximum results from 1 to 100; default 50 |
| `offset` | Number of results skipped; default 0 |

Results are ordered by detection time from newest to oldest.

## Example Query

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/anomalies?service=payment-service&severity=critical" `
  -Method Get
```

## Validation

The API returns `422 Unprocessable Content` when:

- An unsupported category or severity is supplied.
- `limit` is outside the range 1–100.
- `offset` is negative.
- `detected_from` is later than `detected_to`.