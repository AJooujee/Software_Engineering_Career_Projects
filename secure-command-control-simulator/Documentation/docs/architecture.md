# System Architecture

## 1. Purpose

The Secure Command-and-Control Message Processing Simulator demonstrates a layered software architecture for receiving, authenticating, validating, executing, and auditing remote commands.

The implementation is educational and portfolio-oriented. It is not intended for real safety-critical, military, industrial-control, or production deployment.

## 2. System Context

```text
+---------------------------+
| Python Control Station    |
| - Creates commands        |
| - Canonicalizes payload   |
| - Calculates HMAC         |
| - Sends JSON over TCP     |
| - Waits for ACK           |
| - Retries lost ACKs       |
+-------------+-------------+
              |
              | TCP 6060
              | newline-delimited UTF-8 JSON
              v
+-------------+-------------+
| Java Remote Unit Server   |
| - Parses JSON             |
| - Verifies HMAC           |
| - Applies replay checks   |
| - Handles idempotent retry|
| - Executes state machine  |
| - Returns JSON ACK        |
| - Writes audit events     |
+---------------------------+
```

## 3. Major Components

### 3.1 CommandControlApplication

Application entry point. It creates and starts `CommandServer`.

### 3.2 CommandServer

Coordinates the end-to-end request path:

1. accepts a TCP client
2. reads one JSON command per line
3. parses and validates the message
4. verifies authentication
5. checks retry cache
6. checks replay and timestamp rules
7. executes the command state machine
8. caches the acknowledgement
9. sends the acknowledgement
10. records audit events

### 3.3 CommandMessageParser

Converts raw JSON to an immutable `CommandMessage`.

It validates:

- top-level JSON object
- allowed field names
- required text fields
- positive integral sequence number
- supported command type
- ISO-8601 UTC timestamp
- object payload
- 64-character hexadecimal signature

### 3.4 MessageAuthenticator

Calculates and verifies HMAC-SHA256 signatures.

Canonical message:

```text
message_id
command_type
target_id
sequence_number
timestamp
canonical_payload_json
```

The signature field is excluded from the signed data.

Payload keys are sorted to maintain deterministic cross-language serialization.

### 3.5 ReplayProtectionService

Maintains:

- processed message IDs
- highest accepted sequence number per target

Rules:

- maximum command age: 30 seconds
- maximum future clock skew: 5 seconds
- message IDs cannot repeat
- sequence numbers must increase per target

### 3.6 AcknowledgementCache

Stores the completed ACK and original signature for every processed command.

An identical authenticated retry receives the cached ACK.

A repeated message ID with different authenticated content is treated as a collision and rejected.

### 3.7 CommandProcessor

Maintains the remote-unit state and applies deterministic state-transition rules.

```text
OFFLINE --START_SYSTEM--> STANDBY
STANDBY --ACTIVATE_SYSTEM--> ACTIVE
ACTIVE --STOP_SYSTEM--> STANDBY
STANDBY/ACTIVE --ENTER_SAFE_MODE--> SAFE_MODE
SAFE_MODE --RESET_SYSTEM--> STANDBY
STANDBY/ACTIVE/SAFE_MODE --SHUTDOWN_SYSTEM--> OFFLINE
```

Rejected commands do not change the state.

### 3.8 AuditLogger

Writes newline-delimited JSON records to:

```text
logs/command_audit.log
```

Representative events:

- `SERVER_STARTED`
- `CLIENT_CONNECTED`
- `AUTHENTICATION_PASSED`
- `AUTHENTICATION_FAILED`
- `SECURITY_VALIDATION_PASSED`
- `SECURITY_VALIDATION_REJECTED`
- `COMMAND_ACCEPTED`
- `COMMAND_REJECTED`
- `ACK_SENT`
- `ACK_DROPPED_FOR_TEST`
- `IDEMPOTENT_RETRY`
- `CLIENT_DISCONNECTED`

## 4. Processing Sequence

```text
Client sends JSON
      |
      v
Parse and validate structure
      |
      +-- invalid --> INVALID ACK
      |
      v
Verify HMAC signature
      |
      +-- failed --> UNAUTHORIZED ACK
      |
      v
Check acknowledgement cache
      |
      +-- exact retry --> cached ACK
      |
      +-- ID collision --> SECURITY_REJECTED ACK
      |
      v
Timestamp and replay validation
      |
      +-- failed --> SECURITY_REJECTED ACK
      |
      v
Execute state transition
      |
      v
Create and cache ACK
      |
      v
Write audit event
      |
      v
Send ACK
```

## 5. Reliability Design

The Python client uses:

- 2-second ACK timeout
- up to 3 delivery attempts
- one fresh TCP connection per attempt
- identical command content and signature for retries

The Java server stores the ACK before network transmission. Therefore, loss of the response does not cause duplicate command execution.

## 6. Security Boundary

The shared secret is loaded from:

```text
COMMAND_CONTROL_SHARED_SECRET
```

It is not stored in source code, Docker images, Git, or network messages.

The development ACK-loss configuration is loaded from:

```text
COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID
```

## 7. Deployment Architecture

### Local

```text
Windows Python client -> 127.0.0.1:6060 -> Local Java process
```

### Docker

```text
Windows Python client
        |
        | host port 6060
        v
Docker port mapping
        |
        v
Java server container port 6060
        |
        v
Host-mounted logs directory
```

The runtime container uses a Java 21 JRE and a non-root user.

## 8. Data Persistence

Current persistent data:

- audit log through the host-mounted `logs` directory

Current in-memory data:

- remote-unit state
- processed message IDs
- highest sequence numbers
- cached acknowledgements

A server restart resets all in-memory state.

## 9. Design Qualities

- clear package separation
- immutable domain models
- dependency injection for testability
- synchronized mutable security/state components
- deterministic state behavior
- structured machine-readable logs
- Gradle Wrapper reproducibility
- automated unit and integration verification
- multi-stage container image
- non-root runtime process

## 10. Limitations

- TCP is not encrypted
- no persistent replay database
- single-client synchronous server
- no identity-specific authorization
- no key rotation
- no log rotation
- no high-availability design
