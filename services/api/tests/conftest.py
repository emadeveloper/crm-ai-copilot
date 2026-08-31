"""Shared fixtures. Integration tests get an ephemeral PostgreSQL via pytest-postgresql."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import pytest_asyncio
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.adapters.persistence.models import Base

postgresql_proc = factories.postgresql_proc()


@pytest.fixture
def pg_async_url(postgresql_proc: Any) -> Iterator[str]:
    """Create a fresh database on the running PG process and yield an asyncpg URL."""
    proc = postgresql_proc
    with DatabaseJanitor(
        user=proc.user,
        host=proc.host,
        port=proc.port,
        dbname="test_db",
        password=proc.password,
    ):
        yield f"postgresql+asyncpg://{proc.user}:{proc.password}@{proc.host}:{proc.port}/test_db"


@pytest_asyncio.fixture
async def engine(pg_async_url: str) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(pg_async_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
