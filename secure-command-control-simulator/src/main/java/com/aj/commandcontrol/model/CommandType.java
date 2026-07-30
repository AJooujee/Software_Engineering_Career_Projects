package com.aj.commandcontrol.model;

/**
 * Defines every command currently supported by the remote unit.
 */
public enum CommandType {

    /**
     * Start an offline remote unit and place it in standby mode.
     */
    START_SYSTEM,

    /**
     * Move a standby remote unit into active operation.
     */
    ACTIVATE_SYSTEM,

    /**
     * Stop active operation and return to standby mode.
     */
    STOP_SYSTEM,

    /**
     * Immediately place the remote unit into safe mode.
     */
    ENTER_SAFE_MODE,

    /**
     * Recover a remote unit from safe mode into standby mode.
     */
    RESET_SYSTEM,

    /**
     * Shut down the remote unit and return it to offline state.
     */
    SHUTDOWN_SYSTEM
}