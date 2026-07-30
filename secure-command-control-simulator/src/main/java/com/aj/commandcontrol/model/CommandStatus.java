package com.aj.commandcontrol.model;

/**
 * Represents the final processing status of a command.
 */
public enum CommandStatus {

    /**
     * The command was valid and successfully executed.
     */
    ACCEPTED,

    /**
     * The command was understood but was not allowed in the current state.
     */
    REJECTED
}