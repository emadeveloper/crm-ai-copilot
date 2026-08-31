# Migration path: `PostgresTaskQueue` → `CloudTasksAdapter`

**Status:** design note (Phase 3 of the roadmap). The MVP uses a Postgres-backed queue so it
needs exactly one datastore and no extra infra.

## The port

`app/domain/ports.py`:

```python
class TaskQueue(Protocol):
    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None: ...
    async def claim(self, kinds: set[TaskKind]) -> Task | None: ...
    async def complete(self, task_id: TaskId) -> None: ...
    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None: ...
```

The current implementation is **pull-based**: a worker loop calls `claim()` in a
`SELECT … FOR UPDATE SKIP LOCKED` transaction. Cloud Tasks is **push-based**, which changes the
shape of the solution.

## What Cloud Tasks gives you

- Managed retries with exponential backoff (`maxRetryDuration`, `maxAttempts`).
- Per-queue rate limiting (`maxDispatchesPerSecond`) — replaces the `aiolimiter` throttle.
- At-least-once delivery to an HTTP endpoint.

## Shape of the change

1. **`enqueue`** creates a Cloud Tasks task targeting an internal HTTP endpoint,
   `POST /internal/tasks/{kind}` with the `lead_id` in the body and an OIDC token for auth.
2. The **worker loop disappears**. Instead, add handlers:

   ```python
   @router.post("/internal/tasks/enrich")
   async def run_enrich(body: TaskBody, uc: EnrichLead = Depends(...)):
       await uc.execute(body.lead_id)
       return Response(status_code=200)  # 2xx = ack; non-2xx = Cloud Tasks retries
   ```

3. **`claim` / `complete`** become no-ops (or are removed from the port for the Cloud Tasks build);
   ack/nack is expressed by the HTTP status code.
4. **`fail`** with `retry_in` maps to returning a non-2xx so Cloud Tasks reschedules; permanent
   failure returns 2xx after `lead.mark_failed(...)` so the task is not retried.

## What stays the same

`EnrichLead` and `SyncLeadToCrm` are untouched — they already take a `lead_id` and are
idempotent. The status lifecycle guard (`app/domain/status.py`) already tolerates
at-least-once delivery (re-running `enrich` on a `qualified` lead is a no-op).

## Keep both

Ship `CloudTasksAdapter` alongside `PostgresTaskQueue` and pick via config, so local dev and CI
keep using Postgres (no GCP emulator needed) while production uses Cloud Tasks.
