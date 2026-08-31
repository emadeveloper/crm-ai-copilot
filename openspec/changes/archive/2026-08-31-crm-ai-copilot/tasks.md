# Tasks: CRM AI Copilot — MVP

## Phase 1: Foundation

- [x] 1.1 Root scaffold: `pnpm-workspace.yaml`, `justfile`, `.gitignore`, `env.example`, `README.md` skeleton
- [x] 1.2 `services/api/pyproject.toml` (uv): fastapi, strawberry-graphql, sqlalchemy, alembic, asyncpg, google-genai, httpx, aiolimiter, pydantic-settings, pytest(-asyncio), pytest-postgresql, respx, ruff, mypy
- [x] 1.3 `app/infra/config.py`: pydantic-settings (GEMINI_API_KEY, HUBSPOT_PRIVATE_APP_TOKEN, DATABASE_URL, LLM_MODEL, LLM_RATE_PER_MIN, MAX_TASK_ATTEMPTS)
- [x] 1.4 `app/infra/db.py`: async engine + session factory
- [x] 1.5 Alembic init + baseline revision: `leads`, `enrichments`, `scores`, `reply_drafts`, `sync_state`, `tasks`
- [x] 1.6 `services/api/Dockerfile`

## Phase 2: Domain

- [x] 2.1 `domain/status.py`: `LeadStatus` enum + allowed-transitions map + `assert_transition()` guard
- [x] 2.2 `domain/{lead,enrichment,score,reply_draft,sync_state,value_objects}.py`: dataclasses + value objects (LeadId, TaskId, Email, CrmContactId); `Score` validates value 0..100 ↔ band
- [x] 2.3 `domain/errors.py`: domain exceptions
- [x] 2.4 `domain/ports.py`: `LLMProvider`, `CrmGateway`, `LeadRepository`, `TaskQueue` Protocols + `Task`/`TaskKind`/`LeadAnalysis` DTOs

## Phase 3: Application

- [x] 3.1 `application/submit_lead.py`: validate, dedupe (email, source, 24h), save `received`, enqueue `enrich`
- [x] 3.2 `application/enrich_lead.py`: call `LLMProvider`, validate, persist trio atomically, → `qualified`, enqueue `sync`; on exhaustion → `failed`
- [x] 3.3 `application/sync_lead_to_crm.py`: upsert contact + note, `SyncState=synced`; on gateway error `SyncState=failed`, keep derived data
- [x] 3.4 `application/{get_lead,list_leads}.py`: aggregate assembly + pagination (newest-first)

## Phase 4: Outbound adapters

- [x] 4.1 `adapters/persistence/`: SQLAlchemy models + mappers + `SqlLeadRepository` (save/get/find-dup/save-analysis/save-sync-state/get-aggregate/list-aggregates) + migration↔ORM parity test
- [x] 4.2 `adapters/queue/postgres.py`: `PostgresTaskQueue` — enqueue / claim (single-statement `FOR UPDATE SKIP LOCKED`) / complete / fail(retry_in) + stale-lock reclaim
- [x] 4.3 `adapters/llm/gemini.py`: `GeminiAIStudioAdapter` — structured JSON output, `aiolimiter` throttle, error translation (retry/backoff lives in `EnrichLead`)
- [x] 4.4 `adapters/crm/hubspot.py`: `HubSpotPrivateAppAdapter` — contact search+upsert, note create+associate, `CrmError` translation

## Phase 5: Inbound adapters + wiring

- [x] 5.1 `adapters/api/rest/`: schemas + `leads.py` (POST /leads 201/200-dedup, GET /leads, GET /leads/{id} 404) + `health.py` + `api/deps.py`
- [x] 5.2 `adapters/api/graphql/`: Strawberry schema + types, `lead` / `leads` resolvers → use cases via context, mounted `/graphql`
- [x] 5.3 `infra/container.py`: `Container.from_settings` wires adapters; use-case provider methods; `tests/fakes/container.py` for API tests
- [x] 5.4 `infra/worker.py` + `app/worker.py`: `PipelineWorker.run_once`/`run_forever`, `LeadTaskHandler` protocol, bounded retry via `queue.fail(retry_in)`; standalone `python -m app.worker` with signal handling
- [x] 5.5 `app/main.py`: `create_app(container?, run_worker?)`, lifespan starts/stops the worker + closes the container, routers mounted, `infra/logging.py`
- [x] 5.6 `app/seed.py`: `seed_leads(submit, leads=SYNTHETIC_LEADS)` + 8 synthetic (fictitious) leads + `python -m app.seed`

