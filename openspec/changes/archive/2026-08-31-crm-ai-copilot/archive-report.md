# Archive Report — crm-ai-copilot

**Archived:** 2026-08-31
**Archived to:** `openspec/changes/archive/2026-08-31-crm-ai-copilot/`
**Verify verdict:** PASS WITH WARNINGS (0 CRITICAL) — see `verify-report.md`

---

## Specs synced to source of truth

All five were **new capabilities** (no pre-existing main spec) — copied in full to `openspec/specs/`.

| Domain | Action | Requirements |
|--------|--------|--------------|
| `lead-api` | Created | 3 (Lead submission over REST · Lead retrieval over REST · Lead retrieval over GraphQL) |
| `ai-enrichment` | Created | 3 (Enrichment/score/draft generation · Provider abstraction · Rate-limit & transient-failure handling) |
| `crm-sync` | Created | 3 (Contact upsert with note · Idempotent re-sync · Sync failure isolation) |
| `lead-pipeline` | Created | 3 (Status lifecycle · Non-blocking submission · Retry, throttle and durability) |
| `web-dashboard` | Created | 4 (Lead queue view · Lead detail view · Manual lead creation · Installable and offline-tolerant) |

`openspec/specs/` is now the source of truth for CRM AI Copilot behaviour.

## Archive contents

- `proposal.md` ✅
- `exploration.md` ✅
- `design.md` ✅
- `specs/` (5 delta/full specs) ✅
- `tasks.md` ✅ — 42/42 task lines complete
- `verify-report.md` ✅
- `archive-report.md` ✅ (this file)

## Engram artifact trail

| Artifact | topic_key | obs id |
|----------|-----------|--------|
| Exploration | `sdd/crm-ai-copilot/explore` | 297 |
| Proposal | `sdd/crm-ai-copilot/proposal` | 298 |
| Spec (concatenated) | `sdd/crm-ai-copilot/spec` | 299 |
| Design | `sdd/crm-ai-copilot/design` | 300 |
| Tasks | `sdd/crm-ai-copilot/tasks` | 301 |
| Apply progress | `sdd/crm-ai-copilot/apply-progress` | 302 |
| Verify report | `sdd/crm-ai-copilot/verify-report` | 307 |
| Project context (SDD init) | `sdd-init/fullstack-ia-python-project` | 294 |
| Testing capabilities | `sdd/fullstack-ia-python-project/testing-capabilities` | 295 |

Supporting decision/discovery memories: #303 domain design decisions, #304 design deviations,
#305 Postgres queue pattern, #306 frontend test gotchas.

## Final state

- **Backend:** 196 tests, 98.22% coverage, ruff + ruff format + mypy(strict) clean.
- **Frontend:** 11 tests, 99% statements, tsc clean, `vite build` emits PWA SW + manifest.
- **Deploy:** `render.yaml`, `apps/web/vercel.json`, `.github/workflows/{ci,keepalive}.yml`, `README.md`, `docs/` migration notes — all in place, not yet provisioned.
- **git:** initialised, branch `main`, nothing committed yet.

## Carried forward (not blocking — from the verify WARNINGs)

1. `lead-pipeline / Response does not wait on the pipeline` — add a slow-fake-provider test asserting the POST returns first.
2. `lead-pipeline / Throttling under burst` — add a runtime test that paces N > budget calls through the limiter.
3. `web-dashboard / Manual add succeeds` — add a Dashboard test asserting the new row renders in the queue after submit.
4. Phase-8 live smoke against real Gemini + HubSpot (closes the 4 `# pragma: no cover` glue spots).

## SDD cycle complete

Planned → specced → designed → tasked → implemented (8 phases, Strict TDD) → verified → archived.
`openspec/changes/` has no active changes. Ready for the next one.
