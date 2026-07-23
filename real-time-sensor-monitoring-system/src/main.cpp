#include "system/FaultDetector.hpp"
#include "system/SensorMessageParser.hpp"
#include "system/SystemStateManager.hpp"

// Standard library used for fixed-size receive buffers.
#include <array>

// Standard library used for console output.
#include <iostream>

// Standard library used for exceptions.
#include <stdexcept>

// Standard library used for incoming message text.
#include <string>


#ifdef _WIN32

// Prevent Windows headers from defining conflicting macros.
#define NOMINMAX

#include <winsock2.h>
#include <ws2tcpip.h>

using SocketHandle = SOCKET;

constexpr SocketHandle INVALID_SOCKET_HANDLE = INVALID_SOCKET;

#else

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

using SocketHandle = int;

constexpr SocketHandle INVALID_SOCKET_HANDLE = -1;

#endif


namespace
{
    // TCP port shared by the C++ server and Python simulator.
    constexpr unsigned short SERVER_PORT = 5050;

    // Only one simulator connection is required at a time.
    constexpr int CONNECTION_BACKLOG = 1;

    // Maximum amount of data read during one recv operation.
    constexpr std::size_t RECEIVE_BUFFER_SIZE = 4096;


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


    void cleanupNetworking()
    {
#ifdef _WIN32
        WSACleanup();
#endif
    }


    SocketHandle createServerSocket()
    {
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

        serverAddress.sin_family = AF_INET;
        serverAddress.sin_addr.s_addr = htonl(INADDR_ANY);
        serverAddress.sin_port = htons(SERVER_PORT);

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

        return clientSocket;
    }


    void processSensorMessage(
        const std::string& message,
        const FaultDetector& faultDetector,
        SystemStateManager& stateManager
    )
    {
        try
        {
            // Convert incoming JSON into a validated C++ object.
            const SensorReading reading{
                SensorMessageParser::parse(message)
            };

            // Evaluate the reading against its configured limits.
            const Fault fault{
                faultDetector.analyze(reading)
            };

            // Update the current system health and operating state.
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
            }
            else
            {
                std::cout
                    << "[STATUS] Reading accepted.\n";
            }

            std::cout
                << "[SYSTEM] State: "
                << stateManager.getStateName()
                << " | Active faults: "
                << stateManager.getActiveFaultCount()
                << "\n--------------------------------------------\n";
        }
        catch (const std::exception& error)
        {
            // Invalid JSON is rejected without stopping the server.
            std::cerr
                << "[INVALID MESSAGE] "
                << error.what()
                << "\n--------------------------------------------\n";
        }
    }


    void receiveSensorMessages(
        const SocketHandle clientSocket,
        const FaultDetector& faultDetector,
        SystemStateManager& stateManager
    )
    {
        std::array<char, RECEIVE_BUFFER_SIZE> receiveBuffer{};

        // Stores incomplete TCP data until a newline arrives.
        std::string pendingData;

        std::cout
            << "Python simulator connected successfully.\n"
            << "Receiving and evaluating sensor messages...\n"
            << "--------------------------------------------\n";

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

            if (bytesReceived == 0)
            {
                std::cout
                    << "Python simulator disconnected.\n";

                break;
            }

            if (bytesReceived < 0)
            {
                throw std::runtime_error(
                    "An error occurred while receiving sensor data."
                );
            }

            pendingData.append(
                receiveBuffer.data(),
                static_cast<std::size_t>(bytesReceived)
            );

            std::size_t newlinePosition{
                pendingData.find('\n')
            };

            while (newlinePosition != std::string::npos)
            {
                const std::string message{
                    pendingData.substr(
                        0,
                        newlinePosition
                    )
                };

                pendingData.erase(
                    0,
                    newlinePosition + 1
                );

                if (!message.empty())
                {
                    processSensorMessage(
                        message,
                        faultDetector,
                        stateManager
                    );
                }

                newlinePosition =
                    pendingData.find('\n');
            }
        }
    }
}


int main()
{
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
        initializeNetworking();

        serverSocket = createServerSocket();

        const FaultDetector faultDetector{};
        SystemStateManager stateManager{};

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
                    stateManager
                );
            }
            catch (const std::exception& error)
            {
                std::cerr
                    << "Client connection error: "
                    << error.what()
                    << '\n';
            }

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