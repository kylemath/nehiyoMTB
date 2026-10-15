import { useSyncExternalStore } from 'react';

import rawData from '@/data/trails.json';
import { trailIcons } from '@/data/trail-assets';
import { LatLng } from '@/lib/geo';

export type Trail = {
  id: string;
  signNumber: number | null;
  title: string;
  englishName: string | null;
  creeName: string | null;
  creeSyllabics: string | null;
  description: string | null;
  status: string;
  accentColor: string;
  /** Physical sign colourway (filament colours), e.g. ['white','black','red']. */
  colors: string[];
  hasIcon: boolean;
  trailforksUrl: string | null;
  /** Trailforks rating: 'green' | 'blue' | 'black' | 'dblblack', or null. */
  difficulty: string | null;
  start: { lat: number | null; lng: number | null } | null;
  end: { lat: number | null; lng: number | null } | null;
  lengthM: number | null;
  track: [number, number][];
  /** Remote sign icon on the website, used when no icon is bundled yet
   * (signs added to the catalogue after this build). */
  iconUrl?: string | null;
  /** Shopify listing for the physical sign (from the catalogue's `shopify`
   * block), or null when it isn't for sale yet. */
  shop?: { variantId: string; priceCAD: number | null } | null;
};

/** STL-rendered sign icon (same art as the web app), or null if none yet.
 * This is the one piece of sign artwork the app ships per trail — used for
 * map markers, list rows, and trail pages. */
export function trailIcon(id: string): number | { uri: string } | null {
  const bundled = trailIcons[id];
  if (bundled != null) return bundled;
  const url = trailById(id)?.iconUrl;
  return url ? { uri: url } : null;
}

export type SignKind = 'start' | 'end';

export type TrailSign = {
  id: string; // `${trailId}:${kind}` — matches public.signs in the database
  trailId: string;
  kind: SignKind;
  coordinate: LatLng;
  basePoints: number;
};

// The trail set is live: it starts from the bundled snapshot and is replaced
// in place by applyTrails() once the website catalogue loads (see
// lib/catalogue.ts). The arrays keep their identity so module-level imports
// stay valid; components that render trail lists call useTrailsVersion() so
// they re-render when the set changes.
export const trails: Trail[] = [];
export const mappedTrails: Trail[] = [];
export const allSigns: TrailSign[] = [];

let version = 0;
const listeners = new Set<() => void>();

export function applyTrails(next: Trail[]) {
  trails.splice(0, trails.length, ...next);
  mappedTrails.splice(
    0,
    mappedTrails.length,
    ...next.filter((t) => t.track.length > 1 && t.start?.lat != null),
  );
  allSigns.splice(0, allSigns.length, ...mappedTrails.flatMap(signsFor));
  version += 1;
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Bumps whenever the live catalogue replaces the trail set. */
export function useTrailsVersion(): number {
  return useSyncExternalStore(subscribe, () => version, () => version);
}

export function trailById(id: string): Trail | undefined {
  return trails.find((t) => t.id === id);
}

export function trackToLatLng(track: [number, number][]): LatLng[] {
  return track.map(([lat, lng]) => ({ latitude: lat, longitude: lng }));
}

export function displayName(t: Trail): string {
  return t.englishName && t.englishName !== t.title
    ? `${t.title} (${t.englishName})`
    : t.title;
}

function signsFor(t: Trail): TrailSign[] {
  const signs: TrailSign[] = [];
  if (t.start?.lat != null && t.start.lng != null) {
    signs.push({
      id: `${t.id}:start`,
      trailId: t.id,
      kind: 'start',
      coordinate: { latitude: t.start.lat, longitude: t.start.lng },
      basePoints: 10,
    });
  }
  if (t.end?.lat != null && t.end.lng != null) {
    signs.push({
      id: `${t.id}:end`,
      trailId: t.id,
      kind: 'end',
      coordinate: { latitude: t.end.lat, longitude: t.end.lng },
      basePoints: 10,
    });
  }
  return signs;
}

export function signById(id: string): TrailSign | undefined {
  return allSigns.find((s) => s.id === id);
}

applyTrails((rawData as { trails: Trail[] }).trails);
