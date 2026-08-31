"""Build a Container wired to in-memory fakes, for API-level tests."""

from __future__ import annotations

from app.infra.config import Settings
from app.infra.container import Container
from tests.fakes import (
    FakeCrmGateway,
    FakeLLMProvider,
    InMemoryLeadRepository,
    InMemoryTaskQueue,
)


def make_fake_container(
    *,
    leads: InMemoryLeadRepository | None = None,
    queue: InMemoryTaskQueue | None = None,
    llm: FakeLLMProvider | None = None,
    crm: FakeCrmGateway | None = None,
) -> Container:
    settings = Settings(
        database_url="postgresql+asyncpg://x/x",
        gemini_api_key="test",
        hubspot_private_app_token="test",
    )
    return Container(
        settings=settings,
        leads=leads or InMemoryLeadRepository(),
        queue=queue or InMemoryTaskQueue(),
        llm=llm or FakeLLMProvider(),
        crm=crm or FakeCrmGateway(),
        _closables=[],
    )
