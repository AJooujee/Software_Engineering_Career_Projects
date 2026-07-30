package com.aj.commandcontrol.network;

import com.aj.commandcontrol.logging.AuditLevel;
import com.aj.commandcontrol.logging.AuditLogger;
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
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

/**
 * TCP server that receives authenticated, replay-protected commands,
 * supports reliable retries, and writes structured audit events.
 */
public final class CommandServer {

    // TCP port shared with the Python control station.
    public static final int DEFAULT_PORT = 6060;

    // Optional setting used to simulate one lost acknowledgement.
    public static final String DROP_ACK_ENVIRONMENT_VARIABLE =
        "COMMAND_CONTROL_DROP_FIRST_ACK_MESSAGE_ID";

    private final CommandMessageParser commandParser;
    private final CommandProcessor commandProcessor;
    private final MessageAuthenticator messageAuthenticator;
    private final ReplayProtectionService replayProtectionService;
    private final AcknowledgementCache acknowledgementCache;
    private final AuditLogger auditLogger;
    private final ObjectMapper objectMapper;
    private final Set<String> intentionallyDroppedAcknowledgements;

    private final int port;
    private final String messageIdWhoseFirstAckShouldBeDropped;

    /**
     * Create a server using production dependencies.
     */
    public CommandServer() {
        this(
            DEFAULT_PORT,
            MessageAuthenticator.fromEnvironment(),
            new ReplayProtectionService(),
            new AcknowledgementCache(),
            new AuditLogger(),
            System.getenv(
                DROP_ACK_ENVIRONMENT_VARIABLE
            )
        );
    }

    /**
     * Create a server with explicit dependencies.
     *
     * Dependency injection makes the class easier to test later.
     */
    public CommandServer(
        final int port,
        final MessageAuthenticator messageAuthenticator,
        final ReplayProtectionService replayProtectionService,
        final AcknowledgementCache acknowledgementCache,
        final AuditLogger auditLogger,
        final String messageIdWhoseFirstAckShouldBeDropped
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

        if (acknowledgementCache == null) {
            throw new IllegalArgumentException(
                "acknowledgementCache cannot be null"
            );
        }

        if (auditLogger == null) {
            throw new IllegalArgumentException(
                "auditLogger cannot be null"
            );
        }

        this.port = port;
        this.commandParser = new CommandMessageParser();
        this.commandProcessor = new CommandProcessor();
        this.messageAuthenticator = messageAuthenticator;
        this.replayProtectionService =
            replayProtectionService;
        this.acknowledgementCache =
            acknowledgementCache;
        this.auditLogger = auditLogger;
        this.objectMapper = new ObjectMapper();

        this.intentionallyDroppedAcknowledgements =
            new HashSet<>();

        if (
            messageIdWhoseFirstAckShouldBeDropped == null
            || messageIdWhoseFirstAckShouldBeDropped.isBlank()
        ) {
            this.messageIdWhoseFirstAckShouldBeDropped = null;
        } else {
            this.messageIdWhoseFirstAckShouldBeDropped =
                messageIdWhoseFirstAckShouldBeDropped.trim();
        }
    }

