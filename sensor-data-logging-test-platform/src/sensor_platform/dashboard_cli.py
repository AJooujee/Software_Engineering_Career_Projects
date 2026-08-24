"""Launch the Streamlit dashboard from the command line."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Start Streamlit using the installed Python environment."""

    dashboard_path = Path(__file__).with_name("dashboard.py")

    # Using the current interpreter guarantees the correct virtual environment.
    completed_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
        ],
        check=False,
    )

    raise SystemExit(completed_process.returncode)


if __name__ == "__main__":
    main()
