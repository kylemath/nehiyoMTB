import rawData from '@/data/trails.json';
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
  trailforksUrl: string | null;
  start: { lat: number | null; lng: number | null } | null;
  end: { lat: number | null; lng: number | null } | null;
  lengthM: number | null;
  track: [number, number][];
};

export type SignKind = 'start' | 'end';

export type TrailSign = {
  id: string; // `${trailId}:${kind}` — matches public.signs in the database
  trailId: string;
  kind: SignKind;
  coordinate: LatLng;
  basePoints: number;
};

export const trails: Trail[] = (rawData as { trails: Trail[] }).trails;

export const mappedTrails = trails.filter(
  (t) => t.track.length > 1 && t.start?.lat != null,
);

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

export const allSigns: TrailSign[] = mappedTrails.flatMap((t) => {
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
});

export function signById(id: string): TrailSign | undefined {
  return allSigns.find((s) => s.id === id);
}
