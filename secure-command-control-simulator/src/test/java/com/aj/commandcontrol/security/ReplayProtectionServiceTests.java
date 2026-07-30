package com.aj.commandcontrol.security;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandType;

import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for replay, duplicate, and timestamp protection.
 */
class ReplayProtectionServiceTests {

    private static final Instant FIXED_TIME =
        Instant.parse("2026-07-30T20:00:00Z");

    /**
     * Verify acceptance of a fresh command with an increasing sequence.
     */
    @Test
    void acceptsFreshCommand() {
        final ReplayProtectionService service =
            createService();

        final SecurityValidationResult result =
            service.validateAndRecord(
                createCommand(
                    "CMD-000001",
                    "UNIT-01",
                    1,
                    FIXED_TIME
                )
            );

        assertTrue(result.isAccepted());
        assertEquals(1, service.getProcessedMessageCount());
        assertEquals(
            1L,
            service.getHighestSequenceNumber("UNIT-01")
        );
    }

    /**
     * Verify that the same message ID cannot be recorded twice.
     */
    @Test
    void rejectsDuplicateMessageId() {
        final ReplayProtectionService service =
            createService();

        service.validateAndRecord(
            createCommand(
                "CMD-000001",
                "UNIT-01",
                1,
                FIXED_TIME
            )
        );

        final SecurityValidationResult result =
            service.validateAndRecord(
                createCommand(
                    "CMD-000001",
                    "UNIT-01",
                    2,
                    FIXED_TIME
                )
            );

        assertFalse(result.isAccepted());
        assertEquals(
            "DUPLICATE_MESSAGE_ID",
            result.getCode()
        );
    }

    /**
     * Verify that sequence numbers must increase for one target.
     */
    @Test
    void rejectsReplayedSequenceNumber() {
        final ReplayProtectionService service =
            createService();

        service.validateAndRecord(
            createCommand(
                "CMD-000001",
                "UNIT-01",
                5,
                FIXED_TIME
            )
        );

        final SecurityValidationResult result =
            service.validateAndRecord(
                createCommand(
                    "CMD-000002",
                    "UNIT-01",
                    5,
                    FIXED_TIME
                )
            );

        assertFalse(result.isAccepted());
        assertEquals(
            "REPLAYED_SEQUENCE_NUMBER",
            result.getCode()
        );
    }

    /**
     * Verify rejection of a command older than 30 seconds.
     */
    @Test
    void rejectsExpiredTimestamp() {
        final ReplayProtectionService service =
            createService();

        final SecurityValidationResult result =
            service.validateAndRecord(
                createCommand(
                    "CMD-000001",
                    "UNIT-01",
                    1,
                    FIXED_TIME.minusSeconds(31)
                )
            );

        assertFalse(result.isAccepted());
        assertEquals(
            "EXPIRED_TIMESTAMP",
            result.getCode()
        );
    }

    /**
     * Verify rejection beyond the five-second future tolerance.
     */
    @Test
    void rejectsFutureTimestamp() {
        final ReplayProtectionService service =
            createService();

        final SecurityValidationResult result =
            service.validateAndRecord(
                createCommand(
                    "CMD-000001",
                    "UNIT-01",
                    1,
                    FIXED_TIME.plusSeconds(6)
                )
            );

        assertFalse(result.isAccepted());
        assertEquals(
            "FUTURE_TIMESTAMP",
            result.getCode()
        );
    }

    /**
     * Verify that sequence tracking is independent per target.
     */
    @Test
    void allowsSameSequenceForDifferentTargets() {
        final ReplayProtectionService service =
            createService();

        final SecurityValidationResult firstResult =
            service.validateAndRecord(
                createCommand(
                    "CMD-000001",
                    "UNIT-01",
                    1,
                    FIXED_TIME
                )
            );

        final SecurityValidationResult secondResult =
            service.validateAndRecord(
                createCommand(
                    "CMD-000002",
                    "UNIT-02",
                    1,
                    FIXED_TIME
                )
            );

        assertTrue(firstResult.isAccepted());
        assertTrue(secondResult.isAccepted());
    }

    /**
     * Create replay protection with a deterministic fixed clock.
     */
    private static ReplayProtectionService createService() {
        return new ReplayProtectionService(
            Clock.fixed(
                FIXED_TIME,
                ZoneOffset.UTC
            ),
            Duration.ofSeconds(30),
            Duration.ofSeconds(5)
        );
    }

    /**
     * Create one authenticated command model for security testing.
     */
    private static CommandMessage createCommand(
        final String messageId,
        final String targetId,
        final long sequenceNumber,
        final Instant timestamp
    ) {
        return new CommandMessage(
            messageId,
            CommandType.START_SYSTEM,
            targetId,
            sequenceNumber,
            timestamp,
            Collections.emptyMap(),
            "a".repeat(64)
        );
    }
}