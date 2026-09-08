"""Safe structured request logging and correlation identifiers."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from uuid import uuid4


_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_REQUEST_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "error_type",
)


class JsonRequestFormatter(logging.Formatter):
    """Render a compact JSON object without request bodies or credentials."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        for field_name in _REQUEST_FIELDS:
            if hasattr(record, field_name):
                payload[field_name] = getattr(record, field_name)

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def configure_request_logger() -> logging.Logger:
    """Return one process-wide JSON request logger."""

    logger = logging.getLogger("cloud_operations.requests")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(
        getattr(handler, "cloud_operations_json", False)
        for handler in logger.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonRequestFormatter())
        handler.cloud_operations_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)

    return logger


def resolve_request_id(candidate: str | None) -> str:
    """Accept a safe correlation ID or create a new opaque identifier."""

    if candidate is not None and _SAFE_REQUEST_ID.fullmatch(candidate):
        return candidate

    return uuid4().hex
