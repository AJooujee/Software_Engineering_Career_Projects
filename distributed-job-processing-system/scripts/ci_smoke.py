"""Run an end-to-end smoke test against the production Compose stack."""

import argparse
import json
import time
import uuid
from typing import Any
from urllib.request import Request, urlopen


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send an HTTP request and decode its JSON response."""

    request_data = None
    headers: dict[str, str] = {}

    if payload is not None:
        request_data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    request = Request(
        url,
        data=request_data,
        headers=headers,
        method=method,
    )

    with urlopen(request, timeout=5) as response:
        return json.load(response)


def request_text(url: str) -> str:
    """Return the text body from an HTTP endpoint."""

    with urlopen(url, timeout=5) as response:
        return response.read().decode()


def wait_for_success(
    api_url: str,
    job_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Poll one job until it succeeds or reaches an unexpected state."""

    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        job = request_json("GET", f"{api_url}/jobs/{job_id}")
        status = job["status"]

        if status == "succeeded":
            return job

        if status == "dead_lettered":
            raise RuntimeError(f"Smoke-test job was dead-lettered: {job}")

        time.sleep(0.25)

    raise TimeoutError(f"Smoke-test job {job_id} did not succeed in time")


def main() -> None:
    """Validate API health, worker execution, and Prometheus metrics."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8002",
    )
    parser.add_argument(
        "--worker-url",
        default="http://127.0.0.1:9000",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
    )
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    worker_url = args.worker_url.rstrip("/")

    liveness = request_json("GET", f"{api_url}/health/live")
    readiness = request_json("GET", f"{api_url}/health/ready")

    if liveness["status"] != "healthy":
        raise RuntimeError(f"Unexpected liveness response: {liveness}")

    if readiness["status"] != "healthy":
        raise RuntimeError(f"Unexpected readiness response: {readiness}")

    report_id = f"phase8-ci-{uuid.uuid4().hex}"
    submitted_job = request_json(
        "POST",
        f"{api_url}/jobs",
        {
            "queue": "reports",
            "task_name": "generate-report",
            "payload": {
                "report_id": report_id,
                "format": "json",
                "delay_seconds": 0,
            },
            "max_attempts": 3,
        },
    )

    completed_job = wait_for_success(
        api_url,
        submitted_job["id"],
        args.timeout_seconds,
    )

    result = completed_job.get("result")

    if not isinstance(result, dict) or result.get("generated") is not True:
        raise RuntimeError(f"Unexpected job result: {completed_job}")

    api_metrics = request_text(f"{api_url}/metrics")
    worker_metrics = request_text(f"{worker_url}/metrics")

    if "job_system_jobs_submitted_total" not in api_metrics:
        raise RuntimeError("API submission metric was not exposed")

    required_worker_metrics = (
        "job_system_jobs_claimed_total",
        'job_system_job_transitions_total{status="succeeded"}',
        "job_system_job_processing_seconds_count",
    )

    for metric in required_worker_metrics:
        if metric not in worker_metrics:
            raise RuntimeError(f"Worker metric was not exposed: {metric}")

    print(
        "Smoke test passed:",
        completed_job["id"],
        completed_job["status"],
    )


if __name__ == "__main__":
    main()
