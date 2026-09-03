# Tasks: Dashboard redesign — "operational precision"

## Phase 1: Foundation

- [x] 1.1 `apps/web/package.json`: add `tailwindcss` + `@tailwindcss/vite`, `@fontsource-variable/hanken-grotesk`, `@fontsource/ibm-plex-mono`; `pnpm install`
- [x] 1.2 `apps/web/vite.config.ts`: add `tailwindcss()` to `plugins`; set PWA `manifest.theme_color` + `background_color` to `#0a0b0d`
- [x] 1.3 `apps/web/src/index.css`: replace with `@import "tailwindcss"` + `@theme` tokens (surfaces, text, dim, `--color-accent: #c9f24a`, status + band hues, `--font-sans`, `--font-mono`) + `@layer base` (body bg/color/font, grain `::before` feTurbulence data-URI, `@keyframes rise`, `prefers-reduced-motion` guard)
- [x] 1.4 `apps/web/src/main.tsx`: `import "@fontsource-variable/hanken-grotesk"` + `import "@fontsource/ibm-plex-mono"`
- [x] 1.5 `apps/web/index.html`: `<meta name="theme-color">` → `#0a0b0d`
- [x] 1.6 Verify: `pnpm --filter web build` + `pnpm --filter web exec vitest run` + `tsc --noEmit` all green (baseline before restyle)

## Phase 2: Components (Strict TDD)

- [x] 2.1 RED `src/components/StatusBadge.test.tsx`: renders the status text verbatim for each of the 6 statuses; carries `data-status={status}`
- [x] 2.2 GREEN `src/components/StatusBadge.tsx`: `<span>` per design (mono, uppercase, dot, hue-by-status via a lookup); export
- [x] 2.3 RED `src/components/ScoreMeter.test.tsx`: renders `value` and `band` text; has `role="meter"` with `aria-valuenow={value}`, `aria-valuemin=0`, `aria-valuemax=100`; bar width reflects value
- [x] 2.4 GREEN `src/components/ScoreMeter.tsx`: number + `/100` + band tag + track/fill bar (band-coloured); `size?: "sm" | "lg"` variant
- [x] 2.5 RED+GREEN `src/features/leads/hooks.ts`: add + test `detailRefetchInterval(status?: string)` → `false` for `synced`/`failed`, else `3000`

## Phase 3: Restyle & wire

- [x] 3.1 Safety-net: run each of `QueueView/LeadDetail/AddLeadForm/Dashboard.test.tsx` — capture green baseline
- [x] 3.2 `src/Dashboard.tsx`: two-column CSS-grid shell (`lg:` side-by-side, stacked below), header with mark + tagline + `+ Add lead` toggle + worker-live dot; right column always present (empty prompt), `<section aria-label="lead detail">` still conditional on selection; add-lead as a toggled dropdown panel
- [x] 3.3 `src/features/leads/QueueView.tsx`: restyle table (mono headers, `StatusBadge` in status cell, `ScoreMeter size="sm"` in score cell), selected-row + hover styling, staggered `rise` on rows; keep `<table>`/`<tr>` and all text tokens
- [x] 3.4 `src/features/leads/LeadDetail.tsx`: restyle to the mockup (header + `StatusBadge`, `ScoreMeter size="lg"`, enrichment grid + intent chips, reply-draft panel, sync footer + HubSpot link); keep roles/link/text tokens
- [x] 3.5 `src/features/leads/AddLeadForm.tsx`: restyle inputs/labels/buttons (mono labels, focus ring); keep `<label>` associations + button name
- [x] 3.6 `src/features/leads/hooks.ts`: `useLead` uses `refetchInterval: (q) => detailRefetchInterval(q.state.data?.status)`
- [x] 3.7 Re-run the Phase 3.1 tests — all still green

## Phase 4: Tests & verification

- [x] 4.1 `src/features/leads/LeadDetail.test.tsx`: add "reflects progress without a reload" — MSW returns `enriching` (no score) then `qualified`+score; `client.refetchQueries(leadKey(id))`; assert view shows `qualified` + score/rationale/draft
- [x] 4.2 `pnpm --filter web exec vitest run --coverage` — all prior + new tests green, thresholds met
- [x] 4.3 `pnpm --filter web build` — Tailwind compiles, PWA SW + manifest emit with new colours
- [x] 4.4 `tsc --noEmit` for `apps/web` + `packages/shared` clean

## Phase 5: Cleanup & docs

- [x] 5.1 Delete any dead selectors / unused vars from the restyled components; `pnpm --filter web exec tsc` still clean
- [x] 5.2 `README.md`: update the "React 19 + Vite PWA" line to mention Tailwind v4; note the design canvas link
- [x] 5.3 Manual check: desktop two-column / mobile single-column, no horizontal body scroll, long reply-draft string contained — record in verify

