# Incident Lifecycle Management

## Overview

Critical anomalies automatically create incidents during telemetry ingestion.
Telemetry, anomalies, and incidents are persisted in a single database
transaction.

Warning anomalies are retained for investigation but do not automatically
create incidents.

## Lifecycle

```text
Open → Acknowledged → Resolved
Open → Resolved
```

A resolved incident cannot return to an earlier state.

## Automatic Incident Creation

When a critical anomaly is detected, the ingestion response includes the
created incident identifiers:

```json
{
  "accepted_count": 1,
  "detected_anomaly_count": 1,
  "created_incident_count": 1,
  "incident_ids": [
    "2c275b40-fb24-40b5-939e-685507dc41ac"
  ]
}
```

Each incident references:

- The monitored service
- The triggering anomaly
- Severity and lifecycle status
- Creation, acknowledgement, and resolution information

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/incidents` | Query incidents |
| `GET` | `/api/v1/incidents/{incident_id}` | Get incident details |
| `PATCH` | `/api/v1/incidents/{incident_id}/acknowledge` | Acknowledge an open incident |
| `PATCH` | `/api/v1/incidents/{incident_id}/resolve` | Resolve an open or acknowledged incident |

## Query Filters

`GET /api/v1/incidents` supports:

| Parameter | Description |
| --- | --- |
| `service` | Filter by monitored service name |
| `environment` | Filter by service environment |
| `status` | Filter by open, acknowledged, or resolved status |
| `severity` | Filter by warning or critical severity |
| `created_from` | Include incidents created at or after this time |
| `created_to` | Include incidents created at or before this time |
| `limit` | Maximum results from 1 to 100; default 50 |
| `offset` | Number of results skipped; default 0 |

## Acknowledge an Incident

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/incidents/{incident_id}/acknowledge" `
  -Method Patch `
  -ContentType "application/json" `
  -Body '{"acknowledged_by":"aj"}'
```

## Resolve an Incident

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/incidents/{incident_id}/resolve" `
  -Method Patch `
  -ContentType "application/json" `
  -Body '{"resolved_by":"aj","resolution_summary":"Service recovered"}'
```

## Validation

The API returns:

- `404 Not Found` when an incident does not exist.
- `409 Conflict` for an invalid lifecycle transition.
- `422 Unprocessable Content` for invalid input or query parameters.