# Proposal: Dashboard redesign — "operational precision"

## Intent

The MVP dashboard is functionally complete but visually plain (117 lines of hand-CSS, a bare
`<table>`, stacked sections). For a portfolio piece the interface is a first-class deliverable —
a recruiter judges it in seconds. This change gives it a distinctive, production-grade look and
fixes one UX gap (the open detail panel does not refresh live).

## Scope

### In Scope
- **Design mockup** via the `/design` skill — layout, type scale, status tags, score meter,
  colour system — approved before any component is built.
- **Tailwind CSS v4** (`@tailwindcss/vite`, CSS-first `@theme`, no config file); remove
  `src/index.css` hand-CSS.
- **Two self-hosted fonts** (`@fontsource`): one characterful mono for numbers/labels, one clean
  grotesk for prose. Not Inter/Roboto/Space Grotesk.
- **Two-column layout** (`Dashboard.tsx`): scrollable lead queue left, sticky lead detail right;
  single column below a breakpoint. Header with the value-prop line.
- **`StatusBadge`** — sharp typographic tag per status (`received`/`enriching`/`qualified`/
  `syncing`/`synced`/`failed`), one colour each.
- **`ScoreMeter`** — horizontal 0–100 bar with band label and colour.
- Restyle `QueueView` (rows keep `<table>`/`<tr>`), `LeadDetail` (visual hierarchy, meter,
  badges), `AddLeadForm` (inputs; `<label>` associations kept).
- **`useLead` live refresh**: `refetchInterval` while `status` ∉ {`synced`,`failed`}.
- Update PWA `manifest` `theme_color`/`background_color` + `index.html` theme-color meta.
- All 11 existing frontend tests stay green; add tests for `StatusBadge`, `ScoreMeter`, and the
  detail-view live refresh.

### Out of Scope
- Filtering, sorting, search, pagination controls.
- Charts / analytics / a metrics header.
- A "re-trigger failed lead" action.
- Backend changes; the `crm-ai-copilot` GraphQL/REST surface is untouched.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `web-dashboard`: (1) the **lead detail view** MUST reflect a lead's status/score changes
  without a manual reload while the lead is still being processed; (2) the dashboard MUST render
  a two-column layout on wide viewports and a single column on narrow ones.

## Approach

Tailwind v4 utility classes + ~4 hand-built components (no component library — shadcn's default
look is the generic aesthetic to avoid; Radix is unnecessary since the detail is an inline
region, not a modal). Aesthetic: near-black ground with grain texture, one electric accent,
mono/grotesk pairing, typographic status tags, a score meter, one staggered load-in. Components
keep their current markup semantics (roles, `<label>` associations, `<tr>` rows) so the test
suite is unaffected by styling.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/index.css` | Removed | replaced by Tailwind `@theme` + a small base layer |
| `apps/web/src/Dashboard.tsx` | Modified | two-column responsive shell, header |
| `apps/web/src/features/leads/{QueueView,LeadDetail,AddLeadForm}.tsx` | Modified | restyle only |
| `apps/web/src/features/leads/hooks.ts` | Modified | `useLead` conditional `refetchInterval` |
| `apps/web/src/components/` | New | `StatusBadge`, `ScoreMeter` (+ tests) |
| `apps/web/{package.json,vite.config.ts,index.html}` | Modified | Tailwind v4, fonts, PWA colours |
| `openspec/specs/web-dashboard/spec.md` | Modified | delta: detail live-refresh + responsive layout |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `@tailwindcss/vite` conflicts with VitePWA | Low | `vitest` has `css:false`; verify `vite build` + dev on first apply |
| A restyle breaks a test selector | Low | Strict TDD safety-net run per component before editing; markup semantics preserved |
| Fonts bloat the bundle | Low | 2 faces max, woff2, `font-display: swap` |
| Scope creep into filters/charts | Med | explicit out-of-scope list; proposal-gated |

## Rollback Plan

Single-change branch. Revert the branch to restore `src/index.css` and the current components;
no data, no API, no migration involved. `openspec/specs/web-dashboard/spec.md` delta is reverted
with it.

## Dependencies

- `tailwindcss` v4 + `@tailwindcss/vite`; `@fontsource/*` for two faces. All dev-time, npm.
- The `/design` skill for the mockup (produces an Artifact).

## Success Criteria

- [ ] `/design` mockup approved by the user before build.
- [ ] `pnpm --filter web build` and `vitest run --coverage` pass; all 11 prior tests + new ones green.
- [ ] Two-column on desktop, single-column on mobile; no horizontal body scroll.
- [ ] Status shown as a coloured tag; score as a meter; both in queue and detail.
- [ ] Opening a lead in `enriching` shows it flip to `qualified` with a score, no manual reload.
- [ ] No Inter/Roboto/Space Grotesk; PWA install splash uses the new palette.
