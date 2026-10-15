// Shopify links for the physical signs.
//
// The website's store (docs/shop.js) sells each sign as a Shopify product;
// the catalogue's `shopify.variantId` reaches the app as `trail.shop`. The app
// doesn't embed a cart: it opens a Shopify cart permalink, which drops the
// sign straight into checkout (and applies a discount code when given).
import * as WebBrowser from 'expo-web-browser';

import { Trail } from '@/lib/trails';
import { supabase } from '@/lib/supabase';

/** The store's myshopify domain (same one docs/shop.js uses). */
const SHOP_DOMAIN = process.env.EXPO_PUBLIC_SHOPIFY_DOMAIN ?? 'w9hrxh-3z.myshopify.com';

export function checkoutUrl(
  variantId: string,
  opts: { discount?: string; note?: string } = {},
): string {
  const params = new URLSearchParams();
  if (opts.discount) params.set('discount', opts.discount);
  if (opts.note) params.set('note', opts.note);
  const query = params.toString();
  return `https://${SHOP_DOMAIN}/cart/${variantId}:1${query ? `?${query}` : ''}`;
}

export async function buySign(trail: Trail): Promise<void> {
  if (!trail.shop) return;
  await WebBrowser.openBrowserAsync(
    checkoutUrl(trail.shop.variantId, { note: `Sign: ${trail.title}` }),
  );
}

// ---------------------------------------------------------------------------
// King/Queen of the Mountain: the top three verified times on a trail can
// order the KOM edition of its sign for free. Ranks are computed in the
// database from server-verified sign captures (supabase/migrations/0003_kom.sql)
// and the single-use discount code is minted server-side by the `claim-kom`
// edge function, so the app never holds a Shopify admin credential.
// ---------------------------------------------------------------------------

export type KomRow = {
  trail_id: string;
  user_id: string;
  name: string;
  elapsed_s: number;
  rank: number;
  ridden_on: string;
};

export async function fetchKomBoard(trailId: string): Promise<KomRow[]> {
  const { data, error } = await supabase
    .from('trail_kom_board')
    .select('*')
    .eq('trail_id', trailId)
    .order('rank', { ascending: true })
    .limit(10);
  if (error) throw error;
  return (data as KomRow[]) ?? [];
}

export type KomClaim = { code: string; checkoutUrl: string };

export async function claimKomReward(trailId: string): Promise<KomClaim> {
  const { data, error } = await supabase.functions.invoke('claim-kom', {
    body: { trailId },
  });
  if (error) throw error;
  if (!data?.code || !data?.checkoutUrl) {
    throw new Error(data?.error ?? 'Could not create your reward code.');
  }
  return data as KomClaim;
}
