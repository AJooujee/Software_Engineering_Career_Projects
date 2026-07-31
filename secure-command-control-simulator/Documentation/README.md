# Secure Command-and-Control Message Processing Simulator

A portfolio-grade Java and Python system that simulates secure command delivery from a control station to a remote unit over TCP/IP.

The project demonstrates command validation, deterministic state transitions, HMAC-SHA256 authentication, replay protection, duplicate detection, acknowledgement retry, idempotent processing, structured audit logging, automated tests, and Docker deployment.

## Project Status

| Verification area | Result |
|---|---:|
| Gradle build | Passed |
| Unit tests | 32 passed, 0 failed |
| Integration and regression scenarios | 12 passed, 0 failed |
| Local Java/Python TCP test | Passed |
| HMAC-SHA256 authentication | Passed |
| Replay and timestamp protection | Passed |
| ACK timeout and idempotent retry | Passed |
| Structured JSON audit logging | Passed |
| Docker image build | Passed |
| Host Python client to Docker server | Passed |
| Final demonstrated system state | OFFLINE |

## Main Features

- Java 21 remote-unit TCP server
- Python control-station client
- Newline-delimited JSON messaging over TCP port `6060`
- Immutable command and acknowledgement models
- Deterministic remote-unit state machine
- HMAC-SHA256 message authentication
- Constant-time signature comparison
- Duplicate message ID detection
- Per-target sequence-number replay protection
- Expired and future timestamp rejection
- ACK timeout and automatic retry
- Idempotent retries using cached acknowledgements
- Structured newline-delimited JSON audit logs
- JUnit 5 unit tests
- End-to-end Python integration and regression tests
- Multi-stage Docker build and Docker Compose deployment
- Non-root container runtime

## Technology Stack

- Java 21
- Gradle Wrapper 9.6.1
- Jackson Databind
- JUnit Jupiter
- Python 3.12+
- TCP/IP sockets
- HMAC-SHA256
- Docker and Docker Compose
- PowerShell on Windows

## System Architecture

```text
Python Control Station
        |
        | Signed JSON command over TCP/IP
        v
Java Command Server
        |
        +--> JSON parsing and structural validation
        |
        +--> HMAC-SHA256 authentication
        |
        +--> Timestamp, duplicate, and replay protection
        |
        +--> Idempotent retry / acknowledgement cache
        |
        +--> Remote-unit state machine
        |
        +--> Structured JSON audit logger
        |
        v
JSON acknowledgement returned to Python
```

Detailed architecture information is available in [`docs/architecture.md`](docs/architecture.md).

## Supported Commands

| Command | Required current state | Resulting state |
|---|---|---|
| `START_SYSTEM` | `OFFLINE` | `STANDBY` |
| `ACTIVATE_SYSTEM` | `STANDBY` | `ACTIVE` |
| `STOP_SYSTEM` | `ACTIVE` | `STANDBY` |
| `ENTER_SAFE_MODE` | `STANDBY` or `ACTIVE` | `SAFE_MODE` |
| `RESET_SYSTEM` | `SAFE_MODE` | `STANDBY` |
| `SHUTDOWN_SYSTEM` | Any non-`OFFLINE` state | `OFFLINE` |

Invalid transitions are rejected without changing the current state.

## Command Message Format

```json
{
  "message_id": "CMD-000001",
  "command_type": "START_SYSTEM",
  "target_id": "UNIT-01",
  "sequence_number": 1,
  "timestamp": "2026-07-31T02:27:55.643309Z",
  "payload": {},
  "signature": "64-character-lowercase-hex-HMAC-SHA256"
}
```

## Acknowledgement Format

```json
{
  "messageId": "CMD-000001",
  "status": "ACCEPTED",
  "commandType": "START_SYSTEM",
  "previousState": "OFFLINE",
  "currentState": "STANDBY",
  "message": "Remote unit initialized and entered standby mode.",
  "processedAt": "2026-07-31T02:27:55.739619417Z"
}
```

Possible acknowledgement statuses:

- `ACCEPTED`
- `REJECTED`
- `INVALID`
- `UNAUTHORIZED`
- `SECURITY_REJECTED`

## Project Structure

