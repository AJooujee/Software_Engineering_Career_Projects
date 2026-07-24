# 4. `requirements/software_requirements.md`

```markdown
# Software Requirements Specification

## 1. Purpose

The system receives simulated real-time sensor data, validates incoming
messages, detects faults, maintains a fault-tolerant operating state,
and records important events.

## 2. Functional Requirements

### REQ-NET-001 — TCP Server

The system shall create a TCP server on port 5050.

### REQ-NET-002 — Simulator Connection

The system shall accept a connection from the Python sensor simulator.

### REQ-NET-003 — Reconnection

The system shall return to a waiting state after the simulator
disconnects.

### REQ-MSG-001 — JSON Messages

The simulator shall send sensor readings as newline-delimited JSON.

### REQ-MSG-002 — Required Fields

The system shall require:

- sensor ID
- sensor type
- timestamp
- value
- unit
- sequence number

### REQ-MSG-003 — Invalid Message Handling

The system shall reject malformed or incomplete messages without
terminating the server.

### REQ-SEN-001 — Sensor Types

The simulator shall generate:

- Temperature
- Voltage
- Position
- Motion

### REQ-SEN-002 — Sequence Numbers

Every generated message shall contain an increasing sequence number.

### REQ-FLT-001 — Temperature Warning

The system shall produce a warning when temperature is outside the
normal operating range.

### REQ-FLT-002 — Temperature Critical

The system shall produce a critical fault when temperature exceeds the
critical safety range.

### REQ-FLT-003 — Voltage Warning

The system shall produce a warning when voltage is outside the normal
operating range.

### REQ-FLT-004 — Voltage Critical

The system shall produce a critical fault when voltage exceeds the
critical safety range.

### REQ-FLT-005 — Position Validation

The system shall detect position values outside the permitted boundary.

### REQ-FLT-006 — Motion Validation

The system shall accept only motion values 0 and 1.

### REQ-FLT-007 — Unknown Sensor Type

The system shall reject unsupported sensor types.

### REQ-TIME-001 — Sensor Timeout

The system shall detect when an expected sensor does not provide an
update within two seconds.

### REQ-STATE-001 — Normal State

The system shall remain in `NORMAL` when no faults are active.

### REQ-STATE-002 — Degraded State

The system shall enter `DEGRADED` when one warning-level fault is active.

### REQ-STATE-003 — Safe Mode from Critical Fault

The system shall enter `SAFE_MODE` when one critical fault is active.

### REQ-STATE-004 — Safe Mode from Multiple Faults

The system shall enter `SAFE_MODE` when at least two faults are active.

### REQ-STATE-005 — Fault Recovery

The system shall update its operating state when an active fault clears.

### REQ-LOG-001 — Startup Event

The system shall record a startup event.

### REQ-LOG-002 — Connection Events

The system shall record simulator connection and disconnection events.

### REQ-LOG-003 — Fault Events

The system shall record detected faults with a timestamp, severity,
fault type, and description.

### REQ-LOG-004 — State Transitions

The system shall record operating-state transitions.

### REQ-TEST-001 — Unit Tests

The project shall include automated unit tests for fault detection,
message parsing, and system-state management.

### REQ-TEST-002 — Integration Tests

The project shall include automated end-to-end tests for normal,
warning, critical, multiple-fault, invalid-motion, and timeout scenarios.

## 3. Nonfunctional Requirements

### REQ-NFR-001 — C++ Standard

The C++ application shall use C++17 or newer.

### REQ-NFR-002 — Cross-Platform Networking

The networking layer shall support Windows and POSIX socket APIs.

### REQ-NFR-003 — Build System

The project shall use CMake.

### REQ-NFR-004 — Fault Isolation

An invalid sensor message shall not terminate the monitoring server.

### REQ-NFR-005 — Repeatable Testing

Unit and integration tests shall be executable through documented
commands.