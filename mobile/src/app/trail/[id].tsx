import { router, useLocalSearchParams, useNavigation } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Polyline } from 'react-native-maps';

import { openDirections } from '@/app/(tabs)/index';
import { Body, Button, Card, Row, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { LocalCapture, listCaptures, pairTrailTimes } from '@/lib/captures';
import { formatDuration, formatKm, regionForPoints } from '@/lib/geo';
import { trackToLatLng, trailById } from '@/lib/trails';

export default function TrailDetail() {
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
        <View>
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

        {points.length > 1 && (
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
        )}

        <Card>
          <Row style={{ justifyContent: 'space-between' }}>
            <Stat label="Length" value={trail.lengthM ? formatKm(trail.lengthM) : '—'} />
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
          <Button
            label="Directions to trail start"
            onPress={() =>
              openDirections(
                { latitude: trail.start!.lat!, longitude: trail.start!.lng! },
                trail.title,
              )
            }
          />
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
});
