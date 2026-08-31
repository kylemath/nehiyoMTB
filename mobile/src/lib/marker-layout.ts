/**
 * Marker de-overlap: nudge adjacent sign markers apart so they don't cover
 * each other (e.g. the end sign of one trail at the start sign of the next).
 *
 * Works in screen-pixel space for the current map region, pushes overlapping
 * rectangles apart along the axis of least penetration, and converts the
 * result back to coordinates. Displacement is capped so far-out zoom levels
 * degrade to slight overlap instead of scattering markers across the valley.
 */

import { LatLng } from '@/lib/geo';

export type MarkerItem = {
  key: string;
  base: LatLng;
  width: number;  // px
  height: number; // px
};

export type Region = LatLng & { latitudeDelta: number; longitudeDelta: number };

const GAP = 2;          // px breathing room between badges
const MAX_ITERS = 40;

export function spreadMarkers(
  items: MarkerItem[],
  region: Region,
  screen: { width: number; height: number },
): Map<string, LatLng> {
  const pxPerLat = screen.height / region.latitudeDelta;
  const pxPerLng = screen.width / region.longitudeDelta;

  const pts = items.map((it) => ({
    it,
    x: it.base.longitude * pxPerLng,
    y: -it.base.latitude * pxPerLat,
    shifted: 0,
  }));

  const maxShift = (it: MarkerItem) => 1.6 * Math.max(it.width, it.height);

  for (let iter = 0; iter < MAX_ITERS; iter++) {
    let moved = false;
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const a = pts[i];
        const b = pts[j];
        const minX = (a.it.width + b.it.width) / 2 + GAP;
        const minY = (a.it.height + b.it.height) / 2 + GAP;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        if (Math.abs(dx) >= minX || Math.abs(dy) >= minY) continue;

        // Identical positions: pick a stable direction from the pair index.
        if (dx === 0 && dy === 0) {
          const angle = ((i * 7 + j * 13) % 8) * (Math.PI / 4);
          dx = Math.cos(angle) * 0.01;
          dy = Math.sin(angle) * 0.01;
        }

        const overlapX = minX - Math.abs(dx);
        const overlapY = minY - Math.abs(dy);
        let pushX = 0;
        let pushY = 0;
        if (overlapX < overlapY) pushX = (overlapX / 2 + 0.5) * Math.sign(dx || 1);
        else pushY = (overlapY / 2 + 0.5) * Math.sign(dy || 1);

        if (a.shifted < maxShift(a.it)) {
          a.x -= pushX;
          a.y -= pushY;
          a.shifted += Math.abs(pushX) + Math.abs(pushY);
          moved = true;
        }
        if (b.shifted < maxShift(b.it)) {
          b.x += pushX;
          b.y += pushY;
          b.shifted += Math.abs(pushX) + Math.abs(pushY);
          moved = true;
        }
      }
    }
    if (!moved) break;
  }

  const out = new Map<string, LatLng>();
  for (const p of pts) {
    out.set(p.it.key, { latitude: -p.y / pxPerLat, longitude: p.x / pxPerLng });
  }
  return out;
}
