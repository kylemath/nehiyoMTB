# Shopify + nehiyomtb.ca Setup

This is the human-side checklist that turns the static GitHub Pages catalogue
into a working store at `https://nehiyomtb.ca`. The code on the site is already
wired up — every step below is something you have to do once in a web browser
(Shopify, Squarespace, GitHub) and then paste two strings into one file.

Everything is reversible. The site keeps working even before any of this is
done; buy buttons just stay hidden until Shopify is configured.

---

## 0. What you'll end up with

```
              ┌────────────────────────────────────────┐
              │   nehiyomtb.ca  (GitHub Pages, free)   │
              │   • catalogue + per-sign pages         │
              │   • floating cart drawer               │
              │   • "Add to cart" buttons per sign     │
              └──────────────┬─────────────────────────┘
                             │  Shopify Buy Button SDK
                             ▼
              ┌────────────────────────────────────────┐
              │   nehiyomtb.myshopify.com  (Shopify)   │
              │   • product list + inventory           │
              │   • Shopify-hosted checkout            │
              │   • taxes, shipping, payments          │
              └────────────────────────────────────────┘
```

You do not need a Shopify-hosted storefront theme. The cheapest plan that
allows Buy Buttons is **Shopify Starter — $5 USD/month** (formerly "Lite").
You can also use any higher-tier plan; the integration code is identical.

---

## 1. Sign up for Shopify (≈ 10 min)

