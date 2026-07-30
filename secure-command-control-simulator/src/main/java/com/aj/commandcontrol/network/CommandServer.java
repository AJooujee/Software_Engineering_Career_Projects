package com.aj.commandcontrol.network;

import com.aj.commandcontrol.model.CommandAcknowledgement;
import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.parsing.CommandMessageParser;
import com.aj.commandcontrol.parsing.CommandValidationException;
import com.aj.commandcontrol.processing.CommandProcessor;
import com.aj.commandcontrol.security.MessageAuthenticator;
import com.aj.commandcontrol.security.ReplayProtectionService;
import com.aj.commandcontrol.security.SecurityValidationResult;
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
 * TCP server that receives authenticated and replay-protected
 * JSON commands and returns JSON acknowledgements.
 */
public final class CommandServer {

    // TCP port shared with the Python control station.
    public static final int DEFAULT_PORT = 6060;

    private final CommandMessageParser commandParser;
    private final CommandProcessor commandProcessor;
    private final MessageAuthenticator messageAuthenticator;
    private final ReplayProtectionService replayProtectionService;
    private final ObjectMapper objectMapper;
    private final int port;

    /**
     * Create a server using default production dependencies.
     */
    public CommandServer() {
        this(
            DEFAULT_PORT,
            MessageAuthenticator.fromEnvironment(),
            new ReplayProtectionService()
        );
    }

    /**
     * Create a server with explicit security dependencies.
     *
     * This constructor will support future automated tests.
     */
    public CommandServer(
        final int port,
        final MessageAuthenticator messageAuthenticator,
        final ReplayProtectionService replayProtectionService
    ) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException(
                "Port must be between 1 and 65535."
            );
        }

        if (messageAuthenticator == null) {
            throw new IllegalArgumentException(
                "messageAuthenticator cannot be null"
            );
        }

        if (replayProtectionService == null) {
            throw new IllegalArgumentException(
                "replayProtectionService cannot be null"
            );
        }

        this.port = port;
        this.commandParser = new CommandMessageParser();
        this.commandProcessor = new CommandProcessor();
        this.messageAuthenticator = messageAuthenticator;
        this.replayProtectionService =
            replayProtectionService;
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Start the TCP command server.
     */
    public void start() throws IOException {
        try (ServerSocket serverSocket =
                 new ServerSocket(port)) {

            System.out.println(
                "TCP command server listening on port "
                    + port + "."
            );

            System.out.println(
                "HMAC-SHA256 authentication enabled."
            );

            System.out.println(
                "Replay and timestamp protection enabled."
            );

            System.out.println(
                "Maximum command age: "
                    + ReplayProtectionService
                        .DEFAULT_MAXIMUM_MESSAGE_AGE
                        .toSeconds()
                    + " seconds."
            );

            System.out.println(
                "Waiting for Python control station..."
            );

            while (true) {
                try {
                    final Socket clientSocket =
                        serverSocket.accept();

                    handleClient(
                        clientSocket
                    );
                } catch (IOException error) {
                    System.err.println(
                        "[CLIENT ERROR] "
                            + error.getMessage()
                    );
                }

                System.out.println(
                    "Waiting for Python control station..."
                );
            }
        }
    }

    /**
     * Handle one connected Python control station.
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
     * Parse, authenticate, replay-check, and process one command.
     */
    private CommandAcknowledgement processCommand(
        final String jsonMessage
    ) {
        try {
            final CommandMessage command =
                commandParser.parse(jsonMessage);

            // HMAC verification must occur before replay-state updates.
            if (!messageAuthenticator.verify(command)) {
                System.out.println(
                    "[AUTHENTICATION FAILED] "
                        + command.getMessageId()
                );

                return CommandAcknowledgement.unauthorized(
                    command.getMessageId(),
                    command.getCommandType().name(),
                    "HMAC-SHA256 signature verification failed.",
                    commandProcessor.getCurrentState()
                );
            }

            System.out.println(
                "[AUTHENTICATED] "
                    + command.getMessageId()
            );

            // Reject duplicates, stale timestamps, future timestamps,
            // and non-increasing sequence numbers.
            final SecurityValidationResult securityResult =
                replayProtectionService.validateAndRecord(
                    command
                );

            if (!securityResult.isAccepted()) {
                System.out.println(
                    "[SECURITY REJECTED] "
                        + command.getMessageId()
                        + " | "
                        + securityResult.getCode()
                        + " | "
                        + securityResult.getMessage()
                );

                return CommandAcknowledgement.securityRejected(
                    command.getMessageId(),
                    command.getCommandType().name(),
                    securityResult.getCode(),
                    securityResult.getMessage(),
                    commandProcessor.getCurrentState()
                );
            }

            System.out.println(
                "[SECURITY ACCEPTED] "
                    + command.getMessageId()
                    + " | Sequence: "
                    + command.getSequenceNumber()
            );

            final CommandResult result =
                commandProcessor.process(command);

            System.out.println(result);

            return CommandAcknowledgement.fromResult(
                result
            );
        } catch (CommandValidationException error) {
            System.out.println(
                "[INVALID COMMAND] "
                    + error.getMessage()
            );

            return CommandAcknowledgement.invalid(
                error.getMessage(),
                commandProcessor.getCurrentState()
            );
        } catch (RuntimeException error) {
            System.err.println(
                "[PROCESSING ERROR] "
                    + error.getMessage()
            );

            return CommandAcknowledgement.invalid(
                "Unexpected command-processing failure.",
                commandProcessor.getCurrentState()
            );
        }
    }

    /**
     * Serialize and send one JSON acknowledgement.
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

        writer.write(
            acknowledgementJson
        );

        writer.newLine();
        writer.flush();

        System.out.println(
            "[ACK SENT] " + acknowledgementJson
        );

        System.out.println(
            "------------------------------------------------------------"
        );
    }

    public String getCurrentStateName() {
        return commandProcessor
            .getCurrentState()
            .name();
    }
}