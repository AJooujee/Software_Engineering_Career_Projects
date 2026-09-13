"""Metrics and structured logging used to observe system behavior."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    start_http_server,
)

METRICS_REGISTRY = CollectorRegistry()

JOBS_SUBMITTED_TOTAL = Counter(
    "job_system_jobs_submitted_total",
    "Number of job submission requests.",
    ("outcome",),
    registry=METRICS_REGISTRY,
)

JOBS_CLAIMED_TOTAL = Counter(
    "job_system_jobs_claimed_total",
    "Number of jobs claimed for execution.",
    registry=METRICS_REGISTRY,
)

JOB_TRANSITIONS_TOTAL = Counter(
    "job_system_job_transitions_total",
    "Number of persisted job lifecycle transitions.",
    ("status",),
    registry=METRICS_REGISTRY,
)

LEASE_RENEWALS_TOTAL = Counter(
    "job_system_lease_renewals_total",
    "Number of worker lease renewal attempts.",
    ("outcome",),
    registry=METRICS_REGISTRY,
)

STALE_JOB_RECOVERIES_TOTAL = Counter(
    "job_system_stale_job_recoveries_total",
    "Number of stale jobs recovered after worker lease expiration.",
    ("outcome",),
    registry=METRICS_REGISTRY,
)

JOB_PROCESSING_SECONDS = Histogram(
    "job_system_job_processing_seconds",
    "Time spent executing and persisting one claimed job.",
    registry=METRICS_REGISTRY,
)


class JsonLogFormatter(logging.Formatter):
    """Format application logs as one JSON object per line."""

    context_fields = (
        "event",
        "job_id",
        "worker_id",
        "task_name",
        "slot_number",
        "status",
    )

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Optional fields provide searchable context without changing messages.
        for field_name in self.context_fields:
            field_value = getattr(record, field_name, None)

            if field_value is not None:
                log_entry[field_name] = field_value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            log_entry,
            default=str,
            separators=(",", ":"),
        )


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure the process to emit structured JSON logs."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )


def start_metrics_server(*, port: int) -> None:
    """Expose metrics for a standalone worker process."""

    start_http_server(
        port,
        registry=METRICS_REGISTRY,
    )


def render_metrics() -> tuple[bytes, str]:
    """Render all application metrics in Prometheus text format."""

    return generate_latest(METRICS_REGISTRY), CONTENT_TYPE_LATEST
