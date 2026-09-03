# Exploration: dashboard-redesign

**Date:** 2026-09-02
**Change:** dashboard-redesign
**Artifact store:** hybrid (engram + this file)

## Current State

`apps/web` is a React 19 + Vite 6 + TanStack Query PWA. Styling is **117 lines of hand-written
CSS** in `src/index.css` (dark theme, one cyan accent, plain `<table>`, stacked `<section>`s).
Three feature components + a shell:

| File | Role | Current look |
|------|------|-------------|
| `Dashboard.tsx` | shell: stacked add-form → queue → detail (mounted below on select) | vertical stack, `<main>` max-width 900px |
| `features/leads/QueueView.tsx` | `<table>` of leads (name, company, status, score band) | bare table, status/band as plain text |
| `features/leads/LeadDetail.tsx` | `<article>` with score, enrichment `<dl>`, reply draft, sync footer | headings + `<dl>`, no visual hierarchy |
| `features/leads/AddLeadForm.tsx` | controlled form | `display:grid`, 460px |
| `features/leads/hooks.ts` | `useLeads` (5s poll), `useLead` (**no poll**), `useCreateLead` | — |

No design system, no component library, no fonts loaded (system stack).

## Affected Areas

- `apps/web/src/index.css` — replaced by a token-driven system (or Tailwind layer)
- `apps/web/src/Dashboard.tsx` — new two-column layout + header
- `apps/web/src/features/leads/QueueView.tsx` — restyled rows; **must stay `<table>`/`<tr>`**
- `apps/web/src/features/leads/LeadDetail.tsx` — visual hierarchy, score meter, badges
- `apps/web/src/features/leads/AddLeadForm.tsx` — restyled inputs; **must keep `<label>` assoc**
- `apps/web/src/features/leads/hooks.ts` — `useLead` gains `refetchInterval` while non-terminal
- `apps/web/package.json` — Tailwind v4 + font packages
- `apps/web/vite.config.ts` — `@tailwindcss/vite` plugin; PWA `theme_color` to match new palette
- `apps/web/index.html` — font preconnect / `<link>` if using a CDN
- New: `src/components/` — `StatusBadge`, `ScoreMeter`, small primitives

## Test-suite coupling (must preserve — Strict TDD safety net)

`vitest.config.ts` has `css: false`, so Tailwind/CSS never runs in tests — styling changes are
invisible to the suite. What the 11 tests DO assert (from `QueueView/LeadDetail/AddLeadForm/Dashboard.test.tsx`):

- Queue rows are `<tr>` reachable via `.closest("tr")`; row `toHaveTextContent` for company / status / band
- `Dashboard` detail region has `aria-label="lead detail"` (`getByRole("region")`)
- Form fields reachable via `getByLabelText(/name|email|company/i)`; button `name: /add lead/i`
- Errors are `role="alert"`; HubSpot link is `role="link"` with a real `href`
- Text tokens present verbatim: score value, band, rationale, `"Thanks for reaching out"`, `"fintech"`, `/pending enrichment/i`, `/not found/i`

→ Redesign is **markup-semantics-preserving styling** + one hook tweak. Low risk to the suite;
each touched component's tests get a safety-net run first (Strict TDD).

## Approaches

### 1. Tailwind CSS v4 + hand-built components — RECOMMENDED
- Tailwind v4's `@tailwindcss/vite` plugin: CSS-first (`@theme` in one CSS file), no
  `tailwind.config.js`, tiny output, fast. Build ~6 small components with utilities.
- **Pros:** modern-stack signal; full control over a *distinctive* look (not the generic
  shadcn dashboard everyone ships); minimal bundle; no component-lib lock-in; matches the
  frontend-design brief (execute one bold, intentional vision).
- **Cons:** ~6 components to hand-write (StatusBadge, ScoreMeter, layout, rows).
- **Effort:** Medium.

### 2. shadcn/ui (Radix + Tailwind)
- Copy in Card / Badge / Table / Sheet / Button.
- **Pros:** accessible primitives, fast assembly.
- **Cons:** shadcn's default aesthetic *is* the "AI slop" look to avoid — every portfolio
  dashboard looks identical; adds Radix deps; the design phase already rejected shadcn; weaker
  "I designed this" story.
- **Effort:** Medium (setup + heavy re-theming to not look default).

### 3. Refined hand-CSS only (expand `index.css`)
- Grow the 117 lines into a real token system + layout grid + badge/meter styles.
- **Pros:** zero new deps, smallest diff.
- **Cons:** hand-CSS at dashboard scale gets unwieldy; slow to iterate; weakest stack signal.
- **Effort:** Medium.

## Recommendation

**Approach 1 — Tailwind v4 + hand-built components.** Best "modern + intentional" balance for a
portfolio piece, tiny footprint, and it lets us commit to a real aesthetic direction instead of
a template. Radix/shadcn not needed: the detail view is an inline `region`, not a modal.

**Aesthetic direction to lock in the proposal:** *operational precision* — a lead-triage tool
that reads like Linear × a trading terminal. Near-black ground with grain/noise for depth; one
electric accent; a characterful mono for numbers/labels + a clean grotesk for prose. Score as a
horizontal **meter** with the band; status as sharp **typographic tags** (uppercase, tracked,
hairline border) — not soft pills. **Two-column layout**: scrollable queue left, sticky detail
right. One orchestrated staggered fade-in on load. B2B-appropriate: precise, not childish, not
luxury-brand.

**Fonts (self-hosted via `@fontsource`, keeps PWA offline-clean):** decide exact pairing in
`sdd-design`. Candidates — body: Geist / Hanken Grotesk / Instrument Sans; numeric+labels:
Geist Mono / JetBrains Mono / Spline Sans Mono. Not Inter/Roboto; not Space Grotesk.

**Bundle a small functional fix:** `useLead` gets `refetchInterval` while `status` ∉
{`synced`,`failed`} so the open detail panel updates live (spec `web-dashboard` → "Status
updates without reload" currently only covers the queue).

**Visual mock first:** run the `/design` skill in the design phase to produce a canvas mockup
(layout, badges, meter, type scale) the user approves *before* any component is built.

## Risks

- `@tailwindcss/vite` must coexist with the current `vite.config.ts` (VitePWA) and
  `vitest.config.ts` (`css:false` already isolates tests). Low, but verify on first apply.
- Every restyled component must keep its markup semantics (table rows, label assoc, aria-labels,
  roles) — enforced by the existing tests + a safety-net run per file.
- `@fontsource` adds a few dev deps + a bit of bundle (~30–60KB woff2 per face) — pick 2 faces
  max, `font-display: swap`.
- Scope creep: filters, sorting, charts, a "re-trigger failed lead" action are **out** — later.
- PWA `manifest` `theme_color` / `background_color` and `index.html` `<meta name=theme-color>`
  must be updated to the new palette or the install splash clashes.

## Ready for Proposal

**Yes.** Tell the user: current frontend is 4 small components + 117 lines of CSS; redesign is
styling + layout + one hook tweak, low-risk against the 11 tests. Proposal should lock: (a) the
aesthetic direction above, (b) Tailwind v4 hand-built (not shadcn), (c) two-column layout, (d)
the `useLead` live-refresh fix in scope, (e) `/design` mockup before build, (f) explicit
out-of-scope list.
