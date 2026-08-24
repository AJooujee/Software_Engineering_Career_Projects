import argparse
import json

from sensor_platform.models import SensorType
from sensor_platform.simulator import SensorSimulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate simulated hardware sensor readings."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of readings generated for each sensor type.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used to produce repeatable data.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.count <= 0:
        parser.error("--count must be greater than zero")

    readings = []

    for index, sensor_type in enumerate(SensorType):
        simulator = SensorSimulator(
            sensor_id=f"{sensor_type.value}-001",
            sensor_type=sensor_type,
            seed=args.seed + index,
        )
        readings.extend(simulator.generate_batch(args.count))

    print(
        json.dumps(
            [reading.to_dict() for reading in readings],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
