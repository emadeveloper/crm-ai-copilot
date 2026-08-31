"""Task 7.x — the app lifespan starts and cleanly stops the in-process worker."""

from __future__ import annotations

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from tests.fakes import InMemoryTaskQueue
from tests.fakes.container import make_fake_container


async def test_lifespan_runs_the_worker_and_shuts_it_down() -> None:
    queue = InMemoryTaskQueue()
    container = make_fake_container(queue=queue)
    app = create_app(container=container, run_worker=True)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/health")).status_code == 200
            # Container from a caller is reused, not rebuilt.
            assert app.state.container is container

    # Exiting the context runs shutdown: the worker task is awaited to completion
    # without raising, and the externally-owned container is left open.
    assert container._closables == []
