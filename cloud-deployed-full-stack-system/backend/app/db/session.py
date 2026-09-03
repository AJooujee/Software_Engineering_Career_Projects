"""SQLAlchemy engine, session factory, and FastAPI database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


# Read the database URL once when the backend process starts.
settings = get_settings()

# pool_pre_ping checks connections before returning them from the pool.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

# Each API request receives an independent database session.
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and always close it after the request."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()