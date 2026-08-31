# Task Decomposition — Agent 2219

## Original Task

In the mobile app, two related features exist: (1) a bike-route builder (start trailhead + destination marker → path through as many trails as possible within an X km detour budget) and (2) "Directions to trail start" buttons that open the external maps app. Replace feature 2 with feature 1 so the user never leaves the app, and integrate with the GPS ride-recording feature so a live map shows current location and route-so-far.

- Clicking "Directions to trail start" = build a route from the current GPS location to that trail's start.
- Route builder start options: (1) current location, (2) user-specified point on the map, (3) saved "home" location (per-user, in DB).
- Route builder destination options: (a) a selected trail's start, (b) a tapped map location, (c) saved "home".
- New transit-style itinerary UI: ordered list of trails on the route, each with order, length, difficulty (from Trailforks), sign icon, name; connector distance shown between each trail.

## Atomic Subtasks

1. Research Trailforks difficulty for ~36 trails (Trailforks blocks scraping; use web search) → difficulty token per trail.
2. Store difficulty in `docs/catalogue.json` (`pageContent.trailforks.difficulty`), extend `tools/export_trails_for_app.py` to export it (trails.json + seed.sql), regenerate data.
3. Supabase migration `0002`: `profiles.home_lat/home_lng`, `trails.difficulty`.
4. `mobile/src/lib/home.ts`: saved home location (AsyncStorage + Supabase profile sync).
5. Profile screen card to set/clear home.
6. `mobile/src/components/route-itinerary.tsx`: transit-style itinerary + `DifficultyBadge`.
7. `mobile/src/lib/rides.ts`: shared `RideRecorder` singleton + multi-listener support; `ride.tsx` uses it.
8. `mobile/src/lib/routing.ts`: route-progress helper (`nearestLegIndex`).
9. `index.tsx` route-builder rework: endpoint pickers (My location / Home / Map pin / Trail), trail-tap destination, deep-link param `destTrail`, live navigation mode with recorder + itinerary.
10. `trail/[id].tsx`: "Directions to trail start" → in-app route (keep external maps as secondary action); show difficulty.

## Dependency Graph

- 1 → 2 (difficulty values needed before regeneration)
- 2, 3 independent of 4–8
- 4–8 independent of each other
- 9, 10 depend on contracts from 4, 6, 7, 8 (contracts fixed below, so work proceeds in parallel)
- Main Agent owns 8, 9, 10 (most interdependent files) — the team must NOT touch `mobile/src/app/(tabs)/index.tsx`, `mobile/src/app/trail/[id].tsx`, `mobile/src/lib/routing.ts`.

## Stream Allocation

| Manager | Stream Type | Subtasks | Dependencies | Async? |
|---------|-------------|----------|--------------|--------|
| M1 Data & Backend | mixed | S1+S2: difficulty research (split list), S3: export tool + migration + Trail type; manager merges + regenerates | None | Yes |
| M2 Mobile Libs & UI | parallel | S1: home lib + profile card, S2: itinerary component, S3: shared recorder | None | Yes |
| M3 Catalogue Editor | solo | Difficulty `<select>` in the Trailforks panel of `docs/index.html` (load + save wiring to `pageContent.trailforks.difficulty`) — added after user noted Trailforks fields are managed in that editor | None | Yes |
| Main Agent | serial | routing helper, index.tsx rework, trail detail | Contracts only | Concurrent |

## File Ownership (strict — no agent edits a file outside its column)

| Owner | Files |
|-------|-------|
| M1 | `docs/catalogue.json` (manager merge only), `tools/export_trails_for_app.py`, `supabase/migrations/0002_*.sql`, `mobile/src/lib/trails.ts`, regenerated `mobile/src/data/*`, `supabase/seed.sql`, `mobile/assets/trail-icons/*` |
| M2 | `mobile/src/lib/home.ts` (new), `mobile/src/app/(tabs)/profile.tsx`, `mobile/src/components/route-itinerary.tsx` (new), `mobile/src/lib/rides.ts`, `mobile/src/app/(tabs)/ride.tsx` |
| Main Agent 2219 | `mobile/src/lib/routing.ts`, `mobile/src/app/(tabs)/index.tsx`, `mobile/src/app/trail/[id].tsx` |

## Fixed Cross-Stream Contracts

1. **Difficulty token** (string, stored in catalogue + trails.json + DB): one of `'green' | 'blue' | 'black' | 'dblblack'` or `null` if unknown. (`green` = easy/green circle, `blue` = intermediate/blue square, `black` = black diamond, `dblblack` = double black diamond.)
2. **Trail type** (`mobile/src/lib/trails.ts`): gains `difficulty: string | null`.
3. **home.ts API**:
   - `export type HomeLocation = { latitude: number; longitude: number }`
   - `export async function getHome(): Promise<HomeLocation | null>` — AsyncStorage key `etm.home.v1`
   - `export async function setHome(loc: HomeLocation | null): Promise<void>` — persists locally, best-effort sync to `profiles.home_lat/home_lng` when signed in and backend configured
   - `export async function pullHomeFromProfile(): Promise<HomeLocation | null>` — fetch remote, cache locally, return merged value
4. **route-itinerary.tsx API**:
   - `export function RouteItinerary({ route, activeLegIndex }: { route: BikeRoute; activeLegIndex?: number | null })`
   - `export function DifficultyBadge({ difficulty }: { difficulty: string | null | undefined })` (renders nothing when null)
5. **rides.ts**: `export const sharedRecorder: RideRecorder` (module singleton); `RideRecorder.addListener(fn: (ride: LocalRide) => void): () => void` (unsubscribe return); existing `onUpdate` property must keep working.
6. **Migration**: `supabase/migrations/0002_home_and_difficulty.sql` — `alter table public.profiles add column home_lat double precision, add column home_lng double precision;` and `alter table public.trails add column difficulty text;` (plus seed regeneration including difficulty).

## Complexity Estimate

Medium-large (10 subtasks, 2 managers, ~3 sub-subagents each). Main risk: difficulty research accuracy (web-search-based, Trailforks blocks direct fetch — unknown values stay null and the UI hides the badge), and integration in `index.tsx` (owned by Main Agent to avoid conflicts).
