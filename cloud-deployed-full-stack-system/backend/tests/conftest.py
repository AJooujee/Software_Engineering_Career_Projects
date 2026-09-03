"""Shared pytest fixtures for isolated API integration tests."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


# Configure the test database before importing application modules.
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# These imports must occur after the test environment is configured.
import app.models  # noqa: E402, F401
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


# StaticPool keeps the in-memory database available across test threads.
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def reset_test_database() -> Generator[None, None, None]:
    """Create a clean database schema before every test."""

    Base.metadata.create_all(bind=test_engine)

    yield

    # Remove all test data and tables after the test completes.
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI client connected to the isolated test database."""

    def override_get_db() -> Generator[Session, None, None]:
        """Provide one isolated database session per API request."""

        database_session = TestingSessionLocal()

        try:
            yield database_session
        finally:
            database_session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Prevent dependency overrides from leaking into another test.
        app.dependency_overrides.pop(get_db, None)
