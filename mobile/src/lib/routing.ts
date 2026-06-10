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

import { LatLng, haversineM } from '@/lib/geo';
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
  const lengthM = trail.lengthM ?? 0;
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
