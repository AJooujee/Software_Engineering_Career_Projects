# Import json to serialize command dictionaries and parse acknowledgements.
import json

# Import socket to communicate with the Java TCP server.
import socket

# Import time to generate small delays between commands.
import time

# Import datetime utilities to generate UTC timestamps.
from datetime import datetime, timezone


# IP address of the Java remote-unit server.
SERVER_HOST = "127.0.0.1"

# TCP port configured in CommandServer.java.
SERVER_PORT = 6060

# Remote unit that should receive the commands.
TARGET_ID = "UNIT-01"


def create_command(
    message_id: str,
    command_type: str,
    sequence_number: int,
    payload: dict | None = None,
) -> dict:
    """
    Create one standardized command message.
    """

    return {
        # Unique identifier used later for duplicate protection.
        "message_id": message_id,

        # State-machine command requested by the control station.
        "command_type": command_type,

        # Intended remote unit.
        "target_id": TARGET_ID,

        # Increasing value used later for replay protection.
        "sequence_number": sequence_number,

        # Current UTC command creation time.
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Optional command-specific data.
        "payload": payload or {},
    }


def send_command(
    socket_file,
    command: dict,
) -> dict:
    """
    Send one newline-delimited JSON command and wait for its ACK.
    """

    # Serialize the command into compact JSON text.
    command_json = json.dumps(
        command,
        separators=(",", ":"),
    )

    print(f"[SENT] {command_json}")

    # Write the JSON command followed by a newline.
    socket_file.write(
        f"{command_json}\n"
    )
    socket_file.flush()

    # Read exactly one newline-delimited acknowledgement.
    acknowledgement_line = socket_file.readline()

    if acknowledgement_line == "":
        raise ConnectionError(
            "The Java server closed the connection before sending an ACK."
        )

    acknowledgement = json.loads(
        acknowledgement_line
    )

    print(
        "[ACK] "
        f"Status: {acknowledgement['status']} | "
        f"Command: {acknowledgement['commandType']} | "
        f"State: {acknowledgement['previousState']} "
        f"-> {acknowledgement['currentState']}"
    )
    print(
        f"      {acknowledgement['message']}"
    )
    print(
        "------------------------------------------------------------"
    )

    return acknowledgement


def main() -> None:
    """
    Connect to the Java server and demonstrate end-to-end
    command transmission and acknowledgement handling.
    """

    commands = [
        create_command(
            "CMD-000001",
            "START_SYSTEM",
            1,
        ),
        create_command(
            "CMD-000002",
            "ACTIVATE_SYSTEM",
            2,
            {"operation": "PRIMARY_SENSOR_SCAN"},
        ),
        # Valid JSON but invalid transition while ACTIVE.
        create_command(
            "CMD-000003",
            "START_SYSTEM",
            3,
        ),
        create_command(
            "CMD-000004",
            "ENTER_SAFE_MODE",
            4,
        ),
        create_command(
            "CMD-000005",
            "RESET_SYSTEM",
            5,
        ),
        create_command(
            "CMD-000006",
            "SHUTDOWN_SYSTEM",
            6,
        ),
        # Structurally valid JSON with an unsupported command type.
        create_command(
            "CMD-000007",
            "UNKNOWN_OPERATION",
            7,
        ),
    ]

    print(
        "============================================================"
    )
    print(
        "Python Control Station"
    )
    print(
        f"Connecting to {SERVER_HOST}:{SERVER_PORT}..."
    )
    print(
        "============================================================"
    )

    try:
        # Create an IPv4 TCP socket.
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as client_socket:

            # Fail instead of waiting forever for a network response.
            client_socket.settimeout(5.0)

            # Connect to the Java command server.
            client_socket.connect(
                (SERVER_HOST, SERVER_PORT)
            )

            print(
                "Connected to Java remote unit."
            )
            print(
                "------------------------------------------------------------"
            )

            # Text-mode wrapper allows convenient newline-based messaging.
            with client_socket.makefile(
                mode="rw",
                encoding="utf-8",
                newline="\n",
            ) as socket_file:

                for command in commands:
                    send_command(
                        socket_file,
                        command,
                    )

                    # Small delay makes demonstration output easier to read.
                    time.sleep(0.5)

    except ConnectionRefusedError:
        print(
            "Connection failed. Start the Java server before "
            "running the Python control station."
        )

    except socket.timeout:
        print(
            "Timed out while waiting for the Java server."
        )

    except (
        ConnectionError,
        json.JSONDecodeError,
        OSError,
    ) as error:
        print(
            f"Control-station error: {error}"
        )

    print(
        "Python control station stopped."
    )


# Run main only when this file is executed directly.
if __name__ == "__main__":
    main()