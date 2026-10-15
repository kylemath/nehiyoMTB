// Web map surface: a MapLibre GL implementation of the subset of the
// react-native-maps API the screens use (MapView, Marker, Polyline, Callout),
// so the same screens run in the browser build served at <site>/app.
// Native builds resolve map.tsx (react-native-maps) instead. Basemaps match
// the website's own trail map (CARTO Voyager streets, Esri imagery).
//
// MapLibre is loaded at runtime from the same CDN build the website uses
// (cached by the browser across the site and the app) instead of being
// bundled, which keeps the app bundle ~700 KB smaller. The npm package is a
// dev dependency for its types only.
import type maplibreglType from 'maplibre-gl';
import React, {
  createContext,
  useContext,
  useEffect,
  useId,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import { createPortal } from 'react-dom';
import { StyleSheet, View, ViewProps } from 'react-native';

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

type MapLibre = typeof maplibreglType;

const MAPLIBRE_VERSION = '4.7.1';
const MAPLIBRE_JS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.js`;
const MAPLIBRE_CSS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.css`;

let maplibreLoad: Promise<MapLibre> | null = null;

function loadMapLibre(): Promise<MapLibre> {
  const w = window as unknown as { maplibregl?: MapLibre };
  if (w.maplibregl) return Promise.resolve(w.maplibregl);
  if (!maplibreLoad) {
    maplibreLoad = new Promise((resolve, reject) => {
      const css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = MAPLIBRE_CSS;
      document.head.appendChild(css);
      const script = document.createElement('script');
      script.src = MAPLIBRE_JS;
      script.async = true;
      script.onload = () => (w.maplibregl ? resolve(w.maplibregl) : reject(new Error('maplibre')));
      script.onerror = () => {
        maplibreLoad = null;
        reject(new Error('Could not load MapLibre'));
      };
      document.head.appendChild(script);
    });
  }
  return maplibreLoad;
}

const STREET_TILES = [
  'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
  'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
  'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
];
const SATELLITE_TILES = [
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
];

const BASE_STYLE: maplibreglType.StyleSpecification = {
  version: 8,
  sources: {
    streets: {
      type: 'raster',
      tiles: STREET_TILES,
      tileSize: 256,
      maxzoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    },
    satellite: {
      type: 'raster',
      tiles: SATELLITE_TILES,
      tileSize: 256,
      maxzoom: 19,
      attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics',
    },
  },
  layers: [
    { id: 'streets', type: 'raster', source: 'streets' },
    { id: 'satellite', type: 'raster', source: 'satellite', layout: { visibility: 'none' } },
  ],
};

/** Per-map bookkeeping shared by the overlay components. */
type MapState = {
  lib: MapLibre;
  map: maplibreglType.Map;
  /** Layers that handle their own taps; a tap on them is not a map press. */
  tappableLayers: Set<string>;
  /** Set when a marker or tappable line consumed the current click. */
  consumedAt: number;
};

const MapContext = createContext<MapState | null>(null);

function regionBounds(r: Region): maplibreglType.LngLatBoundsLike {
  return [
    [r.longitude - r.longitudeDelta / 2, r.latitude - r.latitudeDelta / 2],
    [r.longitude + r.longitudeDelta / 2, r.latitude + r.latitudeDelta / 2],
  ];
}

function coordsBounds(lib: MapLibre, coords: LatLng[]): maplibreglType.LngLatBounds | null {
  if (coords.length === 0) return null;
  const b = new lib.LngLatBounds(
    [coords[0].longitude, coords[0].latitude],
    [coords[0].longitude, coords[0].latitude],
  );
  coords.forEach((c) => b.extend([c.longitude, c.latitude]));
  return b;
}

function currentRegion(map: maplibreglType.Map): Region {
  const b = map.getBounds();
  const c = map.getCenter();
  return {
    latitude: c.lat,
    longitude: c.lng,
    latitudeDelta: b.getNorth() - b.getSouth(),
    longitudeDelta: b.getEast() - b.getWest(),
  };
}

const MapView = React.forwardRef<MapViewHandle, MapViewProps>(function MapViewWeb(
  {
    style,
    children,
    initialRegion,
    mapType = 'standard',
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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [state, setState] = useState<MapState | null>(null);
  const callbacks = useRef({ onPress, onRegionChangeComplete });
  useEffect(() => {
    callbacks.current = { onPress, onRegionChangeComplete };
  });
  /** Camera moves requested before the map finished loading. */
  const pending = useRef<((map: maplibreglType.Map, lib: MapLibre) => void) | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    // MapLibre cannot start in a zero-size box (hidden tab, first layout
    // pass), so create the map once the container has a real size and
    // resize it on every later layout change.
    let map: maplibreglType.Map | null = null;
    let lib: MapLibre | null = null;
    let disposed = false;
    const create = (lib: MapLibre) => {
      const m = new lib.Map({
        container,
        style: BASE_STYLE,
        // Spread, not `undefined` keys: MapLibre copies explicit undefineds
        // over its defaults (zoom: undefined → "failed to invert matrix").
        ...(initialRegion
          ? { bounds: regionBounds(initialRegion) }
          : { center: [-113.52, 53.53] as [number, number], zoom: 11 }),
        attributionControl: { compact: true },
        dragRotate: rotateEnabled,
        pitchWithRotate: pitchEnabled,
      });
      const mapState: MapState = { lib, map: m, tappableLayers: new Set(), consumedAt: 0 };

      if (!scrollEnabled) m.dragPan.disable();
      if (!zoomEnabled) {
        m.scrollZoom.disable();
        m.doubleClickZoom.disable();
        m.boxZoom.disable();
        m.touchZoomRotate.disable();
      }
      if (!rotateEnabled) m.touchZoomRotate.disableRotation();
      if (!pitchEnabled) m.touchPitch.disable();
      // The screens draw their own zoom / reset buttons top-right, so the
      // only MapLibre control is "locate me", tucked bottom-right.
      if (showsUserLocation || showsMyLocationButton) {
        m.addControl(
          new lib.GeolocateControl({
            positionOptions: { enableHighAccuracy: true },
            trackUserLocation: true,
            showUserLocation: true,
          }),
          'bottom-right',
        );
      }

      m.on('click', (e) => {
        if (Date.now() - mapState.consumedAt < 300) return;
        const layers = [...mapState.tappableLayers].filter((id) => m.getLayer(id));
        if (layers.length && m.queryRenderedFeatures(e.point, { layers }).length) return;
        callbacks.current.onPress?.({
          nativeEvent: { coordinate: { latitude: e.lngLat.lat, longitude: e.lngLat.lng } },
        });
      });
      m.on('moveend', () => callbacks.current.onRegionChangeComplete?.(currentRegion(m)));
      m.on('load', () => {
        pending.current?.(m, lib);
        pending.current = null;
        setState(mapState);
      });
      return m;
    };

    const observer = new ResizeObserver(() => {
      if (!lib || container.clientWidth === 0 || container.clientHeight === 0) return;
      if (map) map.resize();
      else map = create(lib);
    });
    loadMapLibre()
      .then((loaded) => {
        if (disposed) return;
        lib = loaded;
        observer.observe(container);
      })
      .catch(() => {
        // Offline: the map stays blank; the rest of the screen still works.
      });
    return () => {
      disposed = true;
      observer.disconnect();
      setState(null);
      map?.remove();
    };
    // The map is created once; interaction flags are fixed per screen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = state?.map;
    if (!map) return;
    const imagery = mapType === 'hybrid' || mapType === 'satellite';
    map.setLayoutProperty('satellite', 'visibility', imagery ? 'visible' : 'none');
    map.setLayoutProperty('streets', 'visibility', imagery ? 'none' : 'visible');
  }, [state, mapType]);

  useImperativeHandle(
    ref,
    () => {
      const run = (fn: (map: maplibreglType.Map, lib: MapLibre) => void) => {
        if (state) fn(state.map, state.lib);
        else pending.current = fn;
      };
      return {
        animateToRegion: (region, duration = 500) =>
          run((map) => map.fitBounds(regionBounds(region), { duration, padding: 0 })),
        fitToCoordinates: (coordinates, options) => {
          run((map, lib) => {
            const bounds = coordsBounds(lib, coordinates);
            if (!bounds) return;
            map.fitBounds(bounds, {
              padding: options?.edgePadding ?? 40,
              duration: options?.animated === false ? 0 : 500,
              maxZoom: 17,
            });
          });
        },
      };
    },
    [state],
  );

  return (
    <View style={[styles.container, style]}>
      <div ref={containerRef} style={{ position: 'absolute', inset: 0 }} />
      {state && <MapContext.Provider value={state}>{children}</MapContext.Provider>}
    </View>
  );
});

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
  const ctx = useContext(MapContext);
  const id = `line-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const hitId = `${id}-hit`;
  const pressRef = useRef(onPress);
  useEffect(() => {
    pressRef.current = onPress;
  });

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

  // Add the source + layers once; later effects only update them.
  useEffect(() => {
    if (!ctx) return;
    const { map } = ctx;
    map.addSource(id, { type: 'geojson', data });
    map.addLayer({
      id,
      type: 'line',
      source: id,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
    });
    if (tappable) {
      // Invisible wide stroke so thin trail lines are easy to hit.
      map.addLayer({
        id: hitId,
        type: 'line',
        source: id,
        paint: { 'line-width': 16, 'line-opacity': 0 },
      });
      ctx.tappableLayers.add(hitId);
      const click = () => {
        ctx.consumedAt = Date.now();
        pressRef.current?.();
      };
      const enter = () => (map.getCanvas().style.cursor = 'pointer');
      const leave = () => (map.getCanvas().style.cursor = '');
      map.on('click', hitId, click);
      map.on('mouseenter', hitId, enter);
      map.on('mouseleave', hitId, leave);
    }
    return () => {
      ctx.tappableLayers.delete(hitId);
      if (!map.getStyle()) return; // map already removed
      if (map.getLayer(hitId)) map.removeLayer(hitId);
      if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(id)) map.removeSource(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx, id]);

  useEffect(() => {
    const source = ctx?.map.getSource(id) as maplibreglType.GeoJSONSource | undefined;
    source?.setData(data);
  }, [ctx, id, data]);

  const dash = lineDashPattern?.join(',');
  useEffect(() => {
    const map = ctx?.map;
    if (!map?.getLayer(id)) return;
    const { color, opacity } = splitColor(strokeColor);
    map.setPaintProperty(id, 'line-color', color);
    map.setPaintProperty(id, 'line-opacity', opacity);
    map.setPaintProperty(id, 'line-width', strokeWidth);
    // react-native-maps dashes are in pixels; MapLibre's are in line widths.
    map.setPaintProperty(
      id,
      'line-dasharray',
      dash ? dash.split(',').map((n) => Number(n) / Math.max(strokeWidth, 1)) : undefined,
    );
  }, [ctx, id, strokeColor, strokeWidth, dash]);

  return null;
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

export function Marker({
  coordinate,
  anchor,
  pinColor,
  title,
  rotation = 0,
  flat,
  zIndex,
  onPress,
  children,
}: MarkerProps) {
  const ctx = useContext(MapContext);
  const element = useMemo(() => document.createElement('div'), []);
  const markerRef = useRef<maplibreglType.Marker | null>(null);
  const pressRef = useRef(onPress);
  useEffect(() => {
    pressRef.current = onPress;
  });
  const hasChildren = React.Children.count(children) > 0;
  // react-native-maps anchors pins at the bottom centre by default.
  const ax = anchor?.x ?? 0.5;
  const ay = anchor?.y ?? 1;

  useEffect(() => {
    if (!ctx) return;
    const marker = new ctx.lib.Marker({
      element,
      anchor: 'top-left',
      rotationAlignment: flat ? 'map' : 'viewport',
      pitchAlignment: flat ? 'map' : 'viewport',
    })
      .setLngLat([coordinate.longitude, coordinate.latitude])
      .addTo(ctx.map);
    markerRef.current = marker;
    const click = (e: MouseEvent) => {
      if (!pressRef.current) return;
      e.stopPropagation();
      ctx.consumedAt = Date.now();
      pressRef.current();
    };
    element.addEventListener('click', click);
    return () => {
      element.removeEventListener('click', click);
      marker.remove();
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx, element, flat]);

  useEffect(() => {
    markerRef.current?.setLngLat([coordinate.longitude, coordinate.latitude]);
  }, [coordinate.latitude, coordinate.longitude]);

  useEffect(() => {
    markerRef.current?.setRotation(rotation);
  }, [rotation, ctx, flat]);

  useEffect(() => {
    const el = markerRef.current?.getElement();
    if (!el) return;
    el.style.zIndex = zIndex != null ? String(zIndex) : '';
    el.style.cursor = onPress ? 'pointer' : '';
    if (title) el.title = title;
    else el.removeAttribute('title');
  }, [ctx, flat, zIndex, title, onPress]);

  if (!ctx) return null;
  return createPortal(
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        transform: `translate(${-ax * 100}%, ${-ay * 100}%)`,
      }}>
      {hasChildren ? children : <View style={[styles.pin, { backgroundColor: pinColor ?? '#D9534F' }]} />}
    </div>,
    element,
  );
}

/** Callouts are not used on web: the screens show their own trail sheet. */
export const Callout = (_props: Record<string, unknown>) => null;

const styles = StyleSheet.create({
  container: { overflow: 'hidden' },
  pin: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },
});
