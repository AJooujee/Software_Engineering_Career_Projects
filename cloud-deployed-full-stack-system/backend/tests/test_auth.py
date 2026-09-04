"""Integration tests for registration and JWT authentication."""

from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.users import get_user_by_email


def test_registration_creates_hashed_viewer_account(
    client: TestClient,
    database_session: Session,
) -> None:
    """Register a viewer without exposing password information."""

    response = client.post(
        "/api/auth/register",
        json={
            "email": "New.User@Example.com",
            "full_name": "New User",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 201

    response_body = response.json()

    UUID(response_body["id"])
    assert response_body["email"] == "new.user@example.com"
    assert response_body["role"] == "viewer"
    assert response_body["is_active"] is True
    assert "password" not in response_body
    assert "password_hash" not in response_body

    stored_user = get_user_by_email(
        database_session,
        "new.user@example.com",
    )

    assert stored_user is not None
    assert stored_user.password_hash.startswith("$argon2")
    assert stored_user.password_hash != "SecurePassword123!"
    assert verify_password(
        "SecurePassword123!",
        stored_user.password_hash,
    )


def test_duplicate_email_registration_returns_conflict(
    client: TestClient,
) -> None:
    """Treat differently cased versions of one email as duplicates."""

    registration_payload = {
        "email": "duplicate@example.com",
        "full_name": "First User",
        "password": "SecurePassword123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=registration_payload,
    )

    duplicate_response = client.post(
        "/api/auth/register",
        json={
            **registration_payload,
            "email": "DUPLICATE@EXAMPLE.COM",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": (
            "Email 'duplicate@example.com' is already registered."
        )
    }


def test_login_and_current_user_profile(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Issue a bearer token and use it to load the current user."""

    account = authenticated_user_factory(
        email="login.user@example.com",
    )

    token_data = account["token"]

    assert isinstance(token_data, dict)
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 1800
    assert token_data["access_token"]

    response = client.get(
        "/api/auth/me",
        headers=account["headers"],
    )

    assert response.status_code == 200
    assert response.json()["id"] == account["id"]
    assert response.json()["email"] == account["email"]
    assert response.json()["role"] == "viewer"


def test_invalid_credentials_and_tokens_are_rejected(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Reject incorrect passwords, missing tokens, and malformed tokens."""

    account = authenticated_user_factory(
        email="credentials@example.com",
    )

    invalid_password_response = client.post(
        "/api/auth/token",
        data={
            "username": account["email"],
            "password": "IncorrectPassword123!",
        },
    )

    missing_token_response = client.get("/api/auth/me")

    invalid_token_response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert invalid_password_response.status_code == 401
    assert invalid_password_response.json() == {
        "detail": "Incorrect email or password."
    }

    assert missing_token_response.status_code == 401
    assert (
        missing_token_response.headers["www-authenticate"]
        == "Bearer"
    )

    assert invalid_token_response.status_code == 401
    assert invalid_token_response.json() == {
        "detail": "Could not validate credentials."
    }


def test_disabled_user_cannot_login_or_use_existing_token(
    client: TestClient,
    database_session: Session,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Reject disabled accounts even when a token already exists."""

    account = authenticated_user_factory(
        email="disabled@example.com",
    )

    database_user = database_session.get(
        User,
        UUID(account["id"]),
    )

    assert database_user is not None

    database_user.is_active = False
    database_session.commit()
    database_session.expire_all()

    current_user_response = client.get(
        "/api/auth/me",
        headers=account["headers"],
    )

    login_response = client.post(
        "/api/auth/token",
        data={
            "username": account["email"],
            "password": account["password"],
        },
    )

    assert current_user_response.status_code == 403
    assert current_user_response.json() == {
        "detail": "User account is disabled."
    }

    assert login_response.status_code == 403
    assert login_response.json() == {
        "detail": "User account is disabled."
    }


def test_registration_rejects_invalid_user_input(
    client: TestClient,
) -> None:
    """Reject invalid email addresses and short passwords."""

    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "Invalid User",
            "password": "short",
        },
    )

    assert response.status_code == 422
