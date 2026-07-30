# Import hashlib for the SHA-256 digest used by HMAC.
import hashlib

# Import hmac to authenticate outgoing commands.
import hmac

# Import json to serialize commands and acknowledgements.
import json

# Import os to read the shared secret from an environment variable.
import os

# Import socket for TCP communication.
import socket

# Import time to delay commands during the demonstration.
import time

# Import datetime utilities to generate UTC timestamps.
from datetime import datetime, timezone


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6060
TARGET_ID = "UNIT-01"

# Java and Python must use the same environment variable.
SECRET_ENVIRONMENT_VARIABLE = "COMMAND_CONTROL_SHARED_SECRET"


def get_shared_secret() -> bytes:
    """
    Read and validate the shared authentication secret.
    """

    secret = os.getenv(
        SECRET_ENVIRONMENT_VARIABLE
    )

    if not secret:
        raise RuntimeError(
            f"Environment variable {SECRET_ENVIRONMENT_VARIABLE} "
            "is not configured."
        )

    if len(secret) < 16:
        raise RuntimeError(
            "The shared secret must contain at least 16 characters."
        )

    return secret.encode("utf-8")


def create_canonical_message(
    command: dict,
) -> str:
    """
    Create the exact text signed by both Python and Java.

    The signature field is excluded from this representation.
    """

    # Sorting payload keys guarantees deterministic JSON ordering.
    payload_json = json.dumps(
        command["payload"],
        sort_keys=True,
        separators=(",", ":"),
    )

    return "\n".join(
        [
            command["message_id"],
            command["command_type"],
            command["target_id"],
            str(command["sequence_number"]),
            command["timestamp"],
            payload_json,
        ]
    )


def calculate_signature(
    command: dict,
    shared_secret: bytes,
) -> str:
    """
    Calculate a lowercase hexadecimal HMAC-SHA256 signature.
    """

    canonical_message = create_canonical_message(
        command
    )

    return hmac.new(
        shared_secret,
        canonical_message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_command(
    message_id: str,
    command_type: str,
    sequence_number: int,
    shared_secret: bytes,
    payload: dict | None = None,
    tamper_signature: bool = False,
) -> dict:
    """
    Create and sign one command message.
    """

    command = {
        "message_id": message_id,
        "command_type": command_type,
        "target_id": TARGET_ID,
        "sequence_number": sequence_number,

        # Java Instant.toString() uses the Z suffix for UTC.
        # Matching this format ensures both systems sign identical text.
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z"),

        "payload": payload or {},
    }

    signature = calculate_signature(
        command,
        shared_secret,
    )

    # Replace the real signature to demonstrate authentication failure.
    if tamper_signature:
        signature = "0" * 64

    command["signature"] = signature

    return command


def send_command(
    socket_file,
    command: dict,
) -> dict:
    """
    Send one signed JSON command and wait for its acknowledgement.
    """

    command_json = json.dumps(
        command,
        separators=(",", ":"),
    )

    print(
        f"[SENT] {command_json}"
    )

    socket_file.write(
        f"{command_json}\n"
    )
    socket_file.flush()

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
    Send authenticated and deliberately tampered commands.
    """

    try:
        shared_secret = get_shared_secret()
    except RuntimeError as error:
        print(
            f"Configuration error: {error}"
        )
        return

    commands = [
        create_command(
            "CMD-000001",
            "START_SYSTEM",
            1,
            shared_secret,
        ),
        create_command(
            "CMD-000002",
            "ACTIVATE_SYSTEM",
            2,
            shared_secret,
            {"operation": "PRIMARY_SENSOR_SCAN"},
        ),
        # This command has a deliberately invalid HMAC signature.
        create_command(
            "CMD-000003",
            "ENTER_SAFE_MODE",
            3,
            shared_secret,
            tamper_signature=True,
        ),
        # A correctly signed command should still work afterward.
        create_command(
            "CMD-000004",
            "ENTER_SAFE_MODE",
            4,
            shared_secret,
        ),
        create_command(
            "CMD-000005",
            "RESET_SYSTEM",
            5,
            shared_secret,
        ),
        create_command(
            "CMD-000006",
            "SHUTDOWN_SYSTEM",
            6,
            shared_secret,
        ),
    ]

    print(
        "============================================================"
    )
    print(
        "Authenticated Python Control Station"
    )
    print(
        f"Connecting to {SERVER_HOST}:{SERVER_PORT}..."
    )
    print(
        "============================================================"
    )

    try:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as client_socket:

            client_socket.settimeout(
                5.0
            )

            client_socket.connect(
                (SERVER_HOST, SERVER_PORT)
            )

            print(
                "Connected to Java remote unit."
            )
            print(
                "------------------------------------------------------------"
            )

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

                    time.sleep(
                        0.5
                    )

    except ConnectionRefusedError:
        print(
            "Connection failed. Start the Java server first."
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


if __name__ == "__main__":
    main()