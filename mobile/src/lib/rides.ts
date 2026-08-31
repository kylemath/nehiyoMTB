/**
 * Ride logging: foreground GPS tracking, GPX export, photo-time sync.
 *
 * Rides are saved locally; uploading the GPX (with the user's chosen share
 * level) is opt-in per ride. 'contribute' rides go only to the trail-mapping
 * team to improve Edmonton trail maps.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';

import { ShareLevel } from '@/constants/brand';
import { LatLng, haversineM } from '@/lib/geo';
import { LocalCapture } from '@/lib/captures';
import { supabase } from '@/lib/supabase';

const STORE_KEY = 'etm.rides.v1';

export type TrackPoint = { lat: number; lng: number; ele: number | null; t: string };

export type LocalRide = {
  id: string;
  startedAt: string;
  endedAt: string | null;
  points: TrackPoint[];
  distanceM: number;
  shareLevel: ShareLevel;
  uploaded: boolean;
};

export async function listRides(): Promise<LocalRide[]> {
  const raw = await AsyncStorage.getItem(STORE_KEY);
  return raw ? (JSON.parse(raw) as LocalRide[]) : [];
}

async function persist(rides: LocalRide[]) {
  await AsyncStorage.setItem(STORE_KEY, JSON.stringify(rides));
}

export async function saveRide(ride: LocalRide) {
  const rides = await listRides();
  const idx = rides.findIndex((r) => r.id === ride.id);
  if (idx >= 0) rides[idx] = ride;
  else rides.unshift(ride);
  await persist(rides);
}

export class RideRecorder {
  private subscription: Location.LocationSubscription | null = null;
  private listeners = new Set<(ride: LocalRide) => void>();
  ride: LocalRide | null = null;
  onUpdate: ((ride: LocalRide) => void) | null = null;

  addListener(fn: (ride: LocalRide) => void): () => void {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  }

  private notify(ride: LocalRide) {
    this.onUpdate?.(ride);
    for (const fn of this.listeners) fn(ride);
  }

  async start(): Promise<void> {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') throw new Error('Location permission is required to record a ride.');

    this.ride = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      startedAt: new Date().toISOString(),
      endedAt: null,
      points: [],
      distanceM: 0,
      shareLevel: 'private',
      uploaded: false,
    };

    this.subscription = await Location.watchPositionAsync(
      { accuracy: Location.Accuracy.BestForNavigation, timeInterval: 2000, distanceInterval: 3 },
      (loc) => {
        if (!this.ride) return;
        const pt: TrackPoint = {
          lat: loc.coords.latitude,
          lng: loc.coords.longitude,
          ele: loc.coords.altitude ?? null,
          t: new Date(loc.timestamp).toISOString(),
        };
        const prev = this.ride.points[this.ride.points.length - 1];
        if (prev) {
          this.ride.distanceM += haversineM(
            { latitude: prev.lat, longitude: prev.lng },
            { latitude: pt.lat, longitude: pt.lng },
          );
        }
        this.ride.points.push(pt);
        this.notify(this.ride);
      },
    );
  }

  async stop(): Promise<LocalRide | null> {
    this.subscription?.remove();
    this.subscription = null;
    if (this.ride) {
      this.ride.endedAt = new Date().toISOString();
      await saveRide(this.ride);
    }
    const finished = this.ride;
    this.ride = null;
    return finished;
  }
}

/** App-wide recorder so the Ride tab and live navigation observe one recording. */
export const sharedRecorder = new RideRecorder();

export function rideToGpx(ride: LocalRide, name = 'Ride'): string {
  const pts = ride.points
    .map(
      (p) =>
        `      <trkpt lat="${p.lat.toFixed(6)}" lon="${p.lng.toFixed(6)}">` +
        (p.ele != null ? `<ele>${p.ele.toFixed(1)}</ele>` : '') +
        `<time>${p.t}</time></trkpt>`,
    )
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="EdmontonTrailMaps" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${name}</name>
    <trkseg>
${pts}
    </trkseg>
  </trk>
</gpx>
`;
}

export type PhotoSync = {
  captureId: string;
  takenAt: string;
  /** Nearest GPS fix to the photo time, if the ride covers it. */
  matchedPoint: TrackPoint | null;
  /** Seconds spent essentially stationary around the photo time —
   * an estimate of how long the photo stop took. */
  stationaryS: number;
};

/**
 * Sync photo timestamps with the GPS track: find the fix nearest each photo
 * time, and measure the stationary window around it (speed < 1 m/s). This
 * lets trail times separate riding speed from photo-taking overhead.
 */
export function syncPhotosWithRide(ride: LocalRide, captures: LocalCapture[]): PhotoSync[] {
  const times = ride.points.map((p) => new Date(p.t).getTime());
  return captures
    .filter((c) => {
      const t = new Date(c.takenAt).getTime();
      return (
        times.length > 0 &&
        t >= times[0] - 60_000 &&
        t <= times[times.length - 1] + 60_000
      );
    })
    .map((c) => {
      const t = new Date(c.takenAt).getTime();
      let bestIdx = 0;
      for (let i = 1; i < times.length; i++) {
        if (Math.abs(times[i] - t) < Math.abs(times[bestIdx] - t)) bestIdx = i;
      }
      // Expand outward while movement stays under ~1 m/s.
      let lo = bestIdx;
      let hi = bestIdx;
      const slow = (i: number, j: number) => {
        const d = haversineM(
          { latitude: ride.points[i].lat, longitude: ride.points[i].lng },
          { latitude: ride.points[j].lat, longitude: ride.points[j].lng },
        );
        const dt = Math.abs(times[j] - times[i]) / 1000;
        return dt > 0 && d / dt < 1;
      };
      while (lo > 0 && slow(lo - 1, lo)) lo--;
      while (hi < times.length - 1 && slow(hi, hi + 1)) hi++;
      return {
        captureId: c.id,
        takenAt: c.takenAt,
        matchedPoint: ride.points[bestIdx] ?? null,
        stationaryS: Math.round((times[hi] - times[lo]) / 1000),
      };
    });
}

export async function uploadRide(ride: LocalRide, userId: string): Promise<void> {
  const gpxPath = `${userId}/${ride.id}.gpx`;
  const gpx = rideToGpx(ride, `Ride ${ride.startedAt.slice(0, 10)}`);
  const { error: storageError } = await supabase.storage
    .from('gpx')
    .upload(gpxPath, new Blob([gpx], { type: 'application/gpx+xml' }), { upsert: true });
  if (storageError) throw storageError;

  const { error } = await supabase.from('rides').insert({
    user_id: userId,
    started_at: ride.startedAt,
    ended_at: ride.endedAt,
    distance_m: Math.round(ride.distanceM),
    gpx_path: gpxPath,
    share_level: ride.shareLevel,
  });
  if (error) throw error;

  ride.uploaded = true;
  await saveRide(ride);
}

export type { LatLng };
