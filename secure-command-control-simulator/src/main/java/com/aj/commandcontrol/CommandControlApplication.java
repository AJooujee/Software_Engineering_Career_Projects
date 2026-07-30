package com.aj.commandcontrol;

import com.aj.commandcontrol.network.CommandServer;

import java.io.IOException;

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
     * Start the Java remote-unit TCP server.
     *
     * @param args command-line arguments
     */
    public static void main(final String[] args) {
        System.out.println(
            "============================================================"
        );
        System.out.println(
            "Secure Command-and-Control Message Processing Simulator"
        );
        System.out.println(
            "Remote unit state: OFFLINE"
        );
        System.out.println(
            "============================================================"
        );

        final CommandServer commandServer =
            new CommandServer();

        try {
            commandServer.start();
        } catch (IOException error) {
            System.err.println(
                "Command server failed: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}