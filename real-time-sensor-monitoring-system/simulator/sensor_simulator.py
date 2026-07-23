# Import json to convert Python dictionaries into JSON messages.
import json

# Import random to generate simulated sensor values.
import random

# Import time to control how often readings are generated.
import time

# Import datetime utilities to create UTC timestamps.
from datetime import datetime, timezone


def create_sensor_reading(
    sensor_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    sequence_number: int,
) -> dict:
    """
    Create one standardized sensor reading.

    Each sensor uses the same message structure so the future C++
    receiver can process all sensor types consistently.
    """

    return {
        # Unique identifier for the physical or simulated sensor.
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


def main() -> None:
    """
    Continuously generate readings from four simulated sensors.
    """

    # Each generated message receives a unique sequence number.
    sequence_number = 1

    print("Multi-sensor simulator started.")
    print("Generating temperature, voltage, position, and motion readings.")
    print("Press Ctrl + C to stop.\n")

    try:
        while True:
            # Generate one reading from each sensor.
            sensor_readings = [
                generate_temperature_reading(sequence_number),
                generate_voltage_reading(sequence_number + 1),
                generate_position_reading(sequence_number + 2),
                generate_motion_reading(sequence_number + 3),
            ]

            # Print one compact JSON message per line.
            # This format will be easier to send and parse over TCP/IP.
            for reading in sensor_readings:
                print(json.dumps(reading))

            # Four messages were generated, so advance by four.
            sequence_number += len(sensor_readings)

            # Add a blank line to improve readability in the terminal.
            print()

            # Wait one second before generating the next sensor cycle.
            time.sleep(1)

    except KeyboardInterrupt:
        # Exit cleanly when the user presses Ctrl + C.
        print("\nMulti-sensor simulator stopped.")


# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()