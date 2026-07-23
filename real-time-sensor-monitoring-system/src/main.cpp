#include "system/EventLogger.hpp"
#include "system/FaultDetector.hpp"
#include "system/SensorMessageParser.hpp"
#include "system/SystemStateManager.hpp"

// Standard library used for fixed-size network buffers.
#include <array>

// Standard library used to measure sensor timeout duration.
#include <chrono>

// Standard library used for console output.
#include <iostream>

// Standard library used for exceptions.
#include <stdexcept>

// Standard library used for sensor identifiers and network messages.
#include <string>

// Standard library used to track sensor update times.
#include <unordered_map>

// Standard library used to track currently timed-out sensors.
#include <unordered_set>

// Standard library used for the list of expected sensors.
#include <vector>


#ifdef _WIN32

// Prevent Windows headers from defining conflicting min and max macros.
#define NOMINMAX

// Windows socket networking headers.
#include <winsock2.h>
#include <ws2tcpip.h>

// Common socket type used throughout the application.
using SocketHandle = SOCKET;

// Invalid socket value used by Windows.
constexpr SocketHandle INVALID_SOCKET_HANDLE = INVALID_SOCKET;

#else

// Linux and UNIX socket networking headers.
#include <arpa/inet.h>
#include <cerrno>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

// Common socket type used throughout the application.
using SocketHandle = int;

// Invalid socket value used by Linux and UNIX.
constexpr SocketHandle INVALID_SOCKET_HANDLE = -1;

#endif


namespace
{
    // TCP port shared by the C++ server and Python simulator.
    constexpr unsigned short SERVER_PORT = 5050;

    // Maximum number of pending client connections.
    constexpr int CONNECTION_BACKLOG = 1;

    // Maximum number of bytes read during one recv operation.
    constexpr std::size_t RECEIVE_BUFFER_SIZE = 4096;

    // A sensor is considered timed out after two seconds.
    constexpr auto SENSOR_TIMEOUT{
        std::chrono::seconds{2}
    };

    // recv() wakes every 500 milliseconds so timeout checks can run.
    constexpr long RECEIVE_TIMEOUT_MILLISECONDS = 500;

    // Sensors expected to report during normal operation.
    const std::vector<std::string> EXPECTED_SENSOR_IDS{
        "TEMP-01",
        "VOLT-01",
        "POS-01",
        "MOTION-01"
    };


    /**
     * Close a socket using the correct platform-specific function.
     */
    void closeSocket(
        const SocketHandle socketHandle
    )
    {
#ifdef _WIN32
        closesocket(socketHandle);
#else
        close(socketHandle);
#endif
    }


    /**
     * Initialize platform-specific networking.
     *
     * Windows requires WSAStartup before sockets can be used.
     * Linux and UNIX do not require an equivalent initialization.
     */
    void initializeNetworking()
    {
#ifdef _WIN32
        WSADATA winsockData{};

        const int startupResult{
            WSAStartup(
                MAKEWORD(2, 2),
                &winsockData
            )
        };

        if (startupResult != 0)
        {
            throw std::runtime_error(
                "Failed to initialize Windows networking."
            );
        }
#endif
    }


    /**
     * Release platform-specific networking resources.
     */
    void cleanupNetworking()
    {
#ifdef _WIN32
        WSACleanup();
#endif
    }


    /**
     * Configure recv() to wake periodically instead of blocking forever.
     *
     * This allows the application to check whether any sensor has stopped
     * transmitting while the TCP connection remains open.
     */
    void configureReceiveTimeout(
        const SocketHandle clientSocket
    )
    {
#ifdef _WIN32
        // Windows expects the timeout value in milliseconds.
        const DWORD timeoutValue{
            static_cast<DWORD>(
                RECEIVE_TIMEOUT_MILLISECONDS
            )
        };

        const int result{
            setsockopt(
                clientSocket,
                SOL_SOCKET,
                SO_RCVTIMEO,
                reinterpret_cast<const char*>(&timeoutValue),
                sizeof(timeoutValue)
            )
        };
#else
        // Linux and UNIX use a timeval structure.
        timeval timeoutValue{};

        timeoutValue.tv_sec = 0;
        timeoutValue.tv_usec =
            RECEIVE_TIMEOUT_MILLISECONDS * 1000;

        const int result{
            setsockopt(
                clientSocket,
                SOL_SOCKET,
                SO_RCVTIMEO,
                &timeoutValue,
                sizeof(timeoutValue)
            )
        };
#endif

        if (result < 0)
        {
            throw std::runtime_error(
                "Failed to configure the socket receive timeout."
            );
        }
    }


