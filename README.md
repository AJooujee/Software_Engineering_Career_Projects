
# Real-Time Multi-Sensor Monitoring and Fault-Tolerant System

A real-time software system that receives simulated temperature, voltage,
position, and motion sensor data over TCP/IP, validates incoming JSON
messages, detects abnormal operating conditions, records system events,
and transitions between fault-tolerant operating states.

The project demonstrates practical experience with C++, Python, TCP/IP,
object-oriented design, requirements-based development, software
integration, fault injection, automated testing, and structured logging.

## Project Status

**Completed**

Current validation results:

- 21 unit tests passed
- 6 end-to-end integration and regression scenarios passed
- 0 test failures

## Technologies

- C++17
- Python 3
- TCP/IP
- Windows Sockets
- CMake
- GoogleTest
- CTest
- nlohmann/json
- Microsoft Visual C++
- Git and GitHub

## Core Features

- Simulates four independent sensor types:
  - Temperature
  - Voltage
  - Position
  - Motion
- Sends newline-delimited JSON messages over TCP/IP
- Parses and validates sensor messages in C++
- Detects warning-level and critical faults
- Detects missing sensor updates
- Tracks multiple simultaneous faults
- Supports sensor recovery
- Maintains deterministic system states
- Writes timestamped system events to a structured log
- Accepts new simulator connections after a disconnect
- Includes automated unit, integration, and regression tests

## System States

The monitoring application uses three operating states:

| State | Meaning |
|---|---|
| `NORMAL` | No active sensor faults |
| `DEGRADED` | One warning-level fault is active |
| `SAFE_MODE` | A critical fault or two simultaneous faults are active |

## Architecture

```text
Python Sensor Simulator
        |
        | Newline-delimited JSON over TCP/IP
        v
C++ TCP Receiver
        |
        v
Sensor Message Parser
        |
        v
Fault Detector
        |
        v
System State Manager
       / \
      /   \
     v     v
Console   Event Logger
Output    system_events.log
```

Detailed architecture documentation is available in:

```text
docs/architecture.md
```

## Sensor Message Format

Example temperature reading:

```json
{
  "sensor_id": "TEMP-01",
  "sensor_type": "TEMPERATURE",
  "timestamp": "2026-07-23T20:00:31.293250+00:00",
  "value": 75.77,
  "unit": "F",
  "sequence_number": 65
}
```

Each message must contain:

- `sensor_id`
- `sensor_type`
- `timestamp`
- `value`
- `unit`
- `sequence_number`

Messages with missing or invalid fields are rejected without terminating
the C++ server.

## Fault Rules

### Temperature

| Condition | Result |
|---|---|
| 65°F to 85°F | Normal |
| Below 65°F or above 85°F | Warning |
| Below 32°F or above 120°F | Critical |

### Voltage

| Condition | Result |
|---|---|
| 11.5 V to 12.8 V | Normal |
| Below 11.5 V or above 12.8 V | Warning |
| Below 10.0 V or above 14.5 V | Critical |

### Position

| Condition | Result |
|---|---|
| 0 to 100 units | Normal |
| Outside 0 to 100 units | Warning |

### Motion

| Condition | Result |
|---|---|
| 0 or 1 | Normal |
| Any other value | Warning |

### Sensor Timeout

A sensor is considered unavailable when it fails to provide an update
within two seconds.

A timeout is classified as a critical fault and causes the system to
enter `SAFE_MODE`.

## Project Structure

```text
real-time-sensor-monitoring-system/
├── .vscode/
│   └── settings.json
├── docs/
│   ├── architecture.md
│   └── test_plan.md
├── include/
│   └── system/
│       ├── EventLogger.hpp
│       ├── Fault.hpp
│       ├── FaultDetector.hpp
│       ├── SensorMessageParser.hpp
│       ├── SensorReading.hpp
│       └── SystemStateManager.hpp
├── logs/
│   └── system_events.log
├── requirements/
│   ├── software_requirements.md
│   └── traceability_matrix.md
├── simulator/
│   └── sensor_simulator.py
├── src/
│   ├── EventLogger.cpp
│   ├── FaultDetector.cpp
│   ├── main.cpp
│   ├── SensorMessageParser.cpp
│   └── SystemStateManager.cpp
├── tests/
│   ├── integration/
│   │   └── run_scenarios.py
│   └── unit/
│       ├── FaultDetectorTests.cpp
│       ├── SensorMessageParserTests.cpp
│       └── SystemStateManagerTests.cpp
├── .gitignore
├── CMakeLists.txt
└── README.md
```

