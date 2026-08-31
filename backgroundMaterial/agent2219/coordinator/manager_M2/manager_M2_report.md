# Manager M2 Report — Mobile Libs & UI

Manager M2 under Coordinator 2219-C. All three subtasks were spawned as parallel generalPurpose sub-subagents, completed on the first pass, and verified by me against contracts and file ownership. No resume iterations were needed.

## Status per subtask

### S1 — Home location lib + profile card: COMPLETE
- Files: `mobile/src/lib/home.ts` (new), `mobile/src/app/(tabs)/profile.tsx` (modified)
- Contract 1 verified by grep against actual code:
  - `export type HomeLocation = { latitude: number; longitude: number }` (home.ts:7)
  - `export async function getHome(): Promise<HomeLocation | null>` (home.ts:9), AsyncStorage key `etm.home.v1` (home.ts:5)
  - `export async function setHome(loc: HomeLocation | null): Promise<void>` (home.ts:24) — local persist plus best-effort sync to `profiles.home_lat/home_lng` gated on session + `backendConfigured`, all network work in try/catch
  - `export async function pullHomeFromProfile(): Promise<HomeLocation | null>` (home.ts:43)
- Profile screen: "Home location" card with `pullHomeFromProfile()` on mount, coords via `.toFixed(5)`, "Set to current location" using foreground permission + `getCurrentPositionAsync` (matches existing `capture.tsx` pattern), "Clear" only when set, copy mentioning the route-builder map pin. No existing profile features removed.
- Sub-report: `sub_S1/S1_report.md`

### S2 — Transit-style route itinerary: COMPLETE
- Files: `mobile/src/components/route-itinerary.tsx` (new, only file touched)
- Contract 2 verified by grep:
  - `export function RouteItinerary({ route, activeLegIndex }: { route: BikeRoute; activeLegIndex?: number | null })` (line 142)
  - `export function DifficultyBadge({ difficulty }: { difficulty: string | null | undefined })` (line 21) — handles `green`/`blue`/`black`/`dblblack`, `default: return null` confirmed (lines 66–67)
- Transit-style vertical list: green Start dot, numbered leg rows with `TrailIconBadge` + `displayName` + `DifficultyBadge` + `formatKm` length, dashed connector rows (omitted under `MIN_CONNECTOR_M = 25`), red Destination dot. Active leg highlighted with `Brand.amber` border + `${Brand.amber}22` tint (lines 219–220). Plain Views only — grep confirms zero ScrollView/FlatList. Imports `BikeRoute` from `@/lib/routing` (read-only, as required).
- Sub-report: `sub_S2/S2_report.md`

### S3 — Shared ride recorder: COMPLETE
- Files: `mobile/src/lib/rides.ts`, `mobile/src/app/(tabs)/ride.tsx` (modified)
- Contract 3 verified by reading the code:
  - `RideRecorder` gained private `listeners = new Set<...>()` (rides.ts:50), `addListener(fn): () => void` returning unsubscribe (rides.ts:54–59), private `notify()` firing legacy `onUpdate` first then all listeners (rides.ts:61–64), called per GPS fix (rides.ts:98)
  - `export const sharedRecorder = new RideRecorder()` module-level singleton (rides.ts:117)
- `ride.tsx`: `useRef(sharedRecorder)` (line 27), subscribes via `addListener` inside `useFocusEffect` with unsubscribe cleanup (line 44–47), derives `recording` from `sharedRecorder.ride != null` so navigation-started recordings appear on tab focus. GPX export, upload, photo sync, and pending share flow untouched.
- Sub-report: `sub_S3/S3_report.md`

## Contract compliance & verification

- All three fixed contracts implemented with exact signatures (grep-verified against actual code, not just sub-reports).
- `npx tsc --noEmit` in `mobile/`: the only error is in M1-owned `src/lib/trails.ts` (`difficulty` missing from `trails.json` data — the anticipated M1 mid-edit cross-stream race). Zero errors trace to M2-owned files. Notably, the brief-expected errors in `index.tsx`/`trail/[id].tsx`/`routing.ts` are absent, suggesting Main Agent's edits currently typecheck.
- File ownership: no M2 sub-subagent touched forbidden files. `git status` shows other dirty files (`index.tsx`, `trail/[id].tsx`, `routing.ts`, `trails.ts`, `trails.json`, `catalogue.json`, `seed.sql`, migration `0002`, etc.) — all attributable to the Main Agent / M1 concurrent streams and/or pre-existing at session start; each sub-subagent's diff was confined to its owned files.

## Unresolved issues / notes for coordinator

1. Cross-stream race (expected): the lone tsc error clears when M1 finishes adding `difficulty` to `trails.json`/export pipeline.
2. S1 design note: `pullHomeFromProfile` lets remote win over local (no conflict timestamps); sync is a silent no-op until M1's `0002_home_and_difficulty.sql` migration is applied to the backend.
3. S2 design note: connector legs under 25 m have no row, so an `activeLegIndex` pointing at a suppressed connector has nothing to highlight — spec-compliant, but Main Agent's live nav should be aware.
4. S3 design note: any holder of `sharedRecorder` can `stop()` the shared recording (tab or navigation); acceptable single-recording semantics, flagged for Main Agent.

## Tripartite self-assessment

- **Craftsperson says:** Every contract signature was verified directly in the code, not taken on faith from sub-reports; all three implementations follow existing repo patterns (AsyncStorage keys like `auth.tsx`, location flow like `capture.tsx`, palette/StyleSheet conventions) and the parallel split had zero file overlap, so no merge friction.
- **Skeptic says:** Verification is static — no runtime test of GPS recording, Supabase sync, or pixel rendering in a bottom sheet; git status cannot cryptographically attribute concurrent edits to specific agents, so I rely on sub-report claims plus the known concurrent-stream story; the itinerary's difficulty token vocabulary depends on M1's final data values matching `green|blue|black|dblblack`.
- **Mover says:** All acceptance criteria are met with grep/tsc evidence, the contracts are frozen and the Main Agent is unblocked; residual risks are integration-time concerns owned by other streams and are documented above — shipping. With more time I'd add unit tests for `home.ts` parse guards and the recorder's multi-listener semantics.
