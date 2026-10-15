/*
 * docs/shop.js — single shared Shopify storefront integration for nehiyoMTB.
 *
 * Loaded by every per-sign page rendered by `tools/sign_page_renderer.py`
 * (and by `docs/index.html`, which only shows the cart). It does three jobs:
 *
 *  1. Holds the one-place Shopify store config (domain + Storefront API token).
 *  2. Lazy-loads the Shopify Buy Button SDK on first use.
 *  3. Exposes a tiny `window.NehiyoShop` API that pages call to:
 *       - mount a small "Get one" button against a Shopify productId
 *       - mount the floating cart (one per window, never two)
 *       - add a product to the cart directly (catalogue preview "Get one")
 *
 *  Design notes (why it looks like this):
 *   - Every Shopify component renders inside its own iframe (`iframe: true`).
 *     That isolates the cart from the page's CSS, which is what made the
 *     drawer unreadable on the dark catalogue.
 *   - The product component creates the shared cart itself, with our cart +
 *     toggle styles passed in. We never call `createComponent("cart")` on top
 *     of that, because the SDK would build a second, independent cart.
 *   - Checkout opens in the same tab (`popup: false`) instead of a small
 *     popup window that browsers often block or bury.
 *   - Pages embedded in another page (the catalogue preview iframe) never
 *     mount Shopify themselves; their "Get one" calls the parent window's
 *     `NehiyoShop.addToCart` so the item lands in the catalogue's one cart.
 *
 *  No Shopify credentials? Leave the placeholders below as-is. The script will
 *  detect missing config, log a single console note, and silently no-op so
 *  the rest of the page keeps working.
 *
 *  When you are ready to wire up Shopify, see `docs/SHOPIFY_SETUP.md` for the
 *  exact two strings to paste here.
 */

