# Requirements Traceability Matrix

| Requirement | Implementation | Verification |
|---|---|---|
| REQ-NET-001 | `createServerSocket()` | Manual startup and integration suite |
| REQ-NET-002 | `acceptClientConnection()` | All integration scenarios |
| REQ-NET-003 | Server accept loop in `main.cpp` | Manual reconnection test |
| REQ-MSG-001 | `send_message()` and TCP receive buffer | All integration scenarios |
| REQ-MSG-002 | `SensorMessageParser::parse()` | Parser unit tests |
| REQ-MSG-003 | Exception handling in `processSensorMessage()` | Parser unit tests |
| REQ-SEN-001 | Python sensor generator functions | Normal integration scenario |
| REQ-SEN-002 | Python `sequence_number` | Console output verification |
| REQ-FLT-001 | `analyzeTemperature()` | `DetectsTemperatureWarning` |
| REQ-FLT-002 | `analyzeTemperature()` | `DetectsCriticalTemperature` |
| REQ-FLT-003 | `analyzeVoltage()` | `DetectsVoltageWarning` |
| REQ-FLT-004 | `analyzeVoltage()` | `DetectsCriticalVoltage` |
| REQ-FLT-005 | `analyzePosition()` | `DetectsPositionOutsideBoundary` |
| REQ-FLT-006 | `analyzeMotion()` | `DetectsInvalidMotionState` |
| REQ-FLT-007 | `FaultDetector::analyze()` | `RejectsUnknownSensorType` |
| REQ-TIME-001 | `checkSensorTimeouts()` | `sensor-timeout` integration scenario |
| REQ-STATE-001 | `SystemStateManager` | `StartsInNormalState` and normal integration scenario |
| REQ-STATE-002 | `recalculateState()` | `OneWarningCausesDegradedState` |
| REQ-STATE-003 | `recalculateState()` | `OneCriticalFaultCausesSafeMode` |
| REQ-STATE-004 | `recalculateState()` | `TwoWarningsCauseSafeMode` |
| REQ-STATE-005 | `SystemStateManager::update()` | Recovery unit tests |
| REQ-LOG-001 | `EventLogger` startup call | `system_events.log` inspection |
| REQ-LOG-002 | Connection logging | `system_events.log` inspection |
| REQ-LOG-003 | Fault logging | Timeout and fault scenario logs |
| REQ-LOG-004 | State-transition logging | Warning and critical scenario logs |
| REQ-TEST-001 | GoogleTest and CTest | 21 of 21 unit tests passed |
| REQ-TEST-002 | `run_scenarios.py` | 6 of 6 scenarios passed |
| REQ-NFR-001 | `CMAKE_CXX_STANDARD 17` | CMake configuration |
| REQ-NFR-002 | `_WIN32` and POSIX socket branches | Code review and Windows execution |
| REQ-NFR-003 | `CMakeLists.txt` | Successful configure and build |
| REQ-NFR-004 | Parser exception handling | Invalid-message unit tests |
| REQ-NFR-005 | Documented test commands | README and test plan |