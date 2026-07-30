# Import hashlib for SHA-256 hashing.
import hashlib

# Import hmac to sign integration-test commands.
import hmac

# Import json to serialize commands and parse acknowledgements.
import json

# Import os to configure the Java server environment.
import os

# Import socket for TCP communication and server-readiness checks.
import socket

# Import subprocess to start and stop the Java server automatically.
import subprocess

# Import sys for platform-specific process handling and exit codes.
import sys

# Import time for connection retries and short test delays.
import time

# Import datetime utilities for normal, expired, and future timestamps.
from datetime import datetime, timedelta, timezone

# Import Path for reliable project-relative file paths.
from pathlib import Path

# Import Any for acknowledgement dictionaries.
from typing import Any


# Resolve the project root from tests/integration/run_scenarios.py.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Java server location.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6060

# Remote unit used throughout the integration tests.
TARGET_ID = "UNIT-01"

# Test-only shared secret used by both Python and Java.
# This is not a production credential.
TEST_SHARED_SECRET = "Integration-Test-Secret-2026"

# The server will intentionally drop the first ACK for this message.
ACK_DROP_MESSAGE_ID = "CMD-ACK-0001"

# Maximum time allowed for the Java server to start.
SERVER_START_TIMEOUT_SECONDS = 30.0

# Maximum time to wait for one acknowledgement.
ACK_TIMEOUT_SECONDS = 3.0


class IntegrationTestFailure(Exception):
    """
    Raised when an integration scenario produces an unexpected result.
    """


def utc_timestamp(
    offset_seconds: int = 0,
) -> str:
    """
    Create a Java-compatible ISO-8601 UTC timestamp.

    Negative offsets generate expired messages.
    Positive offsets generate future-dated messages.
    """

    timestamp = (
        datetime.now(timezone.utc)
        + timedelta(seconds=offset_seconds)
    )

    return timestamp.isoformat().replace(
        "+00:00",
        "Z",
    )


def create_canonical_message(
    command: dict[str, Any],
) -> str:
    """
    Create the exact message representation signed by Java and Python.

    The signature itself is intentionally excluded.
    """

    # Sort payload keys so both languages serialize payloads identically.
    payload_json = json.dumps(
        command["payload"],
        sort_keys=True,
        separators=(",", ":"),
    )

    return "\n".join(
        [
            command["message_id"],
            command["command_type"],
            command["target_id"],
            str(command["sequence_number"]),
            command["timestamp"],
            payload_json,
        ]
    )


