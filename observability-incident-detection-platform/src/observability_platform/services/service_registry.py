from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import MonitoredService
from observability_platform.repositories.service_repository import (
    ServiceRepository,
)
from observability_platform.schemas.service import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
)


class ServiceAlreadyExistsError(Exception):
    pass


class ServiceNotFoundError(Exception):
    pass


class ServiceRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ServiceRepository(session)

    async def register(self, service_data: ServiceCreate) -> MonitoredService:
        existing = await self._repository.get_by_identity(
            service_data.name,
            service_data.environment,
        )
        if existing is not None:
            raise ServiceAlreadyExistsError(
                "A service with this name and environment already exists"
            )

        try:
            service = await self._repository.create(service_data)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ServiceAlreadyExistsError(
                "A service with this name and environment already exists"
            ) from error
        except Exception:
            await self._session.rollback()
            raise

        return service

    async def get(self, service_id: UUID) -> MonitoredService:
        service = await self._repository.get_by_id(service_id)

        if service is None:
            raise ServiceNotFoundError("Monitored service was not found")

        return service

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> ServiceListResponse:
        services, total = await self._repository.list_services(
            offset=offset,
            limit=limit,
        )

        return ServiceListResponse(
            items=[ServiceResponse.model_validate(service) for service in services],
            total=total,
        )
