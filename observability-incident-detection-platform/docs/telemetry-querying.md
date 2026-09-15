# Telemetry Querying

## Overview

The telemetry query API retrieves persisted metrics, logs, and operational events.
It supports filtering, time-range queries, pagination, and newest-first ordering.

## Endpoint

```text
GET /api/v1/telemetry
```

## Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `service` | string | — | Filter by registered service name |
| `environment` | string | — | Filter by service environment |
| `type` | string | — | Filter by `metric`, `log`, or `event` |
| `source` | string | — | Filter by telemetry source |
| `observed_from` | datetime | — | Include records observed at or after this time |
| `observed_to` | datetime | — | Include records observed at or before this time |
| `limit` | integer | `50` | Maximum records returned; range 1–100 |
| `offset` | integer | `0` | Number of records skipped |

Results are ordered by `observed_at` from newest to oldest.

## Query All Telemetry

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/telemetry?limit=10&offset=0" `
  -Method Get
```

## Filter Telemetry

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/telemetry?service=payment-service&environment=development&type=metric" `
  -Method Get
```

## Filter by Time Range

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/telemetry?observed_from=2026-09-15T10:00:00Z&observed_to=2026-09-15T16:00:00Z" `
  -Method Get
```

## Example Response

```json
{
  "items": [
    {
      "id": "4b54de0d-07ae-4a19-9275-02ab776180a0",
      "service_id": "4afe4918-1af6-43c0-abce-d53bcffc2cd3",
      "service": "payment-service",
      "environment": "development",
      "type": "metric",
      "source": "payment-instance-1",
      "observed_at": "2026-09-15T15:07:32.790645Z",
      "received_at": "2026-09-15T15:07:32.877701Z",
      "payload": {
        "name": "response_latency",
        "value": 325.5,
        "unit": "milliseconds"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Validation

The API returns `422 Unprocessable Content` when:

- `type` is not `metric`, `log`, or `event`.
- `limit` is outside the range 1–100.
- `offset` is negative.
- `observed_from` is later than `observed_to`.
- A query parameter does not match its expected type.