def calculate_signature(
    command: dict[str, Any],
) -> str:
    """
    Calculate the lowercase hexadecimal HMAC-SHA256 signature.
    """

    canonical_message = create_canonical_message(
        command
    )

    return hmac.new(
        TEST_SHARED_SECRET.encode("utf-8"),
        canonical_message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_command(
    message_id: str,
    command_type: str,
    sequence_number: int,
    payload: dict[str, Any] | None = None,
    timestamp_offset_seconds: int = 0,
    tamper_signature: bool = False,
) -> dict[str, Any]:
    """
    Create one authenticated integration-test command.
    """

    command: dict[str, Any] = {
        "message_id": message_id,
        "command_type": command_type,
        "target_id": TARGET_ID,
        "sequence_number": sequence_number,
        "timestamp": utc_timestamp(
            timestamp_offset_seconds
        ),
        "payload": payload or {},
    }

    signature = calculate_signature(
        command
    )

    # Replace the valid signature to test authentication rejection.
    if tamper_signature:
        signature = "0" * 64

    command["signature"] = signature

    return command


def wait_for_server() -> None:
    """
    Wait until the Java TCP server accepts connections.
    """

    deadline = (
        time.monotonic()
        + SERVER_START_TIMEOUT_SECONDS
    )

    while time.monotonic() < deadline:
        try:
            # Open a temporary connection only to verify readiness.
            with socket.create_connection(
                (SERVER_HOST, SERVER_PORT),
                timeout=1.0,
            ):
                return
        except OSError:
            time.sleep(0.25)

    raise IntegrationTestFailure(
        "Java server did not start within "
        f"{SERVER_START_TIMEOUT_SECONDS} seconds."
    )


def send_raw_message(
    raw_message: str,
    expect_ack: bool = True,
) -> dict[str, Any] | None:
    """
    Send one raw newline-delimited message to the Java server.
    """

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as client_socket:

        client_socket.settimeout(
            ACK_TIMEOUT_SECONDS
        )

        client_socket.connect(
            (SERVER_HOST, SERVER_PORT)
        )

        with client_socket.makefile(
            mode="rw",
            encoding="utf-8",
            newline="\n",
        ) as socket_file:

            socket_file.write(
                raw_message + "\n"
            )

            socket_file.flush()

            acknowledgement_line = (
                socket_file.readline()
            )

            if acknowledgement_line == "":
                if expect_ack:
                    raise ConnectionError(
                        "Connection closed before an ACK was received."
                    )

                return None

            return json.loads(
                acknowledgement_line
            )


def send_command(
    command: dict[str, Any],
    expect_ack: bool = True,
) -> dict[str, Any] | None:
    """
    Serialize and send one authenticated command.
    """

    command_json = json.dumps(
        command,
        separators=(",", ":"),
    )

    return send_raw_message(
        command_json,
        expect_ack=expect_ack,
    )


def require_ack(
    acknowledgement: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Ensure that a scenario received an acknowledgement.
    """

    if acknowledgement is None:
        raise IntegrationTestFailure(
            "Expected an acknowledgement but received none."
        )

    return acknowledgement


def assert_ack(
    acknowledgement: dict[str, Any] | None,
    expected_status: str,
    expected_previous_state: str,
    expected_current_state: str,
    expected_message_text: str | None = None,
) -> None:
    """
    Verify acknowledgement status, state transition, and message text.
    """

    acknowledgement = require_ack(
        acknowledgement
    )

    actual_status = acknowledgement.get(
        "status"
    )

    actual_previous_state = acknowledgement.get(
        "previousState"
    )

    actual_current_state = acknowledgement.get(
        "currentState"
    )

    if actual_status != expected_status:
        raise IntegrationTestFailure(
            f"Expected status {expected_status}, "
            f"but received {actual_status}."
        )

    if actual_previous_state != expected_previous_state:
        raise IntegrationTestFailure(
            f"Expected previous state {expected_previous_state}, "
            f"but received {actual_previous_state}."
        )

    if actual_current_state != expected_current_state:
        raise IntegrationTestFailure(
            f"Expected current state {expected_current_state}, "
            f"but received {actual_current_state}."
        )

    if (
        expected_message_text is not None
        and expected_message_text
        not in acknowledgement.get("message", "")
    ):
        raise IntegrationTestFailure(
            "Expected acknowledgement message to contain "
            f"'{expected_message_text}', but received "
            f"'{acknowledgement.get('message')}'."
        )


def run_scenario(
    name: str,
    scenario_function,
) -> bool:
    """
    Run one scenario and display a readable PASS or FAIL result.
    """

    print(
        f"[RUN] Scenario: {name}"
    )

    try:
        scenario_function()

        print(
            f"[PASS] {name}\n"
        )

        return True

    except Exception as error:
        print(
            f"[FAIL] {name}"
        )

        print(
            f"       {error}\n"
        )

        return False


def scenario_normal_startup() -> None:
    """
    Verify OFFLINE -> STANDBY using a valid authenticated command.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0001",
            "START_SYSTEM",
            1,
        )
    )

    assert_ack(
        acknowledgement,
        "ACCEPTED",
        "OFFLINE",
        "STANDBY",
    )


def scenario_invalid_state_transition() -> None:
    """
    Verify that START_SYSTEM is rejected while already in STANDBY.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0002",
            "START_SYSTEM",
            2,
        )
    )

    assert_ack(
        acknowledgement,
        "REJECTED",
        "STANDBY",
        "STANDBY",
    )


def scenario_tampered_signature() -> None:
    """
    Verify that a command with an invalid HMAC is unauthorized.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0003",
            "ACTIVATE_SYSTEM",
            3,
            tamper_signature=True,
        )
    )

    assert_ack(
        acknowledgement,
        "UNAUTHORIZED",
        "STANDBY",
        "STANDBY",
        "signature verification failed",
    )


