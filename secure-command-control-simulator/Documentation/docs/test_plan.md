# Test Plan

## 1. Objective

Verify that the simulator correctly handles command parsing, state transitions, authentication, replay protection, reliable acknowledgements, audit logging, TCP communication, and Docker deployment.

## 2. Test Levels

### 2.1 Unit Tests

JUnit 5 tests isolate individual Java components.

### 2.2 Integration and Regression Tests

A Python runner starts the Java server and verifies the complete network request path.

### 2.3 Manual Local System Test

The Java server and Python control station are started in separate terminals.

### 2.4 Docker System Test

The Java server runs in Docker while the Python client runs on the host.

## 3. Unit Test Suites

| Test class | Scope | Count |
|---|---|---:|
| `CommandProcessorTests` | state transitions and rejection behavior | 8 |
| `CommandMessageParserTests` | JSON parsing and structural validation | 8 |
| `MessageAuthenticatorTests` | HMAC verification and tampering | 3 |
| `ReplayProtectionServiceTests` | duplicate, sequence, and timestamp rules | 6 |
| `AcknowledgementCacheTests` | storage, signature match, immutability | 4 |
| `AuditLoggerTests` | file creation, append behavior, ACK fields | 3 |
| **Total** |  | **32** |

Run:

```powershell
.\gradlew.bat clean test
```

Pass criteria:

```text
32 tests passed
0 failed
```

## 4. Integration Scenarios

| ID | Scenario | Expected result |
|---|---|---|
| IT-001 | normal startup | `OFFLINE -> STANDBY`, accepted |
| IT-002 | invalid state transition | rejected, state unchanged |
| IT-003 | tampered signature | unauthorized, state unchanged |
| IT-004 | valid activation | `STANDBY -> ACTIVE`, accepted |
| IT-005 | replayed sequence | security rejected |
| IT-006 | expired timestamp | security rejected |
| IT-007 | future timestamp | security rejected |
| IT-008 | malformed JSON | invalid, server continues |
| IT-009 | safe mode and recovery | `ACTIVE -> SAFE_MODE -> STANDBY` |
| IT-010 | shutdown | `STANDBY -> OFFLINE` |
| IT-011 | ACK loss and retry | cached ACK returned, no duplicate execution |
| IT-012 | final shutdown | final state `OFFLINE` |

Run:

```powershell
python .\tests\integration\run_scenarios.py
```

Pass criteria:

```text
Passed: 12
Failed: 0
```

## 5. Local End-to-End Test

### Terminal 1

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "test-secret-at-least-16-characters"
.\gradlew.bat run
```

Expected:

```text
Waiting for Python control station...
```

### Terminal 2

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "test-secret-at-least-16-characters"
python .\control_station\control_station_client.py
```

Expected:

```text
OFFLINE -> STANDBY
STANDBY -> ACTIVE
ACTIVE -> OFFLINE
```

## 6. Docker Test

Build:

```powershell
docker compose build
```

Run:

```powershell
docker compose up
```

Connect from another terminal:

```powershell
$env:COMMAND_CONTROL_SHARED_SECRET = "same-secret-as-env-file"
python .\control_station\control_station_client.py
```

Inspect:

```powershell
docker compose logs command-server
Get-Content .\logs\command_audit.log -Tail 15
```

Stop:

```powershell
docker compose down
```

Pass criteria:

- image builds
- container remains running
- host client connects
- all three demonstration commands are accepted
- audit log is written
- final state is `OFFLINE`
- container and network are removed cleanly

## 7. Security Test Conditions

### Authentication

- valid HMAC accepted
- modified payload rejected
- different secret rejected
- deliberately invalid signature rejected

### Replay

- duplicate message ID rejected
- non-increasing sequence rejected
- same sequence allowed for a different target
- stale timestamp rejected
- excessive future timestamp rejected

### Reliability

- first ACK deliberately dropped
- client retries identical message
- server returns cached ACK
- command executes only once

## 8. Audit Verification

Search for retry evidence:

```powershell
Select-String `
  -Path .\logs\command_audit.log `
  -Pattern "IDEMPOTENT_RETRY"
```

Search for security evidence:

```powershell
Select-String `
  -Path .\logs\command_audit.log `
  -Pattern "AUTHENTICATION_FAILED|SECURITY_VALIDATION_REJECTED"
```

## 9. Entry Criteria

- Java 21 available
- Python 3.12+ available
- dependencies resolvable
- port 6060 available
- matching shared secret configured
- Docker Desktop running for container tests

## 10. Exit Criteria

Testing is complete when:

- Gradle build passes
- 32 unit tests pass
- 12 integration tests pass
- local TCP test passes
- Docker test passes
- audit log contains expected events
- no secret is staged in Git
- final remote-unit state is `OFFLINE`

## 11. Recorded Final Results

```text
Unit tests:         32 passed, 0 failed
Integration tests: 12 passed, 0 failed
Local TCP test:     Passed
Docker test:       Passed
Audit logging:     Passed
Final state:       OFFLINE
```
