// Standard library used for displaying program output.
#include <iostream>

// Standard library used for storing and processing text.
#include <string>

// Standard library used for a fixed-size receive buffer.
#include <array>

// Standard library used for exception handling.
#include <stdexcept>

// Standard library used for numeric size types such as std::size_t.
#include <cstddef>


// Windows uses the Winsock networking API.
#ifdef _WIN32

// Prevent Windows headers from defining min and max macros.
#define NOMINMAX

#include <winsock2.h>
#include <ws2tcpip.h>

// Define a common socket type for Windows.
using SocketHandle = SOCKET;

// Define the platform-specific invalid socket value.
constexpr SocketHandle INVALID_SOCKET_HANDLE = INVALID_SOCKET;

#else

// Linux and UNIX-like systems use POSIX sockets.
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

// Define a common socket type for Linux and UNIX.
using SocketHandle = int;

// Define the platform-specific invalid socket value.
constexpr SocketHandle INVALID_SOCKET_HANDLE = -1;

#endif


namespace
{
    // TCP port shared by the C++ server and Python simulator.
    constexpr unsigned short SERVER_PORT = 5050;

    // Maximum number of pending client connections.
    constexpr int CONNECTION_BACKLOG = 1;

    // Number of bytes read during each network receive operation.
    constexpr std::size_t RECEIVE_BUFFER_SIZE = 4096;


    /**
     * Close a socket using the correct operating-system function.
     */
    void closeSocket(const SocketHandle socketHandle)
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
     * Linux does not require an equivalent initialization step.
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
     * Create a TCP server socket, bind it to port 5050,
     * and begin listening for a client connection.
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

        // Convert the port number into network byte order.
        serverAddress.sin_port = htons(SERVER_PORT);

        // Bind the socket to the selected address and port.
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

        // Start listening for incoming connections.
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

        return clientSocket;
    }


    /**
     * Receive newline-delimited JSON messages from the Python simulator.
     *
     * TCP is a byte stream, so one recv() call may contain:
     * - part of one JSON message
     * - exactly one JSON message
     * - multiple JSON messages
     *
     * The pendingData string stores incomplete data until a newline
     * marks the end of one complete JSON message.
     */
    void receiveSensorMessages(
        const SocketHandle clientSocket
    )
    {
        // Temporary fixed-size network buffer.
        std::array<char, RECEIVE_BUFFER_SIZE> receiveBuffer{};

        // Stores incomplete messages between receive operations.
        std::string pendingData;

        std::cout
            << "Python simulator connected successfully.\n"
            << "Receiving sensor messages...\n"
            << "--------------------------------------------\n";

        while (true)
        {
            // Receive bytes from the connected Python client.
            const int bytesReceived{
                recv(
                    clientSocket,
                    receiveBuffer.data(),
                    static_cast<int>(receiveBuffer.size()),
                    0
                )
            };

            // A return value of zero means the client disconnected normally.
            if (bytesReceived == 0)
            {
                std::cout
                    << "Python simulator disconnected.\n";

                break;
            }

            // A negative value means a receive error occurred.
            if (bytesReceived < 0)
            {
                throw std::runtime_error(
                    "An error occurred while receiving sensor data."
                );
            }

            // Add the newly received bytes to any previous partial data.
            pendingData.append(
                receiveBuffer.data(),
                static_cast<std::size_t>(bytesReceived)
            );

            // Search for the newline that ends one JSON message.
            std::size_t newlinePosition{
                pendingData.find('\n')
            };

            // Process every complete message currently in pendingData.
            while (newlinePosition != std::string::npos)
            {
                // Extract one complete JSON message.
                const std::string message{
                    pendingData.substr(
                        0,
                        newlinePosition
                    )
                };

                // Remove the processed message and its newline.
                pendingData.erase(
                    0,
                    newlinePosition + 1
                );

                if (!message.empty())
                {
                    std::cout
                        << "[RECEIVED] "
                        << message
                        << '\n';
                }

                // Search for another complete message.
                newlinePosition = pendingData.find('\n');
            }
        }
    }
}


int main()
{
    // Display the application header.
    std::cout
        << "============================================\n"
        << "Real-Time Multi-Sensor Monitoring System\n"
        << "System status: STARTUP\n"
        << "============================================\n";

    // Store the server socket so it can be closed during error handling.
    SocketHandle serverSocket{
        INVALID_SOCKET_HANDLE
    };

    // Store the connected client socket.
    SocketHandle clientSocket{
        INVALID_SOCKET_HANDLE
    };

    try
    {
        // Initialize Windows networking when required.
        initializeNetworking();

        // Create, bind, and configure the TCP server.
        serverSocket = createServerSocket();

        std::cout
            << "TCP server listening on port "
            << SERVER_PORT
            << ".\n"
            << "Waiting for Python simulator...\n";

        // Wait until the Python simulator connects.
        clientSocket = acceptClientConnection(
            serverSocket
        );

        // Receive sensor messages until the simulator disconnects.
        receiveSensorMessages(
            clientSocket
        );

        // Close both sockets after normal completion.
        closeSocket(clientSocket);
        closeSocket(serverSocket);

        // Release Windows networking resources.
        cleanupNetworking();

        std::cout
            << "Sensor monitoring system stopped normally.\n";

        return 0;
    }
    catch (const std::exception& error)
    {
        // Display the reason the application failed.
        std::cerr
            << "System error: "
            << error.what()
            << '\n';

        // Close the client socket if it was opened.
        if (clientSocket != INVALID_SOCKET_HANDLE)
        {
            closeSocket(clientSocket);
        }

        // Close the server socket if it was opened.
        if (serverSocket != INVALID_SOCKET_HANDLE)
        {
            closeSocket(serverSocket);
        }

        // Release Windows networking resources before exiting.
        cleanupNetworking();

        return 1;
    }
}