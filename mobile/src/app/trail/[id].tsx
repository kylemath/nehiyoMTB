import { router, useLocalSearchParams, useNavigation } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import MapView, { Marker, Polyline } from '@/components/map';
import { openDirections } from '@/app/(tabs)/map';
import { DifficultyBadge } from '@/components/route-itinerary';
import { TrailIconBadge } from '@/components/trail-icon';
import { Body, Button, Card, Row, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { LocalCapture, listCaptures, pairTrailTimes } from '@/lib/captures';
import { formatDuration, formatKm, regionForPoints } from '@/lib/geo';
import { trackToLatLng, trailById } from '@/lib/trails';

/** Filament colour names from the catalogue → display colours. */
const FILAMENT_COLORS: Record<string, string> = {
  white: '#F4F4F2',
  black: '#1A1A1A',
  red: '#C8362E',
  blue: '#2A5DA8',
  yellow: '#E8C12F',
  green: '#2E7D4F',
  brown: '#6B4A2F',
  midbrown: '#8A6240',
  grey: '#8E9494',
  gray: '#8E9494',
  silver: '#B9BEC4',
  gold: '#C9A33B',
  orange: '#D97A2B',
  purple: '#6C4A9C',
};

function cssColor(name: string): string {
  return FILAMENT_COLORS[name.toLowerCase()] ?? Brand.stone;
}

export default function TrailDetail() {
  const p = usePalette();
  const { id } = useLocalSearchParams<{ id: string }>();
  const navigation = useNavigation();
  const trail = trailById(id);
  const [captures, setCaptures] = useState<LocalCapture[]>([]);

  useEffect(() => {
    if (trail) navigation.setOptions({ title: trail.title });
    listCaptures().then(setCaptures);
  }, [trail, navigation]);

  const points = useMemo(() => (trail ? trackToLatLng(trail.track) : []), [trail]);

  if (!trail) {
    return (
      <Screen style={{ alignItems: 'center', justifyContent: 'center' }}>
        <Body>Trail not found.</Body>
      </Screen>
    );
  }

  const myTimes = pairTrailTimes(captures).filter((t) => t.trailId === trail.id);
  const startCaptured = captures.some((c) => c.signId === `${trail.id}:start` && c.points > 0);
  const endCaptured = captures.some((c) => c.signId === `${trail.id}:end` && c.points > 0);

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        <Row style={{ gap: 12 }}>
          <TrailIconBadge trail={trail} size={52} />
          <View style={{ flex: 1 }}>
            <Title>{trail.title}</Title>
            {trail.creeName ? (
              <Subtitle>
                {trail.creeName}
                {trail.creeSyllabics ? ` • ${trail.creeSyllabics}` : ''}
                {trail.englishName && trail.englishName !== trail.title
                  ? ` • ${trail.englishName}`
                  : ''}
              </Subtitle>
            ) : null}
          </View>
        </Row>

        {trail.hasIcon && (
          <Card style={{ alignItems: 'center', gap: 10, paddingVertical: 20 }}>
            <TrailIconBadge trail={trail} size={120} />
            <Subtitle>The sign to find on this trail</Subtitle>
            {trail.colors.length > 0 && (
              <Row style={{ flexWrap: 'wrap', justifyContent: 'center' }}>
                {[...new Set(trail.colors)].map((c) => (
                  <View key={c} style={[styles.colorChip, { borderColor: p.border }]}>
                    <View style={[styles.colorDot, { backgroundColor: cssColor(c) }]} />
                    <Text style={{ color: p.muted, fontSize: 12 }}>{c}</Text>
                  </View>
                ))}
              </Row>
            )}
          </Card>
        )}

        {points.length > 1 && (
          <Pressable
            onPress={() =>
              router.push({
                pathname: '/map',
                params: { highlightTrail: trail.id, t: String(Date.now()) },
              })
            }>
            {/* pointerEvents none: the preview map must not swallow the tap */}
            <View pointerEvents="none">
              <MapView
                style={styles.map}
                initialRegion={regionForPoints(points)}
                scrollEnabled={false}
                zoomEnabled={false}
                pitchEnabled={false}
                rotateEnabled={false}>
                <Polyline coordinates={points} strokeColor={trail.accentColor} strokeWidth={4} />
                {trail.start?.lat != null && (
                  <Marker
                    coordinate={{ latitude: trail.start.lat, longitude: trail.start.lng! }}
                    pinColor={Brand.pine}
                    title="Start sign"
                  />
                )}
                {trail.end?.lat != null && (
                  <Marker
                    coordinate={{ latitude: trail.end.lat, longitude: trail.end.lng! }}
                    pinColor={Brand.ember}
                    title="End sign"
                  />
                )}
              </MapView>
            </View>
            <Text style={[styles.mapHint, { color: p.muted }]}>Tap to open in the full map</Text>
          </Pressable>
        )}

        <Card>
          <Row style={{ justifyContent: 'space-between' }}>
            <Stat label="Length" value={trail.lengthM ? formatKm(trail.lengthM) : '—'} />
            {trail.difficulty ? (
              <View style={{ alignItems: 'center', flex: 1, gap: 3 }}>
                <DifficultyBadge difficulty={trail.difficulty} />
                <Text style={{ color: p.muted, fontSize: 12 }}>Difficulty</Text>
              </View>
            ) : null}
            <Stat label="Start sign" value={startCaptured ? 'Collected' : 'Not yet'} />
            <Stat label="End sign" value={endCaptured ? 'Collected' : 'Not yet'} />
          </Row>
        </Card>

        {trail.description ? (
          <Card>
            <Body>{trail.description}</Body>
          </Card>
        ) : null}

        {myTimes.length > 0 && (
          <Card>
            <Body style={{ fontWeight: '600' }}>Your times</Body>
            {myTimes.map((t) => (
              <Row key={t.startCapture.id} style={{ justifyContent: 'space-between' }}>
                <Subtitle>{new Date(t.startCapture.takenAt).toLocaleDateString()}</Subtitle>
                <Text style={{ color: Brand.amber, fontWeight: '800' }}>
                  {formatDuration(t.elapsedS)}
                </Text>
              </Row>
            ))}
          </Card>
        )}

        {trail.start?.lat != null && (
          <>
            <Button
              label="Directions to trail start"
              onPress={() =>
                router.push({
                  pathname: '/map',
                  params: { destTrail: trail.id, t: String(Date.now()) },
                })
              }
            />
            <Button
              label="Open in external maps"
              variant="ghost"
              onPress={() =>
                openDirections(
                  { latitude: trail.start!.lat!, longitude: trail.start!.lng! },
                  trail.title,
                )
              }
            />
          </>
        )}
        <Button label="Capture a sign here" variant="secondary" onPress={() => router.push('/capture')} />
      </ScrollView>
    </Screen>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  const p = usePalette();
  return (
    <View style={{ alignItems: 'center', flex: 1 }}>
      <Text style={{ color: p.text, fontWeight: '700', fontSize: 15 }}>{value}</Text>
      <Text style={{ color: p.muted, fontSize: 12 }}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  map: { height: 220, borderRadius: 16 },
  mapHint: { fontSize: 12, textAlign: 'center', marginTop: 6 },
  colorChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 3,
    paddingHorizontal: 9,
  },
  colorDot: { width: 12, height: 12, borderRadius: 6, borderWidth: StyleSheet.hairlineWidth, borderColor: '#00000033' },
});