    /**
     * Start the TCP command server.
     */
    public void start() throws IOException {
        try (
            ServerSocket serverSocket =
                new ServerSocket(port)
        ) {
            auditLogger.logSystemEvent(
                AuditLevel.INFO,
                "SERVER_STARTED",
                "TCP command server started on port "
                    + port + "."
            );

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
                "ACK retry and idempotency support enabled."
            );

            System.out.println(
                "Structured audit logging enabled: "
                    + auditLogger.getLogPath()
            );

            System.out.println(
                "Maximum command age: "
                    + ReplayProtectionService
                        .DEFAULT_MAXIMUM_MESSAGE_AGE
                        .toSeconds()
                    + " seconds."
            );

            if (
                messageIdWhoseFirstAckShouldBeDropped
                    != null
            ) {
                System.out.println(
                    "Development ACK-loss simulation enabled for "
                        + messageIdWhoseFirstAckShouldBeDropped
                        + "."
                );
            }

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
                    auditLogger.logSystemEvent(
                        AuditLevel.ERROR,
                        "CLIENT_CONNECTION_ERROR",
                        error.getMessage()
                    );

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
     * Handle commands from one connected control station.
     */
    private void handleClient(
        final Socket clientSocket
    ) throws IOException {
        final String remoteAddress =
            clientSocket
                .getRemoteSocketAddress()
                .toString();

        auditLogger.logSystemEvent(
            AuditLevel.INFO,
            "CLIENT_CONNECTED",
            "Python control station connected from "
                + remoteAddress + "."
        );

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
                    + remoteAddress
            );

            String jsonLine;

            while (
                (jsonLine = reader.readLine()) != null
            ) {
                if (jsonLine.isBlank()) {
                    continue;
                }

                System.out.println(
                    "[RECEIVED] " + jsonLine
                );

                final CommandAcknowledgement acknowledgement =
                    processCommand(jsonLine);

                if (
                    shouldDropAcknowledgement(
                        acknowledgement.getMessageId()
                    )
                ) {
                    auditLogger.logCommandEvent(
                        AuditLevel.WARNING,
                        "ACK_DROPPED_FOR_TEST",
                        acknowledgement.getMessageId(),
                        acknowledgement.getCommandType(),
                        acknowledgement.getStatus().name(),
                        acknowledgement.getPreviousState(),
                        acknowledgement.getCurrentState(),
                        "The first acknowledgement was intentionally "
                            + "dropped to test retry behavior."
                    );

                    System.out.println(
                        "[ACK DROPPED FOR TEST] "
                            + acknowledgement.getMessageId()
                    );

                    System.out.println(
                        "Closing the connection to simulate "
                            + "acknowledgement loss."
                    );

                    return;
                }

                sendAcknowledgement(
                    writer,
                    acknowledgement
                );
            }

            System.out.println(
                "Python control station disconnected."
            );
        } finally {
            auditLogger.logSystemEvent(
                AuditLevel.INFO,
                "CLIENT_DISCONNECTED",
                "Python control station disconnected from "
                    + remoteAddress + "."
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

            if (!messageAuthenticator.verify(command)) {
                auditLogger.logCommandEvent(
                    AuditLevel.SECURITY,
                    "AUTHENTICATION_FAILED",
                    command.getMessageId(),
                    command.getCommandType().name(),
                    "UNAUTHORIZED",
                    commandProcessor.getCurrentState().name(),
                    commandProcessor.getCurrentState().name(),
                    "HMAC-SHA256 signature verification failed."
                );

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

            auditLogger.logCommandEvent(
                AuditLevel.INFO,
                "AUTHENTICATION_PASSED",
                command.getMessageId(),
                command.getCommandType().name(),
                "AUTHENTICATED",
                commandProcessor.getCurrentState().name(),
                commandProcessor.getCurrentState().name(),
                "HMAC-SHA256 signature verified."
            );

            System.out.println(
                "[AUTHENTICATED] "
                    + command.getMessageId()
            );

            if (
                acknowledgementCache.contains(
                    command.getMessageId()
                )
            ) {
                if (
                    acknowledgementCache.signatureMatches(
                        command.getMessageId(),
                        command.getSignature()
                    )
                ) {
                    final Optional<CommandAcknowledgement>
                        cachedAcknowledgement =
                            acknowledgementCache
                                .findAcknowledgement(
                                    command.getMessageId()
                                );

                    if (cachedAcknowledgement.isPresent()) {
                        final CommandAcknowledgement acknowledgement =
                            cachedAcknowledgement.get();

                        auditLogger.logCommandEvent(
                            AuditLevel.INFO,
                            "IDEMPOTENT_RETRY",
                            command.getMessageId(),
                            command.getCommandType().name(),
                            acknowledgement
                                .getStatus()
                                .name(),
                            acknowledgement.getPreviousState(),
                            acknowledgement.getCurrentState(),
                            "Cached acknowledgement returned without "
                                + "executing the command again."
                        );

                        System.out.println(
                            "[IDEMPOTENT RETRY] "
                                + command.getMessageId()
                                + " | Returning cached ACK."
                        );

                        return acknowledgement;
                    }
                }

                auditLogger.logCommandEvent(
                    AuditLevel.SECURITY,
                    "MESSAGE_ID_COLLISION",
                    command.getMessageId(),
                    command.getCommandType().name(),
                    "SECURITY_REJECTED",
                    commandProcessor.getCurrentState().name(),
                    commandProcessor.getCurrentState().name(),
                    "The message ID was reused with different "
                        + "authenticated content."
                );

                return CommandAcknowledgement.securityRejected(
                    command.getMessageId(),
                    command.getCommandType().name(),
                    "MESSAGE_ID_COLLISION",
                    "The message ID was previously used "
                        + "with different authenticated content.",
                    commandProcessor.getCurrentState()
                );
            }

            final SecurityValidationResult securityResult =
                replayProtectionService.validateAndRecord(
                    command
                );

            if (!securityResult.isAccepted()) {
                auditLogger.logCommandEvent(
                    AuditLevel.SECURITY,
                    "SECURITY_VALIDATION_REJECTED",
                    command.getMessageId(),
                    command.getCommandType().name(),
                    "SECURITY_REJECTED",
                    commandProcessor.getCurrentState().name(),
                    commandProcessor.getCurrentState().name(),
                    securityResult.getCode()
                        + ": "
                        + securityResult.getMessage()
                );

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

            auditLogger.logCommandEvent(
                AuditLevel.INFO,
                "SECURITY_VALIDATION_PASSED",
                command.getMessageId(),
                command.getCommandType().name(),
                "SECURITY_ACCEPTED",
                commandProcessor.getCurrentState().name(),
                commandProcessor.getCurrentState().name(),
                "Replay and timestamp validation passed."
            );

            final CommandResult result =
                commandProcessor.process(command);

            final CommandAcknowledgement acknowledgement =
                CommandAcknowledgement.fromResult(result);

            auditLogger.logCommandEvent(
                result.isAccepted()
                    ? AuditLevel.INFO
                    : AuditLevel.WARNING,
                result.isAccepted()
                    ? "COMMAND_ACCEPTED"
                    : "COMMAND_REJECTED",
                result.getMessageId(),
                result.getCommandType().name(),
                result.getStatus().name(),
                result.getPreviousState().name(),
                result.getCurrentState().name(),
                result.getMessage()
            );

            System.out.println(result);

            acknowledgementCache.store(
                command.getMessageId(),
                command.getSignature(),
                acknowledgement
            );

            return acknowledgement;
        } catch (CommandValidationException error) {
            auditLogger.logSystemEvent(
                AuditLevel.WARNING,
                "INVALID_COMMAND",
                error.getMessage()
            );

            System.out.println(
                "[INVALID COMMAND] "
                    + error.getMessage()
            );

            return CommandAcknowledgement.invalid(
                error.getMessage(),
                commandProcessor.getCurrentState()
            );
        } catch (RuntimeException error) {
            auditLogger.logSystemEvent(
                AuditLevel.ERROR,
                "COMMAND_PROCESSING_ERROR",
                error.getMessage()
            );

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
     * Determine whether the configured first acknowledgement
     * should be intentionally dropped.
     */
    private synchronized boolean shouldDropAcknowledgement(
        final String messageId
    ) {
        if (
            messageIdWhoseFirstAckShouldBeDropped == null
            || !messageIdWhoseFirstAckShouldBeDropped.equals(
                messageId
            )
        ) {
            return false;
        }

        return intentionallyDroppedAcknowledgements.add(
            messageId
        );
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

        auditLogger.logAcknowledgement(
            "ACK_SENT",
            acknowledgement
        );

        System.out.println(
            "[ACK SENT] "
                + acknowledgementJson
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