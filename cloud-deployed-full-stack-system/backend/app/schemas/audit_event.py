"""Pydantic response schema for immutable audit history."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.audit_event import (
    AuditAction,
    AuditResourceType,
)
from app.models.user import UserRole


class AuditEventResponse(BaseModel):
    """Return one safe audit event without authentication secrets."""

    id: UUID
    actor_user_id: UUID
    actor_email: str
    actor_role: UserRole
    action: AuditAction
    resource_type: AuditResourceType
    resource_id: UUID
    resource_label: str
    changes: dict[str, dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
