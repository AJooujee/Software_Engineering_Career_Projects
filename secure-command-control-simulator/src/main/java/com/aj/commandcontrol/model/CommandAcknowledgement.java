package com.aj.commandcontrol.model;

import java.time.Instant;
import java.util.Objects;

/**
 * Represents the acknowledgement returned to the control station
 * after one command has been validated and processed.
 */
public final class CommandAcknowledgement {

    // Identifier copied from the incoming command when available.
    private final String messageId;

    // Final acknowledgement status.
    private final AcknowledgementStatus status;

    // Command type associated with the request.
    private final String commandType;

    // Remote-unit state before command processing.
    private final String previousState;

    // Remote-unit state after command processing.
    private final String currentState;

    // Human-readable explanation.
    private final String message;

    // UTC time at which the acknowledgement was created.
    private final String processedAt;

    /**
     * Create an immutable acknowledgement.
     *
     * @param messageId incoming command identifier
     * @param status acknowledgement status
     * @param commandType incoming command type
     * @param previousState state before processing
     * @param currentState state after processing
     * @param message processing explanation
     */
    public CommandAcknowledgement(
        final String messageId,
        final AcknowledgementStatus status,
        final String commandType,
        final String previousState,
        final String currentState,
        final String message
    ) {
        this.messageId = Objects.requireNonNull(messageId);
        this.status = Objects.requireNonNull(status);
        this.commandType = Objects.requireNonNull(commandType);
        this.previousState = Objects.requireNonNull(previousState);
        this.currentState = Objects.requireNonNull(currentState);
        this.message = Objects.requireNonNull(message);

        // Store the timestamp as ISO-8601 text so Jackson can serialize
        // it without requiring an additional Java-time module.
        this.processedAt = Instant.now().toString();
    }

    public String getMessageId() {
        return messageId;
    }

    public AcknowledgementStatus getStatus() {
        return status;
    }

    public String getCommandType() {
        return commandType;
    }

    public String getPreviousState() {
        return previousState;
    }

    public String getCurrentState() {
        return currentState;
    }

    public String getMessage() {
        return message;
    }

    public String getProcessedAt() {
        return processedAt;
    }

    /**
     * Convert an accepted or rejected CommandResult into
     * a network acknowledgement.
     *
     * @param result completed command-processing result
     * @return acknowledgement ready for JSON serialization
     */
    public static CommandAcknowledgement fromResult(
        final CommandResult result
    ) {
        final AcknowledgementStatus acknowledgementStatus =
            result.isAccepted()
                ? AcknowledgementStatus.ACCEPTED
                : AcknowledgementStatus.REJECTED;

        return new CommandAcknowledgement(
            result.getMessageId(),
            acknowledgementStatus,
            result.getCommandType().name(),
            result.getPreviousState().name(),
            result.getCurrentState().name(),
            result.getMessage()
        );
    }

        /**
     * Create an acknowledgement for a command whose
     * HMAC signature could not be verified.
     */
    public static CommandAcknowledgement unauthorized(
        final String messageId,
        final String commandType,
        final String message,
        final RemoteUnitState currentState
    ) {
        return new CommandAcknowledgement(
            messageId,
            AcknowledgementStatus.UNAUTHORIZED,
            commandType,
            currentState.name(),
            currentState.name(),
            message
        );
    }

        /**
     * Create an acknowledgement for an authenticated command
     * rejected by replay or timestamp validation.
     */
    public static CommandAcknowledgement securityRejected(
        final String messageId,
        final String commandType,
        final String securityCode,
        final String message,
        final RemoteUnitState currentState
    ) {
        return new CommandAcknowledgement(
            messageId,
            AcknowledgementStatus.SECURITY_REJECTED,
            commandType,
            currentState.name(),
            currentState.name(),
            securityCode + ": " + message
        );
    }

    /**
     * Create an acknowledgement for an invalid JSON command.
     *
     * @param message explanation of the validation failure
     * @param currentState current remote-unit state
     * @return invalid acknowledgement
     */
    public static CommandAcknowledgement invalid(
        final String message,
        final RemoteUnitState currentState
    ) {
        return new CommandAcknowledgement(
            "UNKNOWN",
            AcknowledgementStatus.INVALID,
            "UNKNOWN",
            currentState.name(),
            currentState.name(),
            message
        );
    }
}