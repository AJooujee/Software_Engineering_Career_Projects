# Software Requirements Specification

## 1. Scope

This document defines the implemented requirements for the Secure Command-and-Control Message Processing Simulator.

## 2. Functional Requirements

### FR-001 — TCP Server

The system shall listen for TCP connections on configurable port `6060` by default.

### FR-002 — Newline-Delimited JSON

The system shall receive one UTF-8 JSON command per line and return one JSON acknowledgement per line.

### FR-003 — Required Command Fields

The system shall require:

- `message_id`
- `command_type`
- `target_id`
- `sequence_number`
- `timestamp`
- `signature`

The `payload` field shall be optional and treated as an empty object when absent.

### FR-004 — Unknown Fields

The system shall reject unsupported top-level JSON fields.

### FR-005 — Command Types

The system shall support:

- `START_SYSTEM`
- `ACTIVATE_SYSTEM`
- `STOP_SYSTEM`
- `ENTER_SAFE_MODE`
- `RESET_SYSTEM`
- `SHUTDOWN_SYSTEM`

### FR-006 — Initial State

The remote unit shall begin in `OFFLINE`.

### FR-007 — State Transitions

The system shall apply deterministic state-transition rules and reject invalid transitions without changing state.

### FR-008 — Acknowledgements

The system shall return an acknowledgement containing:

- message ID
- status
- command type
- previous state
- current state
- human-readable message
- processing timestamp

### FR-009 — Authentication

The system shall verify every structurally valid command using HMAC-SHA256 before state-machine processing.

### FR-010 — Shared Secret Configuration

The system shall load the shared secret from `COMMAND_CONTROL_SHARED_SECRET`.

### FR-011 — Authentication Failure

The system shall return `UNAUTHORIZED` when signature verification fails and shall not change state.

### FR-012 — Duplicate Message Detection

The system shall reject a previously processed message ID unless the message is an identical idempotent retry with a cached acknowledgement.

### FR-013 — Sequence Replay Protection

The system shall require sequence numbers to increase independently for each target ID.

### FR-014 — Timestamp Expiration

The system shall reject commands older than 30 seconds.

### FR-015 — Future Timestamp Tolerance

The system shall reject commands more than 5 seconds in the future.

### FR-016 — Retry Cache

The system shall cache completed acknowledgements before attempting to transmit them.

### FR-017 — Idempotent Retry

The system shall return a cached acknowledgement for an identical authenticated retry without executing the command again.

### FR-018 — Message ID Collision

The system shall reject reuse of a cached message ID with different authenticated content.

### FR-019 — Client Retry

The Python control station shall retry a command when no valid acknowledgement is received.

### FR-020 — Retry Limits

The client shall use a finite timeout and finite retry count.

### FR-021 — Audit Logging

The system shall record structured JSON audit events for startup, connections, authentication, security validation, command processing, acknowledgements, retries, and failures.

### FR-022 — Persistent Log File

The audit logger shall append events to `logs/command_audit.log`.

### FR-023 — Invalid Input Resilience

Malformed or invalid commands shall not terminate the server.

### FR-024 — Repeated Connections

The server shall continue accepting clients after a client disconnects.

### FR-025 — Docker Deployment

The system shall support building and running the Java server through Docker Compose.

### FR-026 — Host-to-Container Communication

The host Python client shall communicate with the containerized server through published port `6060`.

## 3. Nonfunctional Requirements

### NFR-001 — Java Version

The Java application shall target Java 21.

### NFR-002 — Reproducible Build

The repository shall include the Gradle Wrapper.

### NFR-003 — Unit Testing

The project shall include JUnit 5 unit tests for the core components.

### NFR-004 — Integration Testing

The project shall include automated end-to-end integration and regression scenarios.

### NFR-005 — Security Secret Handling

Secrets shall not be committed to Git or embedded in the Docker image.

### NFR-006 — Constant-Time Comparison

HMAC verification shall use constant-time byte comparison.

### NFR-007 — Immutability

Command and acknowledgement domain models shall be immutable after construction.

### NFR-008 — Thread Safety

Mutable state, replay tracking, cache access, and log writes shall use synchronized access where required.

### NFR-009 — Structured Logs

Each audit event shall be serialized as one compact JSON line.

### NFR-010 — Container Least Privilege

The production container shall run the Java process as a non-root user.

### NFR-011 — Multi-Stage Image

Docker shall use a separate build stage and runtime stage.

### NFR-012 — Documentation

The repository shall document setup, execution, expected results, tests, Docker deployment, architecture, requirements, and limitations.

## 4. Interface Requirements

### 4.1 Network Interface

- protocol: TCP
- host for local client: `127.0.0.1`
- default port: `6060`
- encoding: UTF-8
- framing: one JSON object per line

### 4.2 Environment Variables

| Name | Required | Purpose |
|---|---|---|
| `COMMAND_CONTROL_SHARED_SECRET` | Yes | HMAC shared secret |
| `COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID` | No | Development ACK-loss simulation |

### 4.3 Log Interface

- format: newline-delimited JSON
- default path: `logs/command_audit.log`

## 5. Verification Targets

- 32 JUnit tests pass
- 12 integration scenarios pass
- Gradle clean build succeeds
- local Python/Java TCP test succeeds
- Docker build succeeds
- host Python client communicates with Docker server
- audit events are written
- final demonstrated state is `OFFLINE`
