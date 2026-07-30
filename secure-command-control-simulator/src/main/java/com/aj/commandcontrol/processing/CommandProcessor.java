package com.aj.commandcontrol.processing;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.model.CommandStatus;
import com.aj.commandcontrol.model.RemoteUnitState;

import java.util.Objects;

/**
 * Processes commands and maintains the remote unit's operating state.
 */
public final class CommandProcessor {

    // Current state of the simulated remote unit.
    private RemoteUnitState currentState;

    /**
     * Create a command processor whose remote unit begins offline.
     */
    public CommandProcessor() {
        this(RemoteUnitState.OFFLINE);
    }

    /**
     * Create a command processor with a specified initial state.
     *
     * This constructor will also be useful for automated tests.
     *
     * @param initialState initial remote-unit state
     */
    public CommandProcessor(
        final RemoteUnitState initialState
    ) {
        this.currentState = Objects.requireNonNull(
            initialState,
            "initialState cannot be null"
        );
    }

    /**
     * Process one command using deterministic state-transition rules.
     *
     * synchronized prevents multiple future network threads from
     * changing the state at the same time.
     *
     * @param command incoming command
     * @return command-processing result
     */
    public synchronized CommandResult process(
        final CommandMessage command
    ) {
        Objects.requireNonNull(
            command,
            "command cannot be null"
        );

        final RemoteUnitState previousState = currentState;

        return switch (command.getCommandType()) {
            case START_SYSTEM ->
                processStartSystem(command, previousState);

            case ACTIVATE_SYSTEM ->
                processActivateSystem(command, previousState);

            case STOP_SYSTEM ->
                processStopSystem(command, previousState);

            case ENTER_SAFE_MODE ->
                processEnterSafeMode(command, previousState);

            case RESET_SYSTEM ->
                processResetSystem(command, previousState);

            case SHUTDOWN_SYSTEM ->
                processShutdownSystem(command, previousState);
        };
    }

    /**
     * OFFLINE -> STANDBY
     */
    private CommandResult processStartSystem(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState != RemoteUnitState.OFFLINE) {
            return reject(
                command,
                previousState,
                "START_SYSTEM is allowed only while OFFLINE."
            );
        }

        currentState = RemoteUnitState.STANDBY;

        return accept(
            command,
            previousState,
            "Remote unit initialized and entered standby mode."
        );
    }

    /**
     * STANDBY -> ACTIVE
     */
    private CommandResult processActivateSystem(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState != RemoteUnitState.STANDBY) {
            return reject(
                command,
                previousState,
                "ACTIVATE_SYSTEM is allowed only while STANDBY."
            );
        }

        currentState = RemoteUnitState.ACTIVE;

        return accept(
            command,
            previousState,
            "Remote unit entered active operation."
        );
    }

    /**
     * ACTIVE -> STANDBY
     */
    private CommandResult processStopSystem(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState != RemoteUnitState.ACTIVE) {
            return reject(
                command,
                previousState,
                "STOP_SYSTEM is allowed only while ACTIVE."
            );
        }

        currentState = RemoteUnitState.STANDBY;

        return accept(
            command,
            previousState,
            "Active operation stopped; remote unit returned to standby."
        );
    }

    /**
     * Any non-offline state -> SAFE_MODE
     */
    private CommandResult processEnterSafeMode(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState == RemoteUnitState.OFFLINE) {
            return reject(
                command,
                previousState,
                "An offline remote unit cannot enter safe mode."
            );
        }

        if (currentState == RemoteUnitState.SAFE_MODE) {
            return reject(
                command,
                previousState,
                "Remote unit is already in safe mode."
            );
        }

        currentState = RemoteUnitState.SAFE_MODE;

        return accept(
            command,
            previousState,
            "Remote unit entered safe mode."
        );
    }

    /**
     * SAFE_MODE -> STANDBY
     */
    private CommandResult processResetSystem(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState != RemoteUnitState.SAFE_MODE) {
            return reject(
                command,
                previousState,
                "RESET_SYSTEM is allowed only while in SAFE_MODE."
            );
        }

        currentState = RemoteUnitState.STANDBY;

        return accept(
            command,
            previousState,
            "Safe-mode condition cleared; remote unit returned to standby."
        );
    }

    /**
     * STANDBY, ACTIVE, or SAFE_MODE -> OFFLINE
     */
    private CommandResult processShutdownSystem(
        final CommandMessage command,
        final RemoteUnitState previousState
    ) {
        if (currentState == RemoteUnitState.OFFLINE) {
            return reject(
                command,
                previousState,
                "Remote unit is already offline."
            );
        }

        currentState = RemoteUnitState.OFFLINE;

        return accept(
            command,
            previousState,
            "Remote unit shut down successfully."
        );
    }

    /**
     * Build an accepted command result.
     */
    private CommandResult accept(
        final CommandMessage command,
        final RemoteUnitState previousState,
        final String message
    ) {
        return new CommandResult(
            command.getMessageId(),
            command.getCommandType(),
            CommandStatus.ACCEPTED,
            previousState,
            currentState,
            message
        );
    }

    /**
     * Build a rejected result without changing the current state.
     */
    private CommandResult reject(
        final CommandMessage command,
        final RemoteUnitState previousState,
        final String message
    ) {
        return new CommandResult(
            command.getMessageId(),
            command.getCommandType(),
            CommandStatus.REJECTED,
            previousState,
            currentState,
            message
        );
    }

    /**
     * Return the current remote-unit state.
     */
    public synchronized RemoteUnitState getCurrentState() {
        return currentState;
    }
}