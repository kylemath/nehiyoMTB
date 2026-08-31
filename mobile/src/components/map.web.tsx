// Web fallback for the native map. react-native-maps cannot run under
// react-native-web, so on web we render a lightweight placeholder and turn
// Marker/Polyline/Callout into no-ops. All non-map UI keeps working; the full
// interactive map lives in the iOS/Android app.
import React from 'react';
import { StyleSheet, Text, View, ViewProps } from 'react-native';

import { usePalette } from '@/components/ui';

export type LatLng = { latitude: number; longitude: number };
export type Region = LatLng & { latitudeDelta: number; longitudeDelta: number };
export type MapPressEvent = { nativeEvent: { coordinate: LatLng } };

export const Marker = (_props: Record<string, unknown>) => null;
export const Polyline = (_props: Record<string, unknown>) => null;
export const Callout = (_props: Record<string, unknown>) => null;

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

type MapViewProps = ViewProps & {
  children?: React.ReactNode;
  // Accept (and ignore) the native map props so screens don't need branching.
  initialRegion?: Region;
  mapType?: 'standard' | 'hybrid' | 'satellite' | 'terrain';
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

const MapView = React.forwardRef<MapViewHandle, MapViewProps>(({ style, children }, ref) => {
  const p = usePalette();
  React.useImperativeHandle(
    ref,
    () => ({ animateToRegion: () => {}, fitToCoordinates: () => {} }),
    [],
  );
  return (
    <View style={[styles.fallback, { backgroundColor: p.surface, borderColor: p.border }, style]}>
      <Text style={[styles.title, { color: p.text }]}>Map runs in the app</Text>
      <Text style={[styles.body, { color: p.muted }]}>
        Open EdmontonTrailMaps on iOS or Android to see the trail map, your location, and bike
        routes. Everything else works here on the web.
      </Text>
      <View style={styles.hidden}>{children}</View>
    </View>
  );
});
MapView.displayName = 'MapViewWeb';

export default MapView;

const styles = StyleSheet.create({
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    padding: 24,
    gap: 8,
  },
  title: { fontSize: 18, fontWeight: '700' },
  body: { fontSize: 14, lineHeight: 20, textAlign: 'center', maxWidth: 420 },
  hidden: { display: 'none' },
});
