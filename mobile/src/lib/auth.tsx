import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Session } from '@supabase/supabase-js';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { backendConfigured, supabase } from '@/lib/supabase';

WebBrowser.maybeCompleteAuthSession();

const GUEST_KEY = 'etm.guestMode.v1';

export type OAuthProvider = 'google' | 'twitter';

type AuthState = {
  session: Session | null;
  /** Riding without an account: everything stays on-device, nothing syncs. */
  guest: boolean;
  loading: boolean;
  backendConfigured: boolean;
  signInWithEmail: (email: string, password: string) => Promise<string | null>;
  signUpWithEmail: (email: string, password: string) => Promise<string | null>;
  signInWithOAuth: (provider: OAuthProvider) => Promise<string | null>;
  continueAsGuest: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [guest, setGuest] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [{ data }, guestFlag] = await Promise.all([
        supabase.auth.getSession(),
        AsyncStorage.getItem(GUEST_KEY),
      ]);
      setSession(data.session);
      setGuest(guestFlag === '1');
      setLoading(false);
    })();

    const { data: sub } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      session,
      guest,
      loading,
      backendConfigured,
      async signInWithEmail(email, password) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        return error?.message ?? null;
      },
      async signUpWithEmail(email, password) {
        const { error } = await supabase.auth.signUp({ email, password });
        return error?.message ?? null;
      },
      async signInWithOAuth(provider) {
        // Supabase OAuth in a system browser, returning via the app scheme.
        const redirectTo = Linking.createURL('auth/callback');
        const { data, error } = await supabase.auth.signInWithOAuth({
          provider,
          options: { redirectTo, skipBrowserRedirect: true },
        });
        if (error) return error.message;
        const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
        if (result.type !== 'success') return 'Sign-in was cancelled.';
        const url = new URL(result.url);
        const params = new URLSearchParams(url.hash ? url.hash.slice(1) : url.search);
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        const code = params.get('code');
        if (accessToken && refreshToken) {
          const { error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });
          return sessionError?.message ?? null;
        }
        if (code) {
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          return exchangeError?.message ?? null;
        }
        return 'Sign-in did not return a session.';
      },
      async continueAsGuest() {
        await AsyncStorage.setItem(GUEST_KEY, '1');
        setGuest(true);
      },
      async signOut() {
        await supabase.auth.signOut();
        await AsyncStorage.removeItem(GUEST_KEY);
        setGuest(false);
      },
    }),
    [session, guest, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
