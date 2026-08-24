"""Launch the FastAPI application with Uvicorn."""

import argparse

import uvicorn


def main() -> None:
    """Start the API server using command-line configuration."""

    parser = argparse.ArgumentParser(
        description="Run the sensor platform REST API."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload automatically during local development.",
    )
    args = parser.parse_args()

    uvicorn.run(
        "sensor_platform.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
