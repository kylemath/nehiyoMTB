import * as Location from 'expo-location';
import React, { useEffect, useState } from 'react';
import { Alert, ScrollView, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ShareLevelPicker } from '@/components/share-level-picker';
import { Body, Button, Card, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { APP_NAME, ShareLevel } from '@/constants/brand';
import { useAuth } from '@/lib/auth';
import { HomeLocation, pullHomeFromProfile, setHome } from '@/lib/home';
import { supabase } from '@/lib/supabase';

export default function ProfileTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const { session, guest, backendConfigured, signOut } = useAuth();
  const [defaultShare, setDefaultShare] = useState<ShareLevel>('private');
  const [home, setHomeValue] = useState<HomeLocation | null>(null);
  const [settingHome, setSettingHome] = useState(false);

  useEffect(() => {
    pullHomeFromProfile().then(setHomeValue);
  }, []);

  const setHomeToCurrent = async () => {
    setSettingHome(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Location needed', 'Allow location access to save your home location.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({});
      const coord = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
      await setHome(coord);
      setHomeValue(coord);
    } finally {
      setSettingHome(false);
    }
  };

  const clearHome = async () => {
    await setHome(null);
    setHomeValue(null);
  };

  useEffect(() => {
    if (!session || !backendConfigured) return;
    supabase
      .from('profiles')
      .select('default_share_level')
      .eq('id', session.user.id)
      .single()
      .then(({ data }) => {
        if (data?.default_share_level) setDefaultShare(data.default_share_level as ShareLevel);
      });
  }, [session, backendConfigured]);

  const updateDefault = async (level: ShareLevel) => {
    setDefaultShare(level);
    if (session && backendConfigured) {
      await supabase.from('profiles').update({ default_share_level: level }).eq('id', session.user.id);
    }
  };

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingHorizontal: 16,
          paddingBottom: insets.bottom + 24,
          gap: 14,
        }}>
        <Title>You</Title>

        <Card>
          <Body style={{ fontWeight: '700' }}>
            {session ? (session.user.email ?? 'Signed in') : 'Exploring without an account'}
          </Body>
          <Subtitle>
            {session
              ? 'Your captures and rides can sync to your account at the share level you choose.'
              : 'Everything is saved on this phone only. Sign in to sync, share and join leaderboards.'}
          </Subtitle>
        </Card>

        <Card>
          <Body style={{ fontWeight: '600' }}>Home location</Body>
          <Subtitle>
            {home
              ? `Saved at ${home.latitude.toFixed(5)}, ${home.longitude.toFixed(5)}. `
              : 'Not set yet. '}
            Used as the starting point for bike routes. You can also drop a map pin in the route
            builder to set it.
          </Subtitle>
          <Button
            label="Set to current location"
            variant="secondary"
            loading={settingHome}
            onPress={setHomeToCurrent}
          />
          {home && <Button label="Clear" variant="ghost" onPress={clearHome} />}
        </Card>

        {session && (
          <Card>
            <Body style={{ fontWeight: '600', marginBottom: 4 }}>
              Default choice for new uploads
            </Body>
            <Subtitle style={{ marginBottom: 8 }}>
              Every photo and ride still asks before it leaves your phone — this just sets which
              option is pre-selected.
            </Subtitle>
            <ShareLevelPicker value={defaultShare} onChange={updateDefault} />
          </Card>
        )}

        <Card>
          <Body style={{ fontWeight: '600' }}>How {APP_NAME} treats your data</Body>
          <Subtitle>
            • Photos and GPS tracks are yours. Nothing uploads without an explicit choice.{'\n'}
            • &ldquo;Just for me&rdquo; uploads are visible only to you — they exist as your proof
            of arrival.{'\n'}
            • &ldquo;Contribute&rdquo; shares with the trail-mapping team only, to improve
            Edmonton&apos;s trail maps and wayfinding. Never public, never sold.{'\n'}
            • &ldquo;Share with riders&rdquo; is visible in-app and can be reverted any time.{'\n'}
            • Leaderboards show only your name and points — never photos or locations.{'\n'}
            • Deleting a capture or ride removes it from our servers too.
          </Subtitle>
        </Card>

        <Button
          label={guest && !session ? 'Sign in or create account' : 'Sign out'}
          variant="secondary"
          onPress={signOut}
        />
        <Text style={{ textAlign: 'center', color: p.muted, fontSize: 12 }}>
          {APP_NAME} • built around the Edmonton river-valley sign set
        </Text>
      </ScrollView>
    </Screen>
  );
}
