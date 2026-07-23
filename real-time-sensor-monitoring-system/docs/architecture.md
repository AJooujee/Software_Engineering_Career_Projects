# System Architecture

## 1. Overview

The Real-Time Multi-Sensor Monitoring and Fault-Tolerant System uses a
client-server architecture.

A Python application simulates physical sensors and sends structured
JSON messages to a C++ monitoring application over TCP/IP.

The C++ application validates the messages, evaluates sensor values,
updates system health, records important events, and reports the
current operating state.

## 2. High-Level Architecture

```text
+---------------------------+
| Python Sensor Simulator   |
|                           |
| TEMP-01                   |
| VOLT-01                   |
| POS-01                    |
| MOTION-01                 |
+-------------+-------------+
              |
              | JSON over TCP/IP
              | Port 5050
              v
+-------------+-------------+
| C++ TCP Receiver          |
+-------------+-------------+
              |
              v
+-------------+-------------+
| SensorMessageParser       |
|                           |
| - JSON syntax validation  |
| - Required-field checks   |
| - Field-type validation   |
+-------------+-------------+
              |
              v
+-------------+-------------+
| FaultDetector             |
|                           |
| - Temperature limits      |
| - Voltage limits          |
| - Position limits         |
| - Motion validation       |
+-------------+-------------+
              |
              v
+-------------+-------------+
| SystemStateManager        |
|                           |
| NORMAL                    |
| DEGRADED                  |
| SAFE_MODE                 |
+---------+-----------------+
          |
          +---------------------+
          |                     |
          v                     v
+---------+----------+  +-------+-----------+
| Console Output     |  | EventLogger       |
|                    |  |                   |
| Sensor readings    |  | Structured events |
| Faults             |  | Timestamped logs  |
| System state       |  | Recovery events   |
+--------------------+  +-------------------+