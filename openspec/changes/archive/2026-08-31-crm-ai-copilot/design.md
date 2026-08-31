# Design: CRM AI Copilot — MVP

## Technical Approach

Hexagonal backend (`services/api`): a pure-Python `domain` (entities + port protocols), an
`application` layer of use cases, and `adapters` for inbound (FastAPI REST, Strawberry GraphQL) and
outbound (Gemini, HubSpot, SQLAlchemy, Postgres queue) concerns wired in `infra`. One use-case layer
serves both API protocols. A worker drains a Postgres-backed task queue, running `EnrichLead` then
`SyncLeadToCrm`. Frontend (`apps/web`) is a Vite React PWA consuming a generated OpenAPI client.

## Architecture Decisions

| Topic | Options | Decision & rationale |
|---|---|---|
| Port style | ABC base classes / `typing.Protocol` | **Protocol** — adapters implement structurally, never import a domain base; keeps the boundary one-directional. |
| Domain types | pydantic / dataclasses | **dataclasses + value objects** in domain; pydantic only at API + adapter boundaries. Domain stays dependency-free. |
| Async queue | Redis+arq / Celery / FastAPI BackgroundTasks / Postgres table | **Postgres `tasks` table** claimed with `SELECT … FOR UPDATE SKIP LOCKED`. No extra infra on free tier, durable across restarts, already multi-worker safe. BackgroundTasks rejected (no durability/retry). |
| Worker process | separate Render worker (paid) / in-process asyncio task | **In-process asyncio task** started on app startup; code shaped as `python -m app.worker` so it splits out unchanged. One instance is enough for the demo. |
| LLM call shape | 3 calls / 1 structured call | **One call** with Gemini `response_schema` (JSON) → validated by a pydantic model. Fits the 15 req/min budget; deterministic parsing. |
| Rate limiting | rely on retries / token bucket | **`aiolimiter` token bucket** in the Gemini adapter (`LLM_RATE_PER_MIN`) plus worker pacing; backoff on 429. |
| Status refresh | WebSocket/SSE / polling | **Polling** (TanStack Query, ~5s) on the queue view. SSE deferred to Phase 2. |
| Generated client | hand-written fetch / openapi-typescript | **`openapi-typescript` + `openapi-fetch`** — types flow from the API schema, no drift. |

## Data Flow

    POST /leads ─→ SubmitLead ─→ LeadRepository.save(received)
                                └─ TaskQueue.enqueue(enrich) ─→ 201 {id}

    worker ─ claim(enrich) ─→ EnrichLead ─→ LLMProvider.analyze(lead)
                                          ├─ persist Enrichment/Score/ReplyDraft, status=qualified
                                          └─ TaskQueue.enqueue(sync)
    worker ─ claim(sync)   ─→ SyncLeadToCrm ─→ CrmGateway.upsert_contact + attach_note
                                             └─ persist SyncState, status=synced

    GET /leads/{id}  |  GraphQL lead(id) ─→ GetLead ─→ aggregate

## File Changes

| Path | Action | Description |
|---|---|---|
| `services/api/app/domain/` | Create | `lead.py`, `enrichment.py`, `score.py`, `reply_draft.py`, `sync_state.py`, `status.py`, `errors.py`, `ports.py` (LLMProvider, CrmGateway, LeadRepository, TaskQueue) |
| `services/api/app/application/` | Create | `submit_lead.py`, `enrich_lead.py`, `sync_lead_to_crm.py`, `get_lead.py`, `list_leads.py` |
| `services/api/app/adapters/api/rest/` | Create | FastAPI routers: `leads.py`, `health.py`; pydantic request/response schemas |
| `services/api/app/adapters/api/graphql/` | Create | Strawberry schema, `lead`/`leads` resolvers → use cases |
| `services/api/app/adapters/llm/gemini.py` | Create | `GeminiAIStudioAdapter` (google-genai, structured output, limiter, backoff) |
| `services/api/app/adapters/crm/hubspot.py` | Create | `HubSpotPrivateAppAdapter` (contacts upsert, notes) |
| `services/api/app/adapters/persistence/` | Create | SQLAlchemy models + `SqlLeadRepository` |
| `services/api/app/adapters/queue/postgres.py` | Create | `PostgresTaskQueue` (`SKIP LOCKED`), `tasks` model |
| `services/api/app/infra/` | Create | `config.py` (pydantic-settings), `db.py`, `container.py` (wiring), `worker.py`, `logging.py` |
| `services/api/migrations/` | Create | Alembic env + first revision (`leads`, `enrichments`, `scores`, `reply_drafts`, `sync_state`, `tasks`) |
| `services/api/tests/` | Create | port fakes, use-case unit tests, API + repository + queue integration tests |
| `services/api/{pyproject.toml,Dockerfile}` | Create | uv deps, ruff, mypy; container image |
| `apps/web/` | Create | Vite React TS app, TanStack Query, generated client, `vite-plugin-pwa`, queue + detail + add-lead form, vitest + Testing Library + MSW |
| `packages/shared/` | Create | `openapi-typescript` output + shared types |
| root | Create | `pnpm-workspace.yaml`, `justfile`, `render.yaml`, `.github/workflows/ci.yml` + `keepalive.yml`, `README.md`, `.env.example` |

## Interfaces / Contracts

```python
class LLMProvider(Protocol):
    async def analyze(self, lead: Lead) -> LeadAnalysis: ...      # Enrichment + Score + ReplyDraft

class CrmGateway(Protocol):
    async def upsert_contact(self, lead: Lead) -> CrmContactId: ...
    async def attach_note(self, contact_id: CrmContactId, note: str) -> None: ...

class LeadRepository(Protocol):
    async def save(self, lead: Lead) -> None: ...
    async def get(self, lead_id: LeadId) -> Lead | None: ...
    async def list(self, limit: int, offset: int) -> list[Lead]: ...

class TaskQueue(Protocol):
    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None: ...
    async def claim(self, kinds: set[TaskKind]) -> Task | None: ...   # FOR UPDATE SKIP LOCKED
    async def complete(self, task_id: TaskId) -> None: ...
    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None: ...
```

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | use cases, status transitions, score validation, backoff | in-memory fakes for all 4 ports; `pytest-asyncio` |
| Integration | REST + GraphQL, `SqlLeadRepository`, `PostgresTaskQueue` `SKIP LOCKED` | `httpx.AsyncClient`; real Postgres via `pytest-postgresql`/docker |
| Contract | Gemini + HubSpot adapters | `respx`-mocked HTTP against recorded fixtures |
| Frontend | queue render, status refresh, add-lead validation, offline read | vitest + Testing Library + MSW |
| E2E (optional) | submit → synced happy path | Playwright against a seeded local stack |

## Migration / Rollout

No data migration (greenfield). Alembic baseline revision creates all tables. Phase 1 deploys behind
no feature flags; the worker starts with the API process.

## Open Questions

- [ ] Frontend styling: shadcn/ui vs. minimal hand-rolled CSS — decide at tasks time (leaning minimal).
- [ ] E2E in Phase 1 CI or deferred to Phase 2 (leaning deferred — keep CI fast).
