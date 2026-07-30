package com.aj.commandcontrol.model;

import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Represents one command sent from the control station
 * to the remote unit.
 */
public final class CommandMessage {

    // Unique identifier used for duplicate-message and replay detection.
    private final String messageId;

    // Command requested by the control station.
    private final CommandType commandType;

    // Identifier of the remote unit that should receive the command.
    private final String targetId;

    // Increasing sequence number used to verify message ordering.
    private final long sequenceNumber;

    // Time at which the command was created.
    private final Instant timestamp;

    // Optional command-specific values.
    private final Map<String, Object> payload;

    /**
     * Create an immutable command message.
     *
     * @param messageId unique command identifier
     * @param commandType requested command
     * @param targetId intended remote-unit identifier
     * @param sequenceNumber increasing message sequence number
     * @param timestamp command creation time
     * @param payload optional command-specific data
     */
    public CommandMessage(
        final String messageId,
        final CommandType commandType,
        final String targetId,
        final long sequenceNumber,
        final Instant timestamp,
        final Map<String, Object> payload
    ) {
        // Reject missing model data early so invalid objects
        // cannot enter the processing layer.
        this.messageId = requireText(messageId, "messageId");
        this.commandType = Objects.requireNonNull(
            commandType,
            "commandType cannot be null"
        );
        this.targetId = requireText(targetId, "targetId");

        if (sequenceNumber < 1) {
            throw new IllegalArgumentException(
                "sequenceNumber must be greater than zero"
            );
        }

        this.sequenceNumber = sequenceNumber;
        this.timestamp = Objects.requireNonNull(
            timestamp,
            "timestamp cannot be null"
        );

        // Copy the supplied map so callers cannot change this message
        // after it has been constructed.
        if (payload == null) {
            this.payload = Collections.emptyMap();
        } else {
            this.payload = Collections.unmodifiableMap(
                new HashMap<>(payload)
            );
        }
    }

    /**
     * Validate a required text field.
     *
     * @param value field value
     * @param fieldName field name used in the error message
     * @return trimmed valid text
     */
    private static String requireText(
        final String value,
        final String fieldName
    ) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                fieldName + " cannot be blank"
            );
        }

        return value.trim();
    }

    public String getMessageId() {
        return messageId;
    }

    public CommandType getCommandType() {
        return commandType;
    }

    public String getTargetId() {
        return targetId;
    }

    public long getSequenceNumber() {
        return sequenceNumber;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public Map<String, Object> getPayload() {
        return payload;
    }
}