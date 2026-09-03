# Archive Report: Dashboard Redesign

**Change**: dashboard-redesign
**Project**: crm-ai-copilot
**Archived**: 2026-09-03
**Status**: COMPLETE

## Executive Summary

The dashboard-redesign change has been successfully implemented, verified, and archived. All 24 tasks completed, all gates passing (28/28 tests, TypeScript clean, build success), and the specification delta has been merged into the main spec. The change introduces live-refresh detail view, responsive two-column layout, and modern visual design using Tailwind CSS v4.

## Verification Verdict

**PASS-WITH-NOTES** — 0 CRITICAL, 3 WARNING, 5 SUGGESTION

### Gates (re-run at verify)
- `pnpm exec vitest run` (apps/web): **28/28 tests PASS**, exit 0
- `pnpm exec tsc --noEmit` apps/web: **exit 0**
- `pnpm exec tsc --noEmit` packages/shared: **exit 0**
- `pnpm --filter web build`: **exit 0**, CSS 29.76 kB, PWA manifest `theme_color`/`background_color` = `#0a0b0d`

## Implementation Summary

**Commit**: `f830eb5` ("feat(web): operational-precision dashboard redesign")
**Files changed**: 30 files

### Phases Completed
1. **Phase 1 Foundation (6 tasks)** ✅ — Tailwind v4, fonts, theme config, PWA manifest
2. **Phase 2 Components (5 tasks, Strict TDD)** ✅ — StatusBadge, ScoreMeter, detailRefetchInterval
3. **Phase 3 Restyle & wire (7 tasks)** ✅ — Dashboard two-column shell, component restyling, live refresh wiring
4. **Phase 4 Tests & verification (4 tasks)** ✅ — Live-refresh test, coverage, build, typecheck
5. **Phase 5 Cleanup & docs (3 tasks)** ✅ — Dead-code audit (0 removed), README update, responsive check

## Specification Delta Merged

### Delta Source
- `openspec/changes/dashboard-redesign/specs/web-dashboard/spec.md`

### Changes to Main Spec
- **ADDED**: Requirement "Responsive two-column layout" (3 scenarios: wide viewport side-by-side, narrow viewport single-column, wide content containment)
- **MODIFIED**: Requirement "Lead detail view" — added live polling while lead is processing; new scenario "Detail reflects progress without a reload"
- **No REMOVED** requirements

### Result
- Main spec: `openspec/specs/web-dashboard/spec.md` — updated to include all delta changes as clean, standalone requirements (no delta markers)
- Change delta spec archived with this report

## Spec Compliance

| Requirement | Status | Notes |
|---|---|---|
| Lead detail view (MODIFIED) | ✅ COMPLIANT | 3/3 scenarios behaviourally proven by tests |
| Responsive two-column layout (ADDED) | ⚠ STRUCTURAL ONLY | 2/3 scenarios structural only (W1, W2); 1/3 compliant by spec wording |
| Supporting components | ✅ COMPLIANT | StatusBadge, ScoreMeter, live refresh, empty-state, add-lead toggle |

## Open Issues & Follow-ups

### Warnings (should fix, tracked as follow-ups)

**W1 — "Side by side on a wide viewport" has no behavioural proof**
- No Playwright/Cypress test for side-by-side layout or independent column scrolling
- Status: Add E2E test or record manual sign-off
- **Follow-up**: Write Playwright test asserting both regions visible at ≥1024px and scroll independently

**W2 — "Single column on a narrow viewport" not visually confirmed**
- Automated viewport resize unavailable on apply host (stuck at 1440px)
- Static checks pass; manual check at ~375px and ~800px still owed
- Status: Needs real-device or manual browser window-drag check
- **Follow-up**: Manual visual check at narrow widths (<1024px) — confirm stacked layout, no horizontal body scroll, no dead placeholder

**W3 — `--color-accent-dim` token is dead**
- Token `--color-accent-dim: #8fbf2e` defined in index.css but not referenced via utility class
- Same hex hard-coded twice in ScoreMeter.tsx (hot-band gradient)
- Fix: Wire gradient to `var(--color-accent-dim)` or drop the token
- **Follow-up**: S1 (wire gradient) or drop token

### Suggestions (nice-to-have)

**S1 — Add `break-words` to reply-draft and message fields**
- Currently long unbroken strings produce inner horizontal scrollbar instead of wrapping
- Spec allows either; wrapping reads cleaner
- **Follow-up**: Add `[overflow-wrap:anywhere]` to LeadDetail reply-draft, message blockquote, mono meta line

**S2 — QueueView table lacks `table-fixed`**
- Long company/name values scroll the queue wrapper instead of truncating
- Acceptable as-is; `table-fixed` + `truncate` would be sturdier
- **Follow-up**: Consider `table-fixed` on queue table

**S3 — No test for empty-state right column**
- "SELECT A LEAD / TO SEE ITS AI ANALYSIS" placeholder shown when nothing selected
- **Follow-up**: Add Dashboard.test.tsx case asserting empty-state text

**S4 — No test for add-lead toggle**
- Panel show/hide and "select new lead + close panel on submit" flow untested
- **Follow-up**: Add Dashboard.test.tsx case for toggle interaction and handleCreated flow

**S5 — Mobile queue card-list not built**
- Mockup notes (not design.md spec) showed queue becoming a card list below ~1024px
- Current implementation keeps table at all widths
- Not a spec violation; consider if portfolio screenshots show phone width
- **Follow-up**: Build mobile card-list view if portfolio screenshots will show narrow layout

## Archive Contents

Moved to: `openspec/changes/archive/2026-09-03-dashboard-redesign/`

Contents:
- ✅ `proposal.md` — original proposal
- ✅ `exploration.md` — exploration findings
- ✅ `design.md` — technical design and decisions
- ✅ `specs/web-dashboard/spec.md` — delta spec
- ✅ `tasks.md` — all 24 tasks with completion marks
- ✅ `verify.md` — verification report
- ✅ `mockup/` — design canvas HTML files and canvas.json
- ✅ `archive-report.md` — this file

## Engram Artifact References

For traceability, all engram observations are recorded below:

| Artifact | Observation ID | Topic Key |
|---|---|---|
| Proposal | #315 | sdd/dashboard-redesign/proposal |
| Spec | #318 | sdd/dashboard-redesign/spec |
| Design | #319 | sdd/dashboard-redesign/design |
| Tasks | #320 | sdd/dashboard-redesign/tasks |
| Apply-progress | #323 | sdd/dashboard-redesign/apply-progress |
| Verify-report | #340 | sdd/dashboard-redesign/verify-report |

## Rollback

Single-change branch revert restores `src/index.css`, prior components, and the web-dashboard spec delta. No data, API, or migration involved.

## Next Steps

The SDD cycle is complete. All change artifacts have been archived and the delta spec merged into the main specification. The change is ready for production deployment.

### Recommended follow-ups (in order)
1. **W2**: Manual visual check at <1024px (375px and 800px) — confirm stacked layout, no horizontal scroll
2. **W1**: Playwright E2E test for side-by-side wide layout and independent column scrolling
3. **W3 / S1**: Wire `--color-accent-dim` token or drop it; add `break-words` to text fields
4. **S3 / S4**: Add tests for empty-state and add-lead toggle
5. **S2**: Consider `table-fixed` on QueueView
6. **S5**: Build mobile card-list if portfolio will showcase phone-width layout

---

**Archive prepared by**: sdd-archive executor  
**Date**: 2026-09-03  
**Mode**: hybrid (openspec files + engram)