1. Go to [https://www.shopify.com/starter](https://www.shopify.com/starter) and
   create an account. Use the email you want order notifications to land in.
2. Store name: anything — most people use `nehiyomtb`. This becomes the
   `nehiyomtb.myshopify.com` domain Shopify gives you for free; **write it
   down**, you'll need it in step 4.
3. Pick **Shopify Starter** ($5 USD/mo). You can switch plans later without
   re-doing any of this.
4. Skip the "choose a theme" / "design your store" prompts. You are using your
   own site as the storefront, so no theme is needed.

While you're in the admin, set:

- **Settings → Locations** — your shipping origin (your address).
- **Settings → Shipping and delivery** — flat rate or calculated rates. For
  small flat plaques a simple "Canada – $12 flat rate, Free over $100" works.
- **Settings → Taxes and duties** — register for Canadian tax collection.
  Shopify auto-applies GST/PST/HST per province once you tick the boxes and
  enter your tax numbers (or mark "not yet registered" for the early months).
- **Settings → Payments** — turn on Shopify Payments (Visa/Mastercard/Apple
  Pay) and any others you want.

---

## 2. Add each sign as a product (≈ 5 min per sign)

In Shopify admin, **Products → Add product** for each sign you want to sell:

- **Title** — match the catalogue, e.g. `Raven (kahkakiw)`.
- **Description** — a short paragraph. You can copy from the per-sign page on
  the live site.
- **Media** — upload the photo from `docs/assets/{folder}/`.
- **Pricing** — CAD price (e.g. `35.00`). Compare-at-price optional.
- **Inventory** — leave SKU blank or use the sign id. Tick "Track quantity"
  and set a number, or untick if it's print-on-demand.
- **Shipping** — weight in grams (≈ 200 g for a small plaque).
- **Status** — **Active**.
- **Sales channels** — make sure **Online Store** is ticked (this is what
  exposes the product to the Storefront API the SDK uses, even though you
  aren't using the Online Store theme itself).

Save the product. The URL bar will now look like
`https://admin.shopify.com/store/.../products/8123456789012`. That long number
at the end is the **productId** you'll paste into the catalogue in step 5.

> Tip: do one product first end-to-end (steps 3 → 7) before adding the other
> twenty-something. Once the first sign works in `nehiyomtb.ca`, the rest is
> copy-paste.

---

## 3. Create a Storefront API access token (≈ 3 min, one time)

The Buy Button SDK on the site needs an "unauthenticated" Storefront API
token. This is safe to put in client-side JavaScript — it can only read
products and create carts, not edit anything.

1. Shopify admin → **Settings** → **Apps and sales channels** → **Develop
   apps** → **Allow custom app development** (if it's the first time) →
   **Create an app**.
2. Name: `nehiyomtb-site`. Click Create.
3. **Configuration** tab → **Storefront API integration** → **Configure**.
4. Tick at minimum:
   - `unauthenticated_read_product_listings`
   - `unauthenticated_read_product_inventory`
   - `unauthenticated_write_checkouts`
   - `unauthenticated_read_checkouts`
   - `unauthenticated_read_selling_plans` (optional)
5. **Save** → **API credentials** tab → **Install app** → copy the
   **Storefront API access token** (starts with random letters/digits, ~32
   chars). **Write it down**, you'll paste it in step 5.

---

## 4. Allow your domains in Shopify (≈ 1 min)

Shopify blocks Storefront API calls from unknown origins by default.

1. Shopify admin → **Settings** → **Customer accounts** is not relevant.
   Instead go to **Settings** → **Apps and sales channels** → your
   `nehiyomtb-site` app → **API credentials** → scroll to **Allowed Storefront
   API CORS origins**.
2. Add each of these on its own line:
   - `https://nehiyomtb.ca`
   - `https://www.nehiyomtb.ca`
   - `https://kylemath.github.io` (the GitHub Pages fallback, useful for
     testing before the custom domain is live)
   - `http://localhost:8765` (local catalogue editor)
3. Save.

---

## 5. Paste two strings into the site (≈ 1 min)

Open [`docs/shop.js`](shop.js) and replace the two placeholder strings near
the top of the file:

```js
const SHOPIFY_DOMAIN = "nehiyomtb.myshopify.com";          // from step 1
const STOREFRONT_ACCESS_TOKEN = "shpat_xxxxxxxxxxxxxxxx";   // from step 3
```

Commit and push to `main`. GitHub Pages will redeploy in ~30 seconds. At this
point the cart icon and any product buttons whose ids are filled in below
become live.

---

## 6. Paste the productId for each sign (≈ 1 min per sign)

Every sign has an empty `shopify` block in `docs/catalogue.json` already. For
each sign you've created in Shopify, edit its entry to fill in:

```json
"shopify": {
  "productId": "8123456789012",
  "variantId": "",
  "priceCAD": 35,
  "available": true
}
```

- `productId` — the long number from the Shopify admin URL (step 2).
- `variantId` — leave `""` unless you have multiple variants and want to
  target a specific one.
- `priceCAD` — reference only; the site does not display prices. Shopify shows
  the price in the cart and at checkout.
- `available` — set to `true` once you're ready for it to be buyable. Setting
  it back to `false` hides the button without deleting any other data.

You can also edit `shopify` through the local catalogue editor
(`python3 tools/catalogue_editor_server.py`) if you prefer a form.

If you change any per-sign content (not just `shopify`), re-render that sign's
page with:

```sh
python3 tools/sign_page_renderer.py kahkakiw
```

The renderer always reads the latest `shopify` block and emits the button.

---

## 7. Point nehiyomtb.ca at GitHub Pages (≈ 15 min + DNS wait)

You bought the domain through Squarespace. There are two ways to point it at
GitHub Pages. Pick **A** if you want the simplest path; pick **B** if you want
the cleanest long-term setup.

### Option A — Keep the domain at Squarespace, change DNS only (simplest)

You will keep paying Squarespace for the domain (≈ $20/yr) but cancel any
Squarespace website plan. DNS stays with Squarespace; GitHub Pages serves the
content.

1. **Squarespace** → **Settings** → **Domains** → click `nehiyomtb.ca` →
   **DNS Settings** (sometimes "DNS / Custom Records").
2. **Delete** every existing A, CNAME, ALIAS, and ANAME record for `@` and
   `www` that points at Squarespace. Leave MX records alone (email).
3. Add the following four **A records for `@`** (apex / root domain), all
   pointing at GitHub's Pages servers:

   | Type | Host | Value             |
   | ---- | ---- | ----------------- |
   | A    | @    | 185.199.108.153   |
   | A    | @    | 185.199.109.153   |
   | A    | @    | 185.199.110.153   |
   | A    | @    | 185.199.111.153   |

4. Add one **CNAME for `www`** pointing at your GitHub Pages subdomain:

   | Type  | Host | Value                       |
   | ----- | ---- | --------------------------- |
   | CNAME | www  | kylemath.github.io.         |

   (Trailing dot if Squarespace requires it; it usually adds it for you.)

5. Save. DNS propagation typically takes 10–60 minutes; sometimes up to 24h.

6. Cancel your Squarespace **website** plan if you still have one — go to
   **Settings → Billing → Subscriptions** and downgrade the site. Keep the
   **domain** subscription (different line item) so the registration stays.

### Option B — Transfer the domain registrar to Cloudflare (cheaper long-term)

Cloudflare charges at-cost for `.ca` (≈ $11/yr vs Squarespace's $20/yr) and
gives you faster DNS + free analytics. Skip this if Option A is fine.

1. Sign up at [cloudflare.com](https://cloudflare.com), add `nehiyomtb.ca`.
2. Copy the Cloudflare nameservers it shows you.
3. Squarespace → Domains → `nehiyomtb.ca` → **Use custom nameservers** →
   paste the two Cloudflare nameservers. Save.
4. Wait for the nameserver change (a few hours), then in Cloudflare add the
   same A + CNAME records as Option A above. Set the cloud icons to
   **DNS only** (grey, not orange) — orange-proxied breaks GitHub Pages HTTPS
   provisioning until you switch to "Full (strict)" SSL mode.
5. Cloudflare → **SSL/TLS** → mode **Full (strict)**.
6. Once propagated, Cloudflare → **Domain Registration → Transfer** and
   transfer the registration from Squarespace. Squarespace will email a
   confirmation; approve it. Cancel the Squarespace domain billing once
   transfer completes (usually 5–7 days).

---

## 8. Tell GitHub Pages about the custom domain (≈ 2 min)

1. GitHub repo → **Settings** → **Pages**.
2. **Source**: Deploy from a branch → branch `main` → folder `/docs`. (This
   is probably already set; the catalogue lives at `/docs`.)
3. **Custom domain**: enter `nehiyomtb.ca` → Save. GitHub will run a DNS
   check; once green, tick **Enforce HTTPS** (the box becomes clickable after
   GitHub provisions a Let's Encrypt certificate, usually within an hour).

The repo already contains [`docs/CNAME`](CNAME) with `nehiyomtb.ca`, so the
custom-domain setting persists across deploys.

---

## 9. Test the full purchase flow

Use a real card you control (you can refund yourself afterward via Shopify
admin → Orders → Refund).

1. Open `https://nehiyomtb.ca`.
2. Click any sign that has `shopify.available: true` filled in.
3. Click **Add to cart** in the detail pane or on the per-sign page.
4. Click the floating cart icon → **Checkout**. This bounces you to
   `nehiyomtb.myshopify.com/checkouts/...` — that's Shopify's PCI-compliant
   checkout. (You can customise its appearance later in Shopify admin →
   **Online Store → Themes → Customize checkout**, included in Starter.)
5. Place a small test order. Confirm the order appears in Shopify admin →
   **Orders**.
6. Refund it from the same order page.

---

## 10. Day-to-day operations

- **Add a new sign to the store**: add the product in Shopify (step 2), then
  fill in the `shopify` block for that sign in `docs/catalogue.json` (step 6),
  commit + push.
- **Take a sign off the store temporarily**: set `shopify.available` to
  `false` and push. The catalogue still shows the sign — only the buy button
  disappears.
- **Change a price**: change it in Shopify admin. The site shows no prices,
  so nothing else needs updating.
- **Refund / cancel an order**: Shopify admin → Orders. Email goes out
  automatically.
- **Shipping label**: Shopify admin → Orders → "Buy shipping label" (Canada
  Post / UPS rates are pre-negotiated).

---

## 11. Troubleshooting

- **Buttons don't appear** → open the browser console. If you see
  `[NehiyoShop] Shopify is not configured yet` the two strings in `shop.js`
  weren't updated or weren't deployed. If you see a CORS error, re-check
  step 4 (allowed origins).
- **Buttons appear but "Add to cart" does nothing** → token missing the
  `unauthenticated_write_checkouts` scope (step 3.4). Recreate the token.
- **`nehiyomtb.ca` shows a Squarespace 404 / parking page** → DNS hasn't
  propagated yet, or the old Squarespace A/CNAME records weren't deleted.
  Verify with `dig nehiyomtb.ca +short` — it should return the four
  `185.199.10x.153` IPs.
- **GitHub Pages says "DNS check failed"** → wait 15 min and retry. Apex
  domains can take longer than `www` to propagate.
- **HTTPS won't enable** → make sure no Cloudflare orange-cloud is on the
  records (Option B), or that Squarespace isn't still serving its own SSL on
  the domain (Option A — disable any "use this domain for a site" toggle in
  Squarespace).

---

## Quick reference

| Thing                          | Where                                                              |
| ------------------------------ | ------------------------------------------------------------------ |
| Shopify store admin            | `https://admin.shopify.com/store/<your-store>`                     |
| Shopify checkout for customers | `https://nehiyomtb.myshopify.com/checkouts/...` (linked from cart) |
| Live site                      | `https://nehiyomtb.ca`                                             |
| GitHub Pages source            | `docs/` folder of this repo                                        |
| Per-sign Shopify binding       | `docs/catalogue.json` → each model's `shopify` block               |
| Global Shopify keys            | `docs/shop.js` (two strings at the top)                            |
| Custom domain pin              | `docs/CNAME`                                                       |
