import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Body, Button, Card, Screen, Subtitle, Title, usePalette } from '@/components/ui';
import { APP_NAME, APP_TAGLINE, Brand } from '@/constants/brand';
import { useAuth } from '@/lib/auth';

export default function SignInScreen() {
  const p = usePalette();
  const insets = useSafeAreaInsets();
  const auth = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (key: string, fn: () => Promise<string | null>) => {
    setBusy(key);
    setError(null);
    const message = await fn();
    if (message) setError(message);
    setBusy(null);
  };

  return (
    <Screen>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={[
            styles.content,
            { paddingTop: insets.top + 48, paddingBottom: insets.bottom + 24 },
          ]}>
          <View style={styles.brand}>
            <View style={[styles.mark, { backgroundColor: p.primary }]}>
              <Text style={styles.markText}>ET</Text>
            </View>
            <Title style={{ fontSize: 28 }}>{APP_NAME}</Title>
            <Subtitle>{APP_TAGLINE}</Subtitle>
          </View>

          <Card style={{ gap: 12 }}>
            <TextInput
              placeholder="Email"
              placeholderTextColor={p.muted}
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
              style={[styles.input, { borderColor: p.border, color: p.text }]}
            />
            <TextInput
              placeholder="Password"
              placeholderTextColor={p.muted}
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              style={[styles.input, { borderColor: p.border, color: p.text }]}
            />
            {error && <Text style={{ color: Brand.ember, fontSize: 13 }}>{error}</Text>}
            <Button
              label={mode === 'signin' ? 'Sign in' : 'Create account'}
              loading={busy === 'email'}
              onPress={() =>
                run('email', () =>
                  mode === 'signin'
                    ? auth.signInWithEmail(email.trim(), password)
                    : auth.signUpWithEmail(email.trim(), password),
                )
              }
            />
            <Button
              label={mode === 'signin' ? 'New here? Create an account' : 'Have an account? Sign in'}
              variant="ghost"
              onPress={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
            />
          </Card>

          <View style={styles.divider}>
            <View style={[styles.line, { backgroundColor: p.border }]} />
            <Subtitle>or</Subtitle>
            <View style={[styles.line, { backgroundColor: p.border }]} />
          </View>

          <View style={{ gap: 10 }}>
            <Button
              label="Continue with Google"
              variant="secondary"
              loading={busy === 'google'}
              onPress={() => run('google', () => auth.signInWithOAuth('google'))}
            />
            <Button
              label="Continue with X (Twitter)"
              variant="secondary"
              loading={busy === 'twitter'}
              onPress={() => run('twitter', () => auth.signInWithOAuth('twitter'))}
            />
            <Button
              label="Explore without an account"
              variant="ghost"
              onPress={() => auth.continueAsGuest()}
            />
          </View>

          <Card style={{ marginTop: 8 }}>
            <Body style={{ fontWeight: '600' }}>Your data, your call</Body>
            <Subtitle>
              Photos and rides stay on your phone unless you choose otherwise. Every upload asks:
              keep it private, contribute it to Edmonton trail mapping (maintainers only), or
              share it with other riders. You can change or delete anything later.
            </Subtitle>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, gap: 20 },
  brand: { alignItems: 'center', gap: 6, marginBottom: 8 },
  mark: {
    width: 64,
    height: 64,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  markText: { color: '#FFFFFF', fontSize: 24, fontWeight: '800', letterSpacing: 1 },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    fontSize: 16,
  },
  divider: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  line: { flex: 1, height: StyleSheet.hairlineWidth },
});
