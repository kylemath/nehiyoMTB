import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import { Alert, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ShareLevelPicker } from '@/components/share-level-picker';
import { Body, Button, Card, Screen, Subtitle, Title } from '@/components/ui';
import { Brand, ShareLevel } from '@/constants/brand';
import { CAPTURE_RADIUS_M, nearestSign, saveCapture, uploadCapture } from '@/lib/captures';
import { useAuth } from '@/lib/auth';
import { trailById } from '@/lib/trails';

type Shot = {
  uri: string;
  takenAt: Date;
  lat: number | null;
  lng: number | null;
  accuracyM: number | null;
};

export default function CaptureScreen() {
  const insets = useSafeAreaInsets();
  const { session, backendConfigured } = useAuth();
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [shot, setShot] = useState<Shot | null>(null);
  const [shareLevel, setShareLevel] = useState<ShareLevel>('private');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        setLocation(await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High }));
      }
    })();
  }, []);

  if (!permission) return <Screen />;

  if (!permission.granted) {
    return (
      <Screen style={[styles.center, { paddingTop: insets.top }]}>
        <Card style={{ margin: 20, alignItems: 'center', gap: 12 }}>
          <Title>Camera access</Title>
          <Subtitle style={{ textAlign: 'center' }}>
            The sign hunt uses your camera to photograph trail signs. Photos stay on your phone
            unless you choose to upload them.
          </Subtitle>
          <Button label="Allow camera" onPress={requestPermission} />
          <Button label="Cancel" variant="ghost" onPress={() => router.back()} />
        </Card>
      </Screen>
    );
  }

  const takePhoto = async () => {
    const photo = await cameraRef.current?.takePictureAsync({ exif: true, quality: 0.7 });
    if (!photo) return;
    // Refresh the fix at the moment of capture when possible.
    let loc = location;
    try {
      loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
      setLocation(loc);
    } catch {
      // keep the last known fix
    }
    setShot({
      uri: photo.uri,
      takenAt: new Date(),
      lat: loc?.coords.latitude ?? null,
      lng: loc?.coords.longitude ?? null,
      accuracyM: loc?.coords.accuracy ?? null,
    });
  };

  const near = shot && shot.lat != null && shot.lng != null ? nearestSign(shot.lat, shot.lng) : null;
  const inRange = near != null && near.distanceM <= CAPTURE_RADIUS_M;
  const nearTrail = near ? trailById(near.sign.trailId) : null;

  const save = async () => {
    if (!shot || !near) return;
    setSaving(true);
    try {
      const capture = await saveCapture({
        signId: near.sign.id,
        takenAt: shot.takenAt,
        lat: shot.lat,
        lng: shot.lng,
        accuracyM: shot.accuracyM,
        photoUri: shot.uri,
        shareLevel,
      });
      if (session && backendConfigured && shareLevel !== 'private') {
        try {
          await uploadCapture(capture, session.user.id);
        } catch {
          Alert.alert('Saved locally', 'Upload failed — it will stay on your phone for now.');
        }
      }
      router.back();
    } finally {
      setSaving(false);
    }
  };

  if (shot) {
    return (
      <Screen>
        <ScrollView
          contentContainerStyle={{
            paddingTop: insets.top + 16,
            paddingHorizontal: 16,
            paddingBottom: insets.bottom + 24,
            gap: 14,
          }}>
          <Title>Sign captured?</Title>
          <Image source={{ uri: shot.uri }} style={styles.preview} />
          <Card>
            {near && nearTrail ? (
              <>
                <Body style={{ fontWeight: '700' }}>
                  {inRange ? 'Matched: ' : 'Nearest sign: '}
                  {nearTrail.title} — {near.sign.kind === 'start' ? 'start' : 'end'} sign
                </Body>
                <Subtitle>
                  {Math.round(near.distanceM)} m away
                  {inRange
                    ? ` • verified, +${near.sign.basePoints} points (first capture today)`
                    : ` • outside the ${CAPTURE_RADIUS_M} m verification radius, saved unverified`}
                </Subtitle>
              </>
            ) : (
              <Subtitle>
                No GPS fix — the photo will be saved unverified. Turn on location services to earn
                points.
              </Subtitle>
            )}
            <Subtitle>
              Photo time {shot.takenAt.toLocaleTimeString()} — pairs with this trail&apos;s other
              sign to estimate your ride time.
            </Subtitle>
          </Card>
          <Card>
            <Body style={{ fontWeight: '600', marginBottom: 4 }}>Who can see this photo?</Body>
            <ShareLevelPicker value={shareLevel} onChange={setShareLevel} />
            {!session && (
              <Subtitle style={{ marginTop: 6 }}>
                You&apos;re exploring without an account, so everything stays on this phone. Sign in
                to sync and share.
              </Subtitle>
            )}
          </Card>
          <Button label="Save capture" loading={saving} disabled={!near} onPress={save} />
          <Button label="Retake" variant="secondary" onPress={() => setShot(null)} />
          <Button label="Discard" variant="ghost" onPress={() => router.back()} />
        </ScrollView>
      </Screen>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />
      <Pressable
        onPress={() => router.back()}
        style={[styles.close, { top: insets.top + 12 }]}
        hitSlop={12}>
        <Ionicons name="close" size={26} color="#fff" />
      </Pressable>
      <View style={[styles.hint, { top: insets.top + 14 }]}>
        <Text style={styles.hintText}>
          {location
            ? 'Frame the trail sign and shoot'
            : 'Waiting for GPS — photos without a fix are unverified'}
        </Text>
      </View>
      <View style={[styles.shutterRow, { bottom: insets.bottom + 30 }]}>
        <Pressable onPress={takePhoto} style={styles.shutter}>
          <View style={styles.shutterInner} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', justifyContent: 'center' },
  preview: { width: '100%', aspectRatio: 3 / 4, borderRadius: 16 },
  close: {
    position: 'absolute',
    left: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  hint: {
    position: 'absolute',
    alignSelf: 'center',
    backgroundColor: 'rgba(0,0,0,0.45)',
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  hintText: { color: '#fff', fontSize: 13 },
  shutterRow: { position: 'absolute', left: 0, right: 0, alignItems: 'center' },
  shutter: {
    width: 74,
    height: 74,
    borderRadius: 37,
    borderWidth: 4,
    borderColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterInner: { width: 58, height: 58, borderRadius: 29, backgroundColor: Brand.amber },
});
