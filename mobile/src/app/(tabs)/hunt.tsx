import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { TrailIconBadge } from '@/components/trail-icon';
import { Button, Card, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { LocalCapture, listCaptures, localScore } from '@/lib/captures';
import { Trail, displayName, mappedTrails } from '@/lib/trails';

export default function HuntTab() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const [captures, setCaptures] = useState<LocalCapture[]>([]);

  useFocusEffect(
    useCallback(() => {
      listCaptures().then(setCaptures);
    }, []),
  );

  const score = localScore(captures);
  const captured = score.signsCollected;

  const renderTrail = ({ item: trail }: { item: Trail }) => {
    const hasStart = captured.has(`${trail.id}:start`);
    const hasEnd = captured.has(`${trail.id}:end`);
    return (
      <Pressable onPress={() => router.push(`/trail/${trail.id}`)}>
        <Card style={styles.trailCard}>
          <TrailIconBadge trail={trail} size={56} />
          <View style={{ flex: 1 }}>
            <Text style={{ color: p.text, fontWeight: '600', fontSize: 15 }}>
              {displayName(trail)}
            </Text>
            {trail.creeSyllabics ? (
              <Text style={{ color: p.muted, fontSize: 13 }}>{trail.creeSyllabics}</Text>
            ) : null}
          </View>
          <View style={styles.signBadges}>
            <SignBadge label="Start" done={hasStart} />
            <SignBadge label="End" done={hasEnd} />
          </View>
        </Card>
      </Pressable>
    );
  };

  return (
    <Screen>
      <FlatList
        data={mappedTrails}
        keyExtractor={(t) => t.id}
        renderItem={renderTrail}
        // Mount and draw every row up front (the list is small): this is what
        // warms the icon bitmap cache that the Map tab's markers rely on.
        initialNumToRender={mappedTrails.length}
        removeClippedSubviews={false}
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingHorizontal: 16,
          paddingBottom: insets.bottom + 90,
          gap: 10,
        }}
        ListHeaderComponent={
          <View style={{ gap: 12, marginBottom: 12 }}>
            <Title>Sign hunt</Title>
            <Subtitle>
              Photograph the signs at trail starts and ends to collect points. Photo timestamps
              double as your trail timer.
            </Subtitle>
            <Card>
              <View style={styles.scoreRow}>
                <ScoreCell label="Overall" value={score.overall} />
                <ScoreCell label="This week" value={score.weekly} />
                <ScoreCell label="Weekend" value={score.weekend} />
                <ScoreCell label="Signs" value={captured.size} />
              </View>
            </Card>
          </View>
        }
      />
      <View style={[styles.captureBar, { bottom: insets.bottom + 16 }]}>
        <Button
          label="Capture a sign"
          onPress={() => router.push('/capture')}
          style={{ flex: 1, shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 8 }}
        />
      </View>
    </Screen>
  );
}

function ScoreCell({ label, value }: { label: string; value: number }) {
  const p = usePalette();
  return (
    <View style={{ alignItems: 'center', flex: 1 }}>
      <Text style={{ fontSize: 22, fontWeight: '800', color: Brand.amber }}>{value}</Text>
      <Text style={{ fontSize: 12, color: p.muted }}>{label}</Text>
    </View>
  );
}

function SignBadge({ label, done }: { label: string; done: boolean }) {
  const p = usePalette();
  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: done ? `${Brand.moss}22` : 'transparent',
          borderColor: done ? Brand.moss : p.border,
        },
      ]}>
      <Ionicons
        name={done ? 'checkmark-circle' : 'ellipse-outline'}
        size={14}
        color={done ? Brand.moss : p.muted}
      />
      <Text style={{ fontSize: 12, color: done ? Brand.moss : p.muted, fontWeight: '600' }}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  trailCard: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 12 },
  signBadges: { flexDirection: 'row', gap: 6 },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  scoreRow: { flexDirection: 'row' },
  captureBar: { position: 'absolute', left: 16, right: 16, flexDirection: 'row' },
});
