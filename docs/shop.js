/*
 * docs/shop.js — single shared Shopify storefront integration for nehiyoMTB.
 *
 * This file is loaded by both `docs/index.html` (the catalogue) and every
 * per-sign page rendered by `tools/sign_page_renderer.py`. It does three jobs:
 *
 *  1. Holds the one-place Shopify store config (domain + Storefront API token).
 *  2. Lazy-loads the Shopify Buy Button SDK on first use.
 *  3. Exposes a tiny `window.NehiyoShop` API that pages call to:
 *       - mount an "Add to cart" button against a Shopify productId
 *       - mount the floating cart drawer
 *
 *  No Shopify credentials? Leave the placeholders below as-is. The script will
 *  detect missing config, log a single console warning, and silently no-op so
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

  const isConfigured = () =>
    SHOPIFY_DOMAIN &&
    STOREFRONT_ACCESS_TOKEN &&
    !SHOPIFY_DOMAIN.startsWith("YOUR") &&
    !STOREFRONT_ACCESS_TOKEN.startsWith("YOUR");

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

  // Shared cart-button styling. Lives once on the page so re-mounting product
  // buttons reuses the same drawer (single cart across the whole catalogue).
  const CART_OPTIONS = {
    iframe: false,
    text: { total: "Subtotal", button: "Checkout" },
    styles: {
      button: {
        "background-color": "#dc3545",
        ":hover": { "background-color": "#b02a37" },
        ":focus": { "background-color": "#b02a37" },
        "border-radius": "8px",
      },
      footer: { "background-color": "#ffffff" },
    },
  };

  const TOGGLE_OPTIONS = {
    iframe: false,
    sticky: true,
    styles: {
      toggle: {
        "background-color": "#dc3545",
        ":hover": { "background-color": "#b02a37" },
        ":focus": { "background-color": "#b02a37" },
      },
      count: { color: "#ffffff" },
      iconPath: { fill: "#ffffff" },
    },
  };

  const PRODUCT_OPTIONS_BASE = {
    iframe: false,
    contents: {
      img: false,
      title: false,
      price: true,
      description: false,
      options: true,
      quantity: false,
      buttonWithQuantity: false,
      button: true,
    },
    text: { button: "Add to cart" },
    styles: {
      product: {
        "text-align": "center",
        "@media (min-width: 601px)": { "max-width": "100%" },
      },
      button: {
        "background-color": "#dc3545",
        ":hover": { "background-color": "#b02a37" },
        ":focus": { "background-color": "#b02a37" },
        "border-radius": "8px",
        "padding-top": "12px",
        "padding-bottom": "12px",
        "font-size": "16px",
        "font-weight": "700",
      },
      price: { "font-size": "20px", "font-weight": "700", color: "#000" },
      compareAt: { "font-size": "14px" },
    },
  };

  let cartMounted = false;
  function mountCart() {
    if (!isConfigured() || cartMounted) return Promise.resolve();
    cartMounted = true;
    return getClient()
      .then(({ ui }) => {
        ui.createComponent("cart", { options: { cart: CART_OPTIONS, toggle: TOGGLE_OPTIONS } });
      })
      .catch((err) => {
        cartMounted = false;
        console.warn("[NehiyoShop] cart mount failed:", err);
      });
  }

  function mountProduct(target, productId, opts = {}) {
    if (!target) return Promise.resolve();
    if (!isConfigured()) {
      target.classList.add("shop-disabled");
      target.innerHTML =
        '<div class="shop-disabled-note">Online checkout coming soon. ' +
        "Email <a href=\"mailto:hello@nehiyomtb.ca\">hello@nehiyomtb.ca</a> to order.</div>";
      return Promise.resolve();
    }
    if (!productId) {
      target.classList.add("shop-empty");
      return Promise.resolve();
    }
    return getClient()
      .then(({ ui }) => {
        const productOptions = JSON.parse(JSON.stringify(PRODUCT_OPTIONS_BASE));
        if (opts.buttonText) productOptions.text = { button: opts.buttonText };
        if (opts.showPrice === false) productOptions.contents.price = false;
        ui.createComponent("product", {
          id: String(productId),
          node: target,
          moneyFormat: "%24%7B%7Bamount%7D%7D%20CAD",
          options: { product: productOptions },
        });
        // Make sure the floating cart is mounted on any page with a product.
        mountCart();
      })
      .catch((err) => {
        target.classList.add("shop-error");
        target.textContent = "Could not load the buy button.";
        console.warn("[NehiyoShop] product mount failed:", err);
      });
  }

  window.NehiyoShop = {
    isConfigured,
    mountCart,
    mountProduct,
  };
})();
