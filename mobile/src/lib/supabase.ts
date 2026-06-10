import 'react-native-url-polyfill/auto';

import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

// Configure via mobile/.env (see mobile/.env.example):
//   EXPO_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
//   EXPO_PUBLIC_SUPABASE_ANON_KEY=<anon key>
const url = process.env.EXPO_PUBLIC_SUPABASE_URL;
const anonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

/** True when a Supabase project is configured. Without it the app still runs
 * fully offline (guest mode, local captures/rides) — only sync is disabled. */
export const backendConfigured = Boolean(url && anonKey);

export const supabase = createClient(
  url ?? 'https://placeholder.supabase.co',
  anonKey ?? 'public-anon-key-placeholder',
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  },
);
