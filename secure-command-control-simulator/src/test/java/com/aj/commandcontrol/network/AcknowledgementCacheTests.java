package com.aj.commandcontrol.network;

import com.aj.commandcontrol.model.AcknowledgementStatus;
import com.aj.commandcontrol.model.CommandAcknowledgement;

import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for cached acknowledgements and idempotent retries.
 */
class AcknowledgementCacheTests {

    /**
     * Verify that a new cache contains no entries.
     */
    @Test
    void newCacheIsEmpty() {
        final AcknowledgementCache cache =
            new AcknowledgementCache();

        assertEquals(0, cache.size());
        assertFalse(cache.contains("CMD-000001"));
    }

    /**
     * Verify that a stored acknowledgement can be retrieved.
     */
    @Test
    void storesAndFindsAcknowledgement() {
        final AcknowledgementCache cache =
            new AcknowledgementCache();

        final CommandAcknowledgement acknowledgement =
            createAcknowledgement("CMD-000001");

        cache.store(
            "CMD-000001",
            "a".repeat(64),
            acknowledgement
        );

        final Optional<CommandAcknowledgement> cachedResult =
            cache.findAcknowledgement("CMD-000001");

        assertTrue(cachedResult.isPresent());
        assertEquals(
            "CMD-000001",
            cachedResult.get().getMessageId()
        );
    }

    /**
     * Verify signature matching for an identical retry.
     */
    @Test
    void identifiesMatchingRetrySignature() {
        final AcknowledgementCache cache =
            new AcknowledgementCache();

        cache.store(
            "CMD-000001",
            "a".repeat(64),
            createAcknowledgement("CMD-000001")
        );

        assertTrue(
            cache.signatureMatches(
                "CMD-000001",
                "a".repeat(64)
            )
        );

        assertFalse(
            cache.signatureMatches(
                "CMD-000001",
                "b".repeat(64)
            )
        );
    }

    /**
     * Verify that putIfAbsent preserves the original command result.
     */
    @Test
    void doesNotReplaceExistingAcknowledgement() {
        final AcknowledgementCache cache =
            new AcknowledgementCache();

        cache.store(
            "CMD-000001",
            "a".repeat(64),
            createAcknowledgement("CMD-000001")
        );

        final CommandAcknowledgement replacement =
            new CommandAcknowledgement(
                "CMD-000001",
                AcknowledgementStatus.REJECTED,
                "START_SYSTEM",
                "STANDBY",
                "STANDBY",
                "Replacement result"
            );

        cache.store(
            "CMD-000001",
            "b".repeat(64),
            replacement
        );

        final CommandAcknowledgement stored =
            cache.findAcknowledgement("CMD-000001")
                .orElseThrow();

        assertEquals(
            AcknowledgementStatus.ACCEPTED,
            stored.getStatus()
        );

        assertTrue(
            cache.signatureMatches(
                "CMD-000001",
                "a".repeat(64)
            )
        );
    }

    /**
     * Create one accepted acknowledgement for cache tests.
     */
    private static CommandAcknowledgement createAcknowledgement(
        final String messageId
    ) {
        return new CommandAcknowledgement(
            messageId,
            AcknowledgementStatus.ACCEPTED,
            "START_SYSTEM",
            "OFFLINE",
            "STANDBY",
            "Remote unit entered standby mode."
        );
    }
}