## Build Instructions

### Prerequisites

Install:

- Visual Studio with Desktop Development with C++
- CMake
- Python 3
- Git

Open Developer PowerShell for Visual Studio and enter the project:

```powershell
cd C:\Dev\Software_Engineering_Career_Projects\real-time-sensor-monitoring-system
```

Configure the project:

```powershell
cmake -S . -B build -A x64
```

Build:

```powershell
cmake --build build --config Debug
```

CMake automatically retrieves:

- nlohmann/json
- GoogleTest

## Run the Monitoring System

Start the C++ server first:

```powershell
.\build\Debug\sensor_monitor.exe
```

Expected startup output:

```text
Real-Time Multi-Sensor Monitoring System
System status: STARTUP
TCP server listening on port 5050.
Waiting for Python simulator...
```

Open a second terminal and run the simulator:

```powershell
python .\simulator\sensor_simulator.py --scenario normal
```

## Fault-Injection Scenarios

View all options:

```powershell
python .\simulator\sensor_simulator.py --help
```

Available scenarios:

```text
normal
temperature-warning
temperature-critical
voltage-warning
voltage-critical
multiple-faults
invalid-motion
sensor-timeout
```

Examples:

```powershell
python .\simulator\sensor_simulator.py --scenario temperature-warning
```

```powershell
python .\simulator\sensor_simulator.py --scenario multiple-faults
```

```powershell
python .\simulator\sensor_simulator.py --scenario sensor-timeout
```

## Unit Tests

Run all tests through CTest:

```powershell
ctest --test-dir build -C Debug --output-on-failure
```

Current result:

```text
100% tests passed, 0 tests failed out of 21
```

Run the test executable directly:

```powershell
.\build\Debug\sensor_tests.exe
```

The unit tests cover:

- Temperature fault detection
- Voltage fault detection
- Position validation
- Motion validation
- Unknown sensor types
- JSON parsing
- Missing JSON fields
- Invalid JSON field types
- Normal system state
- Degraded system state
- Safe mode
- Multiple faults
- Fault recovery

## Integration and Regression Tests

Run the end-to-end test suite:

```powershell
python .\tests\integration\run_scenarios.py
```

Current result:

```text
Passed: 6
Failed: 0
Total: 6
All integration and regression scenarios passed.
```

The integration suite verifies:

- Normal operation
- Warning-level temperature fault
- Critical temperature fault
- Multiple simultaneous faults
- Invalid motion value
- Sensor timeout

[PASS] normal
[PASS] temperature-warning
[PASS] temperature-critical
[PASS] multiple-faults
[PASS] invalid-motion
[PASS] sensor-timeout

Passed: 6
Failed: 0
Total: 6

100% tests passed, 0 tests failed out of 21

## Event Logging

The application writes structured events to:

```text
logs/system_events.log
```

Example:

```text
2026-07-23 17:39:36 | INFO | SYSTEM_STARTUP | Sensor monitoring system started.
2026-07-23 17:42:17 | INFO | CLIENT_CONNECTED | Python sensor simulator connected.
2026-07-23 17:42:21 | CRITICAL | SENSOR_TIMEOUT | TEMP-01 failed to provide an update within two seconds.
```

Runtime logs are excluded from Git through `.gitignore`.

## Requirements Traceability

Software requirements and their associated tests are documented in:

```text
requirements/software_requirements.md
requirements/traceability_matrix.md
```

## Skills Demonstrated

- C++ software development
- Python scripting
- Object-oriented analysis and design
- TCP/IP socket programming
- JSON message processing
- Software integration
- Fault-tolerant state management
- Error handling
- Requirements-based testing
- Unit testing
- Integration testing
- Regression testing
- CMake build configuration
- Structured event logging
- Git version control

## Run Program (run Developer Powershell VS)
1. check the version
cmake --version
cl

2. running unit test
cmake --build build --config Debug

ctest --test-dir build -C Debug --output-on-failure

3. running integration scenarios
python .\tests\integration\run_scenarios.py