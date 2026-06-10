import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { SHARE_LEVELS, SHARE_LEVEL_INFO, ShareLevel } from '@/constants/brand';
import { usePalette } from '@/components/ui';

/**
 * The single place users make data-use decisions. Shows what each choice
 * means in plain words before anything leaves the device.
 */
export function ShareLevelPicker({
  value,
  onChange,
}: {
  value: ShareLevel;
  onChange: (level: ShareLevel) => void;
}) {
  const p = usePalette();
  const [expanded, setExpanded] = useState<ShareLevel | null>(null);

  return (
    <View style={{ gap: 8 }}>
      {SHARE_LEVELS.map((level) => {
        const info = SHARE_LEVEL_INFO[level];
        const active = value === level;
        return (
          <Pressable
            key={level}
            onPress={() => {
              onChange(level);
              setExpanded(expanded === level ? null : level);
            }}
            style={[
              styles.option,
              {
                borderColor: active ? p.primary : p.border,
                backgroundColor: active ? `${p.primary}14` : p.surface,
              },
            ]}>
            <View style={styles.header}>
              <View style={[styles.radio, { borderColor: active ? p.primary : p.border }]}>
                {active && <View style={[styles.radioDot, { backgroundColor: p.primary }]} />}
              </View>
              <Text style={[styles.label, { color: p.text }]}>{info.label}</Text>
            </View>
            <Text style={[styles.summary, { color: p.muted }]}>{info.summary}</Text>
            {expanded === level && (
              <Text style={[styles.detail, { color: p.muted }]}>{info.detail}</Text>
            )}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  option: { borderWidth: 1.5, borderRadius: 12, padding: 12, gap: 4 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioDot: { width: 10, height: 10, borderRadius: 5 },
  label: { fontSize: 15, fontWeight: '600' },
  summary: { fontSize: 13, lineHeight: 18, marginLeft: 30 },
  detail: { fontSize: 13, lineHeight: 18, marginLeft: 30, marginTop: 4, fontStyle: 'italic' },
});
