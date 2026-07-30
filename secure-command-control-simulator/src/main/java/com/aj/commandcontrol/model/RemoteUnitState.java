package com.aj.commandcontrol.model;

/**
 * Represents the current operating state of the simulated remote unit.
 */
public enum RemoteUnitState {

    /**
     * The remote unit is powered down and cannot perform operations.
     */
    OFFLINE,

    /**
     * The remote unit is initialized but not performing active work.
     */
    STANDBY,

    /**
     * The remote unit is performing its assigned operation.
     */
    ACTIVE,

    /**
     * The remote unit has entered a protected state because of
     * a fault, security event, or emergency command.
     */
    SAFE_MODE
}