#!/usr/bin/env python3
"""One-shot migration: add an empty ``shopify`` block to every sign in
``docs/catalogue.json`` if it does not already have one.

The shopify block is the per-sign Shopify product binding consumed by
``docs/shop.js`` and ``tools/sign_page_renderer.py``:

    "shopify": {
        "productId": "",          # numeric Shopify product id, as a string
        "variantId": "",          # optional specific variant id; otherwise first
        "priceCAD": null,         # advisory price for catalogue/page chips
        "available": false        # explicit kill switch; false hides the button
    }

Leaving the strings empty and ``available`` false means the buy button stays
hidden on the live site until you fill in the values. Editing the catalogue
through this migration keeps key order stable and preserves every other field.

Idempotent: run it as many times as you want.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = REPO_ROOT / "docs" / "catalogue.json"


def default_shopify_block() -> dict:
    return {
        "productId": "",
        "variantId": "",
        "priceCAD": None,
        "available": False,
    }


def main() -> None:
    data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    changed = 0
    for model in data.get("models", []):
        if "shopify" not in model:
            model["shopify"] = default_shopify_block()
            changed += 1
        else:
            block = model["shopify"]
            for key, value in default_shopify_block().items():
                block.setdefault(key, value)

    CATALOGUE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {changed} model(s); catalogue saved.")


if __name__ == "__main__":
    main()
