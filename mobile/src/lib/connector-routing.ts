/**
 * Connector refinement: swap the route builder's straight "as the crow flies"
 * connector legs for real bike paths from the public FOSSGIS Valhalla router
 * (OSM-based, no API key). Failures degrade gracefully back to straight lines.
 */

import { LatLng, haversineM, pathLengthM } from '@/lib/geo';
import { BikeRoute, RouteLeg } from '@/lib/routing';

export type BikePath = { points: LatLng[]; distanceM: number };

const VALHALLA_URL = 'https://valhalla1.openstreetmap.de/route';
const TIMEOUT_MS = 8000;
const MIN_CONNECTOR_M = 30;

const cache = new Map<string, BikePath>();

function cacheKey(from: LatLng, to: LatLng): string {
  const r = (n: number) => n.toFixed(5);
  return `${r(from.latitude)},${r(from.longitude)}|${r(to.latitude)},${r(to.longitude)}`;
}

/** Decode a Valhalla-encoded polyline (standard algorithm, precision 6). */
function decodePolyline6(encoded: string): LatLng[] {
  const points: LatLng[] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;
  while (index < encoded.length) {
    let result = 0;
    let shift = 0;
    let byte: number;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lat += result & 1 ? ~(result >> 1) : result >> 1;
    result = 0;
    shift = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lng += result & 1 ? ~(result >> 1) : result >> 1;
    points.push({ latitude: lat / 1e6, longitude: lng / 1e6 });
  }
  return points;
}

/** Bike path between two points via the public Valhalla router.
 * Returns null on any failure (offline, timeout, bad response). */
export async function fetchBikePath(from: LatLng, to: LatLng): Promise<BikePath | null> {
  const key = cacheKey(from, to);
  const cached = cache.get(key);
  if (cached) return cached;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(VALHALLA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        locations: [
          { lat: from.latitude, lon: from.longitude },
          { lat: to.latitude, lon: to.longitude },
        ],
        costing: 'bicycle',
        costing_options: {
          bicycle: { bicycle_type: 'Mountain', use_roads: 0.3, use_hills: 0.7 },
        },
      }),
      signal: controller.signal,
    });
    if (!res.ok) return null;
    const data = await res.json();
    const shape: unknown = data?.trip?.legs?.[0]?.shape;
    const lengthKm: unknown = data?.trip?.summary?.length;
    if (typeof shape !== 'string' || typeof lengthKm !== 'number') return null;

    const points = decodePolyline6(shape);
    if (points.length < 2) return null;
    const distanceM = lengthKm * 1000;

    // Guard against router detours through unmapped areas.
    const straightM = haversineM(from, to);
    if (pathLengthM(points) > straightM * 4 + 500) return null;

    const path: BikePath = { points, distanceM };
    cache.set(key, path);
    return path;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** Snap-correct: keep refined connectors visually attached to trail ends by
 * pinning the exact original endpoints when the routed path snaps away. */
function pinEndpoints(points: LatLng[], from: LatLng, to: LatLng): LatLng[] {
  const out = [...points];
  if (haversineM(out[0], from) > 1) out.unshift(from);
  if (haversineM(out[out.length - 1], to) > 1) out.push(to);
  return out;
}

/** Replace every connector leg's straight line with a real bike path.
 * Trail legs are untouched. Returns the rebuilt route, or null when nothing
 * could be improved (e.g. fully offline) so the caller keeps the original. */
export async function refineRouteConnectors(route: BikeRoute): Promise<BikeRoute | null> {
  const legs: RouteLeg[] = await Promise.all(
    route.legs.map(async (leg): Promise<RouteLeg> => {
      if (leg.type !== 'connector' || leg.distanceM < MIN_CONNECTOR_M) return leg;
      const from = leg.points[0];
      const to = leg.points[leg.points.length - 1];
      const path = await fetchBikePath(from, to);
      if (!path) return leg;
      return {
        type: 'connector',
        points: pinEndpoints(path.points, from, to),
        distanceM: path.distanceM,
      };
    }),
  );

  if (legs.every((leg, i) => leg === route.legs[i])) return null;

  let connectorM = 0;
  for (const leg of legs) {
    if (leg.type === 'connector') connectorM += leg.distanceM;
  }
  return {
    ...route,
    legs,
    connectorM,
    totalM: route.trailM + connectorM,
  };
}
