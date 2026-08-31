from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # Fail quickly when PostgreSQL is unavailable instead of hanging tests.
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class shared by every Order Service database model."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session for each API request."""

    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()