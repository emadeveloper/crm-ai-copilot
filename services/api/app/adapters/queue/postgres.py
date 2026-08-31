"""PostgreSQL-backed :class:`TaskQueue`.

Claiming is a single atomic statement: ``UPDATE ... WHERE id = (SELECT ... FOR UPDATE SKIP LOCKED
LIMIT 1) RETURNING ...``. Concurrent workers never receive the same task, and a task locked by a
worker that then crashes is reclaimed once its lock goes stale.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.ports import Task, TaskKind
from app.domain.value_objects import LeadId, TaskId

_DEFAULT_STALE_AFTER = timedelta(minutes=5)
_DEFAULT_RETRY_IN = timedelta(seconds=30)

_CLAIM_SQL = text(
    """
    UPDATE tasks SET
        status = 'in_progress',
        locked_at = now(),
        locked_by = :worker_id,
        attempts = attempts + 1,
        updated_at = now()
    WHERE id = (
        SELECT id FROM tasks
        WHERE kind IN :kinds
          AND (
                (status = 'queued' AND run_after <= now())
             OR (status = 'in_progress' AND locked_at < now() - CAST(:stale AS interval))
          )
        ORDER BY run_after
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    RETURNING id, lead_id, kind, attempts
    """
).bindparams(bindparam("kinds", expanding=True))


class PostgresTaskQueue:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        *,
        worker_id: str = "worker",
        stale_after: timedelta = _DEFAULT_STALE_AFTER,
        default_retry_in: timedelta = _DEFAULT_RETRY_IN,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._worker_id = worker_id
        self._stale_after = stale_after
        self._default_retry_in = default_retry_in

    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(
                text(
                    "INSERT INTO tasks (id, lead_id, kind, status, run_after) "
                    "VALUES (:id, :lead_id, :kind, 'queued', now())"
                ),
                {"id": uuid4(), "lead_id": lead_id.value, "kind": str(kind)},
            )

    async def claim(self, kinds: set[TaskKind]) -> Task | None:
        async with self._sessionmaker() as session, session.begin():
            row = (
                await session.execute(
                    _CLAIM_SQL,
                    {
                        "worker_id": self._worker_id,
                        "kinds": [str(k) for k in kinds],
                        "stale": self._stale_after,
                    },
                )
            ).one_or_none()
        if row is None:
            return None
        return Task(
            id=TaskId(row.id),
            lead_id=LeadId(row.lead_id),
            kind=TaskKind(row.kind),
            attempts=row.attempts,
        )

    async def complete(self, task_id: TaskId) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(
                text("UPDATE tasks SET status = 'done', updated_at = now() WHERE id = :id"),
                {"id": task_id.value},
            )

    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None:
        if retry_in is None:
            statement = text(
                "UPDATE tasks SET status = 'failed', last_error = :error, updated_at = now() "
                "WHERE id = :id"
            )
            params: dict[str, object] = {"id": task_id.value, "error": error}
        else:
            statement = text(
                "UPDATE tasks SET status = 'queued', "
                "run_after = now() + CAST(:retry_in AS interval), "
                "last_error = :error, locked_at = NULL, locked_by = NULL, updated_at = now() "
                "WHERE id = :id"
            )
            params = {"id": task_id.value, "error": error, "retry_in": retry_in}
        async with self._sessionmaker() as session, session.begin():
            await session.execute(statement, params)
