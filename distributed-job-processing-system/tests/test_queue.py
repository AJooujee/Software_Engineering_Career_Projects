import pytest

from job_system.queue import (
    calculate_retry_delay_seconds,
    should_retry_job,
)


@pytest.mark.parametrize(
    ("attempt_count", "expected_delay"),
    [
        (1, 5.0),
        (2, 10.0),
        (3, 20.0),
        (4, 40.0),
    ],
)
def test_calculate_retry_delay_uses_exponential_backoff(
    attempt_count: int,
    expected_delay: float,
) -> None:
    delay = calculate_retry_delay_seconds(
        attempt_count=attempt_count,
        base_delay_seconds=5.0,
        max_delay_seconds=300.0,
    )

    assert delay == expected_delay


def test_calculate_retry_delay_respects_maximum() -> None:
    delay = calculate_retry_delay_seconds(
        attempt_count=10,
        base_delay_seconds=5.0,
        max_delay_seconds=300.0,
    )

    assert delay == 300.0


@pytest.mark.parametrize(
    ("retryable", "attempt_count", "max_attempts", "expected"),
    [
        (True, 1, 3, True),
        (True, 2, 3, True),
        (True, 3, 3, False),
        (False, 1, 3, False),
    ],
)
def test_should_retry_job(
    retryable: bool,
    attempt_count: int,
    max_attempts: int,
    expected: bool,
) -> None:
    assert (
        should_retry_job(
            retryable=retryable,
            attempt_count=attempt_count,
            max_attempts=max_attempts,
        )
        is expected
    )
