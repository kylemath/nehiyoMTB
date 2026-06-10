import { useFocusEffect } from 'expo-router';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ShareLevelPicker } from '@/components/share-level-picker';
import { Body, Button, Card, Row, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { Brand, ShareLevel } from '@/constants/brand';
import { useAuth } from '@/lib/auth';
import { LocalCapture, listCaptures, pairTrailTimes } from '@/lib/captures';
import { formatDuration, formatKm } from '@/lib/geo';
import {
  LocalRide,
  RideRecorder,
  listRides,
  rideToGpx,
  saveRide,
  syncPhotosWithRide,
  uploadRide,
} from '@/lib/rides';
import { trailById } from '@/lib/trails';

export default function RideTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const { session, backendConfigured } = useAuth();
  const recorderRef = useRef(new RideRecorder());
  const [recording, setRecording] = useState(false);
  const [live, setLive] = useState<LocalRide | null>(null);
  const [rides, setRides] = useState<LocalRide[]>([]);
  const [captures, setCaptures] = useState<LocalCapture[]>([]);
  const [pendingRide, setPendingRide] = useState<LocalRide | null>(null);
  const [pendingShare, setPendingShare] = useState<ShareLevel>('private');
  const [elapsed, setElapsed] = useState(0);

  const refresh = useCallback(() => {
    listRides().then(setRides);
    listCaptures().then(setCaptures);
  }, []);

  useFocusEffect(refresh);

  useEffect(() => {
    if (!recording) return;
    const interval = setInterval(() => {
      const r = recorderRef.current.ride;
      if (r) setElapsed(Math.round((Date.now() - new Date(r.startedAt).getTime()) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [recording]);

  const start = async () => {
    try {
      recorderRef.current.onUpdate = (r) => setLive({ ...r });
      await recorderRef.current.start();
      setRecording(true);
      setElapsed(0);
    } catch (e) {
      Alert.alert('Cannot record', e instanceof Error ? e.message : 'Location unavailable.');
    }
  };

  const stop = async () => {
    const finished = await recorderRef.current.stop();
    setRecording(false);
    setLive(null);
    if (finished && finished.points.length > 1) {
      setPendingRide(finished);
      setPendingShare('private');
    }
    refresh();
  };

  const confirmPending = async () => {
    if (!pendingRide) return;
    const ride = { ...pendingRide, shareLevel: pendingShare };
    await saveRide(ride);
    if (session && backendConfigured && pendingShare !== 'private') {
      try {
        await uploadRide(ride, session.user.id);
      } catch {
        Alert.alert('Saved locally', 'Upload failed — your ride is safe on this phone.');
      }
    }
    setPendingRide(null);
    refresh();
  };

  const trailTimes = pairTrailTimes(captures);

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingHorizontal: 16,
          paddingBottom: insets.bottom + 24,
          gap: 14,
        }}>
        <Title>Ride</Title>

        <Card style={{ alignItems: 'center', gap: 10 }}>
          {recording ? (
            <>
              <Text style={{ fontSize: 34, fontWeight: '800', color: p.text }}>
                {formatDuration(elapsed)}
              </Text>
              <Subtitle>
                {formatKm(live?.distanceM ?? 0)} • {live?.points.length ?? 0} GPS fixes
              </Subtitle>
              <Button label="Finish ride" variant="danger" onPress={stop} style={{ alignSelf: 'stretch' }} />
            </>
          ) : (
            <>
              <Body style={{ textAlign: 'center' }}>
                Log the GPS track of your ride. Your track stays on your phone unless you choose to
                share or contribute it.
              </Body>
              <Button label="Start ride" onPress={start} style={{ alignSelf: 'stretch' }} />
            </>
          )}
        </Card>

        {pendingRide && (
          <Card style={{ gap: 8 }}>
            <Body style={{ fontWeight: '700' }}>
              Ride saved — {formatKm(pendingRide.distanceM)}
            </Body>
            <Subtitle>Who can see this ride&apos;s GPS track?</Subtitle>
            <ShareLevelPicker value={pendingShare} onChange={setPendingShare} />
            <PhotoSyncSummary ride={pendingRide} captures={captures} />
            <Button label="Confirm" onPress={confirmPending} />
          </Card>
        )}

        {trailTimes.length > 0 && (
          <View style={{ gap: 8 }}>
            <Body style={{ fontWeight: '700', fontSize: 17 }}>Trail times (from sign photos)</Body>
            {trailTimes.slice(0, 10).map((tt) => {
              const trail = trailById(tt.trailId);
              return (
                <Card key={`${tt.trailId}-${tt.startCapture.id}`} style={styles.timeRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: p.text, fontWeight: '600' }}>
                      {trail?.title ?? tt.trailId}
                    </Text>
                    <Text style={{ color: p.muted, fontSize: 12 }}>
                      {new Date(tt.startCapture.takenAt).toLocaleString()}
                    </Text>
                  </View>
                  <Text style={{ color: Brand.amber, fontWeight: '800', fontSize: 18 }}>
                    {formatDuration(tt.elapsedS)}
                  </Text>
                </Card>
              );
            })}
          </View>
        )}

        {rides.length > 0 && (
          <View style={{ gap: 8 }}>
            <Body style={{ fontWeight: '700', fontSize: 17 }}>Past rides</Body>
            {rides.map((ride) => (
              <RideCard key={ride.id} ride={ride} captures={captures} onChanged={refresh} />
            ))}
          </View>
        )}
      </ScrollView>
    </Screen>
  );
}

function PhotoSyncSummary({ ride, captures }: { ride: LocalRide; captures: LocalCapture[] }) {
  const synced = syncPhotosWithRide(ride, captures);
  if (synced.length === 0) return null;
  const overhead = synced.reduce((sum, s) => sum + s.stationaryS, 0);
  return (
    <Subtitle>
      {synced.length} sign photo{synced.length === 1 ? '' : 's'} matched to this track — about{' '}
      {formatDuration(overhead)} of photo stops detected, so your riding-only pace can be
      estimated.
    </Subtitle>
  );
}

function RideCard({
  ride,
  captures,
  onChanged,
}: {
  ride: LocalRide;
  captures: LocalCapture[];
  onChanged: () => void;
}) {
  const p = usePalette();
  const { session, backendConfigured } = useAuth();
  const durationS = ride.endedAt
    ? Math.round((new Date(ride.endedAt).getTime() - new Date(ride.startedAt).getTime()) / 1000)
    : 0;
  const synced = syncPhotosWithRide(ride, captures);

  const exportGpx = async () => {
    await Share.share({
      message: rideToGpx(ride, `Ride ${ride.startedAt.slice(0, 10)}`),
      title: 'ride.gpx',
    });
  };

  return (
    <Card style={{ gap: 6 }}>
      <Row style={{ justifyContent: 'space-between' }}>
        <Text style={{ color: p.text, fontWeight: '600' }}>
          {new Date(ride.startedAt).toLocaleDateString()}{' '}
          {new Date(ride.startedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
        <Text style={{ color: p.muted, fontSize: 12 }}>
          {ride.shareLevel === 'private'
            ? 'Private'
            : ride.shareLevel === 'contribute'
              ? 'Contributed'
              : 'Public'}
          {ride.uploaded ? ' • synced' : ''}
        </Text>
      </Row>
      <Text style={{ color: p.muted, fontSize: 13 }}>
        {formatKm(ride.distanceM)} • {formatDuration(durationS)}
        {synced.length > 0 ? ` • ${synced.length} sign photo${synced.length === 1 ? '' : 's'}` : ''}
      </Text>
      <Row>
        <Button label="Export GPX" variant="secondary" onPress={exportGpx} style={{ flex: 1 }} />
        {session && backendConfigured && !ride.uploaded && ride.shareLevel !== 'private' && (
          <Button
            label="Upload"
            onPress={async () => {
              try {
                await uploadRide(ride, session.user.id);
                onChanged();
              } catch {
                Alert.alert('Upload failed', 'Your ride is still saved on this phone.');
              }
            }}
            style={{ flex: 1 }}
          />
        )}
      </Row>
    </Card>
  );
}

const styles = StyleSheet.create({
  timeRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 12 },
});
