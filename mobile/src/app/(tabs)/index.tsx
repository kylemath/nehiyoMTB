import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Linking, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Callout, MapPressEvent, Marker, Polyline } from 'react-native-maps';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Button, Chip, Row, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { LatLng, formatKm, regionForPoints } from '@/lib/geo';
import { BikeRoute, buildBikeRoute } from '@/lib/routing';
import { Trail, displayName, mappedTrails, trackToLatLng } from '@/lib/trails';

const DETOUR_OPTIONS_KM = [1, 2, 5, 10];

export function openDirections(to: LatLng, label: string) {
  const lat = to.latitude;
  const lng = to.longitude;
  const url = Platform.select({
    ios: `maps:?daddr=${lat},${lng}&dirflg=b`,
    android: `google.navigation:q=${lat},${lng}&mode=b`,
    default: `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=bicycling`,
  });
  Linking.openURL(url).catch(() =>
    Linking.openURL(
      `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=bicycling`,
    ),
  );
}

type RouteDraft = {
  from: LatLng | null;
  to: LatLng | null;
  detourKm: number;
  result: BikeRoute | null;
};

export default function MapTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapView>(null);
  const [myLocation, setMyLocation] = useState<LatLng | null>(null);
  const [selected, setSelected] = useState<Trail | null>(null);
  const [routeMode, setRouteMode] = useState(false);
  const [draft, setDraft] = useState<RouteDraft>({
    from: null,
    to: null,
    detourKm: 2,
    result: null,
  });

  const initialRegion = useMemo(
    () => regionForPoints(mappedTrails.flatMap((t) => trackToLatLng(t.track))),
    [],
  );

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({});
        setMyLocation({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
      }
    })();
  }, []);

  const onMapPress = (e: MapPressEvent) => {
    if (!routeMode) return;
    const coord = e.nativeEvent.coordinate;
    setDraft((d) => {
      if (!d.from) return { ...d, from: coord, result: null };
      if (!d.to) return { ...d, to: coord, result: null };
      return { ...d, to: coord, result: null };
    });
  };

  const buildRoute = () => {
    const from = draft.from ?? myLocation;
    if (!from || !draft.to) return;
    const result = buildBikeRoute(from, draft.to, draft.detourKm * 1000);
    setDraft((d) => ({ ...d, from, result }));
    const allPts = result.legs.flatMap((l) => l.points);
    mapRef.current?.animateToRegion(regionForPoints(allPts), 600);
  };

  return (
    <View style={{ flex: 1 }}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        initialRegion={initialRegion}
        showsUserLocation
        showsMyLocationButton
        onPress={onMapPress}>
        {mappedTrails.map((trail) => (
          <Polyline
            key={trail.id}
            coordinates={trackToLatLng(trail.track)}
            strokeColor={selected?.id === trail.id ? Brand.amber : trail.accentColor}
            strokeWidth={selected?.id === trail.id ? 5 : 3}
            tappable
            onPress={() => setSelected(trail)}
          />
        ))}
        {mappedTrails.map(
          (trail) =>
            trail.start?.lat != null &&
            trail.start.lng != null && (
              <Marker
                key={`${trail.id}-start`}
                coordinate={{ latitude: trail.start.lat, longitude: trail.start.lng }}
                pinColor={Brand.pine}
                onPress={() => setSelected(trail)}>
                <Callout onPress={() => router.push(`/trail/${trail.id}`)}>
                  <View style={{ maxWidth: 220, padding: 4 }}>
                    <Text style={{ fontWeight: '700' }}>{displayName(trail)}</Text>
                    {trail.creeSyllabics ? <Text>{trail.creeSyllabics}</Text> : null}
                    <Text style={{ color: Brand.stone, marginTop: 2 }}>Tap for details</Text>
                  </View>
                </Callout>
              </Marker>
            ),
        )}
        {routeMode && draft.from && (
          <Marker coordinate={draft.from} pinColor={Brand.moss} title="Start" />
        )}
        {routeMode && draft.to && (
          <Marker coordinate={draft.to} pinColor={Brand.ember} title="Destination" />
        )}
        {draft.result?.legs.map((leg, i) => (
          <Polyline
            key={`route-${i}`}
            coordinates={leg.points}
            strokeColor={leg.type === 'trail' ? Brand.amber : Brand.moss}
            strokeWidth={leg.type === 'trail' ? 6 : 4}
            lineDashPattern={leg.type === 'connector' ? [8, 6] : undefined}
          />
        ))}
      </MapView>

      {/* Route-mode toggle */}
      <Pressable
        onPress={() => {
          setRouteMode(!routeMode);
          setSelected(null);
          if (routeMode) setDraft({ from: null, to: null, detourKm: 2, result: null });
        }}
        style={[
          styles.fab,
          { top: insets.top + 12, backgroundColor: routeMode ? Brand.amber : p.surface },
        ]}>
        <Ionicons name="git-branch-outline" size={22} color={routeMode ? '#fff' : p.primary} />
      </Pressable>

      {/* Selected trail card */}
      {selected && !routeMode && (
        <View
          style={[
            styles.sheet,
            { backgroundColor: p.surface, borderColor: p.border, bottom: insets.bottom + 12 },
          ]}>
          <Text style={[styles.sheetTitle, { color: p.text }]}>{displayName(selected)}</Text>
          {selected.creeSyllabics ? (
            <Text style={{ color: p.muted }}>
              {selected.creeName} • {selected.creeSyllabics}
            </Text>
          ) : null}
          {selected.lengthM ? (
            <Text style={{ color: p.muted }}>{formatKm(selected.lengthM)}</Text>
          ) : null}
          <Row style={{ marginTop: 8 }}>
            <Button
              label="Directions to start"
              style={{ flex: 1 }}
              onPress={() =>
                selected.start?.lat != null &&
                openDirections(
                  { latitude: selected.start.lat, longitude: selected.start.lng! },
                  selected.title,
                )
              }
            />
            <Button
              label="Details"
              variant="secondary"
              onPress={() => router.push(`/trail/${selected.id}`)}
            />
          </Row>
        </View>
      )}

      {/* Route builder sheet */}
      {routeMode && (
        <View
          style={[
            styles.sheet,
            { backgroundColor: p.surface, borderColor: p.border, bottom: insets.bottom + 12 },
          ]}>
          <Text style={[styles.sheetTitle, { color: p.text }]}>Bike route builder</Text>
          <Text style={{ color: p.muted, fontSize: 13 }}>
            {draft.from
              ? draft.to
                ? 'Tap map to move the destination.'
                : 'Tap the map to set your destination.'
              : myLocation
                ? 'Tap the map to set a start, or build from your location.'
                : 'Tap the map to set a start point.'}
          </Text>
          <Row style={{ marginTop: 6, flexWrap: 'wrap' }}>
            <Text style={{ color: p.muted, fontSize: 13 }}>Max detour:</Text>
            {DETOUR_OPTIONS_KM.map((km) => (
              <Chip
                key={km}
                label={`${km} km`}
                active={draft.detourKm === km}
                onPress={() => setDraft((d) => ({ ...d, detourKm: km, result: null }))}
              />
            ))}
          </Row>
          {draft.result && (
            <Text style={{ color: p.text, fontSize: 13, marginTop: 4 }}>
              {formatKm(draft.result.totalM)} total • {formatKm(draft.result.trailM)} on{' '}
              {draft.result.trailsUsed.length} trail
              {draft.result.trailsUsed.length === 1 ? '' : 's'} • direct would be{' '}
              {formatKm(draft.result.directM)}
            </Text>
          )}
          <Row style={{ marginTop: 8 }}>
            <Button
              label={draft.result ? 'Rebuild route' : 'Build route'}
              style={{ flex: 1 }}
              disabled={!draft.to || (!draft.from && !myLocation)}
              onPress={buildRoute}
            />
            <Button
              label="Clear"
              variant="secondary"
              onPress={() => setDraft({ from: null, to: null, detourKm: draft.detourKm, result: null })}
            />
          </Row>
        </View>
      )}
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
  sheetTitle: { fontSize: 17, fontWeight: '700' },
});
