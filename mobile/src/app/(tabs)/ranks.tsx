import { useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Body, Card, Chip, Row, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { useAuth } from '@/lib/auth';
import { listCaptures, localScore } from '@/lib/captures';
import { supabase } from '@/lib/supabase';

const PERIODS = [
  { key: 'overall', label: 'Overall', view: 'leaderboard_overall' },
  { key: 'weekly', label: 'This week', view: 'leaderboard_weekly' },
  { key: 'weekend', label: 'Weekend', view: 'leaderboard_weekend' },
] as const;

type Period = (typeof PERIODS)[number]['key'];
type BoardRow = { user_id: string; name: string; points: number; captures: number };

export default function RanksTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const { session, backendConfigured } = useAuth();
  const [period, setPeriod] = useState<Period>('overall');
  const [rows, setRows] = useState<BoardRow[] | null>(null);
  const [myScore, setMyScore] = useState({ overall: 0, weekly: 0, weekend: 0 });

  useFocusEffect(
    useCallback(() => {
      listCaptures().then((captures) => {
        const s = localScore(captures);
        setMyScore({ overall: s.overall, weekly: s.weekly, weekend: s.weekend });
      });
    }, []),
  );

  useFocusEffect(
    useCallback(() => {
      if (!session || !backendConfigured) {
        setRows(null);
        return;
      }
      const view = PERIODS.find((x) => x.key === period)!.view;
      supabase
        .from(view)
        .select('*')
        .order('points', { ascending: false })
        .limit(50)
        .then(({ data }) => setRows((data as BoardRow[]) ?? []));
    }, [period, session, backendConfigured]),
  );

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingHorizontal: 16,
          paddingBottom: insets.bottom + 24,
          gap: 14,
        }}>
        <Title>Leaderboards</Title>
        <Row>
          {PERIODS.map((x) => (
            <Chip
              key={x.key}
              label={x.label}
              active={period === x.key}
              onPress={() => setPeriod(x.key)}
            />
          ))}
        </Row>

        <Card>
          <Subtitle>Your {PERIODS.find((x) => x.key === period)!.label.toLowerCase()} score</Subtitle>
          <Text style={{ fontSize: 32, fontWeight: '800', color: Brand.amber }}>
            {myScore[period]}
          </Text>
        </Card>

        {session && backendConfigured ? (
          rows && rows.length > 0 ? (
            <View style={{ gap: 8 }}>
              {rows.map((row, i) => (
                <Card key={row.user_id} style={styles.rankRow}>
                  <Text style={[styles.rank, { color: i < 3 ? Brand.amber : p.muted }]}>
                    {i + 1}
                  </Text>
                  <Text style={{ flex: 1, color: p.text, fontWeight: '600' }}>{row.name}</Text>
                  <Text style={{ color: p.muted, fontSize: 12 }}>{row.captures} signs</Text>
                  <Text style={{ color: Brand.amber, fontWeight: '800' }}>{row.points}</Text>
                </Card>
              ))}
            </View>
          ) : (
            <Card>
              <Body>No scores yet for this period. Get out and capture some signs.</Body>
            </Card>
          )
        ) : (
          <Card>
            <Body style={{ fontWeight: '600' }}>Riding solo for now</Body>
            <Subtitle>
              Your points are tracked on this phone. Sign in to join the community leaderboards —
              only your name and points are ever shown, never your photos or locations.
            </Subtitle>
          </Card>
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  rankRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12 },
  rank: { width: 26, fontSize: 16, fontWeight: '800', textAlign: 'center' },
});
