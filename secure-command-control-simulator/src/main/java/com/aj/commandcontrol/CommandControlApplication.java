package com.aj.commandcontrol;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.model.CommandType;
import com.aj.commandcontrol.processing.CommandProcessor;

import java.time.Instant;
import java.util.Collections;

/**
 * Entry point for the Secure Command-and-Control
 * Message Processing Simulator.
 */
public final class CommandControlApplication {

    /**
     * Prevent object creation because this class only contains
     * the application entry point.
     */
    private CommandControlApplication() {
    }

    /**
     * Start the command-control simulator and demonstrate
     * deterministic state transitions.
     *
     * @param args command-line arguments
     */
    public static void main(final String[] args) {
        final CommandProcessor processor = new CommandProcessor();

        System.out.println(
            "============================================================"
        );
        System.out.println(
            "Secure Command-and-Control Message Processing Simulator"
        );
        System.out.println(
            "Initial remote unit state: " + processor.getCurrentState()
        );
        System.out.println(
            "============================================================"
        );

        long sequenceNumber = 1;

        // Demonstrate a valid startup sequence.
        sequenceNumber = executeCommand(
            processor,
            CommandType.START_SYSTEM,
            sequenceNumber
        );

        sequenceNumber = executeCommand(
            processor,
            CommandType.ACTIVATE_SYSTEM,
            sequenceNumber
        );

        // Demonstrate an invalid transition.
        sequenceNumber = executeCommand(
            processor,
            CommandType.START_SYSTEM,
            sequenceNumber
        );

        // Demonstrate emergency safe-mode handling.
        sequenceNumber = executeCommand(
            processor,
            CommandType.ENTER_SAFE_MODE,
            sequenceNumber
        );

        sequenceNumber = executeCommand(
            processor,
            CommandType.RESET_SYSTEM,
            sequenceNumber
        );

        executeCommand(
            processor,
            CommandType.SHUTDOWN_SYSTEM,
            sequenceNumber
        );

        System.out.println(
            "============================================================"
        );
        System.out.println(
            "Final remote unit state: " + processor.getCurrentState()
        );
        System.out.println(
            "Phase 2 command model and state machine completed."
        );
        System.out.println(
            "============================================================"
        );
    }

    /**
     * Create and process one demonstration command.
     *
     * @return the next sequence number
     */
    private static long executeCommand(
        final CommandProcessor processor,
        final CommandType commandType,
        final long sequenceNumber
    ) {
        final CommandMessage command = new CommandMessage(
            String.format("CMD-%06d", sequenceNumber),
            commandType,
            "UNIT-01",
            sequenceNumber,
            Instant.now(),
            Collections.emptyMap()
        );

        final CommandResult result = processor.process(command);

        System.out.println(result);

        return sequenceNumber + 1;
    }
}