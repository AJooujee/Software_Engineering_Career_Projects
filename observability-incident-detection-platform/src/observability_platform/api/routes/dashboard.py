"""HTTP endpoints for operational metric dashboard data."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.dashboard import MetricSummaryResponse
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.services.metric_dashboard_service import (
    InconsistentMetricUnitError,
    InvalidDashboardWindowError,
    MetricDashboardService,
    MetricSamplesNotFoundError,
)

# Group dashboard operations under one versioned API prefix and Swagger tag.
router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Metrics Dashboard"],
)

# Provide one request-scoped asynchronous database session to each endpoint.
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "/metrics/summary",
    response_model=MetricSummaryResponse,
    summary="Summarize one operational metric",
)
async def summarize_metric(
    session: SessionDependency,
    service: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            description="Registered monitored service name",
        ),
    ],
    environment: Annotated[
        ServiceEnvironment,
        Query(description="Registered service environment"),
    ],
    metric_name: Annotated[
        str,
        Query(
            alias="metric",
            min_length=1,
            max_length=100,
            description="Metric name stored in telemetry payloads",
        ),
    ],
    source: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
            description="Optional runtime source filter",
        ),
    ] = None,
    observed_from: Annotated[
        datetime | None,
        Query(description="Inclusive lower observation-time boundary"),
    ] = None,
    observed_to: Annotated[
        datetime | None,
        Query(description="Inclusive upper observation-time boundary"),
    ] = None,
    window_minutes: Annotated[
        int,
        Query(
            ge=1,
            le=10080,
            description=("Default lookback window used when observed_from is omitted"),
        ),
    ] = 60,
) -> MetricSummaryResponse:
    """Return summary statistics and chart points for one metric."""

    # Keep aggregation and persistence logic outside the HTTP route.
    dashboard_service = MetricDashboardService(session)

    try:
        # Delegate time-window calculation, filtering, and statistics to the
        # dashboard application service.
        return await dashboard_service.summarize(
            service=service,
            environment=environment,
            metric_name=metric_name,
            source=source,
            observed_from=observed_from,
            observed_to=observed_to,
            window_minutes=window_minutes,
        )
    except MetricSamplesNotFoundError as error:
        # A valid dashboard query without matching samples represents a missing
        # metric resource for the selected service and time range.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        InconsistentMetricUnitError,
        InvalidDashboardWindowError,
    ) as error:
        # These requests are structurally valid but cannot produce meaningful
        # metric aggregation.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
