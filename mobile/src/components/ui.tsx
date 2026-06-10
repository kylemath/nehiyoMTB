import React from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleProp,
  StyleSheet,
  Text,
  TextStyle,
  View,
  ViewStyle,
  useColorScheme,
} from 'react-native';

import { Brand } from '@/constants/brand';

export function usePalette() {
  const dark = useColorScheme() === 'dark';
  return {
    dark,
    bg: dark ? Brand.ink : Brand.paper,
    surface: dark ? Brand.nightElement : '#FFFFFF',
    text: dark ? Brand.paper : Brand.ink,
    muted: Brand.stone,
    border: dark ? '#2C332F' : Brand.mist,
    primary: dark ? Brand.moss : Brand.pine,
  };
}

export function Screen({ children, style }: { children?: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  const p = usePalette();
  return <View style={[styles.screen, { backgroundColor: p.bg }, style]}>{children}</View>;
}

export function Card({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  const p = usePalette();
  return (
    <View style={[styles.card, { backgroundColor: p.surface, borderColor: p.border }, style]}>
      {children}
    </View>
  );
}

export function Title({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  const p = usePalette();
  return <Text style={[styles.title, { color: p.text }, style]}>{children}</Text>;
}

export function Subtitle({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  const p = usePalette();
  return <Text style={[styles.subtitle, { color: p.muted }, style]}>{children}</Text>;
}

export function Body({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  const p = usePalette();
  return <Text style={[styles.body, { color: p.text }, style]}>{children}</Text>;
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  disabled,
  loading,
  style,
}: {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const p = usePalette();
  const bg =
    variant === 'primary' ? p.primary
    : variant === 'danger' ? Brand.ember
    : variant === 'secondary' ? p.surface
    : 'transparent';
  const fg = variant === 'primary' || variant === 'danger' ? '#FFFFFF' : p.primary;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, opacity: disabled ? 0.5 : pressed ? 0.85 : 1 },
        variant === 'secondary' && { borderWidth: 1, borderColor: p.border },
        style,
      ]}>
      {loading ? (
        <ActivityIndicator color={fg} />
      ) : (
        <Text style={[styles.buttonLabel, { color: fg }]}>{label}</Text>
      )}
    </Pressable>
  );
}

export function Chip({
  label,
  active,
  onPress,
  color,
}: {
  label: string;
  active?: boolean;
  onPress?: () => void;
  color?: string;
}) {
  const p = usePalette();
  const tint = color ?? p.primary;
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={[
        styles.chip,
        { borderColor: active ? tint : p.border, backgroundColor: active ? `${tint}22` : 'transparent' },
      ]}>
      <Text style={{ color: active ? tint : p.muted, fontSize: 13, fontWeight: '600' }}>
        {label}
      </Text>
    </Pressable>
  );
}

export function Row({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.row, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  card: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
    gap: 8,
  },
  title: { fontSize: 22, fontWeight: '700', letterSpacing: -0.3 },
  subtitle: { fontSize: 14, lineHeight: 20 },
  body: { fontSize: 15, lineHeight: 21 },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonLabel: { fontSize: 16, fontWeight: '600' },
  chip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
});
