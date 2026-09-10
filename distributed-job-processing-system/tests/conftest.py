from collections.abc import AsyncIterator

import pytest
from httpx2 import ASGITransport, AsyncClient

from job_system.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an asynchronous client without opening a network port."""

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client
