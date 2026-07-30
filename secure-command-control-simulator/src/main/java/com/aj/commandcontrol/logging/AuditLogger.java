package com.aj.commandcontrol.logging;

import com.aj.commandcontrol.model.CommandAcknowledgement;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Objects;

/**
 * Writes newline-delimited JSON audit events to a persistent log file.
 *
 * Each log entry occupies one line, making the file suitable for:
 * - manual inspection
 * - automated parsing
 * - log aggregation
 * - regression-test verification
 */
public final class AuditLogger {

    // Default project-relative audit log path.
    public static final Path DEFAULT_LOG_PATH =
        Path.of(
            "logs",
            "command_audit.log"
        );

    // Jackson serializer used to convert events into compact JSON.
    private final ObjectMapper objectMapper;

    // Final destination of the audit log.
    private final Path logPath;

    /**
     * Create a logger using logs/command_audit.log.
     */
    public AuditLogger() {
        this(DEFAULT_LOG_PATH);
    }

    /**
     * Create a logger using a specified path.
     *
     * @param logPath audit-log path
     */
    public AuditLogger(
        final Path logPath
    ) {
        this.logPath = Objects.requireNonNull(
            logPath,
            "logPath cannot be null"
        );

        this.objectMapper = new ObjectMapper();

        initializeLogDirectory();
    }

    /**
     * Create the parent log directory when it does not yet exist.
     */
    private void initializeLogDirectory() {
        final Path parentDirectory =
            logPath.getParent();

        if (parentDirectory == null) {
            return;
        }

        try {
            Files.createDirectories(
                parentDirectory
            );
        } catch (IOException error) {
            throw new IllegalStateException(
                "Unable to create the audit-log directory: "
                    + parentDirectory,
                error
            );
        }
    }

    /**
     * Write one event as a compact JSON line.
     *
     * synchronized prevents multiple future client threads from
     * writing interleaved or corrupted log entries.
     *
     * @param event audit event
     */
    public synchronized void log(
        final AuditEvent event
    ) {
        Objects.requireNonNull(
            event,
            "event cannot be null"
        );

        final String eventJson;

        try {
            eventJson =
                objectMapper.writeValueAsString(
                    event
                );
        } catch (JsonProcessingException error) {
            throw new IllegalStateException(
                "Unable to serialize the audit event.",
                error
            );
        }

        try (
            BufferedWriter writer =
                Files.newBufferedWriter(
                    logPath,
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
                )
        ) {
            writer.write(
                eventJson
            );

            writer.newLine();
        } catch (IOException error) {
            throw new IllegalStateException(
                "Unable to write the audit event to "
                    + logPath,
                error
            );
        }
    }

    /**
     * Log a general system event without command details.
     */
    public void logSystemEvent(
        final AuditLevel level,
        final String eventType,
        final String details
    ) {
        log(
            new AuditEvent(
                level,
                eventType,
                "",
                "",
                "",
                "",
                "",
                details
            )
        );
    }

    /**
     * Log an event associated with one command.
     */
    public void logCommandEvent(
        final AuditLevel level,
        final String eventType,
        final String messageId,
        final String commandType,
        final String status,
        final String previousState,
        final String currentState,
        final String details
    ) {
        log(
            new AuditEvent(
                level,
                eventType,
                messageId,
                commandType,
                status,
                previousState,
                currentState,
                details
            )
        );
    }

    /**
     * Log one completed acknowledgement.
     */
    public void logAcknowledgement(
        final String eventType,
        final CommandAcknowledgement acknowledgement
    ) {
        Objects.requireNonNull(
            acknowledgement,
            "acknowledgement cannot be null"
        );

        logCommandEvent(
            AuditLevel.INFO,
            eventType,
            acknowledgement.getMessageId(),
            acknowledgement.getCommandType(),
            acknowledgement.getStatus().name(),
            acknowledgement.getPreviousState(),
            acknowledgement.getCurrentState(),
            acknowledgement.getMessage()
        );
    }

    /**
     * Return the configured audit-log location.
     */
    public Path getLogPath() {
        return logPath;
    }
}