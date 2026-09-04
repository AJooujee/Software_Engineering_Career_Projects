"""Shared pytest fixtures for isolated API integration tests."""

import os
from collections.abc import Callable, Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


# Configure isolated test settings before importing application modules.
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET_KEY"] = (
    "test-only-jwt-secret-key-with-at-least-32-characters"
)
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["JWT_ISSUER"] = "cloud-operations-api"
os.environ["JWT_AUDIENCE"] = "cloud-operations-client"

# These imports must occur after the test environment is configured.
import app.models  # noqa: E402, F401
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


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
def database_session() -> Generator[Session, None, None]:
    """Provide direct database access for arranging test state."""

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI client connected to the isolated test database."""

    def override_get_db() -> Generator[Session, None, None]:
        """Provide one isolated database session per API request."""

        request_session = TestingSessionLocal()

        try:
            yield request_session
        finally:
            request_session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Prevent dependency overrides from leaking into another test.
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def authenticated_user_factory(
    client: TestClient,
    database_session: Session,
) -> Callable[..., dict[str, object]]:
    """Create users with bearer tokens for authorization tests."""

    def create_authenticated_user(
        *,
        role: UserRole = UserRole.VIEWER,
        email: str | None = None,
        password: str = "SecureTestPassword123!",
    ) -> dict[str, object]:
        user_email = email or (
            f"{role.value}-{uuid4()}@example.com"
        )

        registration_response = client.post(
            "/api/auth/register",
            json={
                "email": user_email,
                "full_name": f"{role.value.title()} Test User",
                "password": password,
            },
        )

        assert registration_response.status_code == 201

        registered_user = registration_response.json()
        user_id = UUID(registered_user["id"])

        if role != UserRole.VIEWER:
            database_user = database_session.get(User, user_id)

            assert database_user is not None

            database_user.role = role
            database_session.commit()
            database_session.expire_all()

        token_response = client.post(
            "/api/auth/token",
            data={
                "username": user_email,
                "password": password,
            },
        )

        assert token_response.status_code == 200

        token_data = token_response.json()

        return {
            "id": str(user_id),
            "email": user_email.lower(),
            "password": password,
            "headers": {
                "Authorization": (
                    f"Bearer {token_data['access_token']}"
                )
            },
            "token": token_data,
        }

    return create_authenticated_user