    /**
     * Determine whether recv() returned because the configured
     * receive timeout expired.
     */
    bool wasReceiveTimeout()
    {
#ifdef _WIN32
        return WSAGetLastError() == WSAETIMEDOUT;
#else
        return errno == EAGAIN || errno == EWOULDBLOCK;
#endif
    }


    /**
     * Create, bind, and configure the TCP server socket.
     */
    SocketHandle createServerSocket()
    {
        // Create an IPv4 TCP socket.
        const SocketHandle serverSocket{
            socket(
                AF_INET,
                SOCK_STREAM,
                IPPROTO_TCP
            )
        };

        if (serverSocket == INVALID_SOCKET_HANDLE)
        {
            throw std::runtime_error(
                "Failed to create the TCP server socket."
            );
        }

        sockaddr_in serverAddress{};

        // Use IPv4.
        serverAddress.sin_family = AF_INET;

        // Accept connections from any local network interface.
        serverAddress.sin_addr.s_addr = htonl(INADDR_ANY);

        // Convert the server port into network byte order.
        serverAddress.sin_port = htons(SERVER_PORT);

        // Bind the socket to the configured port.
        const int bindResult{
            bind(
                serverSocket,
                reinterpret_cast<sockaddr*>(&serverAddress),
                sizeof(serverAddress)
            )
        };

        if (bindResult < 0)
        {
            closeSocket(serverSocket);

            throw std::runtime_error(
                "Failed to bind the server socket to port 5050."
            );
        }

        // Start listening for incoming client connections.
        const int listenResult{
            listen(
                serverSocket,
                CONNECTION_BACKLOG
            )
        };

        if (listenResult < 0)
        {
            closeSocket(serverSocket);

            throw std::runtime_error(
                "Failed to listen for incoming connections."
            );
        }

        return serverSocket;
    }


    /**
     * Wait for and accept one Python simulator connection.
     */
    SocketHandle acceptClientConnection(
        const SocketHandle serverSocket
    )
    {
        sockaddr_in clientAddress{};

#ifdef _WIN32
        int clientAddressLength{
            sizeof(clientAddress)
        };
#else
        socklen_t clientAddressLength{
            sizeof(clientAddress)
        };
#endif

        const SocketHandle clientSocket{
            accept(
                serverSocket,
                reinterpret_cast<sockaddr*>(&clientAddress),
                &clientAddressLength
            )
        };

        if (clientSocket == INVALID_SOCKET_HANDLE)
        {
            throw std::runtime_error(
                "Failed to accept the simulator connection."
            );
        }

        // Wake recv() periodically so sensor timeouts can be checked.
        configureReceiveTimeout(clientSocket);

        return clientSocket;
    }


    /**
     * Detect sensors that have stopped providing updates.
     */
    void checkSensorTimeouts(
        std::unordered_map<
            std::string,
            std::chrono::steady_clock::time_point
        >& lastSeenTimes,
        std::unordered_set<std::string>& timedOutSensors,
        SystemStateManager& stateManager,
        EventLogger& eventLogger
    )
    {
        const auto currentTime{
            std::chrono::steady_clock::now()
        };

        for (const std::string& sensorId : EXPECTED_SENSOR_IDS)
        {
            const auto lastSeenIterator{
                lastSeenTimes.find(sensorId)
            };

            // Skip sensors that have not yet been registered.
            if (lastSeenIterator == lastSeenTimes.end())
            {
                continue;
            }

            const auto elapsedTime{
                currentTime - lastSeenIterator->second
            };

            // Sensor is still reporting within the permitted interval.
            if (elapsedTime <= SENSOR_TIMEOUT)
            {
                continue;
            }

            // Report each timeout only once until the sensor recovers.
            if (timedOutSensors.insert(sensorId).second)
            {
                const Fault timeoutFault{
                    true,
                    FaultSeverity::Critical,
                    "SENSOR_TIMEOUT",
                    sensorId +
                        " failed to provide an update within two seconds."
                };

                // Add the timeout fault to the system-health state.
                stateManager.update(
                    sensorId,
                    timeoutFault
                );

                std::cout
                    << "[FAULT] CRITICAL | SENSOR_TIMEOUT | "
                    << timeoutFault.message
                    << '\n'
                    << "[SYSTEM] State: "
                    << stateManager.getStateName()
                    << " | Active faults: "
                    << stateManager.getActiveFaultCount()
                    << "\n--------------------------------------------\n";

                eventLogger.log(
                    "CRITICAL",
                    "SENSOR_TIMEOUT",
                    timeoutFault.message
                );
            }
        }
    }


