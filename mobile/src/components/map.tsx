// Native (iOS/Android) map surface: MapLibre Native behind the subset of the
// react-native-maps API the screens use (MapView, Marker, Polyline), the same
// subset map.web.tsx implements with MapLibre GL in the browser.
//
// Why not react-native-maps: on Android it renders Google Maps, which crashes
// the app outright when no Google Maps API key is configured. MapLibre needs
// no key and draws the same basemaps as the website (CARTO Voyager streets,
// Esri imagery).
import {
  Camera,
  type CameraRef,
  GeoJSONSource,
  Layer,
  Map,
  type MapProps,
  Marker as MLMarker,
  UserLocation,
  type ViewStateChangeEvent,
} from '@maplibre/maplibre-react-native';
import * as Location from 'expo-location';
import React, {
  createContext,
  useCallback,
  useContext,
  useId,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  Text,
  View,
  ViewProps,
} from 'react-native';

export type LatLng = { latitude: number; longitude: number };
export type Region = LatLng & { latitudeDelta: number; longitudeDelta: number };
export type MapPressEvent = { nativeEvent: { coordinate: LatLng } };

export type MapViewHandle = {
  animateToRegion: (region: Region, duration?: number) => void;
  fitToCoordinates: (
    coordinates: LatLng[],
    options?: {
      edgePadding?: { top: number; right: number; bottom: number; left: number };
      animated?: boolean;
    },
  ) => void;
};

type StyleSpecification = Exclude<MapProps['mapStyle'], string>;

type MapType = 'standard' | 'hybrid' | 'satellite' | 'terrain';

type MapViewProps = ViewProps & {
  children?: React.ReactNode;
  initialRegion?: Region;
  mapType?: MapType;
  showsBuildings?: boolean;
  showsCompass?: boolean;
  showsUserLocation?: boolean;
  showsMyLocationButton?: boolean;
  moveOnMarkerPress?: boolean;
  scrollEnabled?: boolean;
  zoomEnabled?: boolean;
  pitchEnabled?: boolean;
  rotateEnabled?: boolean;
  onPress?: (event: MapPressEvent) => void;
  onRegionChangeComplete?: (region: Region) => void;
};

const STREET_TILES = [
  'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
  'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
  'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
];
const SATELLITE_TILES = [
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
];

function baseStyle(imagery: boolean): StyleSpecification {
  return {
    version: 8,
    sources: imagery
      ? {
          base: {
            type: 'raster',
            tiles: SATELLITE_TILES,
            tileSize: 256,
            maxzoom: 19,
            attribution: '© Esri, Maxar, Earthstar Geographics',
          },
        }
      : {
          base: {
            type: 'raster',
            tiles: STREET_TILES,
            tileSize: 256,
            maxzoom: 19,
            attribution: '© OpenStreetMap contributors © CARTO',
          },
        },
    layers: [{ id: 'base', type: 'raster', source: 'base' }],
  };
}
const STREETS = baseStyle(false);
const IMAGERY = baseStyle(true);

/** Overlays call this when they handle a tap, so it isn't also a map press. */
const MapContext = createContext<() => void>(() => {});

type Bounds = [west: number, south: number, east: number, north: number];

function regionBounds(r: Region): Bounds {
  return [
    r.longitude - r.longitudeDelta / 2,
    r.latitude - r.latitudeDelta / 2,
    r.longitude + r.longitudeDelta / 2,
    r.latitude + r.latitudeDelta / 2,
  ];
}

function coordsBounds(coords: LatLng[]): Bounds | null {
  if (coords.length === 0) return null;
  let [w, s, e, n] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const c of coords) {
    w = Math.min(w, c.longitude);
    e = Math.max(e, c.longitude);
    s = Math.min(s, c.latitude);
    n = Math.max(n, c.latitude);
  }
  // A single point (or a straight N-S / E-W line) has no area to fit.
  const pad = 0.002;
  if (e - w < pad) [w, e] = [w - pad / 2, e + pad / 2];
  if (n - s < pad) [s, n] = [s - pad / 2, n + pad / 2];
  return [w, s, e, n];
}

