import json
import logging

from job_system.observability import JsonLogFormatter


def test_json_log_formatter_includes_structured_context() -> None:
    record = logging.LogRecord(
        name="job_system.worker",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Job completed",
        args=(),
        exc_info=None,
    )
    record.job_id = "test-job-id"
    record.worker_id = "test-worker"
    record.status = "succeeded"

    formatted = JsonLogFormatter().format(record)
    log_entry = json.loads(formatted)

    assert log_entry["level"] == "INFO"
    assert log_entry["logger"] == "job_system.worker"
    assert log_entry["message"] == "Job completed"
    assert log_entry["job_id"] == "test-job-id"
    assert log_entry["worker_id"] == "test-worker"
    assert log_entry["status"] == "succeeded"
    assert "timestamp" in log_entry
