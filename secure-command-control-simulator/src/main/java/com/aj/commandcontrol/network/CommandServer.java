package com.aj.commandcontrol.network;

import com.aj.commandcontrol.model.CommandAcknowledgement;
import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.parsing.CommandMessageParser;
import com.aj.commandcontrol.parsing.CommandValidationException;
import com.aj.commandcontrol.processing.CommandProcessor;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * TCP server that receives newline-delimited JSON commands,
 * processes them, and returns JSON acknowledgements.
 */
public final class CommandServer {

    // TCP port shared with the Python control station.
    public static final int DEFAULT_PORT = 6060;

    // Parser used to validate incoming JSON command messages.
    private final CommandMessageParser commandParser;

    // State machine shared across commands and client connections.
    private final CommandProcessor commandProcessor;

    // Jackson serializer used to create acknowledgement JSON.
    private final ObjectMapper objectMapper;

    // Port on which the Java server listens.
    private final int port;

    /**
     * Create a server using the default TCP port.
     */
    public CommandServer() {
        this(DEFAULT_PORT);
    }

    /**
     * Create a command server on a specified port.
     *
     * @param port TCP listening port
     */
    public CommandServer(
        final int port
    ) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException(
                "Port must be between 1 and 65535."
            );
        }

        this.port = port;
        this.commandParser = new CommandMessageParser();
        this.commandProcessor = new CommandProcessor();
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Start the TCP server and continuously accept control-station clients.
     *
     * @throws IOException when the listening socket cannot be created
     */
    public void start() throws IOException {
        try (ServerSocket serverSocket = new ServerSocket(port)) {
            System.out.println(
                "TCP command server listening on port " + port + "."
            );
            System.out.println(
                "Waiting for Python control station..."
            );

            // Continue accepting clients after one client disconnects.
            while (true) {
                try {
                    final Socket clientSocket =
                        serverSocket.accept();

                    handleClient(clientSocket);
                } catch (IOException error) {
                    // A client-level error should not permanently stop
                    // the main server from accepting future connections.
                    System.err.println(
                        "[CLIENT ERROR] " + error.getMessage()
                    );
                }

                System.out.println(
                    "Waiting for Python control station..."
                );
            }
        }
    }

    /**
     * Receive and process commands from one connected control station.
     *
     * Each command and acknowledgement occupies one line of UTF-8 JSON.
     *
     * @param clientSocket connected TCP client
     * @throws IOException when socket communication fails
     */
    private void handleClient(
        final Socket clientSocket
    ) throws IOException {
        try (
            clientSocket;
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(
                    clientSocket.getInputStream(),
                    StandardCharsets.UTF_8
                )
            );
            BufferedWriter writer = new BufferedWriter(
                new OutputStreamWriter(
                    clientSocket.getOutputStream(),
                    StandardCharsets.UTF_8
                )
            )
        ) {
            System.out.println(
                "Python control station connected: "
                    + clientSocket.getRemoteSocketAddress()
            );

            String jsonLine;

            // readLine() matches the newline delimiter added by Python.
            while ((jsonLine = reader.readLine()) != null) {
                if (jsonLine.isBlank()) {
                    continue;
                }

                System.out.println(
                    "[RECEIVED] " + jsonLine
                );

                final CommandAcknowledgement acknowledgement =
                    processCommand(jsonLine);

                sendAcknowledgement(
                    writer,
                    acknowledgement
                );
            }

            System.out.println(
                "Python control station disconnected."
            );
        }
    }

    /**
     * Parse and process one command without allowing an invalid
     * message to terminate the TCP server.
     */
    private CommandAcknowledgement processCommand(
        final String jsonMessage
    ) {
        try {
            final CommandMessage command =
                commandParser.parse(jsonMessage);

            final CommandResult result =
                commandProcessor.process(command);

            System.out.println(result);

            return CommandAcknowledgement.fromResult(
                result
            );
        } catch (CommandValidationException error) {
            System.out.println(
                "[INVALID COMMAND] " + error.getMessage()
            );

            return CommandAcknowledgement.invalid(
                error.getMessage(),
                commandProcessor.getCurrentState()
            );
        } catch (RuntimeException error) {
            // Catch unexpected command-processing errors so a single
            // request cannot stop the server.
            System.err.println(
                "[PROCESSING ERROR] " + error.getMessage()
            );

            return CommandAcknowledgement.invalid(
                "Unexpected command-processing failure.",
                commandProcessor.getCurrentState()
            );
        }
    }

    /**
     * Serialize and send one acknowledgement to the Python client.
     */
    private void sendAcknowledgement(
        final BufferedWriter writer,
        final CommandAcknowledgement acknowledgement
    ) throws IOException {
        final String acknowledgementJson;

        try {
            acknowledgementJson =
                objectMapper.writeValueAsString(
                    acknowledgement
                );
        } catch (JsonProcessingException error) {
            throw new IOException(
                "Failed to serialize command acknowledgement.",
                error
            );
        }

        // Add a newline so the Python client can use readline().
        writer.write(acknowledgementJson);
        writer.newLine();
        writer.flush();

        System.out.println(
            "[ACK SENT] " + acknowledgementJson
        );
        System.out.println(
            "------------------------------------------------------------"
        );
    }

    /**
     * Return the remote unit's current state for tests and diagnostics.
     */
    public String getCurrentStateName() {
        return commandProcessor
            .getCurrentState()
            .name();
    }
}