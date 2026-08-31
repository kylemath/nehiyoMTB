import AsyncStorage from '@react-native-async-storage/async-storage';

import { backendConfigured, supabase } from '@/lib/supabase';

const HOME_KEY = 'etm.home.v1';

export type HomeLocation = { latitude: number; longitude: number };

export async function getHome(): Promise<HomeLocation | null> {
  try {
    const raw = await AsyncStorage.getItem(HOME_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed?.latitude === 'number' && typeof parsed?.longitude === 'number') {
      return { latitude: parsed.latitude, longitude: parsed.longitude };
    }
    return null;
  } catch {
    return null;
  }
}

/** Persist locally, then best-effort sync to the signed-in profile. */
export async function setHome(loc: HomeLocation | null): Promise<void> {
  if (loc) await AsyncStorage.setItem(HOME_KEY, JSON.stringify(loc));
  else await AsyncStorage.removeItem(HOME_KEY);

  if (!backendConfigured) return;
  try {
    const { data } = await supabase.auth.getSession();
    const userId = data.session?.user.id;
    if (!userId) return;
    await supabase
      .from('profiles')
      .update({ home_lat: loc?.latitude ?? null, home_lng: loc?.longitude ?? null })
      .eq('id', userId);
  } catch {
    // Offline or backend error — the local value already stands.
  }
}

/** Fetch the remote home when signed in, cache it locally, return the best value. */
export async function pullHomeFromProfile(): Promise<HomeLocation | null> {
  const local = await getHome();
  if (!backendConfigured) return local;
  try {
    const { data: sessionData } = await supabase.auth.getSession();
    const userId = sessionData.session?.user.id;
    if (!userId) return local;
    const { data } = await supabase
      .from('profiles')
      .select('home_lat, home_lng')
      .eq('id', userId)
      .single();
    if (typeof data?.home_lat === 'number' && typeof data?.home_lng === 'number') {
      const remote = { latitude: data.home_lat, longitude: data.home_lng };
      await AsyncStorage.setItem(HOME_KEY, JSON.stringify(remote));
      return remote;
    }
    return local;
  } catch {
    return local;
  }
}
