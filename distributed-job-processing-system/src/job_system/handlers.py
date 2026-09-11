import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

TaskResult = dict[str, Any]
TaskHandler = Callable[[dict[str, Any]], Awaitable[TaskResult]]


class TaskHandlerError(Exception):
    """Base exception for errors raised while handling a task."""


class UnknownTaskError(TaskHandlerError):
    """Raised when no handler is registered for a task name."""


class InvalidTaskPayloadError(TaskHandlerError):
    """Raised when a task payload contains invalid data."""


def _processing_delay(payload: dict[str, Any]) -> float:
    """Read and validate an optional simulated processing delay."""

    delay = payload.get("delay_seconds", 0.1)

    # bool is a subclass of int, so it must be rejected explicitly.
    if isinstance(delay, bool) or not isinstance(delay, int | float):
        raise InvalidTaskPayloadError("delay_seconds must be a number")

    delay_seconds = float(delay)

    if not 0 <= delay_seconds <= 30:
        raise InvalidTaskPayloadError("delay_seconds must be between 0 and 30")

    return delay_seconds


async def generate_report(payload: dict[str, Any]) -> TaskResult:
    """Simulate generating a report and return its stored result."""

    await asyncio.sleep(_processing_delay(payload))

    return {
        "report_id": str(payload.get("report_id", "generated-report")),
        "format": str(payload.get("format", "json")),
        "generated": True,
    }


async def send_email(payload: dict[str, Any]) -> TaskResult:
    """Simulate an email task without contacting an external service."""

    recipient = payload.get("recipient")

    if not isinstance(recipient, str) or not recipient.strip():
        raise InvalidTaskPayloadError("recipient must be a non-empty string")

    await asyncio.sleep(_processing_delay(payload))

    return {
        "recipient": recipient,
        "status": "accepted",
        "simulated": True,
    }


async def echo(payload: dict[str, Any]) -> TaskResult:
    """Return the submitted payload after an optional delay."""

    await asyncio.sleep(_processing_delay(payload))
    return {"echo": payload}


# A registry decouples the worker runtime from individual task implementations.
TASK_HANDLERS: dict[str, TaskHandler] = {
    "generate-report": generate_report,
    "send-email": send_email,
    "echo": echo,
}


async def execute_task(
    task_name: str,
    payload: dict[str, Any],
) -> TaskResult:
    """Dispatch a task to its registered asynchronous handler."""

    handler = TASK_HANDLERS.get(task_name)

    if handler is None:
        raise UnknownTaskError(f"No handler registered for task: {task_name}")

    return await handler(payload)
