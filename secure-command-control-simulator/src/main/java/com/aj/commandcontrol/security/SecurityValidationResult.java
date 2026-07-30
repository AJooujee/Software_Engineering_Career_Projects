package com.aj.commandcontrol.security;

import java.util.Objects;

/**
 * Describes the result of replay and timestamp validation.
 */
public final class SecurityValidationResult {

    // True when the message passed every replay-protection rule.
    private final boolean accepted;

    // Machine-readable security result.
    private final String code;

    // Human-readable explanation.
    private final String message;

    /**
     * Create an immutable security-validation result.
     *
     * @param accepted whether the command passed validation
     * @param code machine-readable result code
     * @param message readable explanation
     */
    private SecurityValidationResult(
        final boolean accepted,
        final String code,
        final String message
    ) {
        this.accepted = accepted;
        this.code = Objects.requireNonNull(code);
        this.message = Objects.requireNonNull(message);
    }

    /**
     * Create a successful result.
     */
    public static SecurityValidationResult accepted() {
        return new SecurityValidationResult(
            true,
            "ACCEPTED",
            "Command passed replay and timestamp validation."
        );
    }

    /**
     * Create a rejected result.
     *
     * @param code security failure code
     * @param message failure explanation
     */
    public static SecurityValidationResult rejected(
        final String code,
        final String message
    ) {
        return new SecurityValidationResult(
            false,
            code,
            message
        );
    }

    public boolean isAccepted() {
        return accepted;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}