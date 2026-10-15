// Shopify links for the physical signs.
//
// The website's store (docs/shop.js) sells each sign as a Shopify product;
// the catalogue's `shopify.variantId` reaches the app as `trail.shop`. The app
// doesn't embed a cart: it opens a Shopify cart permalink, which drops the
// sign straight into checkout (and applies a discount code when given).
import * as WebBrowser from 'expo-web-browser';

import { Trail } from '@/lib/trails';

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
