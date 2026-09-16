# Distributed Tracing

Phase 7 introduces persistent distributed tracing for following a request
across multiple monitored services.

## Overview

A distributed trace contains one or more spans that share the same `trace_id`.
Each span represents an operation performed by a service. A child span uses
`parent_span_id` to identify the operation that called it.

The platform supports:

- Batch span ingestion
- W3C-compatible trace and span identifiers
- Parent-child span relationships
- Cross-service trace reconstruction
- Per-span and trace-level duration calculation
- Duplicate span protection
- Atomic batch persistence
- PostgreSQL-backed trace storage

## Data Model

Each span stores:

- `trace_id`: 32-character lowercase hexadecimal trace identifier
- `span_id`: 16-character lowercase hexadecimal span identifier
- `parent_span_id`: optional identifier of the parent span
- `service`: registered service name
- `environment`: service deployment environment
- `source`: process, host, container, or instance that produced the span
- `operation`: operation performed by the span
- `status`: `unset`, `ok`, or `error`
- `started_at`: operation start time
- `ended_at`: operation completion time
- `duration_ms`: calculated span duration
- `attributes`: optional structured span metadata

The database enforces uniqueness for each `(trace_id, span_id)` pair.

## Ingest Trace Spans

Endpoint:

```http
POST /api/v1/traces
```

Example request:

```json
{
  "spans": [
    {
      "trace_id": "11111111111111111111111111111111",
      "span_id": "2222222222222222",
      "parent_span_id": null,
      "service": "gateway-service",
      "environment": "production",
      "source": "gateway-instance-1",
      "operation": "POST /checkout",
      "status": "ok",
      "started_at": "2026-09-16T20:00:00Z",
      "ended_at": "2026-09-16T20:00:00.180Z",
      "attributes": {
        "http.method": "POST",
        "http.status_code": 200
      }
    },
    {
      "trace_id": "11111111111111111111111111111111",
      "span_id": "3333333333333333",
      "parent_span_id": "2222222222222222",
      "service": "payment-service",
      "environment": "production",
      "source": "payment-instance-1",
      "operation": "authorize_payment",
      "status": "ok",
      "started_at": "2026-09-16T20:00:00.040Z",
      "ended_at": "2026-09-16T20:00:00.120Z",
      "attributes": {
        "payment.provider": "sandbox"
      }
    }
  ]
}
```

Example response:

```json
{
  "accepted_count": 2,
  "span_record_ids": [
    "80a9a9f5-935a-47af-a4f1-f0c396bd6847",
    "fdad164d-4eb5-4868-8843-eb802808923c"
  ],
  "received_at": "2026-09-16T20:01:39.609130Z"
}
```

All spans in one batch must share the same `trace_id`. Every referenced service
must already exist in the monitored service registry.

The complete batch is stored in one transaction. If validation or persistence
fails, the transaction is rolled back.

## Retrieve a Trace

Endpoint:

```http
GET /api/v1/traces/{trace_id}
```

The response reconstructs the trace from all persisted spans and provides:

- Chronologically ordered spans
- Total span count
- Participating services
- Earliest trace start
- Latest trace end
- Total wall-clock duration

Example response:

```json
{
  "trace_id": "11111111111111111111111111111111",
  "span_count": 2,
  "started_at": "2026-09-16T20:00:00Z",
  "ended_at": "2026-09-16T20:00:00.180000Z",
  "duration_ms": 180.0,
  "services": [
    "gateway-service",
    "payment-service"
  ],
  "spans": []
}
```

Trace duration is calculated from the earliest span start to the latest span
end. It is not the sum of span durations because child spans can overlap their
parents.

## Validation and Error Responses

The tracing API returns:

- `404 Not Found` when the requested trace does not exist
- `409 Conflict` when a `(trace_id, span_id)` pair already exists
- `422 Unprocessable Entity` for malformed identifiers, mixed trace batches,
  self-parenting spans, invalid timestamps, or unregistered services

Duplicate protection checks both repeated identifiers inside the incoming batch
and spans already stored in the database.

## Database Storage

Trace spans are stored in the `trace_spans` table.

Indexes support:

- Trace reconstruction by `trace_id` and `started_at`
- Service timeline queries by `service_id` and `started_at`
- Status queries by `status` and `started_at`
- Parent-span lookups by `parent_span_id`

Deleting a monitored service cascades to its stored trace spans.