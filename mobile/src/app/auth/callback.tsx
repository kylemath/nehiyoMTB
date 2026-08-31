import * as Linking from 'expo-linking';
import { router } from 'expo-router';
import React, { useEffect, useRef } from 'react';
import { ActivityIndicator, View } from 'react-native';

import { Brand } from '@/constants/brand';
import { supabase } from '@/lib/supabase';

/**
 * Deep-link landing for Supabase auth redirects (email confirmation links,
 * OAuth flows that open the app directly instead of resolving inside
 * openAuthSessionAsync). Consumes the tokens from the URL, establishes the
 * session, then bounces to the app root.
 */
export default function AuthCallback() {
  const url = Linking.useURL();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;
    (async () => {
      try {
        if (url) {
          const parsed = new URL(url);
          const params = new URLSearchParams(
            parsed.hash ? parsed.hash.slice(1) : parsed.search,
          );
          const accessToken = params.get('access_token');
          const refreshToken = params.get('refresh_token');
          const code = params.get('code');
          if (accessToken && refreshToken) {
            await supabase.auth.setSession({
              access_token: accessToken,
              refresh_token: refreshToken,
            });
          } else if (code) {
            await supabase.auth.exchangeCodeForSession(code);
          }
        }
      } catch {
        // Fall through to the app root; the sign-in guard takes over.
      }
      router.replace('/');
    })();
  }, [url]);

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator size="large" color={Brand.pine} />
    </View>
  );
}
