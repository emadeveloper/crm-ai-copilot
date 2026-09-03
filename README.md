# CRM AI Copilot

The tech glue between lead-capture forms and a CRM. Every inbound lead is enriched, scored and
given a drafted first reply by an LLM, then synced to HubSpot. A React PWA shows the queue,
scores and drafts.

> **Portfolio project.** Built to demonstrate one thing end to end: connecting AI models to a
> business system through robust REST + GraphQL APIs, with async processing and a real cloud
> deployment — at zero infrastructure cost.

## Value proposition

Inbound leads go cold fast. This service cuts time-to-first-touch to seconds: it qualifies each
lead, drafts a personalised opening message, and writes the result straight into the CRM where
the sales team already works — no new tool to learn.

## What this demonstrates

| Skill | Where |
| --- | --- |
| Robust REST **and** GraphQL over one core | `services/api/app/adapters/api/` — two inbound adapters, one use-case layer, no duplicated logic |
| AI integration in a production shape | `LLMProvider` port + `GeminiAIStudioAdapter` (structured JSON output, rate limiter, error translation) |
| Third-party system integration | `CrmGateway` port + `HubSpotPrivateAppAdapter` (contact search/upsert, notes, real OAuth-style token) |
| Async / automation | `TaskQueue` port + Postgres `FOR UPDATE SKIP LOCKED` queue + a worker with bounded retry and stale-lock reclaim |
| Cloud & migration thinking | every port ships a free adapter now and a documented GCP-native one (`docs/`) |
| Testing discipline | 196 backend tests @ 98% coverage (unit + real-Postgres integration + `respx` contract) · 11 frontend tests (Testing Library + MSW) · strict TDD throughout |

## Architecture

Hexagonal / ports & adapters. The domain and application layers import **no framework and no
vendor SDK** — enforced by an AST guard (`tests/test_architecture.py`). Swapping any adapter is
one module plus one line in the composition root.

```
            REST (FastAPI)   GraphQL (Strawberry)   POST /leads
                     \             |               /
                      \            |              /
                    ┌──────────────────────────────┐
                    │   application: use cases     │   SubmitLead · EnrichLead
                    │   domain: entities + ports   │   SyncLeadToCrm · Get/ListLeads
                    └──────────────────────────────┘
                     /       |          |         \
            LLMProvider   CrmGateway  TaskQueue  LeadRepository
                 |            |          |          |
          GeminiAIStudio   HubSpot   Postgres    Postgres
          [VertexAI: doc] [OAuth:doc][CloudTasks:doc]  (Neon)
```

| Port | Adapter now | Production adapter (design note) |
| --- | --- | --- |
| `LLMProvider` | Gemini API (AI Studio free tier) | Vertex AI — [`docs/vertex-ai-adapter.md`](docs/vertex-ai-adapter.md) |
| `CrmGateway` | HubSpot Private App token | HubSpot OAuth2 — [`docs/hubspot-oauth.md`](docs/hubspot-oauth.md) |
| `TaskQueue` | Postgres `SELECT … FOR UPDATE SKIP LOCKED` | Google Cloud Tasks — [`docs/cloud-tasks-adapter.md`](docs/cloud-tasks-adapter.md) |
| `LeadRepository` | Postgres (Neon) | — |

```
services/api      FastAPI + Strawberry, hexagonal layers, in-process pipeline worker
apps/web          React 19 + Vite installable PWA dashboard, Tailwind CSS v4 (@theme tokens)
packages/shared   TypeScript API client generated from the API's OpenAPI schema (no drift)
```

Pipeline: `POST /leads` → `received` → `enriching` → `qualified` → `syncing` → `synced` (or
`failed`, retryable). Submission is non-blocking — the worker drains the queue.

### Dashboard UI

The dashboard follows an "operational precision" visual direction — near-black surfaces, one
electric-lime accent, IBM Plex Mono for numbers, labels and status tags. Styling is **Tailwind
CSS v4** via the `@tailwindcss/vite` plugin: design tokens live in a `@theme` block in
`apps/web/src/index.css`, and Hanken Grotesk + IBM Plex Mono are self-hosted through `@fontsource`.
Approved design canvas: <https://claude.ai/code/artifact/3cb26483-544e-4283-9e83-8f60089041f7>

## Data & privacy notice

The Gemini **free tier may use prompts for model training**. The deployed demo runs on
**synthetic leads only** (`just seed` — all `@example.com` / `@example.org`). Do not send real
personal data to the free-tier deployment. Vertex AI does not train on prompts; see the migration
note.

## Local development

Prerequisites: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 22 + pnpm, a local Postgres
(or a Neon URL), [just](https://github.com/casey/just).

```bash
cp env.example services/api/.env      # then fill in GEMINI_API_KEY + HUBSPOT_PRIVATE_APP_TOKEN
just install                          # uv sync + pnpm install
just migrate                          # alembic upgrade head
just seed                             # load synthetic leads
just dev-api                          # http://localhost:8000  — /docs, /graphql
just dev-web                          # http://localhost:5173
```

The API starts the pipeline worker in-process. To run it as its own process:
`just worker` (or `python -m app.worker`).

### Checks

```bash
just lint            # ruff + ruff format --check + mypy (strict)
just test            # pytest with a 90% coverage gate
pnpm --filter web exec vitest run --coverage
```

## Deployment

| Piece | Host | Notes |
| --- | --- | --- |
| API + worker | **Render** free web service (Docker) | `render.yaml` blueprint; `alembic upgrade head` runs on boot; `healthCheckPath: /health`. `HUBSPOT_PRIVATE_APP_TOKEN` is optional — leave it unset and CRM sync is disabled (no SYNC tasks are enqueued) |
| Database | **Neon** serverless Postgres | scales to zero, no 30-day expiry; set `DATABASE_URL` to the pooled `postgresql+asyncpg://…` URL |
| Web | **Vercel** | `apps/web/vercel.json`; set `VITE_API_URL` to the Render URL |
| CI | **GitHub Actions** | `.github/workflows/ci.yml` — backend lint/types/tests, frontend types/tests/build |
| Keep-alive | **GitHub Actions** cron | `.github/workflows/keepalive.yml` pings `/health` every 10 min; set repo variable `API_URL` |

Render's free tier cold-starts in ~30–60s after 15 min idle — the keep-alive workflow hides that.

## Roadmap

1. **MVP (this repo)** — domain, REST, thin GraphQL slice, Gemini + HubSpot adapters, Postgres
   queue + worker, PWA dashboard, live deploy. ✅
2. **Full contract** — complete GraphQL schema + mutations, HubSpot inbound webhooks, PWA polish,
   Playwright E2E.
3. **Cloud story** — `VertexAIAdapter`, `CloudTasksAdapter`, HubSpot OAuth, Cloud Run manifests
   (design notes already in [`docs/`](docs/)).

The full spec-driven design trail — proposal, specs, design, tasks — is in
[`openspec/changes/crm-ai-copilot/`](openspec/changes/crm-ai-copilot/).
