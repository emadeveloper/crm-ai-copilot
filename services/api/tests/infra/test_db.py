"""Task 7.x — infra/db wiring (lazy, cached, rollback on error)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.infra import config, db


def test_engine_is_built_lazily_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pw@localhost/db")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("HUBSPOT_PRIVATE_APP_TOKEN", "x")
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()

    try:
        engine = db.get_engine()
        assert isinstance(engine, AsyncEngine)
        assert db.get_engine() is engine  # cached
        assert isinstance(db.get_sessionmaker(), async_sessionmaker)
    finally:
        config.get_settings.cache_clear()
        db.get_engine.cache_clear()
        db.get_sessionmaker.cache_clear()


async def test_get_session_rolls_back_and_closes_on_error(
    sessionmaker: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(db, "get_sessionmaker", lambda: sessionmaker)

    gen = cast(AsyncGenerator[AsyncSession, None], db.get_session())
    session = await gen.__anext__()
    await session.execute(text("SELECT 1"))
    assert session.in_transaction()

    with pytest.raises(RuntimeError):
        await gen.athrow(RuntimeError("boom"))
    assert not session.in_transaction()  # rolled back and closed
