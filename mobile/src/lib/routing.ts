/**
 * Bike-route builder: connect A to B passing through as many trails as
 * possible without exceeding a detour budget.
 *
 * Approach (v1, intentionally simple): cheapest-insertion. Start with the
 * direct leg A->B, then repeatedly insert the trail whose best insertion
 * (in either riding direction) adds the least extra distance, while the
 * total stays within direct-distance + budget. Connectors between trails are
 * straight lines for now; swapping in a real cycling router (OSRM/Valhalla)
 * later only changes `connectorDistance` / connector geometry.
 */

import { LatLng, haversineM, pathLengthM } from '@/lib/geo';
import { Trail, mappedTrails, trackToLatLng } from '@/lib/trails';

export type RouteLeg =
  | { type: 'connector'; points: LatLng[]; distanceM: number }
  | { type: 'trail'; trailId: string; title: string; points: LatLng[]; distanceM: number };

export type BikeRoute = {
  legs: RouteLeg[];
  totalM: number;
  trailM: number;
  connectorM: number;
  directM: number;
  trailsUsed: string[];
};

type Segment = {
  trail: Trail;
  points: LatLng[]; // oriented in riding direction
  lengthM: number;
};

function connectorDistance(a: LatLng, b: LatLng): number {
  return haversineM(a, b);
}

function orientations(trail: Trail): Segment[] {
  const fwd = trackToLatLng(trail.track);
  // A trail with no recorded length must not look "free" to the planner.
  const lengthM = trail.lengthM ?? pathLengthM(fwd);
  return [
    { trail, points: fwd, lengthM },
    { trail, points: [...fwd].reverse(), lengthM },
  ];
}

export function buildBikeRoute(
  start: LatLng,
  endPt: LatLng,
  maxDetourM: number,
  candidates: Trail[] = mappedTrails,
): BikeRoute {
  const directM = connectorDistance(start, endPt);

  // Ordered anchor sequence: start, [trail segments...], end.
  const chosen: Segment[] = [];
  const remaining = candidates.filter((t) => t.track.length > 1);

  const routeLength = (segs: Segment[]): number => {
    let total = 0;
    let cursor = start;
    for (const seg of segs) {
      total += connectorDistance(cursor, seg.points[0]) + seg.lengthM;
      cursor = seg.points[seg.points.length - 1];
    }
    return total + connectorDistance(cursor, endPt);
  };

  for (;;) {
    let best: { segs: Segment[]; length: number; trailId: string } | null = null;
    for (const trail of remaining) {
      if (chosen.some((s) => s.trail.id === trail.id)) continue;
      for (const seg of orientations(trail)) {
        for (let i = 0; i <= chosen.length; i++) {
          const trial = [...chosen.slice(0, i), seg, ...chosen.slice(i)];
          const len = routeLength(trial);
          if (len <= directM + maxDetourM && (best === null || len < best.length)) {
            best = { segs: trial, length: len, trailId: trail.id };
          }
        }
      }
    }
    if (!best) break;
    chosen.length = 0;
    chosen.push(...best.segs);
    const idx = remaining.findIndex((t) => t.id === best!.trailId);
    if (idx >= 0) remaining.splice(idx, 1);
  }

  const legs: RouteLeg[] = [];
  let cursor = start;
  let trailM = 0;
  let connectorM = 0;
  for (const seg of chosen) {
    const cd = connectorDistance(cursor, seg.points[0]);
    legs.push({ type: 'connector', points: [cursor, seg.points[0]], distanceM: cd });
    legs.push({
      type: 'trail',
      trailId: seg.trail.id,
      title: seg.trail.title,
      points: seg.points,
      distanceM: seg.lengthM,
    });
    connectorM += cd;
    trailM += seg.lengthM;
    cursor = seg.points[seg.points.length - 1];
  }
  const lastCd = connectorDistance(cursor, endPt);
  legs.push({ type: 'connector', points: [cursor, endPt], distanceM: lastCd });
  connectorM += lastCd;

  return {
    legs,
    totalM: trailM + connectorM,
    trailM,
    connectorM,
    directM,
    trailsUsed: chosen.map((s) => s.trail.id),
  };
}

/** Approximate distance (m) from a point to a polyline segment, using a
 * local equirectangular projection — plenty accurate at city scale. */
function pointSegmentDistM(p: LatLng, a: LatLng, b: LatLng): number {
  const mPerDegLat = 111320;
  const mPerDegLng = 111320 * Math.cos((p.latitude * Math.PI) / 180);
  const ax = (a.longitude - p.longitude) * mPerDegLng;
  const ay = (a.latitude - p.latitude) * mPerDegLat;
  const bx = (b.longitude - p.longitude) * mPerDegLng;
  const by = (b.latitude - p.latitude) * mPerDegLat;
  const dx = bx - ax;
  const dy = by - ay;
  const lenSq = dx * dx + dy * dy;
  const t = lenSq === 0 ? 0 : Math.max(0, Math.min(1, -(ax * dx + ay * dy) / lenSq));
  const cx = ax + t * dx;
  const cy = ay + t * dy;
  return Math.sqrt(cx * cx + cy * cy);
}