## Phase 6: Frontend

- [x] 6.1 `apps/web`: Vite 6 + React 19 + TS + TanStack Query + `vite-plugin-pwa` (manifest + SW generated in `vite build`); vitest + Testing Library + MSW harness
- [x] 6.2 `packages/shared`: `openapi.json` from FastAPI → `openapi-typescript` (`pnpm gen`) → `src/api.d.ts`; `makeApiClient` wraps `openapi-fetch` (defers to live `globalThis.fetch`)
- [x] 6.3 `QueueView`: table rows (name, company, status, score band), `refetchInterval` 5s, empty state, row click → `onSelect`
- [x] 6.4 `LeadDetail`: score value+band+rationale, enrichment `<dl>`, reply draft, sync state + HubSpot link when `crm_contact_id`; "Pending enrichment" when unscored; "not found" on 404
- [x] 6.5 `AddLeadForm`: controlled form → `POST /leads` via `useCreateLead`; 201 → `onCreated(id)` + reset + queue invalidation; 422 → `role="alert"` error, fields kept

## Phase 7: Tests

- [x] 7.1 `tests/fakes/`: in-memory `InMemoryLeadRepository` / `FakeLLMProvider` / `FakeCrmGateway` / `InMemoryTaskQueue` + `RecordingSleep` + `make_fake_container` (built in Phase 3, `claim` attempt-increment aligned in Phase 5)
- [x] 7.2 Use-case unit tests: `test_submit_lead` (dedupe), `test_rest_api` (422×2), `test_enrich_lead` (retry/exhaustion), `test_gemini_adapter` (score-range→LLMResponseInvalid), `test_sync_lead_to_crm` (idempotent re-sync + failure isolation), `test_status`/`test_lead` (transition guard) + `test_architecture` (hexagonal boundary → ai-enrichment "provider abstraction")
- [x] 7.3 API integration: `test_rest_api` (8), `test_graphql_api` (3, REST↔GraphQL parity), `test_pipeline_e2e` (full flow), `test_app_lifespan` (worker start/stop)
- [x] 7.4 Postgres integration: `test_sql_lead_repository` (8), `test_postgres_task_queue` (7 incl. 8-way concurrent SKIP LOCKED + stale/restart reclaim), `test_migration_matches_models`, `test_db`
- [x] 7.5 Contract tests: `test_gemini_adapter` (10, seam-injected), `test_hubspot_adapter` (10, `respx`)
- [x] 7.6 Frontend (vitest + Testing Library + MSW): `QueueView` (render, status-refresh-without-reload, offline read of cached leads), `LeadDetail`, `AddLeadForm` (422→field error), `Dashboard`. `@vitest/coverage-v8` gate (lines/statements 85, branches 75)
- [x] 7.x Coverage gates: backend `pytest --cov-fail-under=90` (at 98%); `pragma: no cover` only on live-service CLI glue (`app/worker.py`, `seed._main`, `Container.from_settings`, `gemini_generate`)

## Phase 8: Deploy + docs

- [x] 8.1 `render.yaml`: free Docker web service (`dockerContext: ./services/api`), `healthCheckPath: /health`, `DATABASE_URL`/`GEMINI_API_KEY`/`HUBSPOT_PRIVATE_APP_TOKEN` as `sync: false`; `alembic upgrade head` runs in the Dockerfile CMD
- [x] 8.2 `apps/web/vercel.json`: framework vite, monorepo install/build from repo root, SPA rewrite; `VITE_API_URL` documented as a Vercel env var
- [x] 8.3 `.github/workflows/ci.yml` (backend: uv sync --frozen + ruff + ruff format + mypy + pytest; frontend: pnpm + typecheck + vitest --coverage + build; PG binaries on PATH for pytest-postgresql) + `keepalive.yml` (cron `*/10`, pings `vars.API_URL/health`)
- [x] 8.4 `README.md`: value proposition, "what this demonstrates" table mapped to the job, ports table with links to `docs/`, ASCII architecture diagram, local-dev + checks + deployment tables, synthetic-data notice, roadmap
- [x] 8.5 `docs/`: `vertex-ai-adapter.md`, `cloud-tasks-adapter.md`, `hubspot-oauth.md` — each a real migration note (what changes, what stays, keep-both-via-config)
- [x] 8.x `packages/shared/{openapi.json,src/api.d.ts}` regenerated + committed; `just openapi` recipe; `.gitignore` for dev-dist/coverage/.vercel; Dockerfile `uv sync --frozen`
