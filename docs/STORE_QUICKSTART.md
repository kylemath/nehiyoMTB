# 🛒 nehiyoMTB Store — Quick Start

A simple, step-by-step guide to turn the website into a working online store at
**[nehiyomtb.ca](https://nehiyomtb.ca)**.

The code is already built. You just need to do the steps below once. Until you
finish, the site still works perfectly as a catalogue — the "buy" buttons just
stay hidden.

> 📖 Need the long version with every detail and troubleshooting? See
> **[SHOPIFY_SETUP.md](SHOPIFY_SETUP.md)**.

---

## ✅ The 9 steps at a glance

| # | Step | Where | Time |
|---|------|-------|------|
| 1 | Create Shopify account | [shopify.com/starter](https://www.shopify.com/starter) | ~10 min |
| 2 | Add each sign as a product | Shopify admin | ~5 min each |
| 3 | Create an API token | Shopify admin | ~3 min |
| 4 | Allow your website addresses | Shopify admin | ~1 min |
| 5 | Paste 2 keys into the site | `docs/shop.js` | ~1 min |
| 6 | Add prices to each sign | `docs/catalogue.json` | ~1 min each |
| 7 | Point your domain at the site | Squarespace | ~15 min + wait |
| 8 | Turn on the domain in GitHub | GitHub repo settings | ~2 min |
| 9 | Test a real purchase | [nehiyomtb.ca](https://nehiyomtb.ca) | ~5 min |

---

## 1️⃣ Create your Shopify account

1. Go to **[shopify.com/starter](https://www.shopify.com/starter)** and sign up.
2. Choose the **Shopify Starter** plan — **$5 USD/month**. (This is the cheapest
   plan that allows "buy buttons". You do **not** need a Shopify website/theme.)
3. Name your store `nehiyomtb`. Shopify gives you a free address like
   **`nehiyomtb.myshopify.com`** — 📝 **write this down**, you'll need it later.
4. Set these up in **Settings**:
   - **Shipping** → e.g. Canada flat rate $12, free over $100.
   - **Taxes** → your province.
   - **Payments** → turn on Shopify Payments (cards + Apple Pay).

---

## 2️⃣ Add each sign as a product

In Shopify admin, go to **Products → Add product** for each sign:

- **Title** — e.g. `Raven (kahkakiw)`
- **Photo** — upload from the `docs/assets/{sign}/` folder
- **Price** — in CAD (e.g. `35.00`)
- **Weight** — about `200 g` for a small plaque
- **Status** — **Active**
- **Sales channels** — make sure **Online Store** is ✅ ticked

After you save, look at the web address. It ends in a long number:

```
https://admin.shopify.com/store/.../products/8123456789012
                                            └── this is your productId
```

📝 Save that number — you'll paste it in **step 6**.

> 💡 Tip: do **one** sign all the way through steps 3–9 first. Once it works,
> the rest are just copy-paste.

---

## 3️⃣ Create an API token (one time)

This lets the website talk to Shopify safely.

1. Shopify admin → **Settings → Apps and sales channels → Develop apps →
   Create an app**. Name it `nehiyomtb-site`.
2. Open the **Configuration** tab → **Storefront API → Configure**.
3. Tick these boxes:
   - ☑️ `unauthenticated_read_product_listings`
   - ☑️ `unauthenticated_read_product_inventory`
   - ☑️ `unauthenticated_read_checkouts`
   - ☑️ `unauthenticated_write_checkouts`
4. **Save** → **API credentials** tab → **Install app**.
5. Copy the **Storefront API access token** (it starts with `shpat_…`).
   📝 Save it for **step 5**.

---

## 4️⃣ Allow your website addresses

Still in that app → **API credentials → Allowed Storefront API CORS origins**.
Add each of these on its own line:

```
https://nehiyomtb.ca
https://www.nehiyomtb.ca
https://kylemath.github.io
http://localhost:8765
```

Save.

---

## 5️⃣ Paste your 2 keys into the site

Open the file **`docs/shop.js`** and edit the two lines near the top:

```js
const SHOPIFY_DOMAIN = "nehiyomtb.myshopify.com";        // from step 1
const STOREFRONT_ACCESS_TOKEN = "shpat_xxxxxxxxxxxxxxxx"; // from step 3
```

Save, then commit and push to `main`. The site updates in about 30 seconds.

---

## 6️⃣ Add prices to each sign

Open **`docs/catalogue.json`**. Find each sign and fill in its `shopify` block:

```json
"shopify": {
  "productId": "8123456789012",
  "variantId": "",
  "priceCAD": 35,
  "available": true
}
```

- **productId** — the long number from step 2
- **priceCAD** — the price shown on the card before the page fully loads
- **available** — set to `true` to make it buyable (`false` hides the button)

Push your changes. The price tags and "Add to cart" buttons now appear for every
sign you marked `available: true`. 🎉

---

## 7️⃣ Point nehiyomtb.ca at the website

Your domain is at Squarespace right now. We just change where it points.

In **Squarespace → Settings → Domains → nehiyomtb.ca → DNS Settings**:

1. **Delete** all existing records for `@` and `www` that point at Squarespace.
   *(Leave any MX / email records alone.)*
2. Add **four A records** for host `@`:

   | Type | Host | Value |
   |------|------|-------|
   | A | @ | `185.199.108.153` |
   | A | @ | `185.199.109.153` |
   | A | @ | `185.199.110.153` |
   | A | @ | `185.199.111.153` |

3. Add **one CNAME record** for host `www`:

   | Type | Host | Value |
   |------|------|-------|
   | CNAME | www | `kylemath.github.io.` |

4. Save. DNS usually updates in 10–60 minutes (sometimes up to 24 hours).
5. Cancel your Squarespace **website plan** — but **keep the domain** itself.

> 💰 Want cheaper renewals? You can move the domain to
> [Cloudflare](https://cloudflare.com) instead — see
> **[SHOPIFY_SETUP.md → Option B](SHOPIFY_SETUP.md)**.

---

## 8️⃣ Turn on the domain in GitHub

1. Go to your repo → **Settings → Pages**.
2. **Source**: Deploy from branch `main`, folder `/docs`.
3. **Custom domain**: type `nehiyomtb.ca` → **Save**.
   *(The `docs/CNAME` file is already set up for this.)*
4. Wait for the green check, then tick **✅ Enforce HTTPS**
   (the box becomes clickable within an hour once the security certificate is
   ready).

---

## 9️⃣ Test a real purchase

1. Open **[nehiyomtb.ca](https://nehiyomtb.ca)**.
2. Click a sign you marked `available: true`.
3. Click **Add to cart**, then the cart icon → **Checkout**.
4. Complete a small real order with your own card.
5. Confirm it shows in Shopify admin → **Orders**.
6. **Refund yourself** from that same order page. ✅ Done!

---

## 🔧 Everyday tasks later

| I want to… | Do this |
|------------|---------|
| Hide a sign from the store | Set its `"available": false` in `docs/catalogue.json` and push |
| Change a price | Change it in Shopify admin (update `priceCAD` too so the chip matches) |
| Add a new sign | Add the product in Shopify, then fill its `shopify` block and push |
| Refund / cancel an order | Shopify admin → **Orders** |
| Print a shipping label | Shopify admin → **Orders → Buy shipping label** |

---

## ❓ Something not working?

| Problem | Fix |
|---------|-----|
| Buttons don't show up | Check the 2 keys in `docs/shop.js` (step 5) were saved + pushed |
| "Add to cart" does nothing | Token is missing the `write_checkouts` scope — redo step 3 |
| nehiyomtb.ca shows old Squarespace page | DNS not updated yet, or old records weren't deleted (step 7) |
| HTTPS won't turn on | Wait ~1 hour after DNS goes live, then retry in GitHub Pages settings |

Full troubleshooting lives in **[SHOPIFY_SETUP.md](SHOPIFY_SETUP.md)**.

---

### 📂 Where things live

| Thing | File |
|-------|------|
| Your Shopify keys | [`docs/shop.js`](shop.js) |
| Per-sign prices & products | [`docs/catalogue.json`](catalogue.json) |
| Custom domain pin | [`docs/CNAME`](CNAME) |
| This guide | `docs/STORE_QUICKSTART.md` |
| Detailed guide | [`docs/SHOPIFY_SETUP.md`](SHOPIFY_SETUP.md) |
