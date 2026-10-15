import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Dimensions,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import MapView, { MapPressEvent, Marker, Polyline } from '@/components/map';
import { RouteItinerary } from '@/components/route-itinerary';
import { IconPreloader, TrailIconBadge, TrailMarker, badgeBox } from '@/components/trail-icon';
import { Button, Chip, Row, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { refineRouteConnectors } from '@/lib/connector-routing';
import { LatLng, formatKm, haversineM, regionForPoints } from '@/lib/geo';
import { HomeLocation, pullHomeFromProfile, setHome as persistHome } from '@/lib/home';
import { MarkerItem, Region, spreadMarkers } from '@/lib/marker-layout';
import { sharedRecorder } from '@/lib/rides';
import {
  BikeRoute,
  buildBikeRoute,
  nearestLegIndex,
  offsetPath,
  routeChevrons,
} from '@/lib/routing';
import {
  Trail,
  displayName,
  mappedTrails,
  trackToLatLng,
  trailById,
  useTrailsVersion,
} from '@/lib/trails';

const DETOUR_OPTIONS_KM = [1, 2, 5, 10];

/** Zoomed out past this, sign markers hide and only trail lines show. */
const SIGNS_VISIBLE_MAX_DELTA = 0.14;

/** Base-layer cycle: map → satellite (hybrid keeps labels) → terrain relief.
 * Google Maps' terrain layer is Android-only; iOS cycles map → satellite. */
const MAP_TYPES = (
  Platform.OS === 'android'
    ? ['standard', 'hybrid', 'terrain']
    : ['standard', 'hybrid']
) as ('standard' | 'hybrid' | 'terrain')[];

const MAP_TYPE_META: Record<string, { label: string; icon: keyof typeof Ionicons.glyphMap }> = {
  standard: { label: 'Map', icon: 'map-outline' },
  hybrid: { label: 'Satellite', icon: 'earth-outline' },
  terrain: { label: 'Terrain', icon: 'trail-sign-outline' },
};

/** Coarse zoom level: markers are only re-laid-out when this changes, not
 * on every pan (the de-overlap layout doesn't depend on the map centre). */
function zoomBucket(latitudeDelta: number): number {
  return Math.round(Math.log2(latitudeDelta) * 4);
}

/** Marker height grows as you zoom in. Quantized into buckets so marker
 * views only re-render when the bucket actually changes. */
function markerSizeFor(latitudeDelta: number): number {
  if (latitudeDelta > 0.05) return 30;
  if (latitudeDelta > 0.02) return 40;
  if (latitudeDelta > 0.008) return 54;
  return 68;
}

/** mm:ss under an hour, h:mm:ss after. */
function formatElapsed(totalS: number): string {
  const h = Math.floor(totalS / 3600);
  const m = Math.floor((totalS % 3600) / 60);
  const s = totalS % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`;
}

type TrailMarkerItem = { key: string; trail: Trail; base: LatLng };

/** One icon per trail, anchored at the central point of its track. */
function buildTrailMarkers(): TrailMarkerItem[] {
  return mappedTrails.map((trail) => {
    const mid = trail.track[Math.floor(trail.track.length / 2)];
    const base = mid
      ? { latitude: mid[0], longitude: mid[1] }
      : { latitude: trail.start!.lat!, longitude: trail.start!.lng! };
    return { key: trail.id, trail, base };
  });
}

/** Start/end coordinates of a trail, deduped for loops. */
function trailEndpoints(trail: Trail): LatLng[] {
  const pts: LatLng[] = [];
  if (trail.start?.lat != null && trail.start.lng != null) {
    pts.push({ latitude: trail.start.lat, longitude: trail.start.lng });
  }
  if (trail.end?.lat != null && trail.end.lng != null) {
    const end = { latitude: trail.end.lat, longitude: trail.end.lng };
    if (pts.length === 0 || haversineM(pts[0], end) > 30) pts.push(end);
  }
  return pts;
}

/** A route start or destination: where it is and how the user chose it. */
type Endpoint = {
  kind: 'gps' | 'home' | 'pin' | 'trail';
  coord: LatLng;
  label: string;
  trailId?: string;
};

type RouteDraft = {
  from: Endpoint | null;
  to: Endpoint | null;
  detourKm: number;
  result: BikeRoute | null;
};

/** Trail as a destination. The coordinate starts at the trail's start sign,
 * but route building tries every endpoint and keeps whichever direction
 * makes the best route (see buildBestRoute). */
function trailDestEndpoint(trail: Trail): Endpoint | null {
  if (trail.start?.lat == null || trail.start.lng == null) return null;
  return {
    kind: 'trail',
    coord: { latitude: trail.start.lat, longitude: trail.start.lng },
    label: displayName(trail),
    trailId: trail.id,
  };
}

/** Build the route, trying both ends of a trail destination (riders don't
 * care which sign is officially "start") and keeping the best result. */
function buildBestRoute(
  fromCoord: LatLng,
  to: Endpoint,
  detourKm: number,
): { result: BikeRoute; destCoord: LatLng } {
  let candidates = [to.coord];
  if (to.kind === 'trail' && to.trailId) {
    const trail = trailById(to.trailId);
    const ends = trail ? trailEndpoints(trail) : [];
    if (ends.length > 0) candidates = ends;
  }
  let best: BikeRoute | null = null;
  let destCoord = to.coord;
  for (const c of candidates) {
    const r = buildBikeRoute(fromCoord, c, detourKm * 1000);
    if (!best || r.totalM < best.totalM) {
      best = r;
      destCoord = c;
    }
  }
  return { result: best!, destCoord };
}

export default function MapTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapView>(null);
  // Re-render when the live catalogue replaces the trail set.
  const trailsVersion = useTrailsVersion();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const trailMarkers = useMemo(() => buildTrailMarkers(), [trailsVersion]);
  // Track coordinates converted once per trail set, not on every render.
  const trailCoords = useMemo(
    () => new Map(mappedTrails.map((t) => [t.id, trackToLatLng(t.track)])),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [trailsVersion],
  );
  /** Flips once every sign icon has decoded (see IconPreloader). */
  const [iconsReady, setIconsReady] = useState(false);
  const [myLocation, setMyLocation] = useState<LatLng | null>(null);
  const [home, setHomeState] = useState<HomeLocation | null>(null);
  const [selected, setSelected] = useState<Trail | null>(null);
  const [routeMode, setRouteMode] = useState(false);
  /** Which endpoint the next map tap sets. */
  const [pinTarget, setPinTarget] = useState<'from' | 'to'>('to');
  const [mapTypeIdx, setMapTypeIdx] = useState(0);
  const mapType = MAP_TYPES[mapTypeIdx];
  const [draft, setDraft] = useState<RouteDraft>({
    from: null,
    to: null,
    detourKm: 2,
    result: null,
  });

  // Live navigation: follow the rider along the built route while the shared
  // ride recorder logs the GPS track ("route so far").
  const [navigating, setNavigating] = useState(false);
  const [navTrack, setNavTrack] = useState<LatLng[]>([]);
  const [navDistanceM, setNavDistanceM] = useState(0);
  const [activeLeg, setActiveLeg] = useState<number | null>(null);
  const navUnsub = useRef<(() => void) | null>(null);

  // GPS recording status: true whenever the shared recorder has an active
  // ride, whether it was started here (navigation) or on the Ride tab. Drives
  // the REC pill, the live position marker, and the ridden-path polyline.
  const [recording, setRecording] = useState(false);
  const [recordStartedAt, setRecordStartedAt] = useState<string | null>(null);

  const initialRegion = useMemo(() => {
    const region = regionForPoints(mappedTrails.flatMap((t) => trackToLatLng(t.track)));
    // Start within the sign-visible zoom range so icons show immediately.
    // The map fills the screen by expanding the shorter hinted dimension, so
    // on a tall phone the rendered latitudeDelta ≈ max(lat, lng / aspect).
    // Cap BOTH dimensions (accounting for screen aspect) so the rendered
    // latitudeDelta lands inside SIGNS_VISIBLE_MAX_DELTA.
    const cap = SIGNS_VISIBLE_MAX_DELTA * 0.85;
    const screen = Dimensions.get('window');
    const aspect = screen.width / screen.height;
    const latScale = cap / Math.max(region.latitudeDelta, 0.0001);
    const lngScale = (cap * aspect) / Math.max(region.longitudeDelta, 0.0001);
    const scale = Math.min(1, latScale, lngScale);
    return {
      ...region,
      latitudeDelta: region.latitudeDelta * scale,
      longitudeDelta: region.longitudeDelta * scale,
    };
  }, []);

  // The live camera region lives in a ref (read by zoom buttons and
  // navigation); React state only changes when the zoom bucket does, so
  // panning the map doesn't re-render this screen.
  const regionRef = useRef<Region>(initialRegion);
  const [zoomRegion, setZoomRegion] = useState<Region>(initialRegion);
  const onRegionChangeComplete = (r: Region) => {
    regionRef.current = r;
    setZoomRegion((prev) =>
      zoomBucket(prev.latitudeDelta) === zoomBucket(r.latitudeDelta) ? prev : r,
    );
  };
  const showSigns = zoomRegion.latitudeDelta <= SIGNS_VISIBLE_MAX_DELTA;
  const markerSize = markerSizeFor(zoomRegion.latitudeDelta);

  // Nudge overlapping sign badges apart for the current zoom.
  const displaced = useMemo(() => {
    if (!showSigns) return null;
    const screen = Dimensions.get('window');
    const items: MarkerItem[] = trailMarkers.map((m) => ({
      key: m.key,
      base: m.base,
      ...badgeBox(m.trail, markerSize),
    }));
    return spreadMarkers(items, zoomRegion, screen);
  }, [zoomRegion, markerSize, showSigns, trailMarkers]);

  // Route drawn ~5 m beside the underlying trail lines so both stay visible,
  // with chevrons along it showing the riding direction.
  const offsetLegs = useMemo(
    () =>
      draft.result
        ? draft.result.legs.map((leg) => ({ type: leg.type, points: offsetPath(leg.points) }))
        : null,
    [draft.result],
  );
  const chevrons = useMemo(
    () => (draft.result ? routeChevrons(draft.result) : []),
    [draft.result],
  );

  // While a route is active, trails on it stay accentuated and everything
  // else fades back. The destination trail counts as on-route even when the
  // budget didn't allow riding it.
  const routeActive = draft.result != null;
  const routeTrailIds = useMemo(() => {
    const ids = new Set(draft.result?.trailsUsed ?? []);
    if (draft.result && draft.to?.kind === 'trail' && draft.to.trailId) {
      ids.add(draft.to.trailId);
    }
    return ids;
  }, [draft.result, draft.to]);

  const ensureLocation = useCallback(async (): Promise<LatLng | null> => {
    if (myLocation) return myLocation;
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return null;
    const loc = await Location.getCurrentPositionAsync({});
    const coord = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
    setMyLocation(coord);
    return coord;
  }, [myLocation]);

  useEffect(() => {
    ensureLocation().catch(() => {});
    return () => {
      navUnsub.current?.();
      navUnsub.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // While this tab is focused, mirror the shared recorder: live track,
  // distance, and a 1 s elapsed-time tick. Works for rides started on the
  // Ride tab too, and notices when a ride is finished elsewhere.
  useFocusEffect(
    useCallback(() => {
      const sync = (ride: typeof sharedRecorder.ride = sharedRecorder.ride) => {
        setRecording(!!ride);
        setRecordStartedAt(ride?.startedAt ?? null);
        if (!ride) return;
        setNavTrack(ride.points.map((pt) => ({ latitude: pt.lat, longitude: pt.lng })));
        setNavDistanceM(ride.distanceM);
      };
      sync();
      // Track/distance update per GPS fix; the elapsed clock ticks inside
      // RecPill so the map isn't re-rendered every second. A slow poll
      // notices a ride finished on another tab.
      const unsub = sharedRecorder.addListener((ride) => sync(ride));
      const poll = setInterval(() => {
        if (!sharedRecorder.ride) sync(null);
      }, 3000);
      return () => {
        unsub();
        clearInterval(poll);
      };
    }, []),
  );

  // Saved home refreshes whenever the tab regains focus (it can change on
  // the profile screen or via "save pin as home" here).
  useFocusEffect(
    useCallback(() => {
      let active = true;
      pullHomeFromProfile()
        .then((h) => {
          if (active) setHomeState(h);
        })
        .catch(() => {});
      return () => {
        active = false;
      };
    }, []),
  );

  // Select a trail and zoom/transform the map to frame its full track as
  // large as possible, leaving room for the bottom card.
  const selectTrail = (trail: Trail) => {
    setSelected(trail);
    if (trail.track.length > 1) {
      mapRef.current?.fitToCoordinates(trailCoords.get(trail.id) ?? trackToLatLng(trail.track), {
        edgePadding: { top: 110, right: 56, bottom: 300, left: 56 },
        animated: true,
      });
    }
  };

  // In route mode, tapping a trail picks it as the destination.
  const onTrailPress = (trail: Trail) => {
    if (!routeMode) {
      selectTrail(trail);
      return;
    }
    const dest = trailDestEndpoint(trail);
    if (dest) updateDraft({ to: dest });
  };

  const onMapPress = (e: MapPressEvent) => {
    // On Android marker/line taps also bubble a map press ('marker-press',
    // 'polyline-press', ...). Only react to true empty-map presses.
    const action = (e.nativeEvent as { action?: string }).action;
    if (action && action !== 'press') return;
    if (!routeMode) {
      setSelected(null); // tap empty map to clear highlight
      return;
    }
    const pin: Endpoint = { kind: 'pin', coord: e.nativeEvent.coordinate, label: 'Map pin' };
    if (pinTarget === 'from') {
      updateDraft({ from: pin });
      setPinTarget('to');
    } else if (!draft.from && !myLocation) {
      // No usable start yet: first tap places the start, like before.
      updateDraft({ from: pin });
    } else {
      updateDraft({ to: pin });
    }
  };

  // Zoom by scaling the current region's deltas, clamped so the camera can't
  // invert or fly out past the whole-region view. factor < 1 zooms in.
  const zoomBy = (factor: number) => {
    const MIN_DELTA = 0.0006;
    const MAX_DELTA = 2;
    const clamp = (v: number) => Math.min(MAX_DELTA, Math.max(MIN_DELTA, v));
    const region = regionRef.current;
    mapRef.current?.animateToRegion(
      {
        latitude: region.latitude,
        longitude: region.longitude,
        latitudeDelta: clamp(region.latitudeDelta * factor),
        longitudeDelta: clamp(region.longitudeDelta * factor),
      },
      200,
    );
  };

  // Reset view: re-frame the selected trail if there is one, otherwise return
  // to the original all-trails overview.
  const resetView = () => {
    if (selected && selected.track.length > 1) {
      mapRef.current?.fitToCoordinates(trackToLatLng(selected.track), {
        edgePadding: { top: 110, right: 56, bottom: 300, left: 56 },
        animated: true,
      });
    } else {
      mapRef.current?.animateToRegion(initialRegion, 400);
    }
  };

  const fitToRoute = (result: BikeRoute) => {
    const allPts = result.legs.flatMap((l) => l.points);
    // Frame the route in the area right of the builder column (it overlays
    // the left ~250 px of the map). Small delay so layout settles first.
    setTimeout(
      () =>
        mapRef.current?.fitToCoordinates(allPts, {
          edgePadding: { top: 80, right: 40, bottom: 60, left: 280 },
          animated: true,
        }),
      80,
    );
  };

  // Routes build instantly with straight connectors, then snap those legs to
  // real roads/paths in the background (public Valhalla bike router). The
  // token discards stale refinements when the user rebuilds or clears.
  const refineToken = useRef(0);
  const [refining, setRefining] = useState(false);

  const refineConnectors = (result: BikeRoute) => {
    const token = ++refineToken.current;
    setRefining(true);
    refineRouteConnectors(result)
      .then((refined) => {
        if (!refined || refineToken.current !== token) return;
        setDraft((d) => (d.result === result ? { ...d, result: refined } : d));
      })
      .catch(() => {})
      .finally(() => {
        if (refineToken.current === token) setRefining(false);
      });
  };

  /** Change the route's start, destination or detour budget. The route
   * rebuilds immediately whenever both ends are known (planning is
   * synchronous and cheap; connectors are refined in the background). */
  const updateDraft = (patch: Partial<Pick<RouteDraft, 'from' | 'to' | 'detourKm'>>) => {
    const next = { ...draft, ...patch, result: null };
    const from =
      next.from ??
      (myLocation ? ({ kind: 'gps', coord: myLocation, label: 'My location' } as Endpoint) : null);
    if (!from || !next.to) {
      refineToken.current += 1;
      setRefining(false);
      setDraft(next);
      return;
    }
    const { result, destCoord } = buildBestRoute(from.coord, next.to, next.detourKm);
    setDraft({ ...next, from, to: { ...next.to, coord: destCoord }, result });
    fitToRoute(result);
    refineConnectors(result);
  };

  const swapEnds = () => {
    if (!draft.to) return;
    const from =
      draft.from ??
      (myLocation ? ({ kind: 'gps', coord: myLocation, label: 'My location' } as Endpoint) : null);
    if (!from) return;
    updateDraft({ from: draft.to, to: from });
  };

  /** In-app replacement for "directions to trail start": route from the
   * current GPS location (or chosen start) straight to the trail's start. */
  const routeToTrail = useCallback(
    async (trail: Trail) => {
      const dest = trailDestEndpoint(trail);
      if (!dest) return;
      setSelected(null);
      setRouteMode(true);
      let from = draft.from;
      if (!from) {
        const loc = await ensureLocation().catch(() => null);
        if (loc) from = { kind: 'gps', coord: loc, label: 'My location' };
      }
      if (from) {
        const { result, destCoord } = buildBestRoute(from.coord, dest, draft.detourKm);
        setDraft((d) => ({ ...d, from, to: { ...dest, coord: destCoord }, result }));
        fitToRoute(result);
        refineConnectors(result);
      } else {
        updateDraft({ to: dest });
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [draft.from, draft.detourKm, ensureLocation],
  );

  // Deep links from trail pages: destTrail=<id> builds a route there;
  // highlightTrail=<id> selects the trail and frames its track. The t nonce
  // lets the same trail be requested twice in a row.
  const { destTrail, highlightTrail, t: destNonce } = useLocalSearchParams<{
    destTrail?: string;
    highlightTrail?: string;
    t?: string;
  }>();
  const handledNonce = useRef<string | null>(null);
  useEffect(() => {
    const target = destTrail ?? highlightTrail;
    if (!target) return;
    const key = `${destTrail ?? ''}|${highlightTrail ?? ''}:${destNonce ?? ''}`;
    if (handledNonce.current === key) return;
    handledNonce.current = key;
    const trail = trailById(target);
    if (!trail) return;
    if (destTrail) {
      routeToTrail(trail);
      return;
    }
    // Highlight: leave any active navigation alone, but drop plain route mode
    // so the selected-trail card is visible.
    if (!navigating) {
      setRouteMode(false);
      setPinTarget('to');
    }
    // Give the map a beat to mount/lay out before framing the track.
    const timer = setTimeout(() => selectTrail(trail), 350);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [destTrail, highlightTrail, destNonce, routeToTrail]);

  const startNavigation = async () => {
    const route = draft.result;
    if (!route) return;
    try {
      if (!sharedRecorder.ride) await sharedRecorder.start();
    } catch (e) {
      Alert.alert('Cannot navigate', e instanceof Error ? e.message : 'Location unavailable.');
      return;
    }
    navUnsub.current?.();
    navUnsub.current = sharedRecorder.addListener((ride) => {
      const last = ride.points[ride.points.length - 1];
      if (last) {
        const pos = { latitude: last.lat, longitude: last.lng };
        setActiveLeg((prev) => nearestLegIndex(route, pos, prev ?? 0));
        // Follow the rider but keep whatever zoom they chose.
        const { latitudeDelta, longitudeDelta } = regionRef.current;
        mapRef.current?.animateToRegion(
          {
            ...pos,
            latitudeDelta: Math.min(latitudeDelta, 0.02),
            longitudeDelta: Math.min(longitudeDelta, 0.02),
          },
          750,
        );
      }
    });
    setNavigating(true);
    const start = sharedRecorder.ride?.points[sharedRecorder.ride.points.length - 1];
    mapRef.current?.animateToRegion(
      {
        ...(start ? { latitude: start.lat, longitude: start.lng } : draft.from?.coord ?? route.legs[0].points[0]),
        latitudeDelta: 0.006,
        longitudeDelta: 0.006,
      },
      750,
    );
  };

  const stopNavigation = () => {
    navUnsub.current?.();
    navUnsub.current = null;
    setNavigating(false);
    setActiveLeg(null);
    if (sharedRecorder.ride) {
      Alert.alert('Navigation ended', 'Your ride is still being recorded. Finish it now?', [
        { text: 'Keep recording', style: 'cancel' },
        {
          text: 'Finish ride',
          style: 'destructive',
          onPress: async () => {
            await sharedRecorder.stop();
            setNavTrack([]);
            Alert.alert('Ride saved', 'Find it on the Ride tab to share or export.');
          },
        },
      ]);
    }
  };

  const exitRouteMode = () => {
    if (navigating) stopNavigation();
    refineToken.current += 1;
    setRefining(false);
    setRouteMode(false);
    setPinTarget('to');
    setDraft({ from: null, to: null, detourKm: draft.detourKm, result: null });
  };

  const savePinAsHome = async (coord: LatLng) => {
    await persistHome(coord).catch(() => {});
    setHomeState(coord);
    Alert.alert('Home saved', 'Use the Home chip to route to or from it any time.');
  };

  const fromChips = (
    <Row style={{ flexWrap: 'wrap', marginTop: 6 }}>
      <Text style={{ color: p.muted, fontSize: 13, width: 42 }}>From</Text>
      <Chip
        label="My location"
        active={draft.from?.kind === 'gps' || (!draft.from && !!myLocation)}
        onPress={async () => {
          const loc = await ensureLocation().catch(() => null);
          if (!loc) {
            Alert.alert('No location', 'Location permission is needed to start from here.');
            return;
          }
          updateDraft({ from: { kind: 'gps', coord: loc, label: 'My location' } });
        }}
      />
      {home && (
        <Chip
          label="Home"
          active={draft.from?.kind === 'home'}
          onPress={() => updateDraft({ from: { kind: 'home', coord: home, label: 'Home' } })}
        />
      )}
      <Chip
        label={pinTarget === 'from' ? 'Tap the map…' : 'Drop pin'}
        active={pinTarget === 'from' || draft.from?.kind === 'pin'}
        onPress={() => setPinTarget('from')}
      />
    </Row>
  );

  const toChips = (
    <Row style={{ flexWrap: 'wrap', marginTop: 4 }}>
      <Text style={{ color: p.muted, fontSize: 13, width: 42 }}>To</Text>
      {draft.to?.kind === 'trail' && <Chip label={draft.to.label} active />}
      {home && (
        <Chip
          label="Home"
          active={draft.to?.kind === 'home'}
          onPress={() => updateDraft({ to: { kind: 'home', coord: home, label: 'Home' } })}
        />
      )}
      <Chip
        label={draft.to?.kind === 'pin' ? 'Map pin' : 'Drop pin'}
        active={pinTarget === 'to' && (draft.to == null || draft.to.kind === 'pin')}
        onPress={() => setPinTarget('to')}
      />
    </Row>
  );

  return (
    <View style={{ flex: 1 }}>
      {/* Map pane: full screen normally; the route panel below claims the
          lower part of the screen in route mode so the map stays visible. */}
      <View style={{ flex: 1 }}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        initialRegion={initialRegion}
        mapType={mapType}
        pitchEnabled
        showsBuildings
        showsCompass
        showsUserLocation
        showsMyLocationButton
        moveOnMarkerPress={false}
        onPress={onMapPress}
        onRegionChangeComplete={onRegionChangeComplete}>
        {mappedTrails.map((trail) => {
          const isSelected = selected?.id === trail.id;
          const onRoute = routeTrailIds.has(trail.id);
          const dimmed = routeActive ? !onRoute : selected !== null && !isSelected;
          const accent = routeActive ? onRoute : isSelected;
          return (
            <Polyline
              key={trail.id}
              coordinates={trailCoords.get(trail.id) ?? []}
              strokeColor={
                dimmed
                  ? '#9AA09C44'
                  : isSelected
                    ? Brand.amber
                    : trail.accentColor
              }
              strokeWidth={accent ? (isSelected ? 6 : 5) : dimmed ? 1.5 : 3}
              tappable
              onPress={() => onTrailPress(trail)}
            />
          );
        })}
        {showSigns &&
          trailMarkers.map((m) => (
            <TrailMarker
              key={m.key}
              trail={m.trail}
              coordinate={displaced?.get(m.key) ?? m.base}
              selected={selected?.id === m.trail.id || (routeActive && routeTrailIds.has(m.trail.id))}
              dimmed={
                routeActive
                  ? !routeTrailIds.has(m.trail.id)
                  : selected !== null && selected.id !== m.trail.id
              }
              size={markerSize}
              refresh={iconsReady}
              onPress={() => onTrailPress(m.trail)}
            />
          ))}
        {/* Green dots on the selected trail's start and end signs */}
        {selected &&
          trailEndpoints(selected).map((pt, i) => (
            <Marker
              key={`${selected.id}-endpoint-${i}`}
              coordinate={pt}
              anchor={{ x: 0.5, y: 0.5 }}
              zIndex={10}>
              <View style={styles.endpointDot} />
            </Marker>
          ))}
        {routeMode && home && (
          <Marker coordinate={home} anchor={{ x: 0.5, y: 0.5 }} zIndex={9} title="Home">
            <View style={[styles.homeDot, { backgroundColor: p.surface }]}>
              <Ionicons name="home" size={13} color={Brand.pine} />
            </View>
          </Marker>
        )}
        {routeMode && draft.from && draft.from.kind !== 'gps' && (
          <Marker coordinate={draft.from.coord} pinColor={Brand.moss} title="Start" />
        )}
        {routeMode && draft.to && (
          <Marker coordinate={draft.to.coord} pinColor={Brand.ember} title="Destination" />
        )}
        {offsetLegs?.map((leg, i) => (
          <Polyline
            key={`route-${i}`}
            coordinates={leg.points}
            strokeColor={leg.type === 'trail' ? Brand.amber : Brand.moss}
            strokeWidth={leg.type === 'trail' ? 6 : 4}
            lineDashPattern={leg.type === 'connector' ? [8, 6] : undefined}
          />
        ))}
        {chevrons.map((c, i) => (
          <Marker
            key={`chevron-${i}`}
            coordinate={c.coordinate}
            anchor={{ x: 0.5, y: 0.5 }}
            rotation={c.bearing}
            flat
            tracksViewChanges={false}
            zIndex={6}>
            <View style={styles.chevron} />
          </Marker>
        ))}
        {recording && navTrack.length > 1 && (
          <Polyline coordinates={navTrack} strokeColor={Brand.ember} strokeWidth={5} zIndex={5} />
        )}
        {/* Live GPS position while recording: red "recording" dot that rides
            along the track as fixes arrive. */}
        {recording && navTrack.length > 0 && (
          <Marker
            coordinate={navTrack[navTrack.length - 1]}
            anchor={{ x: 0.5, y: 0.5 }}
            tracksViewChanges={false}
            zIndex={20}>
            <View style={styles.recMarkerOuter}>
              <View style={styles.recMarkerInner} />
            </View>
          </Marker>
        )}
      </MapView>

      <IconPreloader
        key={trailsVersion}
        trails={mappedTrails}
        onReady={() => setIconsReady((v) => !v)}
      />

      {/* GPS recording status: red dot + elapsed time + distance so far */}
      {recording && recordStartedAt && (
        <RecPill top={insets.top + 12} startedAt={recordStartedAt} distanceM={navDistanceM} />
      )}

      {/* Route-mode toggle */}
      <Pressable
        onPress={() => {
          if (routeMode) {
            exitRouteMode();
          } else {
            setRouteMode(true);
          }
          setSelected(null);
        }}
        style={[
          styles.fab,
          { top: insets.top + 12, backgroundColor: routeMode ? Brand.amber : p.surface },
        ]}>
        <Ionicons name="git-branch-outline" size={22} color={routeMode ? '#fff' : p.primary} />
      </Pressable>

      {/* Base layer toggle: map / satellite / terrain */}
      <Pressable
        onPress={() => setMapTypeIdx((mapTypeIdx + 1) % MAP_TYPES.length)}
        style={[
          styles.fab,
          styles.layerFab,
          {
            top: insets.top + 64,
            backgroundColor: mapType === 'standard' ? p.surface : Brand.pine,
          },
        ]}>
        <Ionicons
          name={MAP_TYPE_META[MAP_TYPES[(mapTypeIdx + 1) % MAP_TYPES.length]].icon}
          size={20}
          color={mapType === 'standard' ? p.primary : '#fff'}
        />
        <Text
          style={[
            styles.layerLabel,
            { color: mapType === 'standard' ? p.muted : '#ffffffcc' },
          ]}>
          {MAP_TYPE_META[mapType].label}
        </Text>
      </Pressable>

      {/* Zoom + reset controls */}
      <View style={[styles.zoomGroup, { top: insets.top + 132, backgroundColor: p.surface }]}>
        <Pressable
          onPress={() => zoomBy(0.5)}
          hitSlop={6}
          style={({ pressed }) => [styles.zoomBtn, pressed && { opacity: 0.5 }]}>
          <Ionicons name="add" size={24} color={p.primary} />
        </Pressable>
        <View style={[styles.zoomDivider, { backgroundColor: p.border }]} />
        <Pressable
          onPress={() => zoomBy(2)}
          hitSlop={6}
          style={({ pressed }) => [styles.zoomBtn, pressed && { opacity: 0.5 }]}>
          <Ionicons name="remove" size={24} color={p.primary} />
        </Pressable>
        <View style={[styles.zoomDivider, { backgroundColor: p.border }]} />
        <Pressable
          onPress={resetView}
          hitSlop={6}
          style={({ pressed }) => [styles.zoomBtn, pressed && { opacity: 0.5 }]}>
          <Ionicons name="scan-outline" size={20} color={p.primary} />
        </Pressable>
      </View>

      {/* Selected trail card */}
      {selected && !routeMode && (
        <View
          style={[
            styles.sheet,
            { backgroundColor: p.surface, borderColor: p.border, bottom: insets.bottom + 12 },
          ]}>
          <Row style={{ gap: 10 }}>
            <TrailIconBadge trail={selected} size={44} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.sheetTitle, { color: p.text }]}>{displayName(selected)}</Text>
              {selected.creeSyllabics ? (
                <Text style={{ color: p.muted }}>
                  {selected.creeName} • {selected.creeSyllabics}
                </Text>
              ) : null}
              {selected.lengthM ? (
                <Text style={{ color: p.muted }}>{formatKm(selected.lengthM)}</Text>
              ) : null}
            </View>
          </Row>
          <Row style={{ marginTop: 8 }}>
            <Button
              label="Directions to start"
              style={{ flex: 1 }}
              onPress={() => routeToTrail(selected)}
            />
            <Button
              label="Details"
              variant="secondary"
              onPress={() => router.push(`/trail/${selected.id}`)}
            />
          </Row>
        </View>
      )}

      {/* Navigating: bus-stop style trail list in a narrow translucent column
          on the left, so the map (and your live position) stays visible. */}
      {navigating && draft.result && (
        <View
          style={[
            styles.navCard,
            {
              top: insets.top + 56,
              bottom: insets.bottom + 12,
              backgroundColor: p.dark ? 'rgba(14, 17, 15, 0.72)' : 'rgba(255, 255, 255, 0.78)',
              borderColor: p.border,
            },
          ]}>
          <Text style={[styles.navCardTitle, { color: p.muted }]}>
            {formatKm(navDistanceM)} / {formatKm(draft.result.totalM)}
          </Text>
          <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
            <RouteItinerary route={draft.result} activeLegIndex={activeLeg} compact />
          </ScrollView>
          <Pressable onPress={stopNavigation} style={styles.navEndBtn}>
            <Text style={styles.navEndText}>End</Text>
          </Pressable>
        </View>
      )}

      {/* Route builder: same translucent left column as live navigation, so
          the map (and tapped pins/trails) stays visible while planning. */}
      {routeMode && !navigating && (
        <View
          style={[
            styles.navCard,
            styles.builderCard,
            {
              top: insets.top + 56,
              bottom: insets.bottom + 12,
              backgroundColor: p.dark ? 'rgba(14, 17, 15, 0.72)' : 'rgba(255, 255, 255, 0.78)',
              borderColor: p.border,
            },
          ]}>
          <Text style={[styles.builderTitle, { color: p.text }]}>Bike route builder</Text>
          <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
            <Text style={{ color: p.muted, fontSize: 12 }}>
              {draft.to
                ? `To ${draft.to.label}. Tap the map or a trail to change it.`
                : 'Tap the map or a trail sign to set your destination. The route builds itself.'}
            </Text>
            {fromChips}
            {toChips}
            <Row style={{ marginTop: 6, flexWrap: 'wrap' }}>
              <Text style={{ color: p.muted, fontSize: 12 }}>Max detour:</Text>
              {DETOUR_OPTIONS_KM.map((km) => (
                <Chip
                  key={km}
                  label={`+${km} km`}
                  active={draft.detourKm === km}
                  onPress={() => updateDraft({ detourKm: km })}
                />
              ))}
            </Row>
            {draft.to?.kind === 'pin' && (
              <Pressable onPress={() => savePinAsHome(draft.to!.coord)}>
                <Text style={{ color: p.primary, fontSize: 12, marginTop: 4, fontWeight: '600' }}>
                  Save destination pin as home
                </Text>
              </Pressable>
            )}
            {draft.result && (
              <>
                <Text style={{ color: p.text, fontSize: 12, marginTop: 4 }}>
                  {formatKm(draft.result.totalM)} total • {formatKm(draft.result.trailM)} on{' '}
                  {draft.result.trailsUsed.length} trail
                  {draft.result.trailsUsed.length === 1 ? '' : 's'} • direct would be{' '}
                  {formatKm(draft.result.directM)}
                </Text>
                {refining && (
                  <Text style={{ color: p.muted, fontSize: 11, fontStyle: 'italic' }}>
                    Snapping connectors to roads and paths…
                  </Text>
                )}
                <RouteItinerary route={draft.result} compact />
              </>
            )}
          </ScrollView>
          <View style={{ gap: 6, marginTop: 6 }}>
            {draft.result && <Button label="Start navigation" onPress={startNavigation} />}
            <Row>
              {draft.to && (draft.from || myLocation) && (
                <Button label="Swap" variant="secondary" onPress={swapEnds} style={{ flex: 1 }} />
              )}
              <Button
                label="Clear"
                variant="secondary"
                style={{ flex: 1 }}
                onPress={() => {
                  setPinTarget('to');
                  updateDraft({ from: null, to: null });
                }}
              />
            </Row>
          </View>
        </View>
      )}

      </View>

    </View>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: 14,
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  layerFab: {
    height: 52,
    borderRadius: 14,
    paddingTop: 2,
  },
  layerLabel: {
    fontSize: 9,
    fontWeight: '700',
    marginTop: 1,
  },
  // Pill showing the GPS recorder is live: red dot, elapsed time, distance.
  recPill: {
    position: 'absolute',
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 18,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  recDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#E0312D',
  },
  recText: {
    fontSize: 13,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  // Current GPS position while recording.
  recMarkerOuter: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#E0312D33',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recMarkerInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#E0312D',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  // Route builder shares the navCard look but needs more width for chips.
  builderCard: {
    width: 250,
  },
  builderTitle: {
    fontSize: 14,
    fontWeight: '700',
  },
  // Narrow translucent itinerary column on the left during navigation.
  navCard: {
    position: 'absolute',
    left: 10,
    width: 170,
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 8,
    gap: 4,
  },
  navCardTitle: {
    fontSize: 11,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  navEndBtn: {
    backgroundColor: '#C24034',
    borderRadius: 10,
    paddingVertical: 7,
    alignItems: 'center',
  },
  navEndText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  zoomGroup: {
    position: 'absolute',
    right: 14,
    width: 44,
    borderRadius: 14,
    alignItems: 'center',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  zoomBtn: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  zoomDivider: {
    width: 28,
    height: StyleSheet.hairlineWidth,
  },
  endpointDot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: Brand.moss,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 3,
  },
  homeDot: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Brand.pine,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 3,
  },
  sheet: {
    position: 'absolute',
    left: 12,
    right: 12,
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
    gap: 2,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  // Bottom panel that shares the screen with the map (route mode).
  panel: {
    maxHeight: '50%',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    borderWidth: 1,
    borderBottomWidth: 0,
    paddingHorizontal: 14,
    paddingTop: 12,
    gap: 4,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: -4 },
    elevation: 10,
  },
  // Solid arrowhead pointing north at rotation 0; the Marker's flat rotation
  // turns it to the route's travel bearing.
  chevron: {
    width: 0,
    height: 0,
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderBottomWidth: 10,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: '#FFFFFF',
  },
  sheetTitle: { fontSize: 17, fontWeight: '700' },
});

/** GPS recording status: red dot, elapsed time (ticks on its own so the map
 * screen doesn't re-render every second), and distance so far. */
function RecPill({ top, startedAt, distanceM }: { top: number; startedAt: string; distanceM: number }) {
  const p = usePalette();
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const elapsedS = Math.max(0, Math.floor((now - new Date(startedAt).getTime()) / 1000));
  return (
    <View style={[styles.recPill, { top, backgroundColor: p.surface, borderColor: p.border }]}>
      <View style={styles.recDot} />
      <Text style={[styles.recText, { color: p.text }]}>{formatElapsed(elapsedS)}</Text>
      <Text style={[styles.recText, { color: p.muted }]}>{formatKm(distanceM)}</Text>
    </View>
  );
}