    /**
     * Parse, evaluate, display, and log one sensor message.
     */
    void processSensorMessage(
        const std::string& message,
        const FaultDetector& faultDetector,
        SystemStateManager& stateManager,
        EventLogger& eventLogger,
        std::unordered_map<
            std::string,
            std::chrono::steady_clock::time_point
        >& lastSeenTimes,
        std::unordered_set<std::string>& timedOutSensors
    )
    {
        try
        {
            // Convert incoming JSON into a validated C++ object.
            const SensorReading reading{
                SensorMessageParser::parse(message)
            };

            // Record the latest update time for timeout detection.
            lastSeenTimes[reading.sensorId] =
                std::chrono::steady_clock::now();

            // Clear an existing timeout fault when the sensor recovers.
            if (timedOutSensors.erase(reading.sensorId) > 0)
            {
                const Fault recoveredFault{};

                stateManager.update(
                    reading.sensorId,
                    recoveredFault
                );

                const std::string recoveryMessage{
                    reading.sensorId +
                    " resumed transmitting sensor data."
                };

                std::cout
                    << "[RECOVERY] "
                    << recoveryMessage
                    << '\n';

                eventLogger.log(
                    "INFO",
                    "SENSOR_RECOVERY",
                    recoveryMessage
                );
            }

            // Store the state before processing the newest reading.
            const std::string previousState{
                stateManager.getStateName()
            };

            // Evaluate the reading against its configured safety limits.
            const Fault fault{
                faultDetector.analyze(reading)
            };

            // Update the health and overall state of the system.
            stateManager.update(
                reading,
                fault
            );

            std::cout
                << "[SENSOR] "
                << reading.sensorId
                << " | Type: "
                << reading.sensorType
                << " | Value: "
                << reading.value
                << ' '
                << reading.unit
                << " | Sequence: "
                << reading.sequenceNumber
                << '\n';

            if (fault.detected)
            {
                std::cout
                    << "[FAULT] "
                    << faultSeverityToString(fault.severity)
                    << " | "
                    << fault.type
                    << " | "
                    << fault.message
                    << '\n';

                eventLogger.log(
                    faultSeverityToString(fault.severity),
                    fault.type,
                    reading.sensorId + ": " + fault.message
                );
            }
            else
            {
                std::cout
                    << "[STATUS] Reading accepted.\n";
            }

            const std::string currentState{
                stateManager.getStateName()
            };

            std::cout
                << "[SYSTEM] State: "
                << currentState
                << " | Active faults: "
                << stateManager.getActiveFaultCount()
                << "\n--------------------------------------------\n";

            // Log state transitions only when the state changes.
            if (previousState != currentState)
            {
                eventLogger.log(
                    "INFO",
                    "STATE_TRANSITION",
                    previousState + " -> " + currentState
                );
            }
        }
        catch (const std::exception& error)
        {
            // Invalid messages are rejected without stopping the server.
            std::cerr
                << "[INVALID MESSAGE] "
                << error.what()
                << "\n--------------------------------------------\n";

            eventLogger.log(
                "ERROR",
                "INVALID_MESSAGE",
                error.what()
            );
        }
    }


