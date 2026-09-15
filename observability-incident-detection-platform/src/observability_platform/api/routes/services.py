from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.service import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
)
from observability_platform.services.service_registry import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
    ServiceRegistryService,
)

router = APIRouter(
    prefix="/api/v1/services",
    tags=["Service Registry"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a monitored service",
)
async def register_service(
    service_data: ServiceCreate,
    session: SessionDependency,
) -> ServiceResponse:
    registry = ServiceRegistryService(session)

    try:
        service = await registry.register(service_data)
    except ServiceAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return ServiceResponse.model_validate(service)


@router.get(
    "",
    response_model=ServiceListResponse,
    summary="List monitored services",
)
async def list_services(
    session: SessionDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ServiceListResponse:
    registry = ServiceRegistryService(session)

    return await registry.list(offset=offset, limit=limit)


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get a monitored service",
)
async def get_service(
    service_id: UUID,
    session: SessionDependency,
) -> ServiceResponse:
    registry = ServiceRegistryService(session)

    try:
        service = await registry.get(service_id)
    except ServiceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return ServiceResponse.model_validate(service)
