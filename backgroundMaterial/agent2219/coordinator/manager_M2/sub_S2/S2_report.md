# S2 Report — Transit-Style Route Itinerary UI

**Agent:** Sub-subagent S2 (Itinerary UI), Manager M2, Coordinator 2219-C
**Date:** 2026-06-10

## What changed

One new file, nothing else touched:

- `mobile/src/components/route-itinerary.tsx` (NEW)

Summary: a transit-directions-style itinerary for a `BikeRoute`. Renders a vertical
list — green "Start" dot, numbered trail rows (order circle, `TrailIconBadge`,
`displayName`, `DifficultyBadge`, length via `formatKm`), dashed "ride x m/km"
connector rows between trails (omitted under 25 m), and a red "Destination" dot.
`activeLegIndex` highlights the matching leg row with a Brand.amber border and
amber tint (`${Brand.amber}22`, matching the repo's Chip tint convention).

Internal structure: small private row components (`TerminusRow`, `ConnectorRow`,
`TrailRow`) plus the two exported contract functions. The dashed connector line is
a column of three small rounded Views rather than a dashed border (RN dashed
partial borders are unreliable on iOS).

## Acceptance evidence

1. **Exact contract exports** — `export function RouteItinerary({ route, activeLegIndex }: { route: BikeRoute; activeLegIndex?: number | null })` and `export function DifficultyBadge({ difficulty }: { difficulty: string | null | undefined })`, both in `route-itinerary.tsx`. `BikeRoute` imported from `@/lib/routing` as exported there (legs are a discriminated union on `type: 'connector' | 'trail'`).
2. **No ScrollView/FlatList** — the component tree is exclusively `View`/`Text` (plus `TrailIconBadge`, itself View/Image). `container` style uses `gap`, no scroll containers; parent bottom sheet owns scrolling.
3. **DifficultyBadge tokens** — switch over `'green'` (13 px circle, Brand.moss), `'blue'` (12 px rounded square, #2B6CB0), `'black'` (9 px square rotated 45°), `'dblblack'` (two overlapping diamonds); `default` branch returns `null`. Black diamonds render paper-white in dark mode via `usePalette().dark` so they stay visible.
4. **Brand.amber highlighting** — `activeRow` style: `borderColor: Brand.amber`, `backgroundColor: ${Brand.amber}22`; the order-number circle and digit also flip to amber when active. Applied when `activeLegIndex === i` where `i` is the index into `route.legs` (matching `nearestLegIndex` semantics in routing.ts). All rows carry a transparent 1.5 px border so highlighting causes no layout shift.
5. **Connector threshold + formatting** — `MIN_CONNECTOR_M = 25`; connector legs below it are skipped. Distances use `formatKm` from `@/lib/geo` (`>= 1000` → "x.x km", else "n m") for both connectors and trail lengths.
6. **File ownership** — only `mobile/src/components/route-itinerary.tsx` created; verified via git status that no other file was modified by this agent.
7. **TypeScript clean** — `npx tsc --noEmit` reports zero errors traceable to `route-itinerary.tsx`. The sole project error is in M1-owned `src/lib/trails.ts` (the `Trail` type already gained `difficulty` but `trails.json` data hasn't been regenerated — the anticipated cross-stream race). Linter: no errors in my file.

## Self-assessment

**Craftsperson says:** The component follows repo conventions closely — `usePalette()` for theming, `StyleSheet.create`, the `${tint}22` active-tint pattern from `ui.tsx`'s Chip, `TrailIconBadge` at list-row size (32, near the 38 default), `displayName`/`trailById`/`formatKm` from the canonical helpers. The dotted-rail layout (fixed 36 px left rail) keeps start dot, order circles, dashes, and end dot vertically aligned like a real transit view. The dashed line as stacked Views is deliberately more robust than `borderStyle: 'dashed'` on iOS.

**Skeptic says:** Three residual risks. (a) If `activeLegIndex` points at a connector under 25 m, no row exists to highlight — the spec says to omit those rows, so I followed it, but live navigation could briefly show no highlighted row on a short hop. (b) `trail.difficulty` is typed by M1's in-flux `Trail` type; if their final token vocabulary differs from `green/blue/black/dblblack`, badges silently render null (which is the contracted unknown-token behavior, but worth a glance after merge). (c) I could not render the component end-to-end (no running app for this subtask); confidence rests on typecheck + convention match, not pixels.

**Mover says:** All seven acceptance criteria are met with evidence, the contract surface is exact, and the open risks are integration-time concerns owned by other streams, not defects in this file. Shipping. With more time I'd add a tiny visual harness route to eyeball the dark-mode diamond contrast and the active-row tint inside an actual bottom sheet.
