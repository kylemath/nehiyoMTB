# nehiyoMTB
Nehiyawewin trail signs for Edmonton

Set of 3d printable trail signs made for mountain bike trails around Edmonton, Canada, using Cree syllabics and english. You can print the .stl files, tested on a Creality Ender 3. You can also edit the .skp files in google sketchup yourself. 

![Signs](https://github.com/kylemath/nehiyoMTB/assets/3662613/7e0babbf-c782-4f03-8448-ca30d08f8686)
![Signs2](https://github.com/kylemath/nehiyoMTB/assets/3662613/0c3e7731-dcd3-4afa-a2ee-467f3b79b288)

New:
I now pause at certain layers in the slicer and then change the filment to make multicolour signs that are much improved

Old:
After printing in PLA, I spray praint with white primer, then use Acrylic paints for colour.
![Screenshot](whiteprimer.png)

## Sign-design workflow (graphics → 3D icon → plaque)

A connected pipeline turns each trail name into a printable bilingual sign:

1. **Translation Workbench** — [`docs/cree-trail-names.html`](docs/cree-trail-names.html).
   Every trail now has a **Graphic / 3D icon** column with a suggested screenprint
   concept, a type badge (`screenprint` / `hueforge` / `object`), and an **editable
   image-generation prompt** that already carries a common, extrude-friendly style.
   Press **Generate image** (configure your image API once via **⚙ Image API**; the
   key is stored only in your browser) or copy the prompt into any service.
   Already-built signs are flagged `built ✓` and co-named trails (e.g. *Slinky –
   South*) link to the canonical sign instead of repeating a suggestion.

2. **Style guide** — [`docs/style-guide.html`](docs/style-guide.html).
   The single source of truth for the three styles and, importantly, the **output /
   extrudability spec** (flat separable tones, closed shapes, SVG-preferred) plus the
   colour→layer-height mapping. The prompt style fragments live in
   [`docs/graphics-data.js`](docs/graphics-data.js) and are mirrored here.

3. **Icon Extruder** — [`docs/tools/icon-extruder/index.html`](docs/tools/icon-extruder/index.html).
   Load the generated PNG/SVG, posterize it to a few tones, click each closed region
   to assign a filament colour and a layer height (monotonic steps of the plaque layer
   thickness by default), preview the solid in 3D, and export a manifold **icon STL**
   (combined, or one body per colour for AMS).

4. **HueForge Designer** — [`docs/tools/hueforge/index.html`](docs/tools/hueforge/index.html).
   For the ~10% of signs that are continuous-tone images instead of flat icons.

5. **Plaque generator** — [`tools/plaque_gen/plaque_gen.py`](tools/plaque_gen/plaque_gen.py).
   Combines `blanks/blank_plaque_thinner.stl` with auto-fit, multi-line, centred
   English + transliteration + syllabics text (syllabics protrude in front) and an
   optional icon STL fused on top, then renders a draft `.scad` + `.stl`:

   ```bash
   python3 tools/plaque_gen/plaque_gen.py \
     --en "I See You" --translit "kiwâpamitin" --syllabics "ᑭᐚᐸᒥᑎᐣ" \
     --icon path/to/icon.stl --icon-width 55
   # → signs/i_see_you/i_see_you.scad  and  .stl  (needs OpenSCAD on PATH to render)
   ```

   See [`tools/plaque_gen/README.md`](tools/plaque_gen/README.md) for all options.

6. **Sign factory (one-shot automation)** — [`tools/sign_factory/build_signs.py`](tools/sign_factory/build_signs.py).
   Runs the whole pipeline automatically for every un-made, non-aliased trail: it
   keyword-matches a procedural icon motif to the concept, assembles the coloured
   plaque + auto-fit text + extruded multi-height icon, and renders a draft `.stl`
   plus a preview `.png`. No image API needed (swap in a real generated image via the
   Icon Extruder when you want higher fidelity).

   ```bash
   python3 tools/sign_factory/build_signs.py --only "LOV"      # one sign
   python3 tools/sign_factory/build_signs.py --limit 5         # first 5 unmade
   python3 tools/sign_factory/build_signs.py --all             # every unmade sign
   ```

   Previews land in `docs/sign-drafts/` (tracked, web-served) with a `manifest.json`;
   draft STLs land in `signs/<slug>/` (git-ignored — regenerate any time). The
   Workbench's **Draft sign** column shows each preview (click to enlarge); existing
   signs show `built ✓` and co-named trails reuse the canonical draft.

## Trail app

`mobile/` is the NehiyoMTB trail app (map, bike route builder, sign hunt, ride
logging), built with Expo for iOS, Android and the web. It reads the same
`docs/catalogue.json` live from the website, so new signs show up in the app as
soon as they are pushed. The web version is served at
[nehiyomtb.ca/app](https://nehiyomtb.ca/app/); see [`mobile/README.md`](mobile/README.md).

## Online Store

The catalogue at `docs/` doubles as the storefront for [nehiyomtb.ca](https://nehiyomtb.ca). Purchases are powered by the Shopify Buy Button SDK — Shopify handles checkout, payments, taxes, and shipping while every visible page stays here on GitHub Pages.

To wire up Shopify, the custom domain, and per-sign products, follow the step-by-step guide in [`docs/SHOPIFY_SETUP.md`](docs/SHOPIFY_SETUP.md). Until then, buy buttons stay hidden and the site keeps working as a pure catalogue.
