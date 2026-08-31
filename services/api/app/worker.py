"""Standalone entrypoint for the pipeline worker: ``python -m app.worker``.

The same worker also runs in-process inside the API. Running it separately lets you scale the
pipeline independently of HTTP traffic.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal

from app.infra.config import get_settings
from app.infra.container import Container
from app.infra.logging import configure_logging
from app.infra.worker import PipelineWorker

logger = logging.getLogger("app.worker")


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    container = Container.from_settings(settings)
    worker = PipelineWorker(
        queue=container.queue,
        enrich=container.enrich_lead(),
        sync=container.sync_lead_to_crm(),
        max_attempts=settings.max_task_attempts,
        poll_interval=settings.worker_poll_interval_seconds,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    try:
        await worker.run_forever(stop=stop)
    finally:
        await container.aclose()


if __name__ == "__main__":
    asyncio.run(_main())
