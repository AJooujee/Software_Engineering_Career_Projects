"""Password hashing and JSON Web Token utilities."""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings


# Use pwdlib's recommended Argon2 password hashing configuration.
password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Return an Argon2 hash for a plain-text password."""

    return password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Return whether a plain-text password matches its stored hash."""

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for one user identifier."""

    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": subject,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str:
    """Validate an access token and return its subject."""

    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    if payload.get("type") != "access":
        raise InvalidTokenError("Token type is invalid.")

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("Token subject is missing.")

    return subject
