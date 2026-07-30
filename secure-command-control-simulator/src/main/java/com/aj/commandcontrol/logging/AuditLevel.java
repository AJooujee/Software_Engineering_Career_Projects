package com.aj.commandcontrol.logging;

/**
 * Defines the severity level of one structured audit event.
 */
public enum AuditLevel {

    /**
     * Normal system activity.
     */
    INFO,

    /**
     * Activity that deserves attention but does not stop processing.
     */
    WARNING,

    /**
     * Security-related event such as failed authentication or replay.
     */
    SECURITY,

    /**
     * Unexpected failure or invalid application condition.
     */
    ERROR
}