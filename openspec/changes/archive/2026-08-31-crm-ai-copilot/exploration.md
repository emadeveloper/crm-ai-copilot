# Exploration: CRM AI Copilot

**Date:** 2026-08-30
**Change:** crm-ai-copilot
**Artifact store:** hybrid (engram + this file)

## Current State

Greenfield. Empty directory, not yet a git repo, zero code. SDD context initialized
(`openspec/config.yaml`, `.atl/skill-registry.md`, engram `sdd-init/fullstack-ia-python-project`).
Nothing to refactor — this exploration is about **external constraints** and **architecture shape**,
not existing code.

Goal: a portfolio project that demonstrates, 1:1 against a job posting, the ability to be "the tech
glue" between AI models (Gemini/Vertex) and third-party business systems (CRM) via robust REST +
GraphQL APIs, deployed as if production, with a value-proposition pitch for the employer.

## Affected Areas (to be created)

- `services/api/` — Python 3.12 / FastAPI backend, hexagonal layering (domain / application / adapters / infra)
- `apps/web/` — React + Vite + TypeScript dashboard, installable PWA
- `packages/shared/` — TS types generated from the API's OpenAPI schema
- `openspec/specs/` — capability specs, written next phase
- root — `render.yaml`, `Dockerfile`, `.github/workflows/`, `justfile`/`Makefile`, `pnpm-workspace.yaml`, `pyproject.toml` (uv)

## External Constraints (researched 2026-08-30)

### Gemini API — AI Studio free tier
- Real free tier, **no credit card, no expiration**. Prompts on the free tier **may be used for
  Google model training** (paid tier and Vertex AI do not) → **demo must use synthetic data only,
  no real PII**.
- **Flash-class only**: Gemini 2.5 Flash / Flash-Lite / 3.x Flash-class. **Pro models are paid-only
  since April 2026** — do not design around Pro.
- Limits: ~**15 RPM / 1,500 RPD / 1M TPM** per project for Flash models.
- SDK: `google-genai` (the unified Gen AI SDK). Same SDK targets Vertex AI by flipping a
  client option (`vertexai=True` + project/location) → the `LLMProvider` port stays identical,
  the adapter swap is nearly config-only.

### HubSpot — free CRM + API
- API works on the **free CRM plan**, no paid subscription, no per-call charge.
- **Private App access token**: single static bearer token scoped per account. Simplest path for a
  single demo account you own. Limits: **100 requests / 10 s**, **250,000 / day**.
  **Search endpoints are stricter: 4 requests / second.**
- **OAuth2**: required only for a multi-tenant "install into your own HubSpot" flow.
- Objects available: contacts, companies, deals, **notes** (engagements) — read + write.

### Render — free tier
- Free web service: 512 MB RAM, 0.1 CPU, **spins down after 15 min idle**, cold start **30–60 s**.
  750 instance-hours/month (enough for one always-on service if kept warm).
- **Free Postgres expires 30 days after creation** (+14-day grace) then data is deleted.
  → **Not usable** for a project that must stay live for months of job-hunting.

### Postgres host — pick Neon, not Render
- **Neon free tier**: 0.5 GB storage, scale-to-zero when idle, **no expiration**, 100 projects.
  Best fit for an intermittently-used portfolio DB.
- Supabase free tier **pauses the project after 1 week idle** (needs manual unpause) — worse for
  a demo a recruiter might open weeks later.

## Approaches

### 1. LLM provider: port + adapter, Gemini AI Studio now — RECOMMENDED
- **Pros:** domain has zero vendor imports; `google-genai` SDK makes the Vertex swap almost
  config-only; strong "swap infrastructure without touching business logic" story; free.
- **Cons:** Flash-class only (fine for scoring/summary/reply drafting); free-tier training clause
  forces synthetic-data-only demo.
- **Effort:** Low–Medium.

### 2. CRM auth: Private App token now, OAuth2 documented — RECOMMENDED
- **Pros:** real third-party API integration with minimal ceremony on a demo account you own;
  mirrors the LLM decision (ship pragmatic adapter, document the production one); `CrmGateway`
  port hides the choice.
- **Cons:** single-tenant; OAuth (the stronger multi-tenant signal) is deferred to a later adapter.
- **Effort:** Low for the token adapter; Medium if OAuth is pulled into phase 1.
- Alt: OAuth2 from the start — Higher effort, better multi-tenant signal, risks eating time from
  the AI core.

