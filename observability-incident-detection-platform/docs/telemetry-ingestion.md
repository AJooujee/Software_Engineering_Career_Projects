# Telemetry Ingestion

## Overview

The telemetry ingestion API accepts operational data from monitored services.
Phase 2 supports metrics, logs, and operational events through a versioned
FastAPI endpoint.

## Endpoint

```text
POST /api/v1/telemetry
```

Successful requests return `202 Accepted`, indicating that the telemetry batch
has been validated and accepted for processing.

## Supported Telemetry Types

### Metric

Represents a numeric measurement such as CPU usage, memory usage, request
latency, or error rate.

Required fields:

- `type`: `metric`
- `service`
- `source`
- `name`
- `value`

Optional fields:

- `unit`
- `timestamp`
- `attributes`

### Log

Represents a structured application log.

Required fields:

- `type`: `log`
- `service`
- `source`
- `level`
- `message`

Supported levels are `debug`, `info`, `warning`, `error`, and `critical`.

### Event

Represents an operational event such as a deployment, restart, timeout, or
health-check failure.

Required fields:

- `type`: `event`
- `service`
- `source`
- `name`
- `severity`

Supported severities are `info`, `warning`, `error`, and `critical`.

## Validation Rules

- A batch must contain between 1 and 1,000 telemetry records.
- Service and source values cannot be empty.
- Unknown telemetry types are rejected.
- Unexpected fields are rejected.
- Infinite and NaN metric values are rejected.
- Invalid requests return HTTP `422 Unprocessable Entity`.

## Processing Flow

1. FastAPI receives the telemetry batch.
2. Pydantic selects the schema using the `type` discriminator.
3. Each telemetry record is validated.
4. The service generates a unique UUID for each accepted record.
5. Records are stored in a concurrency-safe in-memory store.
6. The API returns the accepted count, generated IDs, and receipt timestamp.
7. Request middleware records the request ID, status code, and duration.

## Current Storage Limitation

Phase 2 uses an in-memory store limited to 10,000 records. Data is lost when the
application restarts. Persistent PostgreSQL storage will replace this
implementation in Phase 3.