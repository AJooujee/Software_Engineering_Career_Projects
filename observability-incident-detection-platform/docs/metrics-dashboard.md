# Metrics Dashboard

Phase 7 introduces an aggregation API that transforms persisted metric
telemetry into dashboard-ready statistics and chronological chart points.

## Overview

The metrics dashboard provides:

- Service and environment filtering
- Metric-name filtering
- Optional source filtering
- Configurable time windows
- Minimum, maximum, average, and p95 values
- Latest-value reporting
- Chronological time-series points
- Detection of inconsistent metric units

The endpoint reads existing telemetry records and does not require a separate
dashboard table.

## Metric Summary Endpoint

Endpoint:

```http
GET /api/v1/dashboard/metrics/summary
```

Required query parameters:

- `service`: registered service name
- `environment`: deployment environment
- `metric`: metric name

Optional query parameters:

- `source`: restrict samples to one telemetry source
- `observed_from`: inclusive UTC start time
- `observed_to`: inclusive UTC end time
- `window_minutes`: fallback window when explicit boundaries are omitted

The default window is 60 minutes. The supported range for `window_minutes` is
1 through 10,080 minutes.

## Example Request

```http
GET /api/v1/dashboard/metrics/summary?service=payment-service&environment=production&metric=checkout_duration&observed_from=2026-09-16T20%3A09%3A00Z&observed_to=2026-09-16T20%3A14%3A00Z
```

The colon characters in the ISO 8601 timestamps are URL-encoded as `%3A`.

## Example Response

```json
{
  "service": "payment-service",
  "environment": "production",
  "metric_name": "checkout_duration",
  "unit": "milliseconds",
  "sources": [
    "payment-instance-1",
    "payment-instance-2"
  ],
  "window_started_at": "2026-09-16T20:10:00Z",
  "window_ended_at": "2026-09-16T20:13:00Z",
  "sample_count": 4,
  "minimum_value": 120.0,
  "maximum_value": 300.0,
  "average_value": 210.0,
  "p95_value": 300.0,
  "latest_value": 300.0,
  "latest_observed_at": "2026-09-16T20:13:00Z",
  "points": [
    {
      "observed_at": "2026-09-16T20:10:00Z",
      "value": 120.0,
      "source": "payment-instance-1"
    },
    {
      "observed_at": "2026-09-16T20:11:00Z",
      "value": 180.0,
      "source": "payment-instance-2"
    },
    {
      "observed_at": "2026-09-16T20:12:00Z",
      "value": 240.0,
      "source": "payment-instance-1"
    },
    {
      "observed_at": "2026-09-16T20:13:00Z",
      "value": 300.0,
      "source": "payment-instance-2"
    }
  ]
}
```

## Aggregation Rules

Only telemetry records whose type is `metric` participate in the aggregation.

The repository first applies filters that are portable across PostgreSQL and
SQLite:

- Service
- Environment
- Optional source
- Inclusive start time
- Inclusive end time

The dashboard service then selects records whose JSON payload name matches the
requested metric.

Statistics are calculated as follows:

- `minimum_value`: smallest matching sample
- `maximum_value`: largest matching sample
- `average_value`: arithmetic mean of all matching samples
- `p95_value`: nearest-rank 95th percentile
- `latest_value`: value from the newest matching sample
- `latest_observed_at`: timestamp of the newest matching sample
- `window_started_at`: timestamp of the earliest matching sample
- `window_ended_at`: timestamp of the latest matching sample

The time-series points are returned from oldest to newest so a frontend can
pass them directly to a charting component.

## Percentile Calculation

The p95 value uses the nearest-rank method:

```text
rank = ceil(0.95 * sample_count)
```

After sorting values from smallest to largest, the service selects the sample
at that one-based rank. The implementation converts the result to a zero-based
list index before selecting the value.

For the samples `120`, `180`, `240`, and `300`, the calculated rank is four.
The p95 value is therefore `300`.

## Time-Window Behavior

When `observed_to` is omitted, the service uses the current UTC time.

When `observed_from` is omitted, the service subtracts `window_minutes` from
the selected end time.

Both time boundaries are inclusive. The API rejects a request when the start
time occurs after the end time.

The response reports the timestamps of the first and last matching samples,
not merely the requested query boundaries.

## Source Filtering

The optional `source` parameter can isolate one application instance, host,
container, or worker.

For example:

```http
GET /api/v1/dashboard/metrics/summary?service=payment-service&environment=production&metric=checkout_duration&source=payment-instance-1
```

Without this parameter, the response combines matching samples from every
source and returns the sorted unique source names in `sources`.

## Unit Consistency

All samples included in one summary must use the same unit.

Mixing values such as `milliseconds` and `seconds` would produce misleading
statistics. The service therefore rejects inconsistent units rather than
converting them implicitly.

## Error Responses

The dashboard API returns:

- `404 Not Found` when no matching metric samples exist
- `422 Unprocessable Entity` when the requested time window is reversed
- `422 Unprocessable Entity` when matching samples use different units
- `422 Unprocessable Entity` when query parameters fail validation

## Database Portability

Metric names, values, units, and attributes are stored inside the telemetry
JSON payload.

The repository performs broadly compatible filtering in SQL, while the
dashboard service applies metric-name filtering to the returned payloads. This
keeps integration tests portable between SQLite and production PostgreSQL
without depending on database-specific JSON operators.

## Current Scope

Phase 7 provides a backend aggregation endpoint rather than a graphical user
interface. The returned summary and ordered points are designed to be consumed
by a future web dashboard, monitoring panel, or visualization service.