package com.aj.commandcontrol.security;

import com.aj.commandcontrol.model.CommandMessage;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Prevents duplicate, replayed, stale, and future-dated commands.
 */
public final class ReplayProtectionService {

    // Maximum permitted age of a command.
    public static final Duration DEFAULT_MAXIMUM_MESSAGE_AGE =
        Duration.ofSeconds(30);

    // Small clock difference permitted between control station and server.
    public static final Duration DEFAULT_FUTURE_CLOCK_SKEW =
        Duration.ofSeconds(5);

    // Provides the current time and supports deterministic unit testing.
    private final Clock clock;

    // Maximum permitted age of an incoming command.
    private final Duration maximumMessageAge;

    // Maximum permitted future clock difference.
    private final Duration futureClockSkew;

    // Every successfully validated message ID is stored here.
    private final Set<String> processedMessageIds;

    // Highest accepted sequence number for each remote-unit target.
    private final Map<String, Long> highestSequenceByTarget;

    /**
     * Create replay protection using the system UTC clock.
     */
    public ReplayProtectionService() {
        this(
            Clock.systemUTC(),
            DEFAULT_MAXIMUM_MESSAGE_AGE,
            DEFAULT_FUTURE_CLOCK_SKEW
        );
    }

    /**
     * Create replay protection with explicit timing dependencies.
     *
     * This constructor is useful for deterministic unit tests.
     */
    public ReplayProtectionService(
        final Clock clock,
        final Duration maximumMessageAge,
        final Duration futureClockSkew
    ) {
        this.clock = Objects.requireNonNull(
            clock,
            "clock cannot be null"
        );

        this.maximumMessageAge = requireNonnegativeDuration(
            maximumMessageAge,
            "maximumMessageAge"
        );

        this.futureClockSkew = requireNonnegativeDuration(
            futureClockSkew,
            "futureClockSkew"
        );

        this.processedMessageIds = new HashSet<>();
        this.highestSequenceByTarget = new HashMap<>();
    }

    /**
     * Validate and record one authenticated command.
     *
     * synchronized ensures that two future client threads cannot
     * validate the same message simultaneously.
     */
    public synchronized SecurityValidationResult validateAndRecord(
        final CommandMessage command
    ) {
        Objects.requireNonNull(
            command,
            "command cannot be null"
        );

        final Instant currentTime =
            clock.instant();

        final Instant oldestPermittedTimestamp =
            currentTime.minus(maximumMessageAge);

        final Instant latestPermittedTimestamp =
            currentTime.plus(futureClockSkew);

        // Reject commands older than the permitted message lifetime.
        if (command.getTimestamp().isBefore(
            oldestPermittedTimestamp
        )) {
            return SecurityValidationResult.rejected(
                "EXPIRED_TIMESTAMP",
                "Command timestamp is older than the permitted "
                    + maximumMessageAge.toSeconds()
                    + "-second message lifetime."
            );
        }

        // Reject commands whose timestamp is too far in the future.
        if (command.getTimestamp().isAfter(
            latestPermittedTimestamp
        )) {
            return SecurityValidationResult.rejected(
                "FUTURE_TIMESTAMP",
                "Command timestamp exceeds the permitted "
                    + futureClockSkew.toSeconds()
                    + "-second future clock tolerance."
            );
        }

        // Reject an already processed message identifier.
        if (processedMessageIds.contains(
            command.getMessageId()
        )) {
            return SecurityValidationResult.rejected(
                "DUPLICATE_MESSAGE_ID",
                "The command message ID has already been processed."
            );
        }

        final long highestSequenceNumber =
            highestSequenceByTarget.getOrDefault(
                command.getTargetId(),
                0L
            );

        // A valid sequence number must always move forward.
        if (command.getSequenceNumber()
            <= highestSequenceNumber) {

            return SecurityValidationResult.rejected(
                "REPLAYED_SEQUENCE_NUMBER",
                "Sequence number "
                    + command.getSequenceNumber()
                    + " is not greater than the highest accepted "
                    + "sequence number "
                    + highestSequenceNumber
                    + " for target "
                    + command.getTargetId()
                    + "."
            );
        }

        // Record the authenticated and validated command.
        //
        // The command is recorded before state-machine processing.
        // This prevents a valid but state-rejected command from being
        // transmitted repeatedly with the same identity.
        processedMessageIds.add(
            command.getMessageId()
        );

        highestSequenceByTarget.put(
            command.getTargetId(),
            command.getSequenceNumber()
        );

        return SecurityValidationResult.accepted();
    }

    /**
     * Return the number of unique accepted message IDs.
     */
    public synchronized int getProcessedMessageCount() {
        return processedMessageIds.size();
    }

    /**
     * Return the highest accepted sequence number for one target.
     */
    public synchronized long getHighestSequenceNumber(
        final String targetId
    ) {
        return highestSequenceByTarget.getOrDefault(
            targetId,
            0L
        );
    }

    /**
     * Validate a duration constructor argument.
     */
    private static Duration requireNonnegativeDuration(
        final Duration duration,
        final String fieldName
    ) {
        Objects.requireNonNull(
            duration,
            fieldName + " cannot be null"
        );

        if (duration.isNegative()) {
            throw new IllegalArgumentException(
                fieldName + " cannot be negative"
            );
        }

        return duration;
    }
}