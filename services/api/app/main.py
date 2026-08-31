"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.adapters.api.graphql.router import graphql_router
from app.adapters.api.rest import health, leads
from app.infra.config import get_settings
from app.infra.container import Container
from app.infra.logging import configure_logging
from app.infra.worker import PipelineWorker


def _build_worker(container: Container) -> PipelineWorker:
    settings = container.settings
    return PipelineWorker(
        queue=container.queue,
        enrich=container.enrich_lead(),
        sync=container.sync_lead_to_crm(),
        max_attempts=settings.max_task_attempts,
        poll_interval=settings.worker_poll_interval_seconds,
    )


def create_app(*, container: Container | None = None, run_worker: bool = True) -> FastAPI:
    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        owns_container = container is None
        active = container or Container.from_settings(get_settings())
        configure_logging(active.settings.log_level)
        app.state.container = active

        stop = asyncio.Event()
        worker_task: asyncio.Task[None] | None = None
        if run_worker:
            worker_task = asyncio.create_task(_build_worker(active).run_forever(stop=stop))
        try:
            yield
        finally:
            stop.set()
            if worker_task is not None:
                await worker_task
            if owns_container:
                await active.aclose()

    app = FastAPI(title="CRM AI Copilot", version="0.1.0", lifespan=lifespan)
    # Also set here so tests using ASGITransport (which skips lifespan) have a container.
    app.state.container = container

    app.include_router(health.router)
    app.include_router(leads.router)
    app.include_router(graphql_router)
    return app


app = create_app()
