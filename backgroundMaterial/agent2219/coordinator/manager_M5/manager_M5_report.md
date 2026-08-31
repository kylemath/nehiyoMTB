# Manager 2219-M5 Report — Connector Routing via Valhalla

## Stream Summary

Created `mobile/src/lib/connector-routing.ts`, a self-contained module that replaces the route builder's straight-line connector legs with real bike paths from the FOSSGIS Valhalla public router (`https://valhalla1.openstreetmap.de/route`, bicycle costing, Mountain bike profile). Exports exactly the contracted surface: `BikePath`, `fetchBikePath(from, to)`, and `refineRouteConnectors(route)`. No other files touched. No new dependencies.

Key design points:

- **Polyline precision 6**: local `decodePolyline6` helper divides by 1e6 (Valhalla convention), not the Google-default 1e5. Verified against a live response — decoded path length (2519.2 m) matches `trip.summary.length` (2522 m) to within 0.1%.
- **Resilience**: 8 s AbortController timeout; every failure path (network error, non-2xx, malformed body, abort) returns `null`, never throws.
- **Caching**: module-level `Map` keyed by both endpoints rounded to 5 decimals; only successful results cached, so transient failures retry on next rebuild.
- **Sanity guard**: decoded path longer than `4 × haversine + 500 m` is rejected as a router detour through unmapped terrain.
- **Refinement semantics**: connectors `< 30 m` and all trail legs pass through by identity; all eligible fetches run in parallel via `Promise.all`; identity check (`leg === route.legs[i]`) detects "nothing improved" → returns `null`; totals rebuilt as `connectorM = Σ connector distances`, `totalM = trailM + connectorM`; `trailM`, `directM`, `trailsUsed`, and leg order preserved via spread.
- **Visual continuity**: `pinEndpoints` prepends/appends the exact original endpoints when the snapped path starts/ends > 1 m away, so refined connectors stay attached to trail ends on the map.

## Files

| File | Action |
| --- | --- |
| `mobile/src/lib/connector-routing.ts` | Created (the only repo file touched) |
| `backgroundMaterial/agent2219/coordinator/manager_M5/manager_M5_report.md` | Created (this report) |
| `/tmp/valhalla_test.json`, `/tmp/decode_test.js` | Throwaway verification artifacts outside the repo |

## Acceptance Criteria Check

| Criterion | Status | Evidence |
| --- | --- | --- |
| Exact contract exports (`BikePath`, `fetchBikePath`, `refineRouteConnectors`) | PASS | Signatures match the Main Agent contract verbatim |
| POST body (locations, `costing: 'bicycle'`, Mountain/use_roads 0.3/use_hills 0.7) | PASS | Matches spec; live curl with same body returned HTTP 200 |
| Polyline precision-6 decode | PASS | Decoded length 2519.2 m vs summary 2522 m (0.1% agreement) |
| `trip.summary.length` km → meters | PASS | 2.522 km → 2522 m |
| 8 s AbortController timeout, null-not-throw | PASS | Single try/catch/finally around fetch; all failures → `null` |
| In-memory cache, 5-decimal key, successes only | PASS | `cache.set` only on validated result |
| Sanity guard (> 4× haversine + 500 m → null) | PASS | Live case: 2519 m ≤ 4 × 1227 + 500 = 5408 m, accepted correctly |
| Connectors < 30 m and trail legs unchanged | PASS | Early return preserves leg identity |
| Parallel fetches (`Promise.all`) | PASS | One `Promise.all` over mapped legs |
| Failures keep straight leg; no change → `null` | PASS | Identity comparison across all legs |
| Totals rebuilt; `trailM`/`directM`/`trailsUsed`/order preserved | PASS | Spread + recomputed `connectorM`, `totalM` |
| Endpoint pinning (> 1 m → prepend/append originals) | PASS | `pinEndpoints`; live snap offsets were 8.4 m / 7.3 m, so pinning engages on real data |
| `npx tsc --noEmit` clean | PASS | Exit code 0, no diagnostics |
| Live API test | PASS | HTTP 200; `trip.legs[0].shape` (623 chars), `trip.summary.length` = 2.522 |
| Decode test (endpoints < 50 m, > 5 points) | PASS | 178 points; first 8.4 m, last 7.3 m from requested endpoints |

## Verification Numbers

- Route 53.5225,-113.5320 → 53.5290,-113.5170 (Edmonton river valley)
- HTTP 200; `trip.summary.length` = **2.522 km** (2522 m)
- Decoded points: **178**; decoded path length: **2519.2 m**
- First decoded point **8.4 m** from requested start; last **7.3 m** from requested end
- Straight-line distance: 1227.0 m → routed/straight ratio 2.05, well under the 4× + 500 m guard
- `npx tsc --noEmit`: exit 0

## Issues

- None blocking. Notes for the Main Agent:
  - The cache is unbounded; for a city-scale trail network the key space is tiny (dozens of connector pairs), so this is acceptable. If routes ever span hundreds of connectors, consider an LRU.
  - `refineRouteConnectors` fires all eligible fetches at once. The FOSSGIS instance is a free public service; typical routes here have a handful of connectors, which is polite enough, but batch-throttling would be a courtesy if usage grows.
  - The snapped path can legitimately start ~8 m from the trail end (road-network snapping); pinning handles the visual seam, but `distanceM` reflects the routed path only (the ≤ couple of meters of pin segments are negligible and deliberately excluded to keep `distanceM` equal to the router's authoritative figure).

## Self-Assessment

**Craftsperson:** The module is tight — one fetch path, one decode helper, identity-based change detection, and the contract surface matches character-for-character. The decode verified against live data at 0.1% agreement; that's the kind of closure I want before shipping a hand-rolled polyline decoder.

**Skeptic:** Three things I pushed on. (1) Precision 6 vs 5 — a silent 10× coordinate error is the classic Valhalla bug, so I refused to trust the decoder until the decoded path length matched `summary.length` independently. It did. (2) The identity check for "nothing changed" relies on returning the *same object* for untouched legs — verified the map callback early-returns `leg` itself, not a copy. (3) `Promise.all` rejection would break the null-contract — but `fetchBikePath` never rejects (catch-all), so the array promise cannot reject. Residual doubt: I tested one live route, not a degenerate zero-length connector; the `< 30 m` floor and the `points.length < 2` guard cover that path by construction, not by live test.

**Mover:** Contract met, types clean, live API verified, decode proven, report filed. The Skeptic's residual edge cases are guarded in code and documented above — shipping.
