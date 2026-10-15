// claim-kom — issue a free KOM-edition sign to a top-3 rider on a trail.
//
// POST { trailId } with the rider's Supabase session (the app calls this via
// supabase.functions.invoke). The rider's rank is read from the
// trail_kom_board view (verified sign captures only). If they are in the top
// three, a single-use 100%-off Shopify discount code limited to the KOM
// edition product is created and returned with a ready checkout link. A rider
// gets at most one code per trail; calling again returns the same code.
//
// Secrets (supabase secrets set ...):
//   SHOPIFY_DOMAIN            e.g. w9hrxh-3z.myshopify.com
//   SHOPIFY_CLIENT_ID         } the KOM app's credentials (Dev Dashboard app with
//   SHOPIFY_CLIENT_SECRET     } write_discounts, installed on the store); exchanged
//                               for a short-lived Admin API token below
//   SHOPIFY_ADMIN_TOKEN       or instead: a legacy custom-app token (shpat_...)
//   SHOPIFY_KOM_PRODUCT_ID    numeric id of the "KOM edition trail sign" product
//   SHOPIFY_KOM_VARIANT_ID    numeric id of its variant (for the checkout link)
// SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY are provided.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.108.1';

const KOM_PLACES = 3;
const SHOPIFY_API_VERSION = '2025-10';

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, 'Content-Type': 'application/json' },
  });
}

function env(name: string): string {
  const value = Deno.env.get(name);
  if (!value) throw new Error(`Missing secret ${name}`);
  return value;
}

function checkoutUrl(code: string, trailTitle: string) {
  const params = new URLSearchParams({ discount: code, note: `KOM edition: ${trailTitle}` });
  return `https://${env('SHOPIFY_DOMAIN')}/cart/${env('SHOPIFY_KOM_VARIANT_ID')}:1?${params}`;
}

let cachedToken: { value: string; expiresAt: number } | null = null;

/** Admin API token: a legacy shpat_ token if set, otherwise one obtained with
 * the client credentials grant (valid ~24 h, cached while the function is warm). */
async function adminToken(): Promise<string> {
  const legacy = Deno.env.get('SHOPIFY_ADMIN_TOKEN');
  if (legacy) return legacy;
  if (cachedToken && cachedToken.expiresAt > Date.now() + 60_000) return cachedToken.value;
  const res = await fetch(`https://${env('SHOPIFY_DOMAIN')}/admin/oauth/access_token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: env('SHOPIFY_CLIENT_ID'),
      client_secret: env('SHOPIFY_CLIENT_SECRET'),
    }),
  });
  if (!res.ok) throw new Error(`Shopify token exchange failed: HTTP ${res.status}`);
  const body = await res.json();
  cachedToken = {
    value: body.access_token,
    expiresAt: Date.now() + (body.expires_in ?? 3600) * 1000,
  };
  return cachedToken.value;
}

async function createShopifyCode(code: string, title: string): Promise<string> {
  const res = await fetch(
    `https://${env('SHOPIFY_DOMAIN')}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': await adminToken(),
      },
      body: JSON.stringify({
        query: `mutation($discount: DiscountCodeBasicInput!) {
          discountCodeBasicCreate(basicCodeDiscount: $discount) {
            codeDiscountNode { id }
            userErrors { field message }
          }
        }`,
        variables: {
          discount: {
            title,
            code,
            startsAt: new Date().toISOString(),
            usageLimit: 1,
            appliesOncePerCustomer: true,
            context: { all: 'ALL' },
            customerGets: {
              value: { percentage: 1.0 },
              items: {
                products: {
                  productsToAdd: [`gid://shopify/Product/${env('SHOPIFY_KOM_PRODUCT_ID')}`],
                },
              },
            },
          },
        },
      }),
    },
  );
  const body = await res.json();
  const result = body?.data?.discountCodeBasicCreate;
  if (!res.ok || !result || result.userErrors?.length) {
    throw new Error(
      result?.userErrors?.map((e: { message: string }) => e.message).join('; ') ||
        `Shopify error ${res.status}`,
    );
  }
  return result.codeDiscountNode.id as string;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  if (req.method !== 'POST') return json({ error: 'POST only' }, 405);

  try {
    const { trailId } = await req.json();
    if (typeof trailId !== 'string' || !trailId) return json({ error: 'trailId required' }, 400);

    // Who is asking: resolve the rider from their own session token.
    const asRider = createClient(env('SUPABASE_URL'), env('SUPABASE_ANON_KEY'), {
      global: { headers: { Authorization: req.headers.get('Authorization') ?? '' } },
    });
    const { data: userData } = await asRider.auth.getUser();
    const user = userData?.user;
    if (!user) return json({ error: 'Sign in to claim a reward.' }, 401);

    const admin = createClient(env('SUPABASE_URL'), env('SUPABASE_SERVICE_ROLE_KEY'));
    const { data: trail } = await admin.from('trails').select('id, title').eq('id', trailId).single();
    if (!trail) return json({ error: 'Unknown trail.' }, 404);

    const { data: existing } = await admin
      .from('kom_rewards')
      .select('discount_code')
      .eq('user_id', user.id)
      .eq('trail_id', trailId)
      .maybeSingle();
    if (existing) {
      return json({ code: existing.discount_code, checkoutUrl: checkoutUrl(existing.discount_code, trail.title) });
    }

    const { data: mine } = await admin
      .from('trail_kom_board')
      .select('rank, elapsed_s')
      .eq('trail_id', trailId)
      .eq('user_id', user.id)
      .maybeSingle();
    if (!mine || mine.rank > KOM_PLACES) {
      return json({ error: `Only the top ${KOM_PLACES} verified times on this trail can claim the KOM sign.` }, 403);
    }

    // Keep the run that earned it, for the maker to review before shipping.
    const { data: run } = await admin
      .from('trail_verified_runs')
      .select('start_capture_id, end_capture_id')
      .eq('trail_id', trailId)
      .eq('user_id', user.id)
      .eq('elapsed_s', mine.elapsed_s)
      .limit(1)
      .maybeSingle();

    const code = `KOM-${trailId.replace(/[^a-z0-9]/gi, '').slice(0, 10).toUpperCase()}-${crypto
      .randomUUID()
      .slice(0, 8)
      .toUpperCase()}`;
    const discountId = await createShopifyCode(code, `KOM ${trail.title} #${mine.rank}`);

    const { error: insertError } = await admin.from('kom_rewards').insert({
      user_id: user.id,
      trail_id: trailId,
      rank: mine.rank,
      elapsed_s: mine.elapsed_s,
      start_capture_id: run?.start_capture_id ?? null,
      end_capture_id: run?.end_capture_id ?? null,
      discount_code: code,
      shopify_discount_id: discountId,
    });
    if (insertError) throw insertError;

    return json({ code, checkoutUrl: checkoutUrl(code, trail.title) });
  } catch (e) {
    return json({ error: e instanceof Error ? e.message : 'Something went wrong.' }, 500);
  }
});
