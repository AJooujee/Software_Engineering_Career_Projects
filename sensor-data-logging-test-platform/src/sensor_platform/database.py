"""Database configuration for the sensor logging platform."""

from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# The application stores generated sensor data in this SQLite file by default.
DEFAULT_DATABASE_PATH = Path("data") / "sensor_data.db"


class Base(DeclarativeBase):
    """Base class shared by every SQLAlchemy database model."""


def create_database_engine(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Engine:
    """Create a SQLite engine and ensure its parent directory exists."""

    resolved_path = Path(database_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # URL.create safely handles Windows paths such as C:\Dev\project\data.
    database_url = URL.create(
        drivername="sqlite",
        database=str(resolved_path),
    )

    return create_engine(database_url)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create database sessions connected to the supplied engine."""

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def initialize_database(engine: Engine) -> None:
    """Create all database tables that do not already exist."""

    # Importing the model registers its table with Base.metadata.
    from sensor_platform.db_models import SensorReadingRecord

    _ = SensorReadingRecord
    Base.metadata.create_all(engine)