```text
secure-command-control-simulator/
├── control_station/
│   └── control_station_client.py
├── docs/
│   ├── architecture.md
│   ├── test_plan.md
│   └── requirements/
│       ├── software_requirements.md
│       └── traceability_matrix.md
├── gradle/
│   └── wrapper/
├── logs/
├── src/
│   ├── main/java/com/aj/commandcontrol/
│   │   ├── logging/
│   │   ├── model/
│   │   ├── network/
│   │   ├── parsing/
│   │   ├── processing/
│   │   ├── security/
│   │   └── CommandControlApplication.java
│   └── test/java/com/aj/commandcontrol/
│       ├── logging/
│       ├── network/
│       ├── parsing/
│       ├── processing/
│       └── security/
├── tests/
│   └── integration/
│       └── run_scenarios.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── build.gradle
├── gradlew
├── gradlew.bat
└── settings.gradle
```

# Prerequisites

Install:

- Java 21 JDK
- Python 3.12 or newer
- Git
- Docker Desktop for Docker execution

Gradle does not need to be installed globally because the project includes the Gradle Wrapper.

Verify the environment:

```powershell
java --version
javac --version
python --version
git --version
docker --version
docker compose version
```

# Complete Local Verification

Run all commands from:

```powershell
cd C:\Dev\Software_Engineering_Career_Projects\secure-command-control-simulator
```

## 1. Build and Run Unit Tests

```powershell
.\gradlew.bat clean build
```

Expected result:

```text
BUILD SUCCESSFUL
32 tests completed
32 tests passed
0 tests failed
```

Run only tests:

```powershell
.\gradlew.bat clean test
```

Open the HTML test report:

```powershell
Start-Process .\build\reports\tests\test\index.html
```

Expected report summary:

```text
32 tests
0 failures
0 skipped
100% successful
```

## 2. Run the Java Server Locally

Open Terminal 1:

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "replace-with-a-secret-of-at-least-16-characters"

Remove-Item Env:COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID -ErrorAction SilentlyContinue

.\gradlew.bat run
```

Expected startup output:

```text
Secure Command-and-Control Message Processing Simulator
Remote unit state: OFFLINE
TCP command server listening on port 6060.
HMAC-SHA256 authentication enabled.
Replay and timestamp protection enabled.
ACK retry and idempotency support enabled.
Structured audit logging enabled: logs\command_audit.log
Maximum command age: 30 seconds.
Waiting for Python control station...
```

Leave Terminal 1 running.

## 3. Run the Python Control Station

Open Terminal 2 in the same project directory:

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "replace-with-the-same-secret"

python .\control_station\control_station_client.py
```

Expected state transitions:

```text
START_SYSTEM      OFFLINE -> STANDBY     ACCEPTED
ACTIVATE_SYSTEM   STANDBY -> ACTIVE      ACCEPTED
SHUTDOWN_SYSTEM   ACTIVE -> OFFLINE      ACCEPTED
```

Expected completion:

```text
Python control station stopped.
```

Stop the Java server with `Ctrl + C`.

## 4. Run Integration and Regression Tests

Confirm port `6060` is free:

```powershell
Get-NetTCPConnection -LocalPort 6060 -ErrorAction SilentlyContinue
```

No output means the port is available.

Run:

```powershell
python .\tests\integration\run_scenarios.py
```

Expected result:

```text
Passed: 12
Failed: 0
Total:  12
All integration and regression scenarios passed.
```

The integration runner automatically:

- starts the Java server
- configures a test shared secret
- runs all scenarios
- simulates one lost acknowledgement
- verifies idempotent retry behavior
- stops the Java server

Integration server output is written to:

```text
logs/integration_server.log
```

## 5. Verify Audit Logs

View recent events:

```powershell
Get-Content .\logs\command_audit.log -Tail 20
```

Search for idempotent retries:

```powershell
Select-String `
  -Path .\logs\command_audit.log `
  -Pattern "IDEMPOTENT_RETRY"
```

Search for security events:

```powershell
Select-String `
  -Path .\logs\command_audit.log `
  -Pattern '"level":"SECURITY"'
```

Audit logs are runtime artifacts and are intentionally excluded from Git.

# Docker Verification

## 1. Create Local Environment Configuration

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
COMMAND_CONTROL_SHARED_SECRET=replace-with-a-secret-of-at-least-16-characters
COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID=
```

The real `.env` file is ignored by Git. Do not commit secrets.

## 2. Build the Docker Image

```powershell
docker compose build
```

The multi-stage build compiles the Java application and runs the JUnit suite.

Expected result:

```text
Image secure-command-control-simulator-command-server Built
```

## 3. Start the Container

```powershell
docker compose up
```

Expected server output:

```text
TCP command server listening on port 6060.
HMAC-SHA256 authentication enabled.
Replay and timestamp protection enabled.
ACK retry and idempotency support enabled.
Structured audit logging enabled: logs/command_audit.log
Waiting for Python control station...
```

Leave this terminal running.

## 4. Connect from the Host Python Client

Open another terminal:

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "the-same-secret-used-in-.env"

python .\control_station\control_station_client.py
```