/** Compass bearing in degrees (0 = north, clockwise) from a to b. */
export function bearingDeg(a: LatLng, b: LatLng): number {
  const la1 = (a.latitude * Math.PI) / 180;
  const la2 = (b.latitude * Math.PI) / 180;
  const dLng = ((b.longitude - a.longitude) * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(la2);
  const x = Math.cos(la1) * Math.sin(la2) - Math.sin(la1) * Math.cos(la2) * Math.cos(dLng);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

/** Unit (east, north) direction in meters from a to b via local
 * equirectangular projection, or null for a zero-length segment. */
function segmentDirM(a: LatLng, b: LatLng): { x: number; y: number } | null {
  const mPerDegLat = 111320;
  const mPerDegLng = 111320 * Math.cos((a.latitude * Math.PI) / 180);
  const x = (b.longitude - a.longitude) * mPerDegLng;
  const y = (b.latitude - a.latitude) * mPerDegLat;
  const len = Math.sqrt(x * x + y * y);
  if (len === 0) return null;
  return { x: x / len, y: y / len };
}

/** Shift points sideways by `offsetM` meters, perpendicular to the local
 * direction of travel, so the route line draws beside the trail line
 * instead of on top of it. Positive offset = right-hand side of travel. */
export function offsetPath(points: LatLng[], offsetM = 5): LatLng[] {
  if (points.length < 2) return points;

  // Per-point travel direction: adjacent segment for endpoints, average of
  // incoming/outgoing for interior points; reuse previous on degenerate cases.
  let lastDir = { x: 0, y: 1 };
  return points.map((p, i) => {
    const incoming = i > 0 ? segmentDirM(points[i - 1], p) : null;
    const outgoing = i < points.length - 1 ? segmentDirM(p, points[i + 1]) : null;
    let dir = incoming && outgoing
      ? { x: incoming.x + outgoing.x, y: incoming.y + outgoing.y }
      : incoming ?? outgoing;
    if (dir) {
      const len = Math.sqrt(dir.x * dir.x + dir.y * dir.y);
      dir = len === 0 ? incoming : { x: dir.x / len, y: dir.y / len };
    }
    if (dir) lastDir = dir;
    else dir = lastDir;

    // Right-hand perpendicular of (east, north) travel direction.
    const px = dir.y * offsetM;
    const py = -dir.x * offsetM;
    const mPerDegLat = 111320;
    const mPerDegLng = 111320 * Math.cos((p.latitude * Math.PI) / 180);
    return {
      latitude: p.latitude + py / mPerDegLat,
      longitude: p.longitude + px / mPerDegLng,
    };
  });
}

export type RouteChevron = { coordinate: LatLng; bearing: number };

/** Evenly spaced direction markers along the whole route (all legs joined),
 * spaced `spacingM` apart (default 150), capped at `maxCount` (default 40).
 * Coordinates sit on the offset route line (offsetPath, default 5 m).
 * Bearing = direction of travel. */
export function routeChevrons(route: BikeRoute, spacingM = 150, maxCount = 40): RouteChevron[] {
  const joined: LatLng[] = [];
  for (const leg of route.legs) {
    for (const p of leg.points) {
      const last = joined[joined.length - 1];
      if (last && last.latitude === p.latitude && last.longitude === p.longitude) continue;
      joined.push(p);
    }
  }
  if (joined.length < 2) return [];

  const offset = offsetPath(joined);
  const total = pathLengthM(joined);
  if (total === 0) return [];
  let spacing = spacingM;
  if (total / spacing > maxCount) spacing = total / maxCount;

  const chevrons: RouteChevron[] = [];
  let traveled = 0;
  let nextAt = spacing;
  for (let i = 1; i < joined.length && chevrons.length < maxCount; i++) {
    const segLen = haversineM(joined[i - 1], joined[i]);
    if (segLen === 0) continue;
    const bearing = bearingDeg(joined[i - 1], joined[i]);
    while (nextAt <= traveled + segLen && chevrons.length < maxCount) {
      const t = (nextAt - traveled) / segLen;
      const a = offset[i - 1];
      const b = offset[i];
      chevrons.push({
        coordinate: {
          latitude: a.latitude + (b.latitude - a.latitude) * t,
          longitude: a.longitude + (b.longitude - a.longitude) * t,
        },
        bearing,
      });
      nextAt += spacing;
    }
    traveled += segLen;
  }
  return chevrons;
}

/** Index of the route leg nearest to `pos` — drives "you are here" progress
 * in the live navigation itinerary. Only looks from `fromLeg` up to two legs
 * ahead, so progress never jumps backwards where a route doubles back. */
export function nearestLegIndex(route: BikeRoute, pos: LatLng, fromLeg = 0): number {
  let bestIdx = fromLeg;
  let bestDist = Infinity;
  route.legs.forEach((leg, i) => {
    if (i < fromLeg || i > fromLeg + 2) return;
    for (let j = 1; j < leg.points.length; j++) {
      const d = pointSegmentDistM(pos, leg.points[j - 1], leg.points[j]);
      if (d < bestDist) {
        bestDist = d;
        bestIdx = i;
      }
    }
  });
  return bestIdx;
}