const EDMONTON: Region = {
  latitude: 53.53,
  longitude: -113.52,
  latitudeDelta: 0.2,
  longitudeDelta: 0.2,
};

const MapView = React.forwardRef<MapViewHandle, MapViewProps>(function MapViewNative(
  {
    style,
    children,
    initialRegion,
    mapType = 'standard',
    showsCompass,
    showsUserLocation,
    showsMyLocationButton,
    scrollEnabled = true,
    zoomEnabled = true,
    pitchEnabled = true,
    rotateEnabled = true,
    onPress,
    onRegionChangeComplete,
  },
  ref,
) {
  const camera = useRef<CameraRef>(null);
  const consumedAt = useRef(0);
  const consume = useCallback(() => {
    consumedAt.current = Date.now();
  }, []);
  // The first region is fixed at mount, like react-native-maps' initialRegion.
  const [initialBounds] = useState(() => regionBounds(initialRegion ?? EDMONTON));

  useImperativeHandle(
    ref,
    () => ({
      animateToRegion: (region, duration = 500) =>
        camera.current?.fitBounds(regionBounds(region), { duration }),
      fitToCoordinates: (coordinates, options) => {
        const bounds = coordsBounds(coordinates);
        if (!bounds) return;
        camera.current?.fitBounds(bounds, {
          padding: options?.edgePadding ?? { top: 40, right: 40, bottom: 40, left: 40 },
          duration: options?.animated === false ? 0 : 500,
        });
      },
    }),
    [],
  );

  const locateMe = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return;
      const pos =
        (await Location.getLastKnownPositionAsync()) ??
        (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));
      camera.current?.flyTo({
        center: [pos.coords.longitude, pos.coords.latitude],
        zoom: 15,
        duration: 600,
      });
    } catch {
      // No fix available: leave the camera where it is.
    }
  };

  const imagery = mapType === 'hybrid' || mapType === 'satellite';

  return (
    <View style={[styles.container, style]}>
      <Map
        style={StyleSheet.absoluteFill}
        mapStyle={imagery ? IMAGERY : STREETS}
        dragPan={scrollEnabled}
        touchZoom={zoomEnabled}
        doubleTapZoom={zoomEnabled}
        touchRotate={rotateEnabled}
        touchPitch={pitchEnabled}
        compass={Boolean(showsCompass)}
        logo={false}
        attributionPosition={{ bottom: 8, left: 8 }}
        onPress={(e: NativeSyntheticEvent<{ lngLat: [number, number] }>) => {
          if (Date.now() - consumedAt.current < 400) return;
          const [longitude, latitude] = e.nativeEvent.lngLat;
          onPress?.({ nativeEvent: { coordinate: { latitude, longitude } } });
        }}
        onRegionDidChange={(e: NativeSyntheticEvent<ViewStateChangeEvent>) => {
          if (!onRegionChangeComplete) return;
          const { center, bounds } = e.nativeEvent;
          const [w, s, east, n] = bounds;
          onRegionChangeComplete({
            longitude: center[0],
            latitude: center[1],
            latitudeDelta: n - s,
            longitudeDelta: east - w,
          });
        }}>
        <Camera ref={camera} initialViewState={{ bounds: initialBounds }} />
        {showsUserLocation && <UserLocation />}
        <MapContext.Provider value={consume}>{children}</MapContext.Provider>
      </Map>
      {showsMyLocationButton && (
        <Pressable
          accessibilityLabel="Show my location"
          onPress={locateMe}
          style={({ pressed }) => [styles.locate, pressed && { opacity: 0.7 }]}>
          <Text style={styles.locateIcon}>◎</Text>
        </Pressable>
      )}
    </View>
  );
});

// Lets screens write `useRef<MapView>(null)` as they did with react-native-maps.
// eslint-disable-next-line @typescript-eslint/no-redeclare
type MapView = MapViewHandle;
export default MapView;

/** '#RRGGBBAA' / '#RGB' / any CSS colour → MapLibre colour + opacity. */
function splitColor(color: string | undefined): { color: string; opacity: number } {
  if (!color) return { color: '#000000', opacity: 1 };
  const m = /^#([0-9a-f]{6})([0-9a-f]{2})$/i.exec(color);
  if (m) return { color: `#${m[1]}`, opacity: parseInt(m[2], 16) / 255 };
  return { color, opacity: 1 };
}