### 5.1 audit result — nothing dead removed

Full audit of `apps/web/src/index.css` + all `.tsx`/`.ts` under `apps/web/src`:

- **Every `@theme` token is referenced by a literal utility class** — `bg-bg`/`text-bg`, `bg-panel`,
  `bg-raised`, `border-line`/`bg-line`, `border-line-soft`, `text-ink`, `text-muted`, `text-dim`,
  `bg-accent`/`text-accent`/`border-accent`, all 6 `st-*` status hues (StatusBadge lookup map),
  all 3 `band-*` hues (ScoreMeter lookup map), `font-sans`, `font-mono`. `--color-dim` /
  `--color-line` also referenced via `var(--…)` in the scrollbar rules.
- **`--color-accent-dim: #8fbf2e` — kept (ambiguous, deliberate palette slot).** No utility class
  references it, BUT its exact hex `#8fbf2e` is inlined in `ScoreMeter`'s hot-band gradient
  (`bg-[linear-gradient(90deg,#8fbf2e,#c9f24a)]`). It is the "dim accent" companion to `--color-accent`.
  Per the cleanup rule (leave deliberate palette slots, don't guess) it stays; verify may downgrade
  to a SUGGESTION (either wire the gradient to `var(--color-accent-dim)` or drop the token).
- `@keyframes rise` — used (`QueueView` row inline `style`). Grain `::before`, `::selection`,
  reduced-motion guard, thin-scrollbar rules — all intentional base styles, kept.
- No leftover pre-redesign bespoke CSS (index.css was fully rewritten in 1.3; only `src/index.css` exists).
- No unused `className` consts (`SECTION_LABEL`, `FIELD_LABEL`, `HEAD_CLASS`, `CELL_CLASS`,
  `LABEL_TEXT`, `FIELD` all referenced), no dead imports, no orphan wrapper divs.
- `data-*` attributes all live: `data-status` (StatusBadge.test asserts it), `data-testid`
  (ScoreMeter tests), `data-selected` (intentional styling/QA hook set in QueueView).

Result: **0 tokens / selectors / consts removed.** `pnpm exec vitest run` → 7 files / 28 tests green.
`pnpm --filter web build` → exit 0, Tailwind CSS 29.76 kB, no missing-token error.

### 5.3 Responsive verification (static / structural)

Automated viewport resize is NOT available on this host (the Chrome extension's `resize_window`
is not honoured — viewport stays 1440), so this is a STATIC verification against the spec's
responsive requirements, not a visual one.

| Spec requirement | Where | Verdict |
|---|---|---|
| Base = stacked, `lg:` = two-column | `Dashboard.tsx` L46 `grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_440px]` | PASS |
| Columns can't force horizontal body scroll | both `<section>` carry `min-w-0` + `overflow-hidden` (L49, L73); `minmax(0,1fr)` first track | PASS |
| `<main>` no horizontal scroll | L16 `flex h-full flex-col overflow-hidden` | PASS |
| Queue scrolls independently of detail | L65 + L84 each `min-h-0 flex-1 overflow-auto` | PASS |
| Empty-state placeholder only in two-column mode | `<aside>` L89 `hidden … lg:flex` | PASS |
| Add-lead form single column below 640px | `AddLeadForm.tsx` L56 `grid gap-3.5 sm:grid-cols-2`, Message `sm:col-span-2` | PASS |
| Long unbroken strings contained | see note below | PASS (contained) / polish flagged |

Long-string containment: `LeadDetail` renders `contact.message` (blockquote L34),
`company · email · role` (mono `<p>` L29), `score.rationale` (L45), `reply_draft.subject`/`body`
(L79–L80) with NO explicit `break-words` / `break-all`. A 60+ char unbroken token would NOT wrap.
However every one of these sits inside a `div.overflow-auto` (Dashboard L84), so the overflow
produces a scrollbar INSIDE the detail panel — the document `<body>` never scrolls horizontally.
This satisfies spec scenario 3 ("long unbroken reply-draft string wraps/scrolls inside the panel,
body still no horizontal scroll"). SUGGESTION for verify: add `break-words` (or `[overflow-wrap:anywhere]`)
to the reply-draft `<p>`, the message blockquote and the mono meta line for a cleaner result than
an inner scrollbar. QueueView `<table>` (L34, no `table-fixed`) similarly scrolls inside its
`overflow-auto` wrapper rather than pushing the body — acceptable, `table-fixed` would be sturdier.

Minor note: `<main>` uses `h-full` off the `html,body,#root { height:100% }` chain rather than
the `100dvh` named in the design — equivalent here, not a regression.

**Visual confirmation at <1024px viewport is still PENDING** — automated resize is unavailable on
this host; needs a manual browser window-drag check (or a real device) at ~375px and ~800px to
confirm the stacked layout renders with no horizontal body scrollbar and no dead placeholder.
