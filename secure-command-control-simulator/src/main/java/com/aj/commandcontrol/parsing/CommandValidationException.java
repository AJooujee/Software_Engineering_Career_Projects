package com.aj.commandcontrol.parsing;

/**
 * Represents a command message that cannot be accepted because
 * its JSON syntax, required fields, or field values are invalid.
 */
public final class CommandValidationException extends Exception {

    /**
     * Create a validation exception with a readable explanation.
     *
     * @param message description of the validation failure
     */
    public CommandValidationException(
        final String message
    ) {
        super(message);
    }

    /**
     * Create a validation exception that preserves the original cause.
     *
     * @param message description of the validation failure
     * @param cause original parsing or conversion error
     */
    public CommandValidationException(
        final String message,
        final Throwable cause
    ) {
        super(message, cause);
    }
}