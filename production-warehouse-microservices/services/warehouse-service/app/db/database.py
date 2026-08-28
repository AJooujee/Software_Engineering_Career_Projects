from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

# The engine owns the PostgreSQL connection pool for this service.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # Fail quickly when PostgreSQL is unavailable instead of hanging tests.
    connect_args={"connect_timeout": 5},
)

# Each API request receives an independent database session.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class shared by all Warehouse Service ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and always close it after the request."""
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()