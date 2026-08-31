"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
import os
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.api.graphql.router import graphql_router
from app.adapters.api.rest import health, leads
from app.infra.config import get_settings
from app.infra.container import Container
from app.infra.logging import configure_logging
from app.infra.worker import PipelineWorker

_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:5174"


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _build_worker(container: Container) -> PipelineWorker:
    settings = container.settings
    return PipelineWorker(
        queue=container.queue,
        enrich=container.enrich_lead(),
        sync=container.sync_lead_to_crm(),
        max_attempts=settings.max_task_attempts,
        poll_interval=settings.worker_poll_interval_seconds,
    )


def create_app(
    *,
    container: Container | None = None,
    run_worker: bool = True,
    cors_origins: list[str] | None = None,
) -> FastAPI:
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins is not None else _cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(leads.router)
    app.include_router(graphql_router)
    return app


app = create_app()
