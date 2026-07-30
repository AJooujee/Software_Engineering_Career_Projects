package com.aj.commandcontrol.model;

/**
 * Represents the status returned by the Java remote unit
 * to the Python control station.
 */
public enum AcknowledgementStatus {

    /**
     * The command passed validation and was executed.
     */
    ACCEPTED,

    /**
     * The command was valid but was not allowed in the current state.
     */
    REJECTED,

    /**
     * The incoming JSON message or command fields were invalid.
     */
    INVALID
}