# Proposal: CRM AI Copilot — MVP (Phase 1)

## Intent

Build a live, portfolio-grade service that acts as "the tech glue" between lead-capture forms and a
CRM: on each inbound lead it runs AI enrichment + scoring + first-reply drafting, then syncs the
result to HubSpot. Demonstrates, 1:1 against the target job posting, REST + GraphQL API design, AI
integration, third-party CRM integration, async processing, and cloud deployment — at zero cost.

## Scope

### In Scope (Phase 1 MVP)
- Hexagonal Python/FastAPI backend: domain + application layers with four ports.
- `LLMProvider` port + `GeminiAIStudioAdapter` (Flash model, internal rate limiter + backoff).
- `CrmGateway` port + `HubSpotPrivateAppAdapter` (upsert contact + attach note with score/draft).
- `TaskQueue` port + Postgres-backed queue + in-process async worker running intake→enrich→sync.
- `LeadRepository` port + Postgres adapter (Neon).
- REST write + read endpoints, plus a thin GraphQL slice (`lead`, `leads` queries) over shared services.
- React + Vite installable PWA: lead queue, lead detail (enrichment/score/draft), manual add-lead form.
- Synthetic-data seed script. Deploy: Render (API) + Neon (DB) + Vercel (web) + GitHub Actions CI + keep-alive ping.

### Out of Scope (deferred to later changes)
- Full GraphQL schema (mutations, filtering, subscriptions).
- HubSpot OAuth2 + inbound webhooks from HubSpot; multi-tenant / user auth.
- `VertexAIAdapter`, `CloudTasksAdapter` (documented as stubs only).
- Native mobile app; analytics dashboards.

## Capabilities

### New Capabilities
- `lead-api`: accept inbound leads (REST `POST /leads`) and expose read access over REST + a thin GraphQL query slice.
- `ai-enrichment`: via `LLMProvider`, produce `Enrichment`, `Score` (0–100 + band + rationale), and `ReplyDraft` for a lead.
- `crm-sync`: via `CrmGateway`, upsert the lead as a HubSpot contact and attach a note carrying score + reply draft; track `SyncState`.
- `lead-pipeline`: `TaskQueue` port + worker orchestrating `received → enriching → qualified → syncing → synced` (and `failed`), with retry + throttle.
- `web-dashboard`: React PWA listing the lead queue and showing per-lead enrichment, score, and draft.

### Modified Capabilities
- None (greenfield).

## Approach

One application/use-case layer; REST and GraphQL are two inbound adapters over it (no duplicated
logic). The domain imports no framework or vendor SDK. For every port, ship the free adapter now and
document the GCP-native production adapter — that consistent decision is the seniority narrative.
Domain model: `Lead`, `Enrichment`, `Score`, `ReplyDraft`, `SyncState`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `services/api/` | New | FastAPI app, domain/application/adapters/infra layers, Alembic migrations |
| `apps/web/` | New | React + Vite PWA dashboard |
| `packages/shared/` | New | TS types generated from OpenAPI |
| root | New | `render.yaml`, `Dockerfile`, `.github/workflows/`, `justfile`, workspace configs |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Gemini free tier trains on prompts | High | Synthetic data only in the deployed demo; stated in README + seed script |
| Gemini 15 RPM throttling | Med | Rate limiter + exponential backoff in the adapter; queue throttles |
| HubSpot search 4 req/s | Med | Store HubSpot IDs locally; no polling loops on search |
| Render cold start 30–60 s | Med | GitHub Actions keep-alive ping every ~10 min |
| Scope vs. learning Python | Med | Phase 1 is independently shippable; phases 2–3 are separate changes |

## Rollback Plan

Greenfield — no existing behavior to restore. Rollback = revert the branch / delete the change
folder. Infra rollback: delete the Render service, Neon project, and Vercel project (no shared
resources, no data migration).

## Dependencies

- Google AI Studio API key (free, no card).
- HubSpot free account + Private App token.
- Neon, Render, Vercel free accounts; GitHub repo.

## Success Criteria

- [ ] Posting a synthetic lead to `POST /leads` results, within one worker cycle, in a HubSpot contact with an attached note containing score + reply draft.
- [ ] The same lead is retrievable via both a REST endpoint and the GraphQL `lead` query.
- [ ] The deployed dashboard (public URL) lists the lead and shows its enrichment, score, and draft.
- [ ] CI runs lint + type check + tests green on every PR.
- [ ] README states the value proposition and the pragmatic-now / GCP-documented adapter strategy.