def scenario_valid_activation() -> None:
    """
    Verify STANDBY -> ACTIVE after the tampered command was rejected.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0004",
            "ACTIVATE_SYSTEM",
            3,
            payload={
                "operation": "PRIMARY_SENSOR_SCAN",
            },
        )
    )

    assert_ack(
        acknowledgement,
        "ACCEPTED",
        "STANDBY",
        "ACTIVE",
    )


def scenario_replayed_sequence() -> None:
    """
    Verify that a different command cannot reuse sequence number 3.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0005",
            "STOP_SYSTEM",
            3,
        )
    )

    assert_ack(
        acknowledgement,
        "SECURITY_REJECTED",
        "ACTIVE",
        "ACTIVE",
        "REPLAYED_SEQUENCE_NUMBER",
    )


def scenario_expired_timestamp() -> None:
    """
    Verify rejection of a command older than 30 seconds.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0006",
            "STOP_SYSTEM",
            4,
            timestamp_offset_seconds=-60,
        )
    )

    assert_ack(
        acknowledgement,
        "SECURITY_REJECTED",
        "ACTIVE",
        "ACTIVE",
        "EXPIRED_TIMESTAMP",
    )


def scenario_future_timestamp() -> None:
    """
    Verify rejection of a command too far in the future.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0007",
            "STOP_SYSTEM",
            4,
            timestamp_offset_seconds=60,
        )
    )

    assert_ack(
        acknowledgement,
        "SECURITY_REJECTED",
        "ACTIVE",
        "ACTIVE",
        "FUTURE_TIMESTAMP",
    )


def scenario_malformed_json() -> None:
    """
    Verify that malformed JSON returns INVALID without stopping the server.
    """

    acknowledgement = send_raw_message(
        '{"message_id":"BROKEN"'
    )

    acknowledgement = require_ack(
        acknowledgement
    )

    if acknowledgement.get("status") != "INVALID":
        raise IntegrationTestFailure(
            "Malformed JSON did not return INVALID."
        )

    if acknowledgement.get("currentState") != "ACTIVE":
        raise IntegrationTestFailure(
            "Malformed JSON unexpectedly changed the remote-unit state."
        )


def scenario_safe_mode_and_recovery() -> None:
    """
    Verify ACTIVE -> SAFE_MODE -> STANDBY.
    """

    safe_mode_ack = send_command(
        create_command(
            "CMD-IT-0008",
            "ENTER_SAFE_MODE",
            4,
        )
    )

    assert_ack(
        safe_mode_ack,
        "ACCEPTED",
        "ACTIVE",
        "SAFE_MODE",
    )

    reset_ack = send_command(
        create_command(
            "CMD-IT-0009",
            "RESET_SYSTEM",
            5,
        )
    )

    assert_ack(
        reset_ack,
        "ACCEPTED",
        "SAFE_MODE",
        "STANDBY",
    )


