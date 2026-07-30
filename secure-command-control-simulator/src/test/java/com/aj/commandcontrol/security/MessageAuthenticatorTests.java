package com.aj.commandcontrol.security;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandType;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for HMAC-SHA256 command authentication.
 */
class MessageAuthenticatorTests {

    private static final String TEST_SECRET =
        "Unit-Test-Shared-Secret-2026";

    /**
     * Verify that a correctly calculated signature is accepted.
     */
    @Test
    void verifiesCorrectSignature() {
        final MessageAuthenticator authenticator =
            new MessageAuthenticator(TEST_SECRET);

        final CommandMessage signedCommand =
            createSignedCommand(
                authenticator,
                Map.of("operation", "PRIMARY_SENSOR_SCAN")
            );

        assertTrue(
            authenticator.verify(signedCommand)
        );
    }

    /**
     * Verify that payload modification invalidates the signature.
     */
    @Test
    void rejectsCommandWhosePayloadWasModified() {
        final MessageAuthenticator authenticator =
            new MessageAuthenticator(TEST_SECRET);

        final CommandMessage originalCommand =
            createSignedCommand(
                authenticator,
                Map.of("operation", "PRIMARY_SENSOR_SCAN")
            );

        // Reuse the original signature with different payload content.
        final CommandMessage tamperedCommand =
            new CommandMessage(
                originalCommand.getMessageId(),
                originalCommand.getCommandType(),
                originalCommand.getTargetId(),
                originalCommand.getSequenceNumber(),
                originalCommand.getTimestamp(),
                Map.of("operation", "UNAUTHORIZED_SCAN"),
                originalCommand.getSignature()
            );

        assertFalse(
            authenticator.verify(tamperedCommand)
        );
    }

    /**
     * Verify that a different shared secret cannot validate the command.
     */
    @Test
    void rejectsSignatureCreatedWithDifferentSecret() {
        final MessageAuthenticator signingAuthenticator =
            new MessageAuthenticator(TEST_SECRET);

        final MessageAuthenticator verifyingAuthenticator =
            new MessageAuthenticator(
                "Different-Shared-Secret-2026"
            );

        final CommandMessage command =
            createSignedCommand(
                signingAuthenticator,
                Map.of()
            );

        assertFalse(
            verifyingAuthenticator.verify(command)
        );
    }

    /**
     * Create a correctly signed production command.
     */
    private static CommandMessage createSignedCommand(
        final MessageAuthenticator authenticator,
        final Map<String, Object> payload
    ) {
        // First create a placeholder model so the canonical HMAC can
        // be calculated without including the signature itself.
        final CommandMessage unsignedCommand =
            new CommandMessage(
                "CMD-000001",
                CommandType.ACTIVATE_SYSTEM,
                "UNIT-01",
                1,
                Instant.parse("2026-07-30T20:00:00Z"),
                payload,
                "0".repeat(64)
            );

        final String calculatedSignature =
            authenticator.calculateSignature(
                unsignedCommand
            );

        return new CommandMessage(
            unsignedCommand.getMessageId(),
            unsignedCommand.getCommandType(),
            unsignedCommand.getTargetId(),
            unsignedCommand.getSequenceNumber(),
            unsignedCommand.getTimestamp(),
            unsignedCommand.getPayload(),
            calculatedSignature
        );
    }
}