Expected result:

```text
CMD-000001  ACCEPTED  OFFLINE -> STANDBY
CMD-000002  ACCEPTED  STANDBY -> ACTIVE
CMD-000003  ACCEPTED  ACTIVE -> OFFLINE
```

## 5. Inspect and Stop Docker

```powershell
docker compose ps
docker compose logs command-server
Get-Content .\logs\command_audit.log -Tail 15
docker compose down
```

Expected shutdown:

```text
Container secure-command-control-server Removed
Network secure-command-control-simulator_default Removed
```

# Security Design

## HMAC Authentication

The Python control station and Java server share a secret through the environment variable:

```text
COMMAND_CONTROL_SHARED_SECRET
```

The secret is never transmitted over TCP.

Both applications construct the same canonical message from:

1. message ID
2. command type
3. target ID
4. sequence number
5. timestamp
6. canonical payload JSON

The signature is:

```text
HMAC-SHA256(shared secret, canonical message)
```

Java uses constant-time comparison through `MessageDigest.isEqual`.

## Replay Protection

A command is rejected when:

- its message ID has already been processed
- its sequence number is not greater than the highest accepted sequence for the target
- its timestamp is older than 30 seconds
- its timestamp is more than 5 seconds in the future

## Reliable Acknowledgements

The client retries when an ACK is lost or times out.

The server caches the original acknowledgement before attempting network delivery. An identical retry receives the cached ACK and does not execute the command again.

A reused message ID with different authenticated content is rejected as a message-ID collision.

# Automated Test Coverage

## Unit Tests

| Test class | Tests |
|---|---:|
| `AuditLoggerTests` | 3 |
| `AcknowledgementCacheTests` | 4 |
| `CommandMessageParserTests` | 8 |
| `CommandProcessorTests` | 8 |
| `MessageAuthenticatorTests` | 3 |
| `ReplayProtectionServiceTests` | 6 |
| **Total** | **32** |

## Integration and Regression Scenarios

1. normal startup
2. invalid state transition
3. tampered signature
4. valid activation after rejected tampering
5. replayed sequence number
6. expired timestamp
7. future timestamp
8. malformed JSON
9. safe mode and recovery
10. shutdown
11. ACK loss and idempotent retry
12. final shutdown

Result:

```text
12 passed
0 failed
```

# Complete Verification Checklist

The project is considered fully verified when every item below passes:

```text
[PASS] Gradle clean build
[PASS] 32 unit tests
[PASS] 12 integration and regression scenarios
[PASS] Local Java TCP server startup
[PASS] Python control-station connection
[PASS] JSON command parsing and validation
[PASS] Deterministic state transitions
[PASS] HMAC-SHA256 authentication
[PASS] Tampered-message rejection
[PASS] Duplicate message ID detection
[PASS] Sequence-number replay protection
[PASS] Expired timestamp rejection
[PASS] Future timestamp rejection
[PASS] ACK timeout and automatic retry
[PASS] Idempotent command handling
[PASS] Structured JSON audit logging
[PASS] Docker image build
[PASS] Host-to-container TCP communication
[PASS] Final system state returns to OFFLINE
```

# Known Limitations

- TCP traffic is authenticated but not encrypted. Production use would require TLS.
- Replay and acknowledgement caches are in memory and reset when the server restarts.
- The current server handles one client connection at a time.
- The shared-secret model does not currently support key rotation or multiple control stations.
- Audit log rotation and retention policies are not implemented.
- Command authorization is not separated by user or role.
- The simulator is not intended for real safety-critical or defense deployment.

# Future Improvements

- TLS mutual authentication
- Persistent replay store and acknowledgement cache
- Multi-client concurrency with a bounded executor
- Key identifiers and shared-secret rotation
- Role-based command authorization
- Metrics and health endpoints
- Log rotation and external log aggregation
- CI pipeline for Gradle and integration tests
- Container health checks
- Protocol versioning
- Protobuf transport option
- Static analysis and code coverage reports

# Documentation

- [Software Requirements](docs/requirements/software_requirements.md)
- [Architecture](docs/architecture.md)
- [Test Plan](docs/test_plan.md)
- [Requirements Traceability Matrix](docs/requirements/traceability_matrix.md)

## Final Demonstrated Result

```text
Unit tests:         32 passed, 0 failed
Integration tests: 12 passed, 0 failed
Local TCP test:     Passed
Security tests:     Passed
Docker test:       Passed
Audit logging:     Passed
Final system state: OFFLINE
```
