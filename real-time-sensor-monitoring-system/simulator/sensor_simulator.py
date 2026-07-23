# Import json to convert Python dictionaries into JSON messages.
import json

# Import random to generate simulated sensor values.
import random

# Import socket to connect the Python simulator to the C++ TCP server.
import socket

# Import time to control how often readings are generated.
import time

# Import datetime utilities to create UTC timestamps.
from datetime import datetime, timezone


# IP address of the C++ server.
# 127.0.0.1 means the server is running on the same computer.
SERVER_HOST = "127.0.0.1"

# TCP port shared by the Python client and C++ server.
SERVER_PORT = 5050

# Number of seconds between each group of sensor readings.
SENSOR_INTERVAL_SECONDS = 1.0


def create_sensor_reading(
    sensor_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    sequence_number: int,
) -> dict:
    """
    Create one standardized sensor reading.

    All sensor types use the same message structure so that
    the C++ receiver can process them consistently.
    """

    return {
        # Unique identifier for the simulated sensor.
        "sensor_id": sensor_id,

        # Category of the sensor.
        "sensor_type": sensor_type,

        # UTC timestamp showing when the reading was generated.
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Current simulated sensor value rounded to two decimal places.
        "value": round(value, 2),

        # Measurement unit associated with the sensor value.
        "unit": unit,

        # Increasing number used to verify message ordering.
        "sequence_number": sequence_number,
    }


def generate_temperature_reading(sequence_number: int) -> dict:
    """
    Generate a normal temperature reading between 68°F and 78°F.
    """

    return create_sensor_reading(
        sensor_id="TEMP-01",
        sensor_type="TEMPERATURE",
        value=random.uniform(68.0, 78.0),
        unit="F",
        sequence_number=sequence_number,
    )


def generate_voltage_reading(sequence_number: int) -> dict:
    """
    Generate a normal voltage reading between 11.8 V and 12.6 V.
    """

    return create_sensor_reading(
        sensor_id="VOLT-01",
        sensor_type="VOLTAGE",
        value=random.uniform(11.8, 12.6),
        unit="V",
        sequence_number=sequence_number,
    )


def generate_position_reading(sequence_number: int) -> dict:
    """
    Generate a simulated position reading between 0 and 100 units.
    """

    return create_sensor_reading(
        sensor_id="POS-01",
        sensor_type="POSITION",
        value=random.uniform(0.0, 100.0),
        unit="unit",
        sequence_number=sequence_number,
    )


def generate_motion_reading(sequence_number: int) -> dict:
    """
    Generate a motion state.

    A value of 1 means motion is detected.
    A value of 0 means no motion is detected.
    """

    return create_sensor_reading(
        sensor_id="MOTION-01",
        sensor_type="MOTION",
        value=random.choice([0.0, 1.0]),
        unit="state",
        sequence_number=sequence_number,
    )


def send_message(
    client_socket: socket.socket,
    reading: dict,
) -> None:
    """
    Convert one sensor reading into newline-delimited JSON
    and send it to the C++ server.
    """

    # Convert the Python dictionary into a compact JSON string.
    json_message = json.dumps(reading)

    # Add a newline so the C++ receiver can detect message boundaries.
    network_message = f"{json_message}\n"

    # Convert the string into UTF-8 bytes and send all bytes.
    client_socket.sendall(network_message.encode("utf-8"))

    # Display the transmitted message for debugging.
    print(f"[SENT] {json_message}")


def main() -> None:
    """
    Connect to the C++ TCP server and continuously send
    four simulated sensor readings.
    """

    # Each generated message receives a unique sequence number.
    sequence_number = 1

    print("Multi-sensor TCP simulator started.")
    print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")

    try:
        # Create an IPv4 TCP client socket.
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as client_socket:

            # Connect to the C++ server.
            # The C++ program must already be running.
            client_socket.connect(
                (SERVER_HOST, SERVER_PORT)
            )

            print("Connected to the C++ sensor monitor.")
            print("Press Ctrl + C to stop.\n")

            while True:
                # Generate one reading from each sensor.
                sensor_readings = [
                    generate_temperature_reading(sequence_number),
                    generate_voltage_reading(sequence_number + 1),
                    generate_position_reading(sequence_number + 2),
                    generate_motion_reading(sequence_number + 3),
                ]

                # Send each reading as one JSON message.
                for reading in sensor_readings:
                    send_message(
                        client_socket,
                        reading,
                    )

                # Four messages were generated during this cycle.
                sequence_number += len(sensor_readings)

                # Add a blank line for readability.
                print()

                # Wait before generating the next cycle.
                time.sleep(SENSOR_INTERVAL_SECONDS)

    except ConnectionRefusedError:
        # This usually means the C++ server is not running yet.
        print(
            "Connection failed. Start the C++ sensor monitor "
            "before starting the Python simulator."
        )

    except ConnectionResetError:
        # This occurs when the C++ server closes unexpectedly.
        print(
            "The C++ sensor monitor closed the connection."
        )

    except KeyboardInterrupt:
        # Exit cleanly when the user presses Ctrl + C.
        print(
            "\nMulti-sensor TCP simulator stopped."
        )

    except OSError as error:
        # Handle other network-related operating-system errors.
        print(
            f"Network error: {error}"
        )


# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()