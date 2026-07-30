package com.aj.commandcontrol.logging;

import java.time.Instant;
import java.util.Objects;

/**
 * Represents one immutable structured audit-log event.
 */
public final class AuditEvent {

    // UTC time at which the event was created.
    private final String timestamp;

    // Severity level associated with the event.
    private final AuditLevel level;

    // Machine-readable event category.
    private final String eventType;

    // Command message identifier when available.
    private final String messageId;

    // Command type when available.
    private final String commandType;

    // Final command or acknowledgement status.
    private final String status;

    // Remote-unit state before processing.
    private final String previousState;

    // Remote-unit state after processing.
    private final String currentState;

    // Human-readable event explanation.
    private final String details;

    /**
     * Create one structured audit event.
     *
     * Empty text is used for fields that do not apply to an event.
     *
     * @param level event severity
     * @param eventType machine-readable event type
     * @param messageId command identifier
     * @param commandType command type
     * @param status event or acknowledgement status
     * @param previousState state before processing
     * @param currentState state after processing
     * @param details readable explanation
     */
    public AuditEvent(
        final AuditLevel level,
        final String eventType,
        final String messageId,
        final String commandType,
        final String status,
        final String previousState,
        final String currentState,
        final String details
    ) {
        this.timestamp = Instant.now().toString();

        this.level = Objects.requireNonNull(
            level,
            "level cannot be null"
        );

        this.eventType = requireText(
            eventType,
            "eventType"
        );

        this.messageId = normalizeOptionalText(
            messageId
        );

        this.commandType = normalizeOptionalText(
            commandType
        );

        this.status = normalizeOptionalText(
            status
        );

        this.previousState = normalizeOptionalText(
            previousState
        );

        this.currentState = normalizeOptionalText(
            currentState
        );

        this.details = requireText(
            details,
            "details"
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
     * Convert missing optional values into empty strings.
     */
    private static String normalizeOptionalText(
        final String value
    ) {
        if (value == null) {
            return "";
        }

        return value.trim();
    }

    public String getTimestamp() {
        return timestamp;
    }

    public AuditLevel getLevel() {
        return level;
    }

    public String getEventType() {
        return eventType;
    }

    public String getMessageId() {
        return messageId;
    }

    public String getCommandType() {
        return commandType;
    }

    public String getStatus() {
        return status;
    }

    public String getPreviousState() {
        return previousState;
    }

    public String getCurrentState() {
        return currentState;
    }

    public String getDetails() {
        return details;
    }
}