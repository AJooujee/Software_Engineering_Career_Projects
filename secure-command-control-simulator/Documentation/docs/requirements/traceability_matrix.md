# Requirements Traceability Matrix

| Requirement | Implementation | Verification |
|---|---|---|
| FR-001 TCP server | `CommandServer` | local test, Docker test, integration runner |
| FR-002 newline JSON | `CommandServer.handleClient`, Python socket file | integration scenarios |
| FR-003 required fields | `CommandMessageParser` | `CommandMessageParserTests` |
| FR-004 unknown fields | `CommandMessageParser.validateUnknownFields` | parser unit test |
| FR-005 supported commands | `CommandType` | processor and parser tests |
| FR-006 initial OFFLINE state | `CommandProcessor` | `startsInOfflineState` |
| FR-007 state transitions | `CommandProcessor` | 8 processor tests, integration tests |
| FR-008 acknowledgements | `CommandAcknowledgement` | cache tests, local/integration tests |
| FR-009 HMAC authentication | `MessageAuthenticator` | authenticator tests, tampered-signature integration |
| FR-010 secret configuration | `MessageAuthenticator.fromEnvironment` | local and Docker startup |
| FR-011 unauthorized rejection | `CommandServer.processCommand` | tampered-signature scenario |
| FR-012 duplicate detection | `ReplayProtectionService`, `AcknowledgementCache` | replay tests, integration tests |
| FR-013 sequence protection | `ReplayProtectionService` | 6 replay tests, replay scenario |
| FR-014 expiration | `ReplayProtectionService` | expired test and scenario |
| FR-015 future tolerance | `ReplayProtectionService` | future test and scenario |
| FR-016 ACK cache | `AcknowledgementCache` | 4 cache tests |
| FR-017 idempotent retry | `CommandServer`, `AcknowledgementCache` | ACK-loss integration scenario |
| FR-018 ID collision | `CommandServer` cache comparison | security branch and audit event |
| FR-019 client retry | `send_command_with_retry` | ACK-loss local/integration tests |
| FR-020 finite retry | Python client constants | local retry output |
| FR-021 audit logging | `AuditLogger`, `AuditEvent` | 3 logger tests and log inspection |
| FR-022 persistent log | `AuditLogger.DEFAULT_LOG_PATH` | local and Docker log inspection |
| FR-023 invalid resilience | `CommandServer` exception handling | malformed-JSON scenario |
| FR-024 repeated clients | server accept loop | integration runner and Python client |
| FR-025 Docker support | `Dockerfile`, `docker-compose.yml` | Docker build and run |
| FR-026 host/container TCP | Compose port mapping | host Python Docker test |
| NFR-001 Java 21 | `build.gradle`, Docker base images | build output |
| NFR-002 Gradle Wrapper | `gradlew`, `gradlew.bat`, wrapper files | clean build |
| NFR-003 unit tests | `src/test` | 32/32 passed |
| NFR-004 integration tests | `tests/integration/run_scenarios.py` | 12/12 passed |
| NFR-005 secret handling | environment variables, `.gitignore`, `.env.example` | `git status --ignored` |
| NFR-006 constant-time comparison | `MessageDigest.isEqual` | authenticator tests |
| NFR-007 immutable models | final classes and fields | compilation and unit tests |
| NFR-008 thread safety | synchronized methods | code review and tests |
| NFR-009 JSON logs | `AuditLogger` | logger tests and runtime log |
| NFR-010 non-root container | Dockerfile `USER commandcontrol` | Docker build |
| NFR-011 multi-stage image | Dockerfile builder/runtime stages | Docker build |
| NFR-012 documentation | README and `docs` files | repository review |

## Final Verification Summary

| Verification | Result |
|---|---:|
| Gradle build | Passed |
| Unit tests | 32/32 |
| Integration scenarios | 12/12 |
| Local TCP test | Passed |
| Docker test | Passed |
| Audit logging | Passed |
| Final state | OFFLINE |
