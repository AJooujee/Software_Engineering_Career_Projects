from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


class RequestContextFilter(logging.Filter):
    """Attach the active request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()

        return True


class JsonFormatter(logging.Formatter):
    """Serialize application and HTTP logs as structured JSON."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "event": record.getMessage(),
        }

        structured_fields = (
            "request_id",
            "http_method",
            "http_path",
            "status_code",
            "duration_ms",
            "client_ip",
        )

        for field_name in structured_fields:
            field_value = getattr(record, field_name, None)

            if field_value is not None:
                payload[field_name] = field_value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(service_name: str) -> None:
    """Configure consistent JSON logging for one service process."""

    configured_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, configured_level, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service_name))
    handler.addFilter(RequestContextFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Route Uvicorn lifecycle logs through the same JSON formatter.
    for logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    # Request middleware produces richer access logs, so disable duplicates.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True


class RequestLoggingMiddleware:
    """Log HTTP outcomes and propagate an X-Request-ID header."""

    def __init__(self, app: ASGIApp, service_name: str) -> None:
        self.app = app
        self.service_name = service_name
        self.logger = logging.getLogger("warehouse_platform.requests")

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_headers = MutableHeaders(scope=scope)
        request_id = (
            request_headers.get("x-request-id")
            or str(uuid4())
        )

        # Adding the generated ID to the ASGI scope lets the Gateway forward
        # the same correlation ID to downstream services.
        request_headers["x-request-id"] = request_id

        request_token = request_id_context.set(request_id)
        started_at = perf_counter()
        status_code = 500

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        client = scope.get("client")
        client_ip = client[0] if client is not None else None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])

                response_headers = MutableHeaders(scope=message)
                response_headers["x-request-id"] = request_id

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )
        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            self.logger.exception(
                "http_request_failed",
                extra={
                    "request_id": request_id,
                    "http_method": method,
                    "http_path": path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            raise
        else:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            if status_code >= 500:
                log_level = logging.ERROR
            elif status_code >= 400:
                log_level = logging.WARNING
            elif path == "/health":
                # Avoid filling production logs with routine health probes.
                log_level = logging.DEBUG
            else:
                log_level = logging.INFO

            self.logger.log(
                log_level,
                "http_request_completed",
                extra={
                    "request_id": request_id,
                    "http_method": method,
                    "http_path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
        finally:
            request_id_context.reset(request_token)