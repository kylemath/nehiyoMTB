/**
 * Sign captures: the treasure hunt.
 *
 * Captures are always saved locally first (offline-first); upload to the
 * backend happens only when signed in, and only at the share level the user
 * picked. Points are estimated locally and re-scored authoritatively by the
 * database trigger on upload.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import { ShareLevel } from '@/constants/brand';
import { haversineM } from '@/lib/geo';
import { supabase } from '@/lib/supabase';
import { TrailSign, allSigns, signById } from '@/lib/trails';

const STORE_KEY = 'etm.captures.v1';

/** Must match public.signs.capture_radius_m default in the database. */
export const CAPTURE_RADIUS_M = 75;

export type LocalCapture = {
  id: string;
  signId: string;
  trailId: string;
  kind: 'start' | 'end';
  takenAt: string; // ISO — photo timestamp, the game clock
  lat: number | null;
  lng: number | null;
  accuracyM: number | null;
  photoUri: string | null; // local file; may stay on-device forever (private)
  shareLevel: ShareLevel;
  verified: boolean;
  points: number;
  uploaded: boolean;
};

export async function listCaptures(): Promise<LocalCapture[]> {
  const raw = await AsyncStorage.getItem(STORE_KEY);
  return raw ? (JSON.parse(raw) as LocalCapture[]) : [];
}

async function persist(captures: LocalCapture[]) {
  await AsyncStorage.setItem(STORE_KEY, JSON.stringify(captures));
}

export function nearestSign(lat: number, lng: number): { sign: TrailSign; distanceM: number } | null {
  let best: { sign: TrailSign; distanceM: number } | null = null;
  for (const sign of allSigns) {
    const d = haversineM({ latitude: lat, longitude: lng }, sign.coordinate);
    if (!best || d < best.distanceM) best = { sign, distanceM: d };
  }
  return best;
}

export async function saveCapture(input: {
  signId: string;
  takenAt: Date;
  lat: number | null;
  lng: number | null;
  accuracyM: number | null;
  photoUri: string | null;
  shareLevel: ShareLevel;
}): Promise<LocalCapture> {
  const sign = signById(input.signId);
  if (!sign) throw new Error(`Unknown sign ${input.signId}`);

  const verified =
    input.lat != null &&
    input.lng != null &&
    haversineM({ latitude: input.lat, longitude: input.lng }, sign.coordinate) <=
      CAPTURE_RADIUS_M;

  const captures = await listCaptures();
  const sameDay = captures.some(
    (c) =>
      c.signId === input.signId &&
      c.takenAt.slice(0, 10) === input.takenAt.toISOString().slice(0, 10) &&
      c.points > 0,
  );

  const capture: LocalCapture = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    signId: sign.id,
    trailId: sign.trailId,
    kind: sign.kind,
    takenAt: input.takenAt.toISOString(),
    lat: input.lat,
    lng: input.lng,
    accuracyM: input.accuracyM,
    photoUri: input.photoUri,
    shareLevel: input.shareLevel,
    verified,
    points: verified && !sameDay ? sign.basePoints : 0,
    uploaded: false,
  };
  await persist([capture, ...captures]);
  return capture;
}

export async function setCaptureShareLevel(id: string, shareLevel: ShareLevel) {
  const captures = await listCaptures();
  const c = captures.find((x) => x.id === id);
  if (c) {
    c.shareLevel = shareLevel;
    c.uploaded = false; // re-sync with the new level
    await persist(captures);
  }
}

export function localScore(captures: LocalCapture[]) {
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setHours(0, 0, 0, 0);
  weekStart.setDate(weekStart.getDate() - ((weekStart.getDay() + 6) % 7)); // Monday

  let overall = 0;
  let weekly = 0;
  let weekend = 0;
  for (const c of captures) {
    overall += c.points;
    const t = new Date(c.takenAt);
    if (t >= weekStart) {
      weekly += c.points;
      const dow = t.getDay();
      if (dow === 0 || dow === 6) weekend += c.points;
    }
  }
  const signsCollected = new Set(captures.filter((c) => c.points > 0).map((c) => c.signId));
  return { overall, weekly, weekend, signsCollected };
}

export type TrailTimeEstimate = {
  trailId: string;
  startCapture: LocalCapture;
  endCapture: LocalCapture;
  elapsedS: number;
};

/** Pair start+end captures of the same trail on the same day into ride times.
 * Photo timestamps are the clock, so nobody needs to upload live. */
export function pairTrailTimes(captures: LocalCapture[]): TrailTimeEstimate[] {
  const out: TrailTimeEstimate[] = [];
  const byTrailDay = new Map<string, LocalCapture[]>();
  for (const c of captures) {
    const key = `${c.trailId}|${c.takenAt.slice(0, 10)}`;
    byTrailDay.set(key, [...(byTrailDay.get(key) ?? []), c]);
  }
  for (const group of byTrailDay.values()) {
    const starts = group.filter((c) => c.kind === 'start').sort((a, b) => a.takenAt.localeCompare(b.takenAt));
    const ends = group.filter((c) => c.kind === 'end').sort((a, b) => a.takenAt.localeCompare(b.takenAt));
    for (const s of starts) {
      const e = ends.find((x) => x.takenAt > s.takenAt);
      if (e) {
        out.push({
          trailId: s.trailId,
          startCapture: s,
          endCapture: e,
          elapsedS: Math.round((new Date(e.takenAt).getTime() - new Date(s.takenAt).getTime()) / 1000),
        });
        ends.splice(ends.indexOf(e), 1);
      }
    }
  }
  return out.sort((a, b) => b.startCapture.takenAt.localeCompare(a.startCapture.takenAt));
}

/** Upload a capture (and its photo, unless the user kept it on-device).
 * Private captures upload metadata + photo readable only by the owner;
 * 'contribute' is maintainer-only; 'public' joins the sign's gallery. */
export async function uploadCapture(capture: LocalCapture, userId: string): Promise<void> {
  let photoPath: string | null = null;

  if (capture.photoUri) {
    photoPath = `${userId}/${capture.id}.jpg`;
    const response = await fetch(capture.photoUri);
    const body = await response.arrayBuffer();
    const { error: storageError } = await supabase.storage
      .from('photos')
      .upload(photoPath, body, { contentType: 'image/jpeg', upsert: true });
    if (storageError) throw storageError;
  }

  const { error } = await supabase.from('sign_captures').insert({
    user_id: userId,
    sign_id: capture.signId,
    captured_at: capture.takenAt,
    device_lat: capture.lat,
    device_lng: capture.lng,
    accuracy_m: capture.accuracyM,
    photo_path: photoPath,
    share_level: capture.shareLevel,
  });
  if (error) throw error;

  const captures = await listCaptures();
  const c = captures.find((x) => x.id === capture.id);
  if (c) {
    c.uploaded = true;
    await persist(captures);
  }
}
