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


# IP address of the C++ monitoring server.
# 127.0.0.1 means the server is running on the same computer.
SERVER_HOST = "127.0.0.1"

# TCP port shared by the Python client and C++ server.
SERVER_PORT = 5050

# Number of seconds between each group of sensor readings.
SENSOR_INTERVAL_SECONDS = 1.0


# Supported normal-operation and fault-injection scenarios.
SUPPORTED_SCENARIOS = (
    "normal",
    "temperature-warning",
    "temperature-critical",
    "voltage-warning",
    "voltage-critical",
    "multiple-faults",
    "invalid-motion",
    "sensor-timeout",
)


def parse_arguments() -> argparse.Namespace:
    """
    Read the selected simulation scenario from the command line.

    Example:
        python sensor_simulator.py --scenario temperature-warning
    """

    # Create the command-line argument parser.
    parser = argparse.ArgumentParser(
        description=(
            "Generate simulated sensor readings and send them "
            "to the C++ monitoring system."
        )
    )

    # Add the optional scenario argument.
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
        # Warning-level temperature.
        return 90.0

    if scenario == "temperature-critical":
        # Critical temperature.
        return 130.0

    if scenario == "multiple-faults":
        # First warning-level fault in the multiple-fault scenario.
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
        # Warning-level voltage.
        return 13.2

    if scenario == "voltage-critical":
        # Critical voltage.
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
    cycle_number: int,
) -> list[dict]:
    """
    Generate one complete cycle of sensor readings.

    During the sensor-timeout scenario, TEMP-01 stops transmitting
    after the first three cycles. The C++ monitor should detect that
    the sensor has not reported within the configured timeout.
    """

    # Store all readings generated during the current cycle.
    sensor_readings: list[dict] = []

    # During normal scenarios, always send the temperature sensor.
    # During sensor-timeout, stop sending TEMP-01 after cycle 3.
    if scenario != "sensor-timeout" or cycle_number <= 3:
        sensor_readings.append(
            generate_temperature_reading(
                sequence_number,
                scenario,
            )
        )

    # Always send voltage, position, and motion readings.
    sensor_readings.extend(
        [
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
    )

    return sensor_readings


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

    # Add a newline so the C++ receiver can detect message boundaries.
    network_message = f"{json_message}\n"

    # Convert the string to UTF-8 bytes and transmit all bytes.
    client_socket.sendall(
        network_message.encode("utf-8")
    )

    # Display the transmitted message for debugging.
    print(f"[SENT] {json_message}")


def main() -> None:
    """
    Connect to the C++ server and continuously transmit
    normal or fault-injected sensor readings.
    """

    # Read the scenario selected by the user.
    arguments = parse_arguments()
    scenario = arguments.scenario

    # Every outgoing message receives a sequence number.
    sequence_number = 1

    # Count how many complete sensor cycles have been generated.
    # This is required for the sensor-timeout scenario.
    cycle_number = 1

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
                # Generate readings using the selected scenario
                # and current cycle number.
                sensor_readings = create_sensor_cycle(
                    sequence_number,
                    scenario,
                    cycle_number,
                )

                # Transmit every generated sensor reading.
                for reading in sensor_readings:
                    send_message(
                        client_socket,
                        reading,
                    )

                # Advance by the number of messages actually sent.
                #
                # During sensor-timeout, only three messages are sent
                # after TEMP-01 stops transmitting.
                sequence_number += len(sensor_readings)

                # Advance to the next simulation cycle.
                cycle_number += 1

                # Separate cycles visually in the terminal.
                print()

                # Wait before generating the next cycle.
                time.sleep(SENSOR_INTERVAL_SECONDS)

    except ConnectionRefusedError:
        # This usually means the C++ server is not running.
        print(
            "Connection failed. Start the C++ sensor monitor "
            "before starting the Python simulator."
        )

    except ConnectionResetError:
        # This occurs if the C++ server closes the connection.
        print(
            "The C++ sensor monitor closed the connection."
        )

    except BrokenPipeError:
        # This occurs when the connection closes during transmission.
        print(
            "The network connection was closed while sending sensor data."
        )

    except KeyboardInterrupt:
        # Exit cleanly when the user presses Ctrl + C.
        print(
            "\nMulti-sensor TCP simulator stopped."
        )

    except OSError as error:
        # Handle other networking or operating-system errors.
        print(
            f"Network error: {error}"
        )


# Run the simulator only when this file is executed directly.
if __name__ == "__main__":
    main()