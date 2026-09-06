"""Administrator-only FastAPI routes for immutable audit history."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession, require_roles
from app.models.user import User, UserRole
from app.schemas.audit_event import AuditEventResponse
import app.services.audit_events as audit_service


router = APIRouter(
    prefix="/audit-events",
    tags=["audit"],
)

Administrator = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.get(
    "",
    response_model=list[AuditEventResponse],
    summary="List audit history",
)
def list_audit_events(
    database_session: DatabaseSession,
    administrator: Administrator,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AuditEventResponse]:
    """Return recent audit history to an active administrator."""

    del administrator

    return audit_service.list_audit_events(
        database_session,
        offset=offset,
        limit=limit,
    )
