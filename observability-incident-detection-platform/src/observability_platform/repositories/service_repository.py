from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import MonitoredService
from observability_platform.schemas.service import (
    ServiceCreate,
    ServiceEnvironment,
)


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, service_data: ServiceCreate) -> MonitoredService:
        service = MonitoredService(
            name=service_data.name,
            environment=service_data.environment.value,
            description=service_data.description,
        )
        self._session.add(service)
        await self._session.flush()
        await self._session.refresh(service)

        return service

    async def get_by_id(self, service_id: UUID) -> MonitoredService | None:
        return await self._session.get(MonitoredService, service_id)

    async def get_by_identity(
        self,
        name: str,
        environment: ServiceEnvironment,
    ) -> MonitoredService | None:
        statement = select(MonitoredService).where(
            MonitoredService.name == name,
            MonitoredService.environment == environment.value,
        )
        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_services(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[MonitoredService], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(MonitoredService)
        )
        total = count_result.scalar_one()

        statement = (
            select(MonitoredService)
            .order_by(
                MonitoredService.environment,
                MonitoredService.name,
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)

        return list(result.scalars().all()), total
