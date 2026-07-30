package com.aj.commandcontrol;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.parsing.CommandMessageParser;
import com.aj.commandcontrol.parsing.CommandValidationException;
import com.aj.commandcontrol.processing.CommandProcessor;

/**
 * Entry point for the Secure Command-and-Control
 * Message Processing Simulator.
 */
public final class CommandControlApplication {

    /**
     * Prevent object creation because this class contains
     * only the application entry point.
     */
    private CommandControlApplication() {
    }

    /**
     * Demonstrate JSON parsing, command validation,
     * and state-machine processing.
     *
     * @param args command-line arguments
     */
    public static void main(final String[] args) {
        final CommandMessageParser parser =
            new CommandMessageParser();

        final CommandProcessor processor =
            new CommandProcessor();

        System.out.println(
            "============================================================"
        );
        System.out.println(
            "Secure Command-and-Control Message Processing Simulator"
        );
        System.out.println(
            "Initial remote unit state: "
                + processor.getCurrentState()
        );
        System.out.println(
            "============================================================"
        );

        // Valid command: OFFLINE -> STANDBY.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000001",
              "command_type": "START_SYSTEM",
              "target_id": "UNIT-01",
              "sequence_number": 1,
              "timestamp": "2026-07-30T19:00:00Z",
              "payload": {}
            }
            """
        );

        // Valid command: STANDBY -> ACTIVE.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000002",
              "command_type": "ACTIVATE_SYSTEM",
              "target_id": "UNIT-01",
              "sequence_number": 2,
              "timestamp": "2026-07-30T19:00:01Z",
              "payload": {
                "operation": "PRIMARY_SENSOR_SCAN"
              }
            }
            """
        );

        // Valid JSON but invalid state transition.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000003",
              "command_type": "START_SYSTEM",
              "target_id": "UNIT-01",
              "sequence_number": 3,
              "timestamp": "2026-07-30T19:00:02Z",
              "payload": {}
            }
            """
        );

        // Invalid command type.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000004",
              "command_type": "LAUNCH_UNKNOWN_OPERATION",
              "target_id": "UNIT-01",
              "sequence_number": 4,
              "timestamp": "2026-07-30T19:00:03Z",
              "payload": {}
            }
            """
        );

        // Missing required sequence_number field.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000005",
              "command_type": "STOP_SYSTEM",
              "target_id": "UNIT-01",
              "timestamp": "2026-07-30T19:00:04Z",
              "payload": {}
            }
            """
        );

        // Malformed JSON.
        processJsonCommand(
            parser,
            processor,
            """
            {
              "message_id": "CMD-000006",
              "command_type": "STOP_SYSTEM"
            """
        );

        System.out.println(
            "============================================================"
        );
        System.out.println(
            "Final remote unit state: "
                + processor.getCurrentState()
        );
        System.out.println(
            "Phase 3 JSON parsing and validation completed."
        );
        System.out.println(
            "============================================================"
        );
    }

    /**
     * Parse, validate, and process one JSON command.
     */
    private static void processJsonCommand(
        final CommandMessageParser parser,
        final CommandProcessor processor,
        final String jsonMessage
    ) {
        try {
            final CommandMessage command =
                parser.parse(jsonMessage);

            final CommandResult result =
                processor.process(command);

            System.out.println(
                "[PARSED] "
                    + command.getMessageId()
                    + " | "
                    + command.getCommandType()
                    + " | Target: "
                    + command.getTargetId()
                    + " | Sequence: "
                    + command.getSequenceNumber()
            );

            System.out.println(result);
        } catch (CommandValidationException error) {
            // Reject invalid input without terminating the application.
            System.out.println(
                "[INVALID COMMAND] "
                    + error.getMessage()
            );
        }

        System.out.println(
            "------------------------------------------------------------"
        );
    }
}