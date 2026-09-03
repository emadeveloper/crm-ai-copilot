# Design: Dashboard redesign — "operational precision"

## Technical Approach

Add Tailwind CSS v4 via `@tailwindcss/vite`; replace `src/index.css` with an `@import "tailwindcss"`
+ `@theme` token block. Restyle the 4 existing components with utility classes, add two small
components (`StatusBadge`, `ScoreMeter`), make `Dashboard.tsx` a responsive CSS-grid shell, and
give `useLead` a status-aware `refetchInterval`. Markup semantics (roles, `<label>` associations,
`<tr>` rows, verbatim text) are preserved so the 11 existing tests are unaffected (`vitest` has
`css: false`). Satisfies spec delta `web-dashboard`: *Responsive two-column layout* + *Lead detail
view* (live refresh).

## Architecture Decisions

| Topic | Options | Decision & rationale |
|---|---|---|
| Styling | hand-CSS / shadcn+Radix / **Tailwind v4** | **Tailwind v4** — CSS-first `@theme`, no config file, tiny output, coexists with VitePWA. shadcn's default look is the generic aesthetic to avoid; Radix unneeded (detail is an inline region, not a modal). |
| Fonts | Google CDN / **`@fontsource` self-host** | Self-host — one request-free, offline-clean for the PWA. **Hanken Grotesk Variable** (UI/prose) + **IBM Plex Mono** (numbers, labels, status tags). Neither is Inter/Roboto/Space Grotesk. |
| Accent | blue / amber / **electric lime** | **Lime `oklch(0.9 0.19 118)`** — reads as "signal/instrument", memorable, avoids the purple-gradient cliché. Used sparingly (focus ring, `qualified`/`hot`, load-in sweep, logo mark). |
| Layout | flex stack / **CSS grid, 2-col** | `<main>` is `height: 100dvh`, `grid-template-columns: minmax(0,1fr) minmax(0,26rem)` at `lg`, one column below. Queue and detail columns each `overflow: auto` → scroll independently. Header spans both. |
| Detail column presence | mount on select / **always present** | Right column always rendered; shows an empty prompt when nothing selected (no layout jump). The `<section aria-label="lead detail">` stays **conditional on selection** so `Dashboard.test.tsx` is unchanged. |
| Live refresh | poll always / **status-aware** | `useLead` `refetchInterval` = `3000` while status ∉ {`synced`,`failed`}, else `false`. Extract `detailRefetchInterval(status)` as a pure helper for a unit test. |
| Motion | framer-motion / **CSS-only** | CSS `@keyframes` + `animation-delay` staggered rise on header + rows; gated by `prefers-reduced-motion`. No new runtime dep. |
| Add-lead form | always-visible section / **header toggle** | A `+ Add lead` control in the header toggles a compact inline form panel — saves vertical space in the 2-col layout. Keeps `getByLabelText` / button-name selectors intact. |
| Grain texture | image asset / **inline SVG data-URI** | `feTurbulence` SVG as a `background-image` on a fixed `::before`, `opacity ~0.035`, `pointer-events:none`. Zero asset, subtle depth. |

## Data Flow

    useLeads (poll 5s) ──► QueueView rows ──(onSelect id)──► Dashboard state
                                                                  │
                                              useLead(id) ◄───────┘
                                              refetchInterval = terminal? false : 3s
                                                     │
                                              LeadDetail  ── ScoreMeter, StatusBadge

## File Changes

| File | Action | Description |
|---|---|---|
| `apps/web/src/index.css` | Rewrite | `@import "tailwindcss"` + `@theme` tokens + `@layer base` (body, grain, fonts, keyframes) |
| `apps/web/src/main.tsx` | Modify | `import "@fontsource-variable/hanken-grotesk"` + `import "@fontsource/ibm-plex-mono"` |
| `apps/web/src/Dashboard.tsx` | Rewrite | grid shell, header + add-lead toggle, always-present detail column with empty state |
| `apps/web/src/features/leads/QueueView.tsx` | Modify | table styling, `StatusBadge`, `ScoreMeter` in the score cell, staggered row rise |
| `apps/web/src/features/leads/LeadDetail.tsx` | Modify | visual hierarchy, `ScoreMeter`, `StatusBadge`, sync footer styling |
| `apps/web/src/features/leads/AddLeadForm.tsx` | Modify | input/label/button styling only |
| `apps/web/src/features/leads/hooks.ts` | Modify | `useLead` status-aware `refetchInterval`; export `detailRefetchInterval` helper |
| `apps/web/src/components/StatusBadge.tsx` | Create | `<span>` uppercase tag, colour by status, renders status text verbatim |
| `apps/web/src/components/ScoreMeter.tsx` | Create | `role="meter"` + `aria-valuenow`; renders value + band text + a coloured bar |
| `apps/web/src/components/*.test.tsx` | Create | unit tests for the two components + `detailRefetchInterval` |
| `apps/web/src/features/leads/LeadDetail.test.tsx` | Modify | add "reflects progress without a reload" scenario |
| `apps/web/vite.config.ts` | Modify | add `tailwindcss()` plugin; PWA `theme_color`/`background_color` → new palette |
| `apps/web/index.html` | Modify | `<meta name="theme-color">` → `#0a0b0d` |
| `apps/web/package.json` | Modify | `+ tailwindcss` `@tailwindcss/vite` `@fontsource-variable/hanken-grotesk` `@fontsource/ibm-plex-mono` |

## Interfaces / Contracts

```ts
// components/StatusBadge.tsx
export function StatusBadge({ status }: { status: string }): JSX.Element

// components/ScoreMeter.tsx  — value 0..100
export function ScoreMeter({ value, band }: { value: number; band: string }): JSX.Element

// features/leads/hooks.ts
export function detailRefetchInterval(status: string | undefined): number | false
// -> false when status is "synced" | "failed", else 3000
```

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | `StatusBadge` renders the status text; `ScoreMeter` renders value + band, `role="meter"`, `aria-valuenow` | Testing Library, no MSW |
| Unit | `detailRefetchInterval("synced") === false`; `detailRefetchInterval("enriching") === 3000` | plain assertion |
| Integration | `LeadDetail` updates on refetch: MSW returns `enriching` then `qualified`+score; `client.refetchQueries(leadKey)` → assert view shows `qualified` + score | mirrors the existing QueueView refresh test |
| Integration | 11 existing tests stay green | safety-net run per component before edit |
| Build | Tailwind compiles, PWA manifest + SW emit | `pnpm --filter web build` |
| Manual | true 2-col ↔ 1-col responsive (jsdom has no layout engine); no horizontal body scroll | resize check + note in verify |

## Migration / Rollout

No migration. CSS-only + one hook tweak. Single-change branch; revert restores `index.css` and the
prior components.

## Open Questions

- [ ] Exact accent (lime vs amber) — the `/design` mockup will make it concrete for approval.
- [ ] Add-lead: header-toggle panel vs a route/modal — mockup decides; leaning header-toggle.