type PolylineProps = {
  coordinates: LatLng[];
  strokeColor?: string;
  strokeWidth?: number;
  lineDashPattern?: number[];
  tappable?: boolean;
  onPress?: () => void;
  zIndex?: number;
};

export function Polyline({
  coordinates,
  strokeColor,
  strokeWidth = 1,
  lineDashPattern,
  tappable,
  onPress,
}: PolylineProps) {
  const consume = useContext(MapContext);
  const id = `line-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const data = useMemo<GeoJSON.Feature<GeoJSON.LineString>>(
    () => ({
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: coordinates.map((c) => [c.longitude, c.latitude]),
      },
    }),
    [coordinates],
  );
  if (coordinates.length < 2) return null;
  const { color, opacity } = splitColor(strokeColor);
  return (
    <GeoJSONSource
      id={id}
      data={data}
      // A wider touch target so thin trail lines are easy to hit.
      hitbox={tappable ? { top: 10, right: 10, bottom: 10, left: 10 } : undefined}
      onPress={
        tappable
          ? () => {
              consume();
              onPress?.();
            }
          : undefined
      }>
      <Layer
        id={id}
        type="line"
        layout={{ 'line-cap': 'round', 'line-join': 'round' }}
        paint={{
          'line-color': color,
          'line-opacity': opacity,
          'line-width': strokeWidth,
          // react-native-maps dashes are in pixels; MapLibre's in line widths.
          ...(lineDashPattern
            ? { 'line-dasharray': lineDashPattern.map((n) => n / Math.max(strokeWidth, 1)) }
            : {}),
        }}
      />
    </GeoJSONSource>
  );
}

type MarkerProps = {
  coordinate: LatLng;
  anchor?: { x: number; y: number };
  pinColor?: string;
  title?: string;
  rotation?: number;
  flat?: boolean;
  zIndex?: number;
  tracksViewChanges?: boolean;
  onPress?: () => void;
  children?: React.ReactNode;
};

type Anchor =
  | 'center'
  | 'top'
  | 'bottom'
  | 'left'
  | 'right'
  | 'top-left'
  | 'top-right'
  | 'bottom-left'
  | 'bottom-right';

/** react-native-maps {x, y} fractions → the nearest MapLibre anchor name. */
function anchorName(x: number, y: number): Anchor {
  const h = x < 0.25 ? 'left' : x > 0.75 ? 'right' : '';
  const v = y < 0.25 ? 'top' : y > 0.75 ? 'bottom' : '';
  if (v && h) return `${v}-${h}` as Anchor;
  return (v || h || 'center') as Anchor;
}

export function Marker({
  coordinate,
  anchor,
  pinColor,
  rotation = 0,
  onPress,
  children,
}: MarkerProps) {
  const consume = useContext(MapContext);
  const hasChildren = React.Children.count(children) > 0;
  // react-native-maps anchors pins at the bottom centre by default.
  const name = anchorName(anchor?.x ?? 0.5, anchor?.y ?? 1);
  const body = hasChildren ? (
    <View>{children}</View>
  ) : (
    <View style={[styles.pin, { backgroundColor: pinColor ?? '#D9534F' }]} />
  );
  return (
    <MLMarker
      lngLat={[coordinate.longitude, coordinate.latitude]}
      anchor={name}
      onPress={
        onPress
          ? () => {
              consume();
              onPress();
            }
          : undefined
      }>
      {rotation ? <View style={{ transform: [{ rotate: `${rotation}deg` }] }}>{body}</View> : body}
    </MLMarker>
  );
}

/** Callouts aren't used: the screens show their own trail sheet. */
export const Callout = (_props: Record<string, unknown>) => null;

const styles = StyleSheet.create({
  container: { overflow: 'hidden' },
  pin: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  locate: {
    position: 'absolute',
    right: 12,
    bottom: 24,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 1 },
  },
  locateIcon: { fontSize: 20, color: '#1E5E46' },
});
