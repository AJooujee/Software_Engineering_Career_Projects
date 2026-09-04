"""Reusable FastAPI application dependencies."""

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
    get_current_user,
    oauth2_scheme,
    require_roles,
)


__all__ = [
    "CurrentUser",
    "DatabaseSession",
    "get_current_user",
    "oauth2_scheme",
    "require_roles",
]
