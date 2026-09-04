"""Pydantic schemas for users and authentication responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Define fields shared by user creation and response schemas."""

    email: EmailStr
    full_name: str = Field(
        min_length=1,
        max_length=120,
    )


class UserCreate(UserBase):
    """Validate data accepted during public user registration."""

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class UserResponse(UserBase):
    """Return public user information without exposing password hashes."""

    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """Validate an administrator request to change a user's role."""

    role: UserRole


class UserStatusUpdate(BaseModel):
    """Validate an administrator request to activate or disable a user."""

    is_active: bool


class TokenResponse(BaseModel):
    """Describe the bearer token returned after successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
