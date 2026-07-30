package com.aj.commandcontrol.model;

/**
 * Represents the status returned by the Java remote unit.
 */
public enum AcknowledgementStatus {

    /**
     * The command passed validation and was executed.
     */
    ACCEPTED,

    /**
     * The command was valid but not permitted in the current state.
     */
    REJECTED,

    /**
     * The JSON structure or command values were invalid.
     */
    INVALID,

    /**
     * The message failed cryptographic authentication.
     */
    UNAUTHORIZED
}