(function () {
  // ─── EDIT THESE TWO LINES WHEN YOU SET UP SHOPIFY ────────────────────────
  // 1. Your store domain. Find it under Shopify admin → Settings → Domains.
  //    It is the "myshopify.com" one, even if you also have nehiyomtb.ca.
  const SHOPIFY_DOMAIN = "w9hrxh-3z.myshopify.com";

  // 2. Your Storefront API access token. Create it under Shopify admin →
  //    Settings → Apps and sales channels → Develop apps → Create an app →
  //    Configure Storefront API scopes (tick unauthenticated_read_product_listings
  //    and unauthenticated_write_checkouts) → Install app → copy the
  //    "Storefront API access token".
  const STOREFRONT_ACCESS_TOKEN = "56a2c05f45f8eba327327a378e317384";
  // ──────────────────────────────────────────────────────────────────────────

  const SDK_URL = "https://sdks.shopifycdn.com/buy-button/latest/buy-button-storefront.min.js";
  const DEFAULT_ACCENT = "#dc3545";
  const FONT_STACK =
    "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

  const isConfigured = () =>
    SHOPIFY_DOMAIN &&
    STOREFRONT_ACCESS_TOKEN &&
    !SHOPIFY_DOMAIN.startsWith("YOUR") &&
    !STOREFRONT_ACCESS_TOKEN.startsWith("YOUR");

  const isEmbedded = () => {
    try {
      return window.self !== window.top;
    } catch (e) {
      return true;
    }
  };

  if (!isConfigured()) {
    console.info(
      "[NehiyoShop] Shopify is not configured yet — buy buttons are hidden. " +
        "Edit docs/shop.js with your store domain and Storefront API token to enable checkout."
    );
  }

  let sdkPromise = null;
  function loadSDK() {
    if (sdkPromise) return sdkPromise;
    sdkPromise = new Promise((resolve, reject) => {
      if (window.ShopifyBuy && window.ShopifyBuy.UI) {
        resolve(window.ShopifyBuy);
        return;
      }
      const script = document.createElement("script");
      script.async = true;
      script.src = SDK_URL;
      script.onload = () => {
        if (window.ShopifyBuy && window.ShopifyBuy.UI) {
          resolve(window.ShopifyBuy);
        } else {
          reject(new Error("Shopify Buy SDK loaded but ShopifyBuy.UI is missing"));
        }
      };
      script.onerror = () => reject(new Error("Failed to load Shopify Buy SDK"));
      document.head.appendChild(script);
    });
    return sdkPromise;
  }

  let clientPromise = null;
  function getClient() {
    if (clientPromise) return clientPromise;
    clientPromise = loadSDK().then((ShopifyBuy) => {
      const client = ShopifyBuy.buildClient({
        domain: SHOPIFY_DOMAIN,
        storefrontAccessToken: STOREFRONT_ACCESS_TOKEN,
      });
      return ShopifyBuy.UI.onReady(client).then((ui) => ({ client, ui }));
    });
    return clientPromise;
  }

  // Darken a #rrggbb colour for hover states.
  function shade(hex, amount) {
    const m = /^#?([0-9a-f]{6})$/i.exec(hex || "");
    if (!m) return hex;
    const n = parseInt(m[1], 16);
    const f = 1 - amount;
    const r = Math.round(((n >> 16) & 255) * f);
    const g = Math.round(((n >> 8) & 255) * f);
    const b = Math.round((n & 255) * f);
    return "#" + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
  }

  // The cart drawer and its floating toggle. Solid accent buttons, dark text
  // on white so it reads clearly over any page.
  function cartOptions(accent) {
    const hover = shade(accent, 0.15);
    return {
      cart: {
        iframe: true,
        popup: false,
        startOpen: false,
        text: {
          title: "Your cart",
          total: "Subtotal",
          button: "Checkout",
          empty: "Your cart is empty.",
          notice: "Shipping and taxes are calculated at checkout.",
        },
        styles: {
          cart: { "font-family": FONT_STACK, "background-color": "#ffffff", color: "#111111" },
          title: { color: "#111111" },
          header: { color: "#111111" },
          lineItems: { color: "#111111" },
          subtotalText: { color: "#111111" },
          subtotal: { color: "#111111" },
          notice: { color: "#555555" },
          currency: { color: "#111111" },
          close: { color: "#555555", ":hover": { color: "#111111" } },
          empty: { color: "#555555" },
          footer: { "background-color": "#ffffff" },
          button: {
            "font-family": FONT_STACK,
            "background-color": accent,
            ":hover": { "background-color": hover },
            ":focus": { "background-color": hover },
            "border-radius": "8px",
          },
        },
      },
      lineItem: {
        styles: {
          variantTitle: { color: "#444444" },
          itemTitle: { color: "#111111" },
          price: { color: "#111111" },
          quantity: { color: "#111111" },
          quantityIncrement: { color: "#111111", "border-color": "#cccccc" },
          quantityDecrement: { color: "#111111", "border-color": "#cccccc" },
          quantityInput: { color: "#111111", "border-color": "#cccccc" },
        },
      },
      toggle: {
        iframe: true,
        sticky: true,
        styles: {
          toggle: {
            "font-family": FONT_STACK,
            "background-color": accent,
            ":hover": { "background-color": hover },
            ":focus": { "background-color": hover },
          },
          count: { color: "#ffffff", ":hover": { color: "#ffffff" } },
          iconPath: { fill: "#ffffff" },
        },
      },
    };
  }

  // A small outlined button in the sign's accent colour. No price, no title,
  // no image: the sign page itself is the product page.
  function productOptions(accent, buttonText) {
    return {
      iframe: true,
      buttonDestination: "cart",
      layout: "vertical",
      width: "130px",
      contents: {
        img: false,
        imgWithCarousel: false,
        title: false,
        variantTitle: false,
        price: false,
        unitPrice: false,
        description: false,
        options: true,
        quantity: false,
        buttonWithQuantity: false,
        button: true,
      },
      text: { button: buttonText || "Get one" },
      styles: {
        product: {
          "text-align": "left",
          "@media (min-width: 601px)": { "max-width": "100%", "margin-left": "0", "margin-bottom": "0" },
        },
        options: { "font-family": FONT_STACK, color: "#333333" },
        button: {
          "font-family": FONT_STACK,
          "background-color": "transparent",
          color: accent,
          border: `1.5px solid ${accent}`,
          "border-radius": "999px",
          "padding-top": "7px",
          "padding-bottom": "7px",
          "padding-left": "18px",
          "padding-right": "18px",
          "font-size": "14px",
          "font-weight": "600",
          ":hover": { "background-color": accent, color: "#ffffff" },
          ":focus": { "background-color": accent, color: "#ffffff" },
        },
      },
    };
  }

  function allOptions(accent, buttonText) {
    return Object.assign({ product: productOptions(accent, buttonText) }, cartOptions(accent));
  }

  // One cart per window. Whichever call gets here first (a product mount or a
  // bare mountCart) creates it; later calls reuse it.
  let cartPromise = null;

  function mountCart(opts = {}) {
    if (!isConfigured() || isEmbedded()) return Promise.resolve();
    if (cartPromise) return cartPromise;
    const accent = opts.accent || DEFAULT_ACCENT;
    cartPromise = getClient()
      .then(({ ui }) => ui.createCart({ options: cartOptions(accent) }))
      .catch((err) => {
        cartPromise = null;
        console.warn("[NehiyoShop] cart mount failed:", err);
      });
    return cartPromise;
  }

  function mountProduct(target, productId, opts = {}) {
    if (!target) return Promise.resolve();
    if (!isConfigured()) {
      target.classList.add("shop-disabled");
      target.innerHTML =
        '<span class="shop-disabled-note">Email <a href="mailto:hello@nehiyomtb.ca">hello@nehiyomtb.ca</a> to ask about one.</span>';
      return Promise.resolve();
    }
    if (!productId) {
      target.classList.add("shop-empty");
      return Promise.resolve();
    }
    const accent = opts.accent || DEFAULT_ACCENT;
    return getClient()
      .then(({ ui }) => {
        // If a cart already exists the SDK reuses it; otherwise the product
        // component creates it with the cart/toggle options passed here.
        const options = allOptions(accent, opts.buttonText);
        const created = ui.createComponent("product", {
          id: String(productId),
          node: target,
          options,
        });
        if (!cartPromise) {
          cartPromise = created.then(() => ui.components.cart[0]);
        }
        return created;
      })
      .catch((err) => {
        // Fall back to email rather than showing an error on a learning page.
        target.classList.add("shop-error");
        target.innerHTML =
          '<span class="shop-disabled-note">Email <a href="mailto:hello@nehiyomtb.ca">hello@nehiyomtb.ca</a> to ask about one.</span>';
        console.warn("[NehiyoShop] product mount failed:", err);
      });
  }

  // Add one of a product straight to this window's cart and open it. Used by
  // the catalogue when a sign page in its preview pane asks for "Get one", so
  // the visitor stays where they are instead of being sent to another page.
  function addToCart(productId, opts = {}) {
    if (!isConfigured() || !productId) {
      return Promise.reject(new Error("[NehiyoShop] store not configured or no product"));
    }
    return Promise.resolve(mountCart(opts))
      .then(() => getClient())
      .then(({ client, ui }) => {
        const cart = ui.components.cart[0];
        if (!cart) throw new Error("[NehiyoShop] cart did not mount");
        return client.product.fetch(`gid://shopify/Product/${productId}`).then((product) => {
          const variants = (product && product.variants) || [];
          const variant = variants.find((v) => v.available) || variants[0];
          if (!variant) throw new Error("[NehiyoShop] product has no variants");
          return cart.addVariantToCart(variant, 1, true);
        });
      });
  }

  window.NehiyoShop = {
    isConfigured,
    isEmbedded,
    mountCart,
    mountProduct,
    addToCart,
  };
})();
