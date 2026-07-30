package com.aj.commandcontrol.model;

import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Represents one authenticated command sent from the control station
 * to the remote unit.
 */
public final class CommandMessage {

    // Unique identifier used for duplicate and replay detection.
    private final String messageId;

    // Command requested by the control station.
    private final CommandType commandType;

    // Identifier of the intended remote unit.
    private final String targetId;

    // Increasing number used for message-order verification.
    private final long sequenceNumber;

    // UTC time at which the command was created.
    private final Instant timestamp;

    // Optional command-specific data.
    private final Map<String, Object> payload;

    // Lowercase hexadecimal HMAC-SHA256 signature.
    private final String signature;

    /**
     * Create an immutable authenticated command message.
     *
     * @param messageId unique command identifier
     * @param commandType requested command
     * @param targetId intended remote-unit identifier
     * @param sequenceNumber increasing sequence number
     * @param timestamp command creation time
     * @param payload optional command-specific data
     * @param signature HMAC-SHA256 signature in hexadecimal form
     */
    public CommandMessage(
        final String messageId,
        final CommandType commandType,
        final String targetId,
        final long sequenceNumber,
        final Instant timestamp,
        final Map<String, Object> payload,
        final String signature
    ) {
        this.messageId = requireText(
            messageId,
            "messageId"
        );

        this.commandType = Objects.requireNonNull(
            commandType,
            "commandType cannot be null"
        );

        this.targetId = requireText(
            targetId,
            "targetId"
        );

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

        if (payload == null) {
            this.payload = Collections.emptyMap();
        } else {
            // Copy the map so callers cannot alter the command
            // after construction.
            this.payload = Collections.unmodifiableMap(
                new HashMap<>(payload)
            );
        }

        this.signature = requireSignature(
            signature
        );
    }

    /**
     * Validate one required text value.
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

    /**
     * Validate the expected hexadecimal SHA-256 signature.
     */
    private static String requireSignature(
        final String value
    ) {
        final String signatureValue = requireText(
            value,
            "signature"
        ).toLowerCase();

        // SHA-256 produces 32 bytes or 64 hexadecimal characters.
        if (!signatureValue.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException(
                "signature must contain exactly 64 hexadecimal characters"
            );
        }

        return signatureValue;
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

    public String getSignature() {
        return signature;
    }
}