# Software Engineering Career Projects

A collection of software engineering projects focused on systems programming,
object-oriented design, software integration, testing, networking, and software
reliability.

These projects are designed to demonstrate practical software engineering
skills through requirements-driven development, implementation, debugging,
testing, and technical documentation.

## Projects

### 1. Real-Time Multi-Sensor Monitoring and Fault-Tolerant System

**Status:** In Development

**Technologies:** C++17, Python, TCP/IP, CMake, MSVC, Windows Sockets, Git

A real-time software system that receives simulated temperature, voltage,
position, and motion sensor readings from a Python simulator through TCP/IP.

The C++ monitoring application currently operates as a TCP server, while the
Python simulator generates structured JSON sensor messages and sends them in
real time.

Current functionality includes:

- Four simulated sensor types
- Real-time sensor data generation
- TCP client-server communication
- Newline-delimited JSON messaging
- Continuous sequence-number tracking
- Cross-platform socket design
- CMake-based C++ build configuration
- Network connection and error handling

Planned functionality includes:

- JSON parsing and message validation
- Sensor range monitoring
- Sensor timeout detection
- Fault injection scenarios
- NORMAL, DEGRADED, and SAFE_MODE system states
- Structured event logging
- Unit and integration testing
- Requirements traceability
- Continuous integration

[View the Real-Time Multi-Sensor Monitoring System](./real-time-sensor-monitoring-system)

---

## Skills Demonstrated

- C++ and Python development
- Object-oriented software design
- TCP/IP socket programming
- Client-server architecture
- Cross-platform development
- Build configuration with CMake
- Error handling and debugging
- Git version-control workflow
- Requirements-driven development
- Software integration and testing

## Repository Structure

```text
Software_Engineering_Career_Projects/
├── real-time-sensor-monitoring-system/
│   ├── config/
│   ├── docs/
│   ├── include/
│   ├── logs/
│   ├── requirements/
│   ├── simulator/
│   ├── src/
│   ├── tests/
│   └── CMakeLists.txt
└── README.md
