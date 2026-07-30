package com.aj.commandcontrol.parsing;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandType;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * Unit tests for JSON command parsing and structural validation.
 */
class CommandMessageParserTests {

    // Parser under test.
    private final CommandMessageParser parser =
        new CommandMessageParser();

    /**
     * Verify that a complete valid command is parsed correctly.
     */
    @Test
    void parsesValidCommand() throws CommandValidationException {
        final CommandMessage command = parser.parse(
            validCommandJson()
        );

        assertEquals("CMD-000001", command.getMessageId());
        assertEquals(CommandType.START_SYSTEM, command.getCommandType());
        assertEquals("UNIT-01", command.getTargetId());
        assertEquals(1L, command.getSequenceNumber());
        assertEquals("a".repeat(64), command.getSignature());
    }

    /**
     * Verify rejection of syntactically malformed JSON.
     */
    @Test
    void rejectsMalformedJson() {
        final String malformedJson =
            """
            {
              "message_id": "CMD-000001",
              "command_type": "START_SYSTEM"
            """;

        assertThrows(
            CommandValidationException.class,
            () -> parser.parse(malformedJson)
        );
    }

    /**
     * Verify rejection when a required field is missing.
     */
    @Test
    void rejectsMissingTargetId() {
        final String json =
            """
            {
              "message_id": "CMD-000001",
              "command_type": "START_SYSTEM",
              "sequence_number": 1,
              "timestamp": "2026-07-30T20:00:00Z",
              "payload": {},
              "signature": "%s"
            }
            """.formatted("a".repeat(64));

        final CommandValidationException error =
            assertThrows(
                CommandValidationException.class,
                () -> parser.parse(json)
            );

        assertEquals(
            "Missing required field: target_id",
            error.getMessage()
        );
    }

    /**
     * Verify rejection of an unsupported command enum value.
     */
    @Test
    void rejectsUnsupportedCommandType() {
        final String json = validCommandJson()
            .replace(
                "\"START_SYSTEM\"",
                "\"UNKNOWN_OPERATION\""
            );

        final CommandValidationException error =
            assertThrows(
                CommandValidationException.class,
                () -> parser.parse(json)
            );

        assertEquals(
            "Unsupported command type: UNKNOWN_OPERATION",
            error.getMessage()
        );
    }

    /**
     * Verify rejection of sequence numbers below one.
     */
    @Test
    void rejectsNonpositiveSequenceNumber() {
        final String json = validCommandJson()
            .replace(
                "\"sequence_number\": 1",
                "\"sequence_number\": 0"
            );

        assertThrows(
            CommandValidationException.class,
            () -> parser.parse(json)
        );
    }

    /**
     * Verify rejection of an invalid ISO-8601 timestamp.
     */
    @Test
    void rejectsInvalidTimestamp() {
        final String json = validCommandJson()
            .replace(
                "2026-07-30T20:00:00Z",
                "not-a-timestamp"
            );

        assertThrows(
            CommandValidationException.class,
            () -> parser.parse(json)
        );
    }

    /**
     * Verify that a SHA-256 signature must contain 64 hex characters.
     */
    @Test
    void rejectsInvalidSignatureLength() {
        final String json = validCommandJson()
            .replace(
                "a".repeat(64),
                "abcd"
            );

        assertThrows(
            CommandValidationException.class,
            () -> parser.parse(json)
        );
    }

    /**
     * Verify rejection of unexpected top-level fields.
     */
    @Test
    void rejectsUnknownTopLevelField() {
        final String json = validCommandJson()
            .replace(
                "\"payload\": {},",
                """
                "payload": {},
                "unexpected_field": true,
                """
            );

        final CommandValidationException error =
            assertThrows(
                CommandValidationException.class,
                () -> parser.parse(json)
            );

        assertEquals(
            "Unknown command field: unexpected_field",
            error.getMessage()
        );
    }

    /**
     * Return one structurally valid authenticated JSON command.
     */
    private static String validCommandJson() {
        return """
            {
              "message_id": "CMD-000001",
              "command_type": "START_SYSTEM",
              "target_id": "UNIT-01",
              "sequence_number": 1,
              "timestamp": "2026-07-30T20:00:00Z",
              "payload": {},
              "signature": "%s"
            }
            """.formatted("a".repeat(64));
    }
}