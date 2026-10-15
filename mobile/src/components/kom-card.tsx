// Per-trail KOM board (top verified times) and the free KOM-sign reward for
// the top three. See lib/shop.ts and supabase/migrations/0003_kom.sql.
import * as WebBrowser from 'expo-web-browser';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Text, View } from 'react-native';

import { Body, Button, Card, Row, Subtitle, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { useAuth } from '@/lib/auth';
import { formatDuration } from '@/lib/geo';
import { KomRow, claimKomReward, fetchKomBoard } from '@/lib/shop';
import { Trail } from '@/lib/trails';

const MEDALS = ['🥇', '🥈', '🥉'];

export function KomCard({ trail }: { trail: Trail }) {
  const p = usePalette();
  const { session, backendConfigured } = useAuth();
  const [rows, setRows] = useState<KomRow[] | null>(null);
  const [claiming, setClaiming] = useState(false);
  const signedIn = Boolean(session) && backendConfigured;

  useEffect(() => {
    if (!signedIn) return;
    let live = true;
    fetchKomBoard(trail.id)
      .then((r) => live && setRows(r))
      .catch(() => live && setRows([]));
    return () => {
      live = false;
    };
  }, [trail.id, signedIn]);

  const mine = rows?.find((r) => r.user_id === session?.user.id);
  const eligible = mine != null && mine.rank <= 3;

  const claim = async () => {
    setClaiming(true);
    try {
      const { checkoutUrl } = await claimKomReward(trail.id);
      await WebBrowser.openBrowserAsync(checkoutUrl);
    } catch (e) {
      Alert.alert('Could not claim yet', e instanceof Error ? e.message : 'Try again later.');
    } finally {
      setClaiming(false);
    }
  };

  return (
    <Card>
      <Row style={{ justifyContent: 'space-between' }}>
        <Body style={{ fontWeight: '700' }}>KOM board</Body>
        <Text style={{ color: Brand.amber, fontWeight: '700', fontSize: 12 }}>
          Top 3 get the KOM sign free
        </Text>
      </Row>
      {!signedIn ? (
        <Subtitle>
          Sign in and photograph the start and end signs on one ride to post a verified time.
        </Subtitle>
      ) : rows == null ? (
        <ActivityIndicator color={Brand.pine} />
      ) : rows.length === 0 ? (
        <Subtitle>No verified times yet. Photograph both signs on one ride to take the crown.</Subtitle>
      ) : (
        rows.slice(0, 5).map((r) => (
          <Row key={r.user_id} style={{ justifyContent: 'space-between' }}>
            <Text style={{ color: p.text, fontWeight: r.user_id === session?.user.id ? '800' : '500' }}>
              {MEDALS[r.rank - 1] ?? `${r.rank}.`} {r.name}
            </Text>
            <Text style={{ color: r.rank <= 3 ? Brand.amber : p.muted, fontWeight: '700' }}>
              {formatDuration(r.elapsed_s)}
            </Text>
          </Row>
        ))
      )}
      {eligible && (
        <View style={{ marginTop: 6 }}>
          <Button label="Claim your free KOM sign" onPress={claim} loading={claiming} />
        </View>
      )}
    </Card>
  );
}
