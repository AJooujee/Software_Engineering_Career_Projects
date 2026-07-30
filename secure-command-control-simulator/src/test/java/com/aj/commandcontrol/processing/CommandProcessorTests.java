package com.aj.commandcontrol.processing;

import com.aj.commandcontrol.model.CommandMessage;
import com.aj.commandcontrol.model.CommandResult;
import com.aj.commandcontrol.model.CommandStatus;
import com.aj.commandcontrol.model.CommandType;
import com.aj.commandcontrol.model.RemoteUnitState;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for deterministic remote-unit state transitions.
 */
class CommandProcessorTests {

    /**
     * Verify that a new processor begins in OFFLINE state.
     */
    @Test
    void startsInOfflineState() {
        final CommandProcessor processor =
            new CommandProcessor();

        assertEquals(
            RemoteUnitState.OFFLINE,
            processor.getCurrentState()
        );
    }

    /**
     * Verify the valid OFFLINE -> STANDBY transition.
     */
    @Test
    void startSystemMovesOfflineToStandby() {
        final CommandProcessor processor =
            new CommandProcessor();

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000001",
                CommandType.START_SYSTEM,
                1
            )
        );

        assertTrue(result.isAccepted());
        assertEquals(CommandStatus.ACCEPTED, result.getStatus());
        assertEquals(RemoteUnitState.OFFLINE, result.getPreviousState());
        assertEquals(RemoteUnitState.STANDBY, result.getCurrentState());
        assertEquals(RemoteUnitState.STANDBY, processor.getCurrentState());
    }

    /**
     * Verify the valid STANDBY -> ACTIVE transition.
     */
    @Test
    void activateSystemMovesStandbyToActive() {
        final CommandProcessor processor =
            new CommandProcessor(RemoteUnitState.STANDBY);

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000002",
                CommandType.ACTIVATE_SYSTEM,
                2
            )
        );

        assertTrue(result.isAccepted());
        assertEquals(RemoteUnitState.ACTIVE, result.getCurrentState());
    }

    /**
     * Verify that ACTIVATE_SYSTEM is rejected while OFFLINE.
     */
    @Test
    void activateSystemIsRejectedWhileOffline() {
        final CommandProcessor processor =
            new CommandProcessor();

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000003",
                CommandType.ACTIVATE_SYSTEM,
                3
            )
        );

        assertFalse(result.isAccepted());
        assertEquals(CommandStatus.REJECTED, result.getStatus());
        assertEquals(RemoteUnitState.OFFLINE, result.getCurrentState());
        assertEquals(RemoteUnitState.OFFLINE, processor.getCurrentState());
    }

    /**
     * Verify that an active unit can enter SAFE_MODE.
     */
    @Test
    void enterSafeModeMovesActiveToSafeMode() {
        final CommandProcessor processor =
            new CommandProcessor(RemoteUnitState.ACTIVE);

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000004",
                CommandType.ENTER_SAFE_MODE,
                4
            )
        );

        assertTrue(result.isAccepted());
        assertEquals(RemoteUnitState.SAFE_MODE, result.getCurrentState());
    }

    /**
     * Verify the SAFE_MODE -> STANDBY reset transition.
     */
    @Test
    void resetSystemMovesSafeModeToStandby() {
        final CommandProcessor processor =
            new CommandProcessor(RemoteUnitState.SAFE_MODE);

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000005",
                CommandType.RESET_SYSTEM,
                5
            )
        );

        assertTrue(result.isAccepted());
        assertEquals(RemoteUnitState.STANDBY, result.getCurrentState());
    }

    /**
     * Verify that shutdown moves an active unit to OFFLINE.
     */
    @Test
    void shutdownSystemMovesActiveToOffline() {
        final CommandProcessor processor =
            new CommandProcessor(RemoteUnitState.ACTIVE);

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000006",
                CommandType.SHUTDOWN_SYSTEM,
                6
            )
        );

        assertTrue(result.isAccepted());
        assertEquals(RemoteUnitState.OFFLINE, result.getCurrentState());
    }

    /**
     * Verify that RESET_SYSTEM cannot be used outside SAFE_MODE.
     */
    @Test
    void resetSystemIsRejectedOutsideSafeMode() {
        final CommandProcessor processor =
            new CommandProcessor(RemoteUnitState.STANDBY);

        final CommandResult result = processor.process(
            createCommand(
                "CMD-000007",
                CommandType.RESET_SYSTEM,
                7
            )
        );

        assertFalse(result.isAccepted());
        assertEquals(RemoteUnitState.STANDBY, result.getCurrentState());
    }

    /**
     * Create a valid test command.
     *
     * The state machine does not inspect the HMAC signature, but the
     * production model requires a valid 64-character hexadecimal value.
     */
    private static CommandMessage createCommand(
        final String messageId,
        final CommandType commandType,
        final long sequenceNumber
    ) {
        return new CommandMessage(
            messageId,
            commandType,
            "UNIT-01",
            sequenceNumber,
            Instant.parse("2026-07-30T20:00:00Z"),
            Collections.emptyMap(),
            "a".repeat(64)
        );
    }
}