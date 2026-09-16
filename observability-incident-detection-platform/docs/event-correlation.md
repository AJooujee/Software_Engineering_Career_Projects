# Event Correlation and Root-Cause Analysis

Phase 6 adds deterministic incident correlation and probable root-cause
analysis to the observability platform.

The correlation workflow groups recent incidents from the same monitored
service and environment, evaluates their anomaly signals, and records the
most likely initiating signal with an explainable confidence score.

## Correlation Workflow

A correlation analysis performs the following steps:

1. Calculate the requested time window.
2. Find unresolved incidents for the selected service and environment.
3. Exclude incidents that already belong to another correlation.
4. Require the configured minimum number of incidents.
5. Convert each incident and its triggering anomaly into a correlation signal.
6. Score each signal using deterministic root-cause rules.
7. Select the highest-scoring signal as the probable root cause.
8. Persist the correlation and its incident links atomically.

An incident can belong to only one correlation. This constraint prevents the
same operational event from being counted in multiple correlation groups.

## Root-Cause Scoring

Each candidate starts with a base confidence score of `0.25`.

Additional confidence is assigned using the following rules:

| Signal characteristic | Score |
| --- | ---: |
| Earliest observed anomaly | +0.25 |
| Event severity category | +0.20 |
| Log severity category | +0.10 |
| Metric threshold category | +0.05 |
| Critical severity | +0.15 |
| Warning severity | +0.05 |
| Source appears more than once | +0.15 |

The final confidence score is capped at `1.0`.

When candidates have equal scores, the engine selects the earliest observed
anomaly. The anomaly UUID provides deterministic tie-breaking when timestamps
are also equal.

The engine is intentionally rule-based and explainable. It does not claim
statistical or machine-learning causality.

## Analyze Incidents

```http
POST /api/v1/correlations/analyze
Content-Type: application/json
```

Example request:

```json
{
  "service": "payment-service",
  "environment": "production",
  "window_minutes": 15,
  "minimum_incidents": 2
}
```

Request fields:

- `service`: Registered monitored service name.
- `environment`: Service environment.
- `window_minutes`: Correlation window from 1 to 1440 minutes.
- `minimum_incidents`: Minimum number of incidents from 2 to 100.

A successful request returns `201 Created`.

Example response:

```json
{
  "id": "5af8fa8d-ce72-4f25-9365-692cb1fc5f75",
  "service": "payment-service",
  "environment": "production",
  "status": "active",
  "incident_count": 2,
  "root_cause": {
    "rule_id": "log.level.critical",
    "category": "log_severity",
    "severity": "critical",
    "source": "payment-instance-1",
    "confidence_score": 0.9,
    "reasons": [
      "Signal is the earliest observed anomaly",
      "Signal severity is critical",
      "Source appears in 2 correlated incidents"
    ]
  }
}
```

The API returns `422 Unprocessable Content` when the selected window does not
contain enough eligible incidents.

## Query Correlations

```http
GET /api/v1/correlations
```

Supported query parameters:

- `service`
- `environment`
- `status`
- `created_from`
- `created_to`
- `limit`
- `offset`

Results are ordered newest first and include the total matching count.

## Get Correlation Details

```http
GET /api/v1/correlations/{correlation_id}
```

The endpoint returns the correlated incident IDs, time window, probable root
cause, confidence score, evidence reasons, and generated summary.

A missing correlation returns `404 Not Found`.

## Persistence Model

Phase 6 introduces two PostgreSQL tables:

- `correlations`: Stores the correlation window, status, probable root cause,
  confidence score, evidence reasons, and summary.
- `correlation_incidents`: Links correlations to their member incidents.

The junction table applies a unique constraint to `incident_id`, ensuring that
an incident cannot be assigned to multiple correlations.

The parent correlation is flushed before its junction rows are inserted so
that PostgreSQL foreign-key ordering is preserved. The service layer commits
the complete operation as one transaction and rolls it back on failure.

## Testing

The test suite covers:

- Deterministic root-cause scoring.
- Earliest-signal selection.
- Repeated-source confidence.
- Stable tie-breaking.
- Successful correlation persistence.
- Insufficient-incident rejection.
- Prevention of incident reuse.
- Filtered correlation queries.
- Correlation detail retrieval.
- Missing-correlation handling.
- SQLite foreign-key enforcement during integration tests.