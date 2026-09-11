import pytest

from job_system.handlers import (
    InvalidTaskPayloadError,
    UnknownTaskError,
    execute_task,
)


async def test_generate_report_handler() -> None:
    result = await execute_task(
        "generate-report",
        {
            "report_id": "sales-2026-09",
            "format": "pdf",
            "delay_seconds": 0,
        },
    )

    assert result == {
        "report_id": "sales-2026-09",
        "format": "pdf",
        "generated": True,
    }


async def test_send_email_handler() -> None:
    result = await execute_task(
        "send-email",
        {
            "recipient": "test@example.com",
            "delay_seconds": 0,
        },
    )

    assert result == {
        "recipient": "test@example.com",
        "status": "accepted",
        "simulated": True,
    }


async def test_echo_handler() -> None:
    payload = {
        "message": "hello worker",
        "delay_seconds": 0,
    }

    result = await execute_task("echo", payload)

    assert result == {"echo": payload}


async def test_unknown_task_is_rejected() -> None:
    with pytest.raises(
        UnknownTaskError,
        match="No handler registered",
    ):
        await execute_task("unknown-task", {})


@pytest.mark.parametrize(
    "invalid_delay",
    [True, "slow", -1, 31],
)
async def test_invalid_processing_delay_is_rejected(
    invalid_delay: object,
) -> None:
    with pytest.raises(InvalidTaskPayloadError):
        await execute_task(
            "echo",
            {"delay_seconds": invalid_delay},
        )


async def test_send_email_requires_recipient() -> None:
    with pytest.raises(
        InvalidTaskPayloadError,
        match="recipient must be a non-empty string",
    ):
        await execute_task(
            "send-email",
            {"delay_seconds": 0},
        )
