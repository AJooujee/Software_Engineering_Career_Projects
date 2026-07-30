# Import hashlib for SHA-256.
import hashlib

# Import hmac to authenticate commands.
import hmac

# Import json for command and acknowledgement serialization.
import json

# Import os to read the shared secret.
import os

# Import socket for TCP communication.
import socket

# Import time for demonstration delays.
import time

# Import datetime utilities for current, old, and future timestamps.
from datetime import datetime, timedelta, timezone


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6060
TARGET_ID = "UNIT-01"

SECRET_ENVIRONMENT_VARIABLE = (
    "COMMAND_CONTROL_SHARED_SECRET"
)


def get_shared_secret() -> bytes:
    """
    Read and validate the shared HMAC secret.
    """

    secret = os.getenv(
        SECRET_ENVIRONMENT_VARIABLE
    )

    if not secret:
        raise RuntimeError(
            f"Environment variable "
            f"{SECRET_ENVIRONMENT_VARIABLE} "
            "is not configured."
        )

    if len(secret) < 16:
        raise RuntimeError(
            "The shared secret must contain at least 16 characters."
        )

    return secret.encode("utf-8")


def utc_timestamp(
    offset_seconds: int = 0,
) -> str:
    """
    Generate a Java-compatible UTC timestamp.

    A negative offset creates a stale timestamp.
    A positive offset creates a future timestamp.
    """

    timestamp = (
        datetime.now(timezone.utc)
        + timedelta(seconds=offset_seconds)
    )

    return timestamp.isoformat().replace(
        "+00:00",
        "Z",
    )


def create_canonical_message(
    command: dict,
) -> str:
    """
    Create the exact message representation signed by Java and Python.
    """

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
    timestamp_offset_seconds: int = 0,
) -> dict:
    """
    Create and sign one command.
    """

    command = {
        "message_id": message_id,
        "command_type": command_type,
        "target_id": TARGET_ID,
        "sequence_number": sequence_number,
        "timestamp": utc_timestamp(
            timestamp_offset_seconds
        ),
        "payload": payload or {},
    }

    command["signature"] = calculate_signature(
        command,
        shared_secret,
    )

    return command


def send_command(
    socket_file,
    command: dict,
) -> dict:
    """
    Send one command and wait for one acknowledgement.
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
            "The Java server closed the connection "
            "before sending an ACK."
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
    Demonstrate normal, duplicate, replayed, expired,
    and future-dated command handling.
    """

    try:
        shared_secret = get_shared_secret()
    except RuntimeError as error:
        print(
            f"Configuration error: {error}"
        )
        return

    # First valid command.
    start_command = create_command(
        "CMD-000001",
        "START_SYSTEM",
        1,
        shared_secret,
    )

    commands = [
        # Accepted: OFFLINE -> STANDBY.
        start_command,

        # Exact duplicate message ID and sequence number.
        start_command.copy(),

        # New message ID but replayed sequence number 1.
        create_command(
            "CMD-000002",
            "ACTIVATE_SYSTEM",
            1,
            shared_secret,
        ),

        # Correct next sequence, but timestamp is 60 seconds old.
        create_command(
            "CMD-000003",
            "ACTIVATE_SYSTEM",
            2,
            shared_secret,
            timestamp_offset_seconds=-60,
        ),

        # Correct next sequence, but timestamp is 60 seconds ahead.
        create_command(
            "CMD-000004",
            "ACTIVATE_SYSTEM",
            2,
            shared_secret,
            timestamp_offset_seconds=60,
        ),

        # Accepted: STANDBY -> ACTIVE.
        create_command(
            "CMD-000005",
            "ACTIVATE_SYSTEM",
            2,
            shared_secret,
            {"operation": "PRIMARY_SENSOR_SCAN"},
        ),

        # Accepted: ACTIVE -> OFFLINE.
        create_command(
            "CMD-000006",
            "SHUTDOWN_SYSTEM",
            3,
            shared_secret,
        ),
    ]

    print(
        "============================================================"
    )

    print(
        "Replay-Protected Python Control Station"
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