### 3. REST + GraphQL: one use-case layer, two inbound adapters — RECOMMENDED
- FastAPI routers for REST (+ OpenAPI → generated TS client), Strawberry for GraphQL.
- **Pros:** both are posting requirements; no duplicated logic (inbound adapters call the same
  application services); GraphQL genuinely helps the dashboard (lead + score + drafts in one query).
- **Cons:** two API surfaces to test and document.
- **Effort:** Medium. A thin GraphQL slice ships in phase 1 to prove the pattern; full schema in phase 2.

### 4. Async enrichment: `TaskQueue` port, Postgres-backed queue now, Cloud Tasks documented — RECOMMENDED
- Enrichment = LLM call + CRM writes = seconds per lead. Must be off the request path.
- Phase-1 adapter: a `tasks`/outbox table in Postgres drained by an in-process asyncio worker.
  Survives restarts, retryable, **zero extra infra**, good architecture talking point.
- Documented production adapter: **Google Cloud Tasks / Pub/Sub**.
- Alt: FastAPI `BackgroundTasks` — Lower effort but no retry, lost on restart/redeploy, weak signal.
- **Effort:** Medium.

### 5. Monorepo: pnpm workspace (JS) + uv (Python), `justfile` at root — RECOMMENDED
- `services/api` (uv), `apps/web` + `packages/shared` (pnpm workspace), `justfile` orchestrates.
- Turborepo optional — nice signal, low cost, can add later.
- **Effort:** Low–Medium.

### 6. Deploy: Render (API, Docker) + Neon (Postgres) + Vercel (web) — RECOMMENDED
- `render.yaml` blueprint committed. GitHub Actions: lint + typecheck + test on PR; deploy hook on main.
- Keep-alive: GitHub Actions scheduled ping every ~10 min to defeat the 15-min spin-down (stays
  under 750 hrs/month).
- **Effort:** Medium.

## Recommendation

Build it as **three ports the domain depends on — `LLMProvider`, `CrmGateway`, `TaskQueue`** (plus
`LeadRepository`) — and for each one ship the pragmatic free adapter now while documenting the
GCP-native production adapter. That single consistent decision *is* the seniority narrative the
posting is asking for, and it keeps cost at zero.

Phase the work:
1. **MVP** — domain + application layer + REST + `GeminiAIStudioAdapter` + `HubSpotPrivateAppAdapter`
   + `PostgresLeadRepository` (Neon) + minimal web view + thin GraphQL slice. Deployed live.
2. **Full contract** — full GraphQL schema, ingestion webhook, Postgres-backed `TaskQueue` + worker,
   PWA polish, green CI, meaningful test coverage.
3. **Cloud story** — `VertexAIAdapter` + `CloudTasksAdapter` + HubSpot OAuth adapter documented/stubbed,
   `Dockerfile` + Cloud Run manifests, scaling diagram, value-prop README with demo metrics.

## Risks

- **Gemini free tier trains on prompts** → the deployed demo MUST use synthetic leads only; state this
  explicitly in the README and seed script. Real PII would be a genuine mistake here.
- **Gemini 15 RPM** → bulk re-scoring from the dashboard will hit the limit; the adapter needs an
  internal rate limiter + exponential backoff, and the queue must throttle.
- **HubSpot search = 4 req/s** → never build polling loops that call search; store HubSpot object IDs
  locally and prefer webhooks.
- **Render cold start 30–60 s** → a recruiter's first click is slow without the keep-alive ping.
- **Render free Postgres 30-day expiry** → avoided by using Neon; don't let a tutorial talk you back
  onto Render Postgres.
- **Scope vs. learning Python** → the phasing is the mitigation; phase 1 must be genuinely shippable
  on its own.

## Ready for Proposal

**Yes.** Tell the user: constraints are researched and the architecture shape is clear (four ports,
pragmatic-now / GCP-documented adapters, three phases). The proposal phase should lock: phase-1
scope boundary, whether the thin GraphQL slice is in or fully deferred, HubSpot auth choice
(Private App vs OAuth) for phase 1, and the exact domain model (Lead / Enrichment / Score /
ReplyDraft / SyncState).

## Sources

- https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier
- https://yingtu.ai/en/blog/gemini-api-free-tier
- https://pricepertoken.com/endpoints/google-ai-studio/free
- https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines
- https://www.scopiousdigital.com/blog/hubspot-api-rate-limits-production
- https://pipewave.de/en/blog/hubspot-free-crm-api-integrations
- https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026
- https://unanswered.io/guide/render-free-tier-details
- https://agentdeals.dev/neon-vs-supabase
- https://perkstack.co/blog/free-postgres-hosting
