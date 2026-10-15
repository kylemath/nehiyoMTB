// Live trail data from the website.
//
// docs/catalogue.json on nehiyomtb.ca is the single source of truth for the
// sign set (the catalogue editor and sign tools write it). The app ships a
// bundled snapshot (src/data/trails.json) for first launch and offline use,
// then on every launch:
//   1. applies the last catalogue it cached on this device, and
//   2. fetches the current catalogue and applies + caches it.
// So signs pushed to the site show up in the app without a new build.
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

import { haversineM } from '@/lib/geo';
import { Trail, applyTrails } from '@/lib/trails';

const CACHE_KEY = 'catalogue:trails:v1';
const FETCH_TIMEOUT_MS = 10000;
/** Same decimation as tools/export_trails_for_app.py keeps polylines light. */
const MAX_TRACK_POINTS = 200;

/** Root of the website, with a trailing slash. On the web build (served at
 * <site>/app) this is the page's own origin so previews and forks work. */
export function siteUrl(): string {
  const env = process.env.EXPO_PUBLIC_SITE_URL;
  if (env) return env.endsWith('/') ? env : `${env}/`;
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const { hostname, origin } = window.location;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') return `${origin}/`;
  }
  return 'https://nehiyomtb.ca/';
}

type CatalogueModel = {
  id: string;
  signNumber?: number | null;
  title?: string;
  englishName?: string | null;
  creeName?: string | null;
  creeSyllabics?: string | null;
  description?: string | null;
  status?: string;
  colors?: string[];
  shopify?: { variantId?: string | null; priceCAD?: number | null; available?: boolean };
  pageContent?: {
    accentColor?: string;
    trailforks?: {
      track?: [number, number][];
      mapCoords?: { lat: number; lng: number };
      mapEndCoords?: { lat: number; lng: number };
      trailUrl?: string;
      difficulty?: string;
      iconSrc?: string;
    };
  };
};

function decimate<T>(track: T[], max: number): T[] {
  if (track.length <= max) return track;
  const step = (track.length - 1) / (max - 1);
  return Array.from({ length: max }, (_, i) => track[Math.round(i * step)]);
}

function trackLengthM(track: [number, number][]): number {
  let m = 0;
  for (let i = 0; i < track.length - 1; i++) {
    m += haversineM(
      { latitude: track[i][0], longitude: track[i][1] },
      { latitude: track[i + 1][0], longitude: track[i + 1][1] },
    );
  }
  return m;
}

/** Catalogue paths are relative to a sign page, e.g. '../assets/x/y.png'. */
function docsUrl(src: string | undefined): string | null {
  if (!src) return null;
  const path = src.replace(/^(\.\.\/|\.\/)+/, '');
  return encodeURI(siteUrl() + path);
}

function shopFrom(block: CatalogueModel['shopify']): Trail['shop'] {
  if (!block?.variantId || block.available === false) return null;
  return { variantId: String(block.variantId), priceCAD: block.priceCAD ?? null };
}

/** Mirrors the trail shape written by tools/export_trails_for_app.py. */
export function trailsFromCatalogue(catalogue: { models?: CatalogueModel[] }): Trail[] {
  return (catalogue.models ?? []).map((model) => {
    const page = model.pageContent ?? {};
    const tf = page.trailforks ?? {};
    const track = (tf.track ?? []).map(
      ([lat, lng]) => [Math.round(lat * 1e6) / 1e6, Math.round(lng * 1e6) / 1e6] as [number, number],
    );
    const start = tf.mapCoords ?? (track.length ? { lat: track[0][0], lng: track[0][1] } : null);
    const last = track[track.length - 1];
    const end = tf.mapEndCoords ?? (last ? { lat: last[0], lng: last[1] } : null);
    const iconUrl = docsUrl(tf.iconSrc);
    return {
      id: model.id,
      signNumber: model.signNumber ?? null,
      title: model.title || model.id,
      englishName: model.englishName ?? null,
      creeName: model.creeName ?? null,
      creeSyllabics: model.creeSyllabics ?? null,
      description: model.description ?? null,
      status: model.status ?? 'published',
      accentColor: page.accentColor || '#1f6f54',
      colors: model.colors ?? [],
      hasIcon: Boolean(iconUrl),
      trailforksUrl: tf.trailUrl ?? null,
      difficulty: tf.difficulty ?? null,
      start: start ? { lat: start.lat ?? null, lng: start.lng ?? null } : null,
      end: end ? { lat: end.lat ?? null, lng: end.lng ?? null } : null,
      lengthM: track.length > 1 ? Math.round(trackLengthM(track) * 10) / 10 : null,
      track: decimate(track, MAX_TRACK_POINTS),
      iconUrl,
      shop: shopFrom(model.shopify),
    };
  });
}

async function fetchCatalogue(): Promise<Trail[]> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(`${siteUrl()}catalogue.json`, {
      signal: controller.signal,
      cache: 'no-cache',
    });
    if (!res.ok) throw new Error(`catalogue.json: HTTP ${res.status}`);
    return trailsFromCatalogue(await res.json());
  } finally {
    clearTimeout(timer);
  }
}

let started = false;

/** Apply the cached catalogue, then refresh it from the website. Safe to call
 * more than once; only the first call does anything. Never throws: the
 * bundled snapshot stays in place if both cache and network fail. */
export async function syncCatalogue(): Promise<void> {
  if (started) return;
  started = true;
  try {
    const cached = await AsyncStorage.getItem(CACHE_KEY);
    if (cached) applyTrails(JSON.parse(cached) as Trail[]);
  } catch {
    // Corrupt or unavailable cache: keep the bundled snapshot.
  }
  try {
    const live = await fetchCatalogue();
    if (live.length === 0) return;
    const serialized = JSON.stringify(live);
    applyTrails(live);
    await AsyncStorage.setItem(CACHE_KEY, serialized);
  } catch {
    // Offline or the site is unreachable: cached/bundled data stays.
  }
}
