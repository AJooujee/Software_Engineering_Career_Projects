package com.aj.commandcontrol.model;

import java.util.Objects;

/**
 * Describes the outcome of processing one command.
 */
public final class CommandResult {

    // Identifier of the processed command.
    private final String messageId;

    // Command that was evaluated.
    private final CommandType commandType;

    // Indicates whether the command was accepted or rejected.
    private final CommandStatus status;

    // Remote-unit state before processing.
    private final RemoteUnitState previousState;

    // Remote-unit state after processing.
    private final RemoteUnitState currentState;

    // Human-readable processing explanation.
    private final String message;

    /**
     * Create an immutable command-processing result.
     */
    public CommandResult(
        final String messageId,
        final CommandType commandType,
        final CommandStatus status,
        final RemoteUnitState previousState,
        final RemoteUnitState currentState,
        final String message
    ) {
        this.messageId = Objects.requireNonNull(messageId);
        this.commandType = Objects.requireNonNull(commandType);
        this.status = Objects.requireNonNull(status);
        this.previousState = Objects.requireNonNull(previousState);
        this.currentState = Objects.requireNonNull(currentState);
        this.message = Objects.requireNonNull(message);
    }

    public String getMessageId() {
        return messageId;
    }

    public CommandType getCommandType() {
        return commandType;
    }

    public CommandStatus getStatus() {
        return status;
    }

    public RemoteUnitState getPreviousState() {
        return previousState;
    }

    public RemoteUnitState getCurrentState() {
        return currentState;
    }

    public String getMessage() {
        return message;
    }

    /**
     * Return true when the command was successfully executed.
     */
    public boolean isAccepted() {
        return status == CommandStatus.ACCEPTED;
    }

    /**
     * Create readable terminal output for demonstrations and debugging.
     */
    @Override
    public String toString() {
        return String.format(
            "[%s] %s | %s -> %s | %s",
            status,
            commandType,
            previousState,
            currentState,
            message
        );
    }
}