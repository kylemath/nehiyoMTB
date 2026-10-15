/**
 * Ride logging: GPS tracking that keeps running with the screen locked,
 * GPX export, photo-time sync.
 *
 * On iOS/Android the recorder uses a background location task (an Android
 * foreground-service notification / the iOS blue location pill), so the
 * track keeps filling while the phone is in a pocket. The in-progress ride is
 * saved as points arrive, so if the OS kills the app the ride survives and
 * recording resumes (or is finalised) on the next launch. In a browser,
 * background GPS is impossible; the recorder keeps the screen awake instead.
 *
 * Rides are saved locally; uploading the GPX (with the user's chosen share
 * level) is opt-in per ride. 'contribute' rides go only to the trail-mapping
 * team to improve Edmonton trail maps.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { Platform } from 'react-native';

import { ShareLevel } from '@/constants/brand';
import { LatLng, haversineM } from '@/lib/geo';
import { LocalCapture } from '@/lib/captures';
import { supabase } from '@/lib/supabase';

const STORE_KEY = 'etm.rides.v1';
/** The ride being recorded right now, saved as points arrive. */
const ACTIVE_KEY = 'etm.activeRide.v1';
const RIDE_TASK = 'nehiyomtb-ride-location';
/** Write the active ride at most this often (plus on stop). */
const PERSIST_EVERY_MS = 5000;

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

const isNative = Platform.OS === 'ios' || Platform.OS === 'android';

/** Screen wake lock for the browser build (no background GPS on the web). */
type WakeLockSentinel = { release: () => Promise<void> };
async function requestWakeLock(): Promise<WakeLockSentinel | null> {
  const nav = (globalThis as { navigator?: { wakeLock?: { request: (t: 'screen') => Promise<WakeLockSentinel> } } })
    .navigator;
  try {
    return (await nav?.wakeLock?.request('screen')) ?? null;
  } catch {
    return null;
  }
}

export class RideRecorder {
  private subscription: Location.LocationSubscription | null = null;
  private wakeLock: WakeLockSentinel | null = null;
  private listeners = new Set<(ride: LocalRide) => void>();
  private lastPersist = 0;
  /** True when points arrive from the background task rather than a watch. */
  private background = false;
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

  private async persistActive(force = false) {
    if (!this.ride) return;
    const now = Date.now();
    if (!force && now - this.lastPersist < PERSIST_EVERY_MS) return;
    this.lastPersist = now;
    await AsyncStorage.setItem(ACTIVE_KEY, JSON.stringify(this.ride));
  }

  /** Append fixes (from the watch or the background task) to the ride. */
  async ingest(locations: Location.LocationObject[]) {
    if (!this.ride) {
      // Woken by the OS after the app was killed: pick the ride back up.
      const raw = await AsyncStorage.getItem(ACTIVE_KEY);
      if (!raw) return;
      this.ride = JSON.parse(raw) as LocalRide;
      this.background = true;
    }
    const ride = this.ride;
    for (const loc of locations) {
      const pt: TrackPoint = {
        lat: loc.coords.latitude,
        lng: loc.coords.longitude,
        ele: loc.coords.altitude ?? null,
        t: new Date(loc.timestamp).toISOString(),
      };
      const prev = ride.points[ride.points.length - 1];
      if (prev) {
        // Background batches can repeat or reorder fixes; keep time order.
        if (pt.t <= prev.t) continue;
        ride.distanceM += haversineM(
          { latitude: prev.lat, longitude: prev.lng },
          { latitude: pt.lat, longitude: pt.lng },
        );
      }
      ride.points.push(pt);
    }
    this.notify(ride);
    await this.persistActive();
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
    await this.persistActive(true);

    // "Allow all the time" lets the track keep filling with the screen off.
    // If the rider declines, fall back to recording while the app is open.
    let background = false;
    if (isNative) {
      try {
        background = (await Location.requestBackgroundPermissionsAsync()).status === 'granted';
      } catch {
        background = false;
      }
    }
    this.background = background;

    if (background) {
      await Location.startLocationUpdatesAsync(RIDE_TASK, {
        accuracy: Location.Accuracy.BestForNavigation,
        timeInterval: 2000,
        distanceInterval: 3,
        activityType: Location.ActivityType.Fitness,
        pausesUpdatesAutomatically: false,
        showsBackgroundLocationIndicator: true,
        foregroundService: {
          notificationTitle: 'Recording your ride',
          notificationBody: 'NehiyoMTB is logging your GPS track.',
          notificationColor: '#1E5E46',
          killServiceOnDestroy: false,
        },
      });
    } else {
      this.subscription = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.BestForNavigation, timeInterval: 2000, distanceInterval: 3 },
        (loc) => {
          this.ingest([loc]);
        },
      );
      if (!isNative) this.wakeLock = await requestWakeLock();
    }
  }

  async stop(): Promise<LocalRide | null> {
    this.subscription?.remove();
    this.subscription = null;
    await this.wakeLock?.release().catch(() => {});
    this.wakeLock = null;
    if (isNative && (await Location.hasStartedLocationUpdatesAsync(RIDE_TASK).catch(() => false))) {
      await Location.stopLocationUpdatesAsync(RIDE_TASK);
    }
    this.background = false;
    if (this.ride) {
      this.ride.endedAt = new Date().toISOString();
      await saveRide(this.ride);
    }
    await AsyncStorage.removeItem(ACTIVE_KEY);
    const finished = this.ride;
    this.ride = null;
    return finished;
  }

  /**
   * Call once at app launch. If a ride was in progress when the app was
   * closed or killed: keep recording when the background task is still
   * running, otherwise save what was recorded so it is never lost.
   */
  async restore(): Promise<void> {
    if (this.ride) return;
    const raw = await AsyncStorage.getItem(ACTIVE_KEY);
    if (!raw) return;
    const active = JSON.parse(raw) as LocalRide;
    const running =
      isNative && (await Location.hasStartedLocationUpdatesAsync(RIDE_TASK).catch(() => false));
    if (running) {
      this.ride = active;
      this.background = true;
      this.notify(active);
      return;
    }
    if (active.points.length > 1) {
      active.endedAt = active.points[active.points.length - 1].t;
      await saveRide(active);
    }
    await AsyncStorage.removeItem(ACTIVE_KEY);
  }
}

/** App-wide recorder so the Ride tab and live navigation observe one recording. */
export const sharedRecorder = new RideRecorder();

// Background fixes are delivered here, even when the app was relaunched by
// the OS without any screen open. Must be defined at module load.
if (isNative) {
  TaskManager.defineTask<{ locations: Location.LocationObject[] }>(RIDE_TASK, async ({ data, error }) => {
    if (error || !data?.locations?.length) return;
    await sharedRecorder.ingest(data.locations);
  });
}

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
<gpx version="1.1" creator="NehiyoMTB" xmlns="http://www.topografix.com/GPX/1/1">
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
