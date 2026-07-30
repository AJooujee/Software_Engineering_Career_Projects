package com.aj.commandcontrol.logging;

import com.aj.commandcontrol.model.AcknowledgementStatus;
import com.aj.commandcontrol.model.CommandAcknowledgement;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for newline-delimited structured JSON audit logging.
 */
class AuditLoggerTests {

    /**
     * JUnit automatically creates and removes this temporary directory.
     */
    @TempDir
    Path temporaryDirectory;

    /**
     * Verify that logging creates a JSON audit file.
     */
    @Test
    void createsAuditLogAndWritesJsonEvent() throws IOException {
        final Path logPath =
            temporaryDirectory.resolve("audit.log");

        final AuditLogger logger =
            new AuditLogger(logPath);

        logger.logSystemEvent(
            AuditLevel.INFO,
            "SERVER_STARTED",
            "Test server started."
        );

        assertTrue(Files.exists(logPath));

        final String content =
            Files.readString(logPath);

        assertTrue(
            content.contains("\"eventType\":\"SERVER_STARTED\"")
        );

        assertTrue(
            content.contains("\"level\":\"INFO\"")
        );
    }

    /**
     * Verify that later events are appended instead of replacing data.
     */
    @Test
    void appendsMultipleAuditEvents() throws IOException {
        final Path logPath =
            temporaryDirectory.resolve("audit.log");

        final AuditLogger logger =
            new AuditLogger(logPath);

        logger.logSystemEvent(
            AuditLevel.INFO,
            "SERVER_STARTED",
            "Server started."
        );

        logger.logSystemEvent(
            AuditLevel.INFO,
            "CLIENT_CONNECTED",
            "Client connected."
        );

        final List<String> lines =
            Files.readAllLines(logPath);

        assertEquals(2, lines.size());
        assertTrue(lines.get(0).contains("SERVER_STARTED"));
        assertTrue(lines.get(1).contains("CLIENT_CONNECTED"));
    }

    /**
     * Verify that acknowledgement details are recorded correctly.
     */
    @Test
    void logsAcknowledgementFields() throws IOException {
        final Path logPath =
            temporaryDirectory.resolve("audit.log");

        final AuditLogger logger =
            new AuditLogger(logPath);

        final CommandAcknowledgement acknowledgement =
            new CommandAcknowledgement(
                "CMD-000001",
                AcknowledgementStatus.ACCEPTED,
                "START_SYSTEM",
                "OFFLINE",
                "STANDBY",
                "Command accepted."
            );

        logger.logAcknowledgement(
            "ACK_SENT",
            acknowledgement
        );

        final String content =
            Files.readString(logPath);

        assertTrue(
            content.contains("\"eventType\":\"ACK_SENT\"")
        );

        assertTrue(
            content.contains("\"messageId\":\"CMD-000001\"")
        );

        assertTrue(
            content.contains("\"previousState\":\"OFFLINE\"")
        );

        assertTrue(
            content.contains("\"currentState\":\"STANDBY\"")
        );
    }
}