def scenario_shutdown() -> None:
    """
    Verify STANDBY -> OFFLINE.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0010",
            "SHUTDOWN_SYSTEM",
            6,
        )
    )

    assert_ack(
        acknowledgement,
        "ACCEPTED",
        "STANDBY",
        "OFFLINE",
    )


def scenario_ack_loss_and_retry() -> None:
    """
    Verify that an ACK-loss retry returns the cached result.

    The server is configured to drop the first ACK for this message.
    """

    command = create_command(
        ACK_DROP_MESSAGE_ID,
        "START_SYSTEM",
        7,
    )

    try:
        # The first send should be processed but its ACK should be dropped.
        send_command(
            command,
            expect_ack=False,
        )
    except (
        ConnectionError,
        socket.timeout,
    ):
        # A closed connection is expected during ACK-loss simulation.
        pass

    # Retry the exact authenticated command.
    retry_acknowledgement = send_command(
        command
    )

    assert_ack(
        retry_acknowledgement,
        "ACCEPTED",
        "OFFLINE",
        "STANDBY",
    )


def scenario_final_shutdown() -> None:
    """
    Return the remote unit to OFFLINE after the retry scenario.
    """

    acknowledgement = send_command(
        create_command(
            "CMD-IT-0011",
            "SHUTDOWN_SYSTEM",
            8,
        )
    )

    assert_ack(
        acknowledgement,
        "ACCEPTED",
        "STANDBY",
        "OFFLINE",
    )


def stop_server(
    server_process: subprocess.Popen,
) -> None:
    """
    Stop the Gradle process and its Java child process.
    """

    if server_process.poll() is not None:
        return

    if sys.platform == "win32":
        # Terminate the complete Windows process tree.
        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(server_process.pid),
                "/T",
                "/F",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        server_process.terminate()

        try:
            server_process.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            server_process.kill()


def main() -> int:
    """
    Start the Java server and execute all integration scenarios.
    """

    print(
        "=" * 72
    )

    print(
        "Secure Command-Control Integration and Regression Tests"
    )

    print(
        "=" * 72
    )

    logs_directory = (
        PROJECT_ROOT / "logs"
    )

    logs_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    server_log_path = (
        logs_directory
        / "integration_server.log"
    )

    environment = os.environ.copy()

    environment[
        "COMMAND_CONTROL_SHARED_SECRET"
    ] = TEST_SHARED_SECRET

    environment[
        "COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID"
    ] = ACK_DROP_MESSAGE_ID

    gradle_wrapper = (
        PROJECT_ROOT
        / (
            "gradlew.bat"
            if sys.platform == "win32"
            else "gradlew"
        )
    )

    creation_flags = (
        subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32"
        else 0
    )

    server_process: subprocess.Popen | None = None

    try:
        with server_log_path.open(
            mode="w",
            encoding="utf-8",
        ) as server_log:

            print(
                "[SETUP] Starting Java command server..."
            )

            server_process = subprocess.Popen(
                [
                    str(gradle_wrapper),
                    "run",
                ],
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=server_log,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creation_flags,
            )

            wait_for_server()

            print(
                "[SETUP] Java command server is ready.\n"
            )

            scenarios = [
                (
                    "normal-startup",
                    scenario_normal_startup,
                ),
                (
                    "invalid-state-transition",
                    scenario_invalid_state_transition,
                ),
                (
                    "tampered-signature",
                    scenario_tampered_signature,
                ),
                (
                    "valid-activation",
                    scenario_valid_activation,
                ),
                (
                    "replayed-sequence",
                    scenario_replayed_sequence,
                ),
                (
                    "expired-timestamp",
                    scenario_expired_timestamp,
                ),
                (
                    "future-timestamp",
                    scenario_future_timestamp,
                ),
                (
                    "malformed-json",
                    scenario_malformed_json,
                ),
                (
                    "safe-mode-and-recovery",
                    scenario_safe_mode_and_recovery,
                ),
                (
                    "shutdown",
                    scenario_shutdown,
                ),
                (
                    "ack-loss-and-idempotent-retry",
                    scenario_ack_loss_and_retry,
                ),
                (
                    "final-shutdown",
                    scenario_final_shutdown,
                ),
            ]

            passed_count = 0

            for scenario_name, scenario_function in scenarios:
                if run_scenario(
                    scenario_name,
                    scenario_function,
                ):
                    passed_count += 1

            total_count = len(
                scenarios
            )

            failed_count = (
                total_count
                - passed_count
            )

            print(
                "=" * 72
            )

            print(
                "Integration Test Summary"
            )

            print(
                "=" * 72
            )

            print(
                f"Passed: {passed_count}"
            )

            print(
                f"Failed: {failed_count}"
            )

            print(
                f"Total:  {total_count}"
            )

            if failed_count == 0:
                print(
                    "All integration and regression scenarios passed."
                )

                return 0

            print(
                "One or more integration scenarios failed."
            )

            print(
                f"Review server output at: {server_log_path}"
            )

            return 1

    except Exception as error:
        print(
            f"[SETUP FAILURE] {error}"
        )

        print(
            f"Review server output at: {server_log_path}"
        )

        return 1

    finally:
        if server_process is not None:
            print(
                "\n[TEARDOWN] Stopping Java command server..."
            )

            stop_server(
                server_process
            )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )