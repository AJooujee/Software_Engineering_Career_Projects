# Import argparse to select a simulation scenario from the command line.
import argparse

# Import json to convert Python dictionaries into JSON messages.
import json

# Import random to generate simulated sensor values.
import random

# Import socket to connect the simulator to the C++ TCP server.
import socket

# Import time to control how frequently sensor readings are generated.
import time

# Import datetime utilities to create UTC timestamps.
from datetime import datetime, timezone


# IP address of the C++ server.
# 127.0.0.1 means the server runs on the same computer.
SERVER_HOST = "127.0.0.1"

# TCP port shared by the Python client and C++ server.
SERVER_PORT = 5050

# Delay between each group of sensor readings.
SENSOR_INTERVAL_SECONDS = 1.0


# Supported fault-injection scenarios.
SUPPORTED_SCENARIOS = (
    "normal",
    "temperature-warning",
    "temperature-critical",
    "voltage-warning",
    "voltage-critical",
    "multiple-faults",
    "invalid-motion",
)


def parse_arguments() -> argparse.Namespace:
    """
    Read the selected simulation scenario from the command line.

    Example:
        python sensor_simulator.py --scenario temperature-warning
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate simulated sensor readings and send them "
            "to the C++ monitoring system."
        )
    )

    parser.add_argument(
        "--scenario",
        choices=SUPPORTED_SCENARIOS,
        default="normal",
        help="Fault-injection scenario to run.",
    )

    return parser.parse_args()


def create_sensor_reading(
    sensor_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    sequence_number: int,
) -> dict:
    """
    Create one standardized sensor reading.

    Every sensor uses the same message structure so the C++
    receiver can parse all messages consistently.
    """

    return {
        # Unique identifier for the simulated sensor.
        "sensor_id": sensor_id,

        # Category of the sensor.
        "sensor_type": sensor_type,

        # UTC time at which the reading was generated.
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Numeric sensor value rounded to two decimal places.
        "value": round(value, 2),

        # Measurement unit associated with the value.
        "unit": unit,

        # Increasing number used to verify message ordering.
        "sequence_number": sequence_number,
    }


def get_temperature_value(
    scenario: str,
) -> float:
    """
    Generate a temperature value based on the selected scenario.
    """

    if scenario == "temperature-warning":
        # Warning range in C++ is above 85°F but not critical.
        return 90.0

    if scenario == "temperature-critical":
        # Critical range in C++ is above 120°F.
        return 130.0

    if scenario == "multiple-faults":
        # First warning-level fault for the multiple-fault scenario.
        return 90.0

    # Normal operating temperature.
    return random.uniform(68.0, 78.0)


def get_voltage_value(
    scenario: str,
) -> float:
    """
    Generate a voltage value based on the selected scenario.
    """

    if scenario == "voltage-warning":
        # Warning range in C++ is above 12.8 V but not critical.
        return 13.2

    if scenario == "voltage-critical":
        # Critical range in C++ is above 14.5 V.
        return 15.2

    if scenario == "multiple-faults":
        # Second warning-level fault.
        # Two simultaneous warnings should trigger SAFE_MODE.
        return 13.2

    # Normal operating voltage.
    return random.uniform(11.8, 12.6)


def get_position_value() -> float:
    """
    Generate a normal position value between 0 and 100 units.
    """

    return random.uniform(0.0, 100.0)


def get_motion_value(
    scenario: str,
) -> float:
    """
    Generate a motion value based on the selected scenario.
    """

    if scenario == "invalid-motion":
        # The C++ system accepts only 0 or 1.
        return 2.0

    # Normal binary motion state.
    return random.choice([0.0, 1.0])


def generate_temperature_reading(
    sequence_number: int,
    scenario: str,
) -> dict:
    """
    Generate one temperature sensor reading.
    """

    return create_sensor_reading(
        sensor_id="TEMP-01",
        sensor_type="TEMPERATURE",
        value=get_temperature_value(scenario),
        unit="F",
        sequence_number=sequence_number,
    )


def generate_voltage_reading(
    sequence_number: int,
    scenario: str,
) -> dict:
    """
    Generate one voltage sensor reading.
    """

    return create_sensor_reading(
        sensor_id="VOLT-01",
        sensor_type="VOLTAGE",
        value=get_voltage_value(scenario),
        unit="V",
        sequence_number=sequence_number,
    )


def generate_position_reading(
    sequence_number: int,
) -> dict:
    """
    Generate one position sensor reading.
    """

    return create_sensor_reading(
        sensor_id="POS-01",
        sensor_type="POSITION",
        value=get_position_value(),
        unit="unit",
        sequence_number=sequence_number,
    )


def generate_motion_reading(
    sequence_number: int,
    scenario: str,
) -> dict:
    """
    Generate one motion sensor reading.
    """

    return create_sensor_reading(
        sensor_id="MOTION-01",
        sensor_type="MOTION",
        value=get_motion_value(scenario),
        unit="state",
        sequence_number=sequence_number,
    )


def create_sensor_cycle(
    sequence_number: int,
    scenario: str,
) -> list[dict]:
    """
    Generate one complete cycle containing four sensor readings.
    """

    return [
        generate_temperature_reading(
            sequence_number,
            scenario,
        ),
        generate_voltage_reading(
            sequence_number + 1,
            scenario,
        ),
        generate_position_reading(
            sequence_number + 2,
        ),
        generate_motion_reading(
            sequence_number + 3,
            scenario,
        ),
    ]


def send_message(
    client_socket: socket.socket,
    reading: dict,
) -> None:
    """
    Convert one reading into newline-delimited JSON
    and send it to the C++ monitoring server.
    """

    # Convert the Python dictionary into compact JSON text.
    json_message = json.dumps(reading)

    # Add a newline to identify the end of the message.
    network_message = f"{json_message}\n"

    # Convert the message to UTF-8 bytes and transmit all bytes.
    client_socket.sendall(
        network_message.encode("utf-8")
    )

    # Display the message sent for debugging and demonstration.
    print(f"[SENT] {json_message}")


def main() -> None:
    """
    Connect to the C++ server and continuously transmit
    normal or fault-injected sensor readings.
    """

    # Read the scenario selected by the user.
    arguments = parse_arguments()
    scenario = arguments.scenario

    # Every outgoing message receives a unique sequence number.
    sequence_number = 1

    print("Multi-sensor TCP simulator started.")
    print(f"Scenario: {scenario}")
    print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")

    try:
        # Create an IPv4 TCP client socket.
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as client_socket:

            # Connect to the waiting C++ monitoring server.
            client_socket.connect(
                (SERVER_HOST, SERVER_PORT)
            )

            print("Connected to the C++ sensor monitor.")
            print("Press Ctrl + C to stop.\n")

            while True:
                # Generate four readings using the selected scenario.
                sensor_readings = create_sensor_cycle(
                    sequence_number,
                    scenario,
                )

                # Transmit each sensor reading individually.
                for reading in sensor_readings:
                    send_message(
                        client_socket,
                        reading,
                    )

                # Four messages were transmitted during the cycle.
                sequence_number += len(sensor_readings)

                # Separate each cycle visually in the terminal.
                print()

                # Wait before generating the next sensor cycle.
                time.sleep(SENSOR_INTERVAL_SECONDS)

    except ConnectionRefusedError:
        # This normally means the C++ server is not running.
        print(
            "Connection failed. Start the C++ sensor monitor "
            "before starting the Python simulator."
        )

    except ConnectionResetError:
        # This occurs when the C++ server closes the connection.
        print(
            "The C++ sensor monitor closed the connection."
        )

    except KeyboardInterrupt:
        # Exit cleanly when Ctrl + C is pressed.
        print(
            "\nMulti-sensor TCP simulator stopped."
        )

    except OSError as error:
        # Handle other operating-system and networking failures.
        print(
            f"Network error: {error}"
        )


# Run the simulator only when this file is executed directly.
if __name__ == "__main__":
    main()