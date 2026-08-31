# Manager 2219-M4 Report — Route Geometry Helpers

## Stream Summary

Added three pure geometry helpers to `mobile/src/lib/routing.ts` per the fixed contract, so the Main Agent's map view can draw the computed route offset ~5 m beside the underlying trail polylines, with direction chevrons along it:

- `bearingDeg(a, b)` — great-circle compass bearing (0 = north, clockwise), normalized to [0, 360).
- `offsetPath(points, offsetM = 5)` — shifts each point perpendicular to local travel direction using the same equirectangular meters-per-degree projection style as the existing `pointSegmentDistM`. Interior points use the normalized average of incoming/outgoing segment directions; endpoints use their single adjacent segment. Zero-length segments are skipped (previous direction reused; 180° reversals fall back to the incoming direction). Positive offset = right-hand side of travel. Arrays with <2 points return as-is.
- `routeChevrons(route, spacingM = 150, maxCount = 40)` — concatenates all leg points (deduping the shared join point between consecutive legs), measures total haversine length, widens spacing to `total/maxCount` when needed so distribution stays even, and walks cumulative distance emitting one chevron per spacing interval. Coordinates are interpolated on the `offsetPath` line (default 5 m) so chevrons sit on the offset route polyline; bearing comes from the underlying segment's direction of travel.

One small private helper `segmentDirM` (unit east/north direction in meters, null for zero-length) was added to share projection logic; no dependencies were added and no existing code was modified beyond extending the `geo.ts` import to include `pathLengthM`.

## Files changed

- `mobile/src/lib/routing.ts` — only file edited. Added `bearingDeg`, `offsetPath`, `RouteChevron`, `routeChevrons` exports plus private `segmentDirM`; extended import from `@/lib/geo`.

## Acceptance criteria check

| Criterion | Status |
|---|---|
| Exact contract signatures exported (`bearingDeg`, `offsetPath` w/ default 5, `RouteChevron`, `routeChevrons` w/ defaults 150/40) | Pass |
| Edit only `routing.ts` | Pass |
| Local equirectangular projection, no new dependencies | Pass |
| `offsetPath` handles <2 points, zero-length segments, averaged interior directions | Pass |
| `routeChevrons` joins legs, even spacing, maxCount cap by widening spacing, skips zero-length segments | Pass |
| Brief JSDoc on exports matching file style | Pass |
| `npx tsc --noEmit` clean for this file | Pass — only remaining errors are in `src/app/(tabs)/index.tsx` (`trailStartEndpoint` not found), the Main Agent's mid-edit file, as the brief anticipated |
| Numeric sanity checks | Pass (see below) |

Numeric verification (real function bodies extracted from the file and run with `tsx`; direct import was blocked by the module chain `routing → trails → trail-assets` requiring PNGs under plain node):

- bearing due-east pair: 89.996°; due-north: 0.000°; due-south: 180.000°
- `offsetPath` on a straight northbound line: every point shifted 4.994 m, to the east (right of travel); negative offset shifts west; 1-point array passes through; duplicate consecutive points handled
- `routeChevrons` on a 1.33 km two-leg northbound route: 8 chevrons, 150.0 m apart, bearing 0.00°, coordinates east of the trail line (on the offset path)
- cap test (spacing 10, maxCount 5): exactly 5 chevrons, evenly redistributed at ~266.9 m
- empty route returns []

## Issues

- None blocking. Two pre-existing/concurrent tsc errors in `src/app/(tabs)/index.tsx` belong to the Main Agent's in-flight edit and reference a symbol (`trailStartEndpoint`) unrelated to this stream.
- Note for integrators: `offsetPath` average-direction handling means very sharp interior corners (near-180° hairpins) fall back to the incoming segment's perpendicular rather than a miter, which avoids the offset point shooting far off the line — visually correct at 5 m scale.

## Self-Assessment

**Craftsperson:** The helpers mirror the file's existing idiom exactly — same 111320 m/deg projection constant as `pointSegmentDistM`, same terse JSDoc voice, haversine for distance where the file already uses it. The maxCount cap widens spacing instead of truncating, which preserves even distribution along the full route rather than crowding chevrons at the start.

**Skeptic:** Three things bothered me. First, the equirectangular perpendicular at city scale — verified numerically: 4.994 m shift vs 5 m requested, within projection error, fine. Second, hairpin corners where the averaged direction is zero — the code falls back to the incoming direction rather than producing NaN; tested via duplicate-point input. Third, the verification itself: I could not import `routing.ts` directly under tsx (the trails import chain requires PNG assets), so I extracted the exact function text with `sed` and ran that — it is the real code, but the import-graph behavior under Metro is vouched for by tsc, not by the runtime test. Acceptable, but worth stating honestly.

**Mover:** tsc is clean for this file, the numbers check out, the contract surface is exactly as specified, and the Main Agent is waiting on these exports. The hairpin and projection caveats are documented above; nothing left here blocks integration. Shipped.