    /**
     * Receive newline-delimited JSON messages from one simulator connection.
     */
    void receiveSensorMessages(
        const SocketHandle clientSocket,
        const FaultDetector& faultDetector,
        SystemStateManager& stateManager,
        EventLogger& eventLogger
    )
    {
        // Temporary network receive buffer.
        std::array<char, RECEIVE_BUFFER_SIZE> receiveBuffer{};

        // Stores partial TCP data until a complete newline-delimited
        // JSON message has been received.
        std::string pendingData;

        // Initialize every expected sensor when the client connects.
        const auto connectionTime{
            std::chrono::steady_clock::now()
        };

        std::unordered_map<
            std::string,
            std::chrono::steady_clock::time_point
        > lastSeenTimes;

        for (const std::string& sensorId : EXPECTED_SENSOR_IDS)
        {
            lastSeenTimes[sensorId] = connectionTime;
        }

        // Stores sensors whose timeout fault is currently active.
        std::unordered_set<std::string> timedOutSensors;

        std::cout
            << "Python simulator connected successfully.\n"
            << "Receiving and evaluating sensor messages...\n"
            << "--------------------------------------------\n";

        eventLogger.log(
            "INFO",
            "CLIENT_CONNECTED",
            "Python sensor simulator connected."
        );

        while (true)
        {
            const int bytesReceived{
                recv(
                    clientSocket,
                    receiveBuffer.data(),
                    static_cast<int>(receiveBuffer.size()),
                    0
                )
            };

            // Zero means the Python client disconnected normally.
            if (bytesReceived == 0)
            {
                std::cout
                    << "Python simulator disconnected.\n";

                eventLogger.log(
                    "INFO",
                    "CLIENT_DISCONNECTED",
                    "Python sensor simulator disconnected."
                );

                break;
            }

            // A negative result may represent a timeout or network failure.
            if (bytesReceived < 0)
            {
                if (wasReceiveTimeout())
                {
                    checkSensorTimeouts(
                        lastSeenTimes,
                        timedOutSensors,
                        stateManager,
                        eventLogger
                    );

                    continue;
                }

                throw std::runtime_error(
                    "An error occurred while receiving sensor data."
                );
            }

            // Append newly received bytes to any existing partial message.
            pendingData.append(
                receiveBuffer.data(),
                static_cast<std::size_t>(bytesReceived)
            );

            // Search for complete newline-delimited messages.
            std::size_t newlinePosition{
                pendingData.find('\n')
            };

            while (newlinePosition != std::string::npos)
            {
                // Extract one complete JSON message.
                const std::string message{
                    pendingData.substr(
                        0,
                        newlinePosition
                    )
                };

                // Remove the processed message and newline.
                pendingData.erase(
                    0,
                    newlinePosition + 1
                );

                if (!message.empty())
                {
                    processSensorMessage(
                        message,
                        faultDetector,
                        stateManager,
                        eventLogger,
                        lastSeenTimes,
                        timedOutSensors
                    );
                }

                // Search for another complete message.
                newlinePosition =
                    pendingData.find('\n');
            }

            // Check for sensors that stopped transmitting while
            // other sensors continue to report.
            checkSensorTimeouts(
                lastSeenTimes,
                timedOutSensors,
                stateManager,
                eventLogger
            );
        }
    }
}


int main()
{
    // Flush output immediately so integration tests can capture
    // server messages without waiting for an internal buffer.
    std::cout << std::unitbuf;
    std::cerr << std::unitbuf;

    std::cout
        << "============================================\n"
        << "Real-Time Multi-Sensor Monitoring System\n"
        << "System status: STARTUP\n"
        << "============================================\n";

    SocketHandle serverSocket{
        INVALID_SOCKET_HANDLE
    };

    try
    {
        // Initialize platform-specific socket networking.
        initializeNetworking();

        // Create and configure the TCP server.
        serverSocket = createServerSocket();

        // Create reusable system components.
        const FaultDetector faultDetector{};
        SystemStateManager stateManager{};

        // Create the logs directory and event log automatically.
        EventLogger eventLogger{
            "logs/system_events.log"
        };

        eventLogger.log(
            "INFO",
            "SYSTEM_STARTUP",
            "Sensor monitoring system started."
        );

        std::cout
            << "TCP server listening on port "
            << SERVER_PORT
            << ".\n";

        // Continue accepting new simulator connections after disconnects.
        while (true)
        {
            std::cout
                << "Waiting for Python simulator...\n";

            const SocketHandle clientSocket{
                acceptClientConnection(serverSocket)
            };

            try
            {
                receiveSensorMessages(
                    clientSocket,
                    faultDetector,
                    stateManager,
                    eventLogger
                );
            }
            catch (const std::exception& error)
            {
                std::cerr
                    << "Client connection error: "
                    << error.what()
                    << '\n';

                eventLogger.log(
                    "ERROR",
                    "CLIENT_CONNECTION_ERROR",
                    error.what()
                );
            }

            // Close the completed client connection.
            closeSocket(clientSocket);

            std::cout
                << "Returning to connection-waiting state.\n";
        }
    }
    catch (const std::exception& error)
    {
        std::cerr
            << "System error: "
            << error.what()
            << '\n';

        if (serverSocket != INVALID_SOCKET_HANDLE)
        {
            closeSocket(serverSocket);
        }

        cleanupNetworking();

        return 1;
    }
}