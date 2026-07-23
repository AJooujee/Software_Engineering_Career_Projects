# Import os to access operating-system-specific process options.
import os

# Import subprocess to start the C++ server and Python simulator.
import subprocess

# Import sys to use the current Python interpreter and return exit codes.
import sys

# Import time to control scenario execution duration.
import time

# Import dataclass to represent each integration-test scenario.
from dataclasses import dataclass

# Import Path to build reliable project-relative file paths.
from pathlib import Path


@dataclass(frozen=True)
class IntegrationScenario:
    """
    Describe one end-to-end integration-test scenario.
    """

    # Name passed to sensor_simulator.py through --scenario.
    name: str

    # Text fragments that must appear in the C++ server output.
    expected_output: tuple[str, ...]

    # Number of seconds to allow the scenario to run.
    duration_seconds: float


# Locate the project root from:
# tests/integration/run_scenarios.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Locate the Python sensor simulator.
SIMULATOR_PATH = (
    PROJECT_ROOT
    / "simulator"
    / "sensor_simulator.py"
)

# Select the expected C++ executable location for each operating system.
if os.name == "nt":
    SERVER_EXECUTABLE = (
        PROJECT_ROOT
        / "build"
        / "Debug"
        / "sensor_monitor.exe"
    )
else:
    SERVER_EXECUTABLE = (
        PROJECT_ROOT
        / "build"
        / "sensor_monitor"
    )


# Define the end-to-end regression scenarios.
SCENARIOS = (
    IntegrationScenario(
        name="normal",
        expected_output=(
            "[STATUS] Reading accepted.",
            "[SYSTEM] State: NORMAL",
            "Active faults: 0",
        ),
        duration_seconds=3.0,
    ),
    IntegrationScenario(
        name="temperature-warning",
        expected_output=(
            "TEMPERATURE_OUT_OF_RANGE",
            "[SYSTEM] State: DEGRADED",
            "Active faults: 1",
        ),
        duration_seconds=3.0,
    ),
    IntegrationScenario(
        name="temperature-critical",
        expected_output=(
            "CRITICAL_TEMPERATURE",
            "[SYSTEM] State: SAFE_MODE",
            "Active faults: 1",
        ),
        duration_seconds=3.0,
    ),
    IntegrationScenario(
        name="multiple-faults",
        expected_output=(
            "TEMPERATURE_OUT_OF_RANGE",
            "VOLTAGE_OUT_OF_RANGE",
            "[SYSTEM] State: SAFE_MODE",
            "Active faults: 2",
        ),
        duration_seconds=3.0,
    ),
    IntegrationScenario(
        name="invalid-motion",
        expected_output=(
            "INVALID_MOTION_STATE",
            "[SYSTEM] State: DEGRADED",
            "Active faults: 1",
        ),
        duration_seconds=3.0,
    ),
    IntegrationScenario(
        name="sensor-timeout",
        expected_output=(
            "SENSOR_TIMEOUT",
            "TEMP-01 failed to provide an update within two seconds.",
            "[SYSTEM] State: SAFE_MODE",
            "Active faults: 1",
        ),
        # TEMP-01 sends for three cycles and then stops.
        # Allow enough time for the two-second timeout to be detected.
        duration_seconds=7.0,
    ),
)


def stop_process(
    process: subprocess.Popen[str],
) -> str:
    """
    Stop a child process and return all captured output.
    """

    # Stop the process when it is still running.
    if process.poll() is None:
        process.terminate()

    try:
        # Collect output after requesting a normal termination.
        output, _ = process.communicate(
            timeout=3.0,
        )
    except subprocess.TimeoutExpired:
        # Forcefully stop the process if it does not terminate.
        process.kill()

        output, _ = process.communicate()

    return output or ""


def validate_project_files() -> None:
    """
    Verify that required application files exist before testing.
    """

    missing_files = []

    if not SERVER_EXECUTABLE.exists():
        missing_files.append(
            str(SERVER_EXECUTABLE)
        )

    if not SIMULATOR_PATH.exists():
        missing_files.append(
            str(SIMULATOR_PATH)
        )

    if missing_files:
        missing_list = "\n".join(
            f"  - {file_path}"
            for file_path in missing_files
        )

        raise FileNotFoundError(
            "Required files were not found:\n"
            f"{missing_list}\n\n"
            "Build the C++ project before running integration tests."
        )


def run_scenario(
    scenario: IntegrationScenario,
) -> tuple[bool, str]:
    """
    Run one C++ server and Python simulator scenario.

    A new server is created for every scenario so that system-state
    information from one test cannot affect another test.
    """

    print(
        f"\n[RUN] Scenario: {scenario.name}"
    )

    server_process: subprocess.Popen[str] | None = None
    simulator_process: subprocess.Popen[str] | None = None

    try:
        # Start the C++ monitoring server.
        server_process = subprocess.Popen(
            [str(SERVER_EXECUTABLE)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Allow the server time to bind to TCP port 5050.
        time.sleep(1.0)

        # Stop immediately when the server failed during startup.
        if server_process.poll() is not None:
            server_output = stop_process(
                server_process
            )

            return (
                False,
                "The C++ server exited before the simulator started.\n"
                f"{server_output}",
            )

        # Start Python in unbuffered mode so output is available promptly.
        simulator_process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(SIMULATOR_PATH),
                "--scenario",
                scenario.name,
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Allow the selected scenario to generate and transmit data.
        time.sleep(
            scenario.duration_seconds
        )

        # Stop the simulator first so the server sees a disconnect.
        simulator_output = stop_process(
            simulator_process
        )

        # Allow the server to process the final network messages.
        time.sleep(0.5)

        server_output = stop_process(
            server_process
        )

        # Identify every expected text fragment that was not observed.
        missing_output = [
            expected_text
            for expected_text in scenario.expected_output
            if expected_text not in server_output
        ]

        if missing_output:
            missing_text = "\n".join(
                f"  - {expected_text}"
                for expected_text in missing_output
            )

            failure_report = (
                f"Missing expected server output:\n"
                f"{missing_text}\n\n"
                "----- C++ SERVER OUTPUT -----\n"
                f"{server_output}\n"
                "----- PYTHON SIMULATOR OUTPUT -----\n"
                f"{simulator_output}"
            )

            return False, failure_report

        return True, server_output

    finally:
        # Ensure no child process remains running after a failed test.
        if simulator_process is not None:
            if simulator_process.poll() is None:
                stop_process(
                    simulator_process
                )

        if server_process is not None:
            if server_process.poll() is None:
                stop_process(
                    server_process
                )


def main() -> int:
    """
    Run all integration and regression scenarios.

    Returns:
        0 when every scenario passes.
        1 when at least one scenario fails.
    """

    print(
        "============================================================"
    )
    print(
        "Real-Time Sensor Monitoring Integration Tests"
    )
    print(
        "============================================================"
    )

    try:
        validate_project_files()
    except FileNotFoundError as error:
        print(
            f"\n[SETUP ERROR]\n{error}"
        )

        return 1

    passed_count = 0
    failed_scenarios = []

    for scenario in SCENARIOS:
        try:
            passed, details = run_scenario(
                scenario
            )
        except Exception as error:
            passed = False
            details = (
                f"Unexpected integration-test error: {error}"
            )

        if passed:
            passed_count += 1

            print(
                f"[PASS] {scenario.name}"
            )
        else:
            failed_scenarios.append(
                scenario.name
            )

            print(
                f"[FAIL] {scenario.name}"
            )
            print(details)

    total_count = len(SCENARIOS)
    failed_count = total_count - passed_count

    print(
        "\n============================================================"
    )
    print(
        "Integration Test Summary"
    )
    print(
        "============================================================"
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

    if failed_scenarios:
        print(
            "Failed scenarios: "
            + ", ".join(failed_scenarios)
        )

        return 1

    print(
        "All integration and regression scenarios passed."
    )

    return 0


# Return the correct process exit code to PowerShell or CI.
if __name__ == "__main__":
    raise SystemExit(main())