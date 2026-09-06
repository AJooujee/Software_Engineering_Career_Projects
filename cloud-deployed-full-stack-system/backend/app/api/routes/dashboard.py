"""FastAPI routes for authenticated operational dashboard metrics."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.dashboard import DashboardSummary
import app.services.dashboard as dashboard_service


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get operational dashboard metrics",
)
def get_dashboard_summary(
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> DashboardSummary:
    """Return current Incident metrics to an authenticated active user."""

    # Authentication is enforced by the dependency; metrics are identical
    # for every authorized role.
    del current_user

    return dashboard_service.get_dashboard_summary(
        database_session,
    )
