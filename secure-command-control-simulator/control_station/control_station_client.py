# Import hashlib for SHA-256.
import hashlib

# Import hmac to authenticate commands.
import hmac

# Import json to serialize commands and acknowledgements.
import json

# Import os to read the shared secret.
import os

# Import socket for TCP communication and timeout handling.
import socket

# Import time to delay retries and demonstration commands.
import time

# Import UTC timestamp utilities.
from datetime import datetime, timezone


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6060
TARGET_ID = "UNIT-01"

SECRET_ENVIRONMENT_VARIABLE = (
    "COMMAND_CONTROL_SHARED_SECRET"
)

# Maximum number of network-send attempts per command.
MAX_ACK_ATTEMPTS = 3

# Maximum time to wait for one acknowledgement.
ACK_TIMEOUT_SECONDS = 2.0

# Delay before resending a command.
RETRY_DELAY_SECONDS = 1.0


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


def utc_timestamp() -> str:
    """
    Generate a Java-compatible UTC timestamp.
    """

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
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
) -> dict:
    """
    Create and authenticate one immutable command dictionary.
    """

    command = {
        "message_id": message_id,
        "command_type": command_type,
        "target_id": TARGET_ID,
        "sequence_number": sequence_number,
        "timestamp": utc_timestamp(),
        "payload": payload or {},
    }

    command["signature"] = calculate_signature(
        command,
        shared_secret,
    )

    return command


def send_one_attempt(
    command: dict,
) -> dict:
    """
    Open one TCP connection, send one command, and read one ACK.

    A fresh connection per attempt allows recovery when the previous
    connection was closed before the ACK reached the client.
    """

    command_json = json.dumps(
        command,
        separators=(",", ":"),
    )

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as client_socket:

        client_socket.settimeout(
            ACK_TIMEOUT_SECONDS
        )

        client_socket.connect(
            (SERVER_HOST, SERVER_PORT)
        )

        with client_socket.makefile(
            mode="rw",
            encoding="utf-8",
            newline="\n",
        ) as socket_file:

            print(
                f"[SENT] {command_json}"
            )

            socket_file.write(
                f"{command_json}\n"
            )

            socket_file.flush()

            acknowledgement_line = (
                socket_file.readline()
            )

            if acknowledgement_line == "":
                raise ConnectionError(
                    "The connection closed before an ACK was received."
                )

            return json.loads(
                acknowledgement_line
            )


def send_command_with_retry(
    command: dict,
) -> dict:
    """
    Send one command and retry when its acknowledgement is lost.

    Every retry uses the exact same:
    - message ID
    - sequence number
    - timestamp
    - payload
    - signature

    This allows the Java server to recognize an idempotent retry.
    """

    last_error: Exception | None = None

    for attempt_number in range(
        1,
        MAX_ACK_ATTEMPTS + 1,
    ):
        print(
            f"[ATTEMPT {attempt_number}/{MAX_ACK_ATTEMPTS}] "
            f"{command['message_id']}"
        )

        try:
            acknowledgement = send_one_attempt(
                command
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

        except (
            socket.timeout,
            ConnectionError,
            ConnectionResetError,
            BrokenPipeError,
            OSError,
            json.JSONDecodeError,
        ) as error:
            last_error = error

            print(
                "[ACK NOT RECEIVED] "
                f"{command['message_id']} | {error}"
            )

            if attempt_number < MAX_ACK_ATTEMPTS:
                print(
                    "Retrying the identical authenticated command "
                    f"in {RETRY_DELAY_SECONDS} second(s)..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    raise ConnectionError(
        f"No valid acknowledgement was received after "
        f"{MAX_ACK_ATTEMPTS} attempts. Last error: {last_error}"
    )


def main() -> None:
    """
    Demonstrate reliable command acknowledgements and retries.
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
            {
                "operation": "PRIMARY_SENSOR_SCAN",
            },
        ),
        create_command(
            "CMD-000003",
            "SHUTDOWN_SYSTEM",
            3,
            shared_secret,
        ),
    ]

    print(
        "============================================================"
    )

    print(
        "Reliable Python Control Station"
    )

    print(
        f"Connecting to {SERVER_HOST}:{SERVER_PORT}"
    )

    print(
        f"ACK timeout: {ACK_TIMEOUT_SECONDS} seconds"
    )

    print(
        f"Maximum attempts: {MAX_ACK_ATTEMPTS}"
    )

    print(
        "============================================================"
    )

    try:
        for command in commands:
            send_command_with_retry(
                command
            )

            time.sleep(
                0.5
            )

    except ConnectionRefusedError:
        print(
            "Connection failed. Start the Java server first."
        )

    except ConnectionError as error:
        print(
            f"Command delivery failed: {error}"
        )

    print(
        "Python control station stopped."
    )


if __name__ == "__main__":
    main()