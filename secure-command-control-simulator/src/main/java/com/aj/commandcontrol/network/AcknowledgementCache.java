package com.aj.commandcontrol.network;

import com.aj.commandcontrol.model.CommandAcknowledgement;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Stores acknowledgements for commands that have already been processed.
 *
 * When the control station retries an identical command because an ACK
 * was lost, the server returns the cached acknowledgement instead of
 * executing the command a second time.
 */
public final class AcknowledgementCache {

    /**
     * Stores one original signature and its completed acknowledgement.
     *
     * The signature is retained so a different command cannot reuse
     * an existing message ID.
     */
    private record CacheEntry(
        String signature,
        CommandAcknowledgement acknowledgement
    ) {
        private CacheEntry {
            Objects.requireNonNull(signature);
            Objects.requireNonNull(acknowledgement);
        }
    }

    // Cached command results indexed by message ID.
    private final Map<String, CacheEntry> entries =
        new HashMap<>();

    /**
     * Store one completed acknowledgement.
     *
     * @param messageId unique command identifier
     * @param signature authenticated command signature
     * @param acknowledgement completed command result
     */
    public synchronized void store(
        final String messageId,
        final String signature,
        final CommandAcknowledgement acknowledgement
    ) {
        Objects.requireNonNull(
            messageId,
            "messageId cannot be null"
        );

        Objects.requireNonNull(
            signature,
            "signature cannot be null"
        );

        Objects.requireNonNull(
            acknowledgement,
            "acknowledgement cannot be null"
        );

        entries.putIfAbsent(
            messageId,
            new CacheEntry(
                signature,
                acknowledgement
            )
        );
    }

    /**
     * Find a cached acknowledgement for one message ID.
     *
     * @param messageId command identifier
     * @return cached acknowledgement when available
     */
    public synchronized Optional<CommandAcknowledgement> findAcknowledgement(
        final String messageId
    ) {
        final CacheEntry cacheEntry =
            entries.get(messageId);

        if (cacheEntry == null) {
            return Optional.empty();
        }

        return Optional.of(
            cacheEntry.acknowledgement()
        );
    }

    /**
     * Verify that a repeated message ID uses the original signature.
     *
     * A matching signature indicates an identical authenticated retry.
     * A different signature indicates message-ID reuse or tampering.
     *
     * @param messageId command identifier
     * @param signature incoming command signature
     * @return true when the stored and incoming signatures match
     */
    public synchronized boolean signatureMatches(
        final String messageId,
        final String signature
    ) {
        final CacheEntry cacheEntry =
            entries.get(messageId);

        return cacheEntry != null
            && cacheEntry.signature().equals(signature);
    }

    /**
     * Determine whether one message ID has already been processed.
     */
    public synchronized boolean contains(
        final String messageId
    ) {
        return entries.containsKey(messageId);
    }

    /**
     * Return the number of cached command results.
     */
    public synchronized int size() {
        return entries.size();
    }
}