# Trail Sign Object Specification

This document defines the working object format for the nehiyoMTB web catalogue and the individual interactive poster pages in `docs/`.

The goal is to keep every sign represented by one predictable data object that can drive:

- the catalogue card in `docs/index.html`
- a dedicated sign page such as `docs/kahkakiw/index.html`
- links to source files, STL files, images, Trailforks pages, and language references

## File Layout

Use these locations unless there is a strong reason to do otherwise.

- `docs/catalogue.json`: collection metadata and the list of sign objects. This is the file the static catalogue page and all `tools/*.py` editors / renderers read and write. (A separate, unrelated `./catalogue.json` stub at the repo root is consumed only by the author's external GitHub-file-organization API and is not touched by any sign tooling.)
- `docs/index.html`: catalogue view that reads `catalogue.json` (resolved relative to itself, i.e. `docs/catalogue.json`).
- `docs/stl-manifest.json`: public STL picker manifest keyed by sign folder.
- `{folder}/`: source and production files for the physical sign.
- `docs/{folder}/`: public sign folder containing `index.html` and web-ready `.stl` files for that sign.
- `docs/assets/{folder}/`: public image and support assets for the sign page.

For signs where the public page name differs from the catalogue id, set `pagePath`.

Example: the catalogue id `kiwapamitin` can point to `docs/kiwapamitin/`.

## Collection Object

`catalogue.json` contains one top-level collection object.

Required fields:

- `id`: stable project id. Current value: `nehiyoMTB`.
- `title`: display title for the collection.
- `oneLiner`: short public description.
- `kind`: object kind. Current value: `collection`.
- `categories`: broad category slugs.
- `tags`: searchable tags.
- `status`: publication status.
- `models`: array of sign objects.

Optional fields:

- `demoUrl`: public catalogue URL.
- `screenshot`: preview image URL.
- `description`: longer collection description.
- `language`: language context, for example `Plains Cree / nēhiyawēwin`.
- `region`: geographic context, for example `Edmonton, Alberta`.

## Sign Object

Each item in `models` represents one trail sign.

Required fields:

- `id`: stable kebab-case identifier used by the web catalogue.
- `signNumber`: stable integer sign number used in cards, labels, printed references, and numbered folder naming.
- `numberedFolder`: canonical numbered folder slug, for example `01-kahkakiw`.
- `title`: display name used on catalogue cards.
- `englishName`: English trail or sign name.
- `creeName`: Standard Roman Orthography text when available. Use an empty string only when no Cree form has been chosen yet.
- `creeSyllabics`: syllabics matching `creeName` when available. Use an empty string only when no syllabics have been chosen yet.
- `folder`: source folder for the sign files.
- `stlPath`: path to the production STL from the repository root.
- `colors`: array of color names used in the printed sign.
- `description`: one-sentence description of the sign.
- `status`: current state.

Recommended fields:

- `pagePath`: individual page path relative to `docs/`, for example `kahkakiw/`.
- `imagePath`: primary image or render path relative to the repository root or `docs/`.
- `docsStlPath`: GitHub Pages-ready STL path relative to `docs/` when different from `stlPath`.
- `trailforksUrl`: Trailforks trail URL.
- `trailforksWidgetUrl`: embeddable Trailforks widget URL.
- `theme`: visual theme metadata for the individual page.
- `colorLayers`: bottom-to-top print color layers for STL preview rendering.
- `language`: linguistic detail object.
- `sources`: citation list for language, trail, and design sources.
- `notes`: internal notes that should not necessarily be displayed.
- `pageContent`: complete per-sign content object used by `tools/sign_page_renderer.py` to generate the public `docs/{folder}/index.html`. See [Page Content Object](#page-content-object) below.
- `checks`: per-sign readiness checklist booleans surfaced as small chips on each catalogue card. See [Card Readiness Checklist](#card-readiness-checklist) below.

Status values:

- `draft`: data is incomplete or not ready to publish.
- `review`: content is being checked, especially language content.
- `published`: public catalogue and page content are ready.
- `archived`: preserved for history but hidden or de-emphasized.

## Extended Sign Object Shape

Use this expanded shape when adding new signs or converting hand-authored pages into data.

```json
{
  "id": "kahkakiw",
  "signNumber": 1,
  "numberedFolder": "01-kahkakiw",
  "title": "Kahkakiw",
  "englishName": "Raven",
  "creeName": "kahkakiw",
  "creeSyllabics": "ᑲᐦᑲᑭᐤ",
  "folder": "kahkakiw",
  "stlPath": "kahkakiw/production.stl",
  "docsStlPath": "kahkakiw/kahkakiw_plaque.stl",
  "imagePath": "assets/kahkakiw/raven_wild.png",
  "pagePath": "kahkakiw/",
  "colors": ["white", "black", "red"],
  "colorLayers": [
    { "color": "white", "maxZ": 983.7, "label": "white back and plaque base" },
    { "color": "black", "maxZ": 1653.483, "label": "black lettering and raven" },
    { "color": "red", "label": "red top surface for syllabics" }
  ],
  "description": "Raven trail sign with black raven graphic.",
  "status": "published",
  "theme": {
    "accent": "#000000",
    "primaryBg": "#f0f0f0",
    "secondaryBg": "#f5f5f5"
  },
  "language": {
    "languageName": "Plains Cree",
    "nativeName": "nēhiyawēwin",
    "orthography": "SRO",
    "meaning": "Raven",
    "type": "noun",
    "parts": [
      {
        "key": "kahkakiw",
        "sro": "kahkakiw",
        "syllabics": "ᑲᐦᑲᑭᐤ",
        "gloss": "raven"
      }
    ],
    "relatedForms": [
      {
        "label": "Plural",
        "english": "Ravens",
        "sro": "kahkakiwak",
        "syllabics": "ᑲᐦᑲᑭᐘᐠ",
        "parts": [
          {
            "key": "kahkakiwak",
            "sro": "kahkakiwak",
            "syllabics": "ᑲᐦᑲᑭᐘᐠ",
            "gloss": "ravens"
          }
        ]
      }
    ],
    "notes": [
      "Syllabics should match the SRO shown.",
      "Dialectal preferences may affect spelling choices."
    ]
  },
  "story": {
    "heading": "About the Raven",
    "body": [
      "The raven holds cultural importance in many Indigenous traditions, including Cree culture.",
      "The trail sign features a stylized raven graphic in black."
    ]
  },
  "trail": {
    "name": "Raven",
    "trailforksUrl": "",
    "trailforksWidgetUrl": ""
  },
  "sources": [
    {
      "label": "itwêwina",
      "url": "https://itwewina.altlab.app/",
      "type": "language"
    },
    {
      "label": "Online Cree Dictionary",
      "url": "https://www.creedictionary.com/",
      "type": "language"
    },
    {
      "label": "Plains Cree Dictionary",
      "url": "https://dictionary.plainscree.atlas-ling.ca/",
      "type": "language"
    }
  ]
}
```

## Field Rules

Identifiers:

- `id` should be lowercase kebab-case ASCII.
- Keep `id` stable once published because it is used for page routing.
- `signNumber` is permanent once assigned. Do not renumber old signs to fill gaps; assign the next unused number.
- Raven / `kahkakiw` is sign `1`.
- `numberedFolder` should start with a zero-padded sign number followed by the `id`, for example `01-kahkakiw`, `18-kiwapamitin`, or `101-new-sign`.
- Use numbered folder slugs for new sign folders when creating new source or public folders.
- Use `folder` for the actual repository folder, even if it contains camelCase, underscores, or diacritics.
- For legacy folders that have not been renamed yet, keep `folder`, `docsStlPath`, and `pagePath` pointing at the actual existing paths, and store the intended numbered name in `numberedFolder`.

Language text:

- `creeName` should use SRO with circumflexes where appropriate: `â ê î ô`.
- `creeSyllabics` must correspond to the SRO form shown.
- For uncertain forms, set `status` to `review` and add a note explaining what needs checking.
- Do not silently replace a checked local spelling with a dictionary spelling unless the change is intentional.

Assets:

- `stlPath` points to the production print file from the repository root.
- `docsStlPath` points to a web-loadable STL under `docs/{folder}/`.
- `imagePath` should point to the main design image, render, or photograph.
- Prefer relative paths so the catalogue works on GitHub Pages.
- Keep original design files, images, gcode, scripts, and work-in-progress assets in the root `{folder}/`.
- Keep `docs/{folder}/` focused on the public page and STL delivery: `index.html` plus `.stl` files.
- Put page images and support files in `docs/assets/{folder}/`.
- If source STLs are nested, flatten them when copying into `docs/{folder}/`; prefix nested parent names when needed to avoid filename collisions.
- Keep `docs/stl-manifest.json` in sync with `docs/{folder}/*.stl`; the catalogue STL dropdown uses this static manifest because GitHub Pages cannot enumerate folders at runtime.

Colors:

- Use lowercase color names.
- Current catalogue colors include `black`, `white`, `red`, `blue`, `purple`, `orange`, `brown`, and `multicolor`.
- Put physical print-layer colors in the order they are intended to be understood or rendered.
- Use `colorLayers` when the STL preview needs explicit filament-change heights. Layers are ordered bottom-to-top and each layer can set `maxZ` in STL model units. The final top layer can omit `maxZ`.

## Local Catalogue Editor

Use the local editor when choosing the final catalogue STL or tuning print colour layers from the web preview. This is intentionally local-only because GitHub Pages cannot write files.

Start it from the repository root:

```sh
python3 tools/catalogue_editor_server.py
```

Then open:

```text
http://127.0.0.1:8765/docs/index.html
```

When the editor is connected, `docs/index.html` enables save controls in the selected-sign panel.

Final STL workflow:

- Pick an STL candidate from the selected sign's STL dropdown.
- Candidates include files from both `docs/{folder}/` and the root `{folder}/`.
- Click `Set selected STL as final` or `Save print setup`.
- If the selected STL is in the root `{folder}/`, the server copies it into `docs/{folder}/`.
- The selected final STL is kept in `docs/{folder}/`.
- A copy of the selected final STL is also kept in the root `{folder}/` working/archive folder.
- Other `.stl` variants currently in `docs/{folder}/` are moved back into the root `{folder}/`; name conflicts get a `_movedN` suffix.
- The server updates `docsStlPath` and regenerates `docs/stl-manifest.json`.

Colour layer workflow:

- Choose the number of colour layers.
- Pick a colour for each layer.
- Move the boundary sliders to match filament-change heights in the loaded STL.
- Click `Save print setup`.
- The server updates `colors` and `colorLayers` in `catalogue.json`.

The published static page ignores the write API when it is unavailable and continues to use the saved `catalogue.json` and `docs/stl-manifest.json` data.

Individual pages:

- The page header should show `English • SRO • Syllabics`.
- Store the page at `docs/{folder}/index.html`.
- Include a back link to `../index.html`.
- Use sections for word or phrase, trail sign design, trail information, related forms, examples or quick reference, and sources.
- Keep hover/copy interactions based on matching `key` values between SRO parts and syllabics parts.

Sources:

- Cite language sources on each page when linguistic content is displayed.
- Current preferred references are itwêwina, Online Cree Dictionary, and Plains Cree Dictionary.
- Add a local consultant, elder, or community source when available and approved for public attribution.

## STL Closure And Repair

Use this workflow when a sign renders as thin walls, missing faces, inverted surfaces, or fails in Creality Print. The most common cause is a non-watertight STL: open boundary edges, flipped normals, or non-manifold edges.

Always keep the original file before repairing:

```sh
cp "docs/{folder}/{name}.stl" "docs/{folder}/{name}_bk.stl"
```

Install `admesh` once:

```sh
brew install admesh
```

Run an automatic closure pass on a copy:

```sh
admesh --nearby --fill-holes --normal-directions --normal-values \
  --write-binary-stl="docs/{folder}/{name}_fixed.stl" \
  "docs/{folder}/{name}.stl"
```

What the flags do:

- `--nearby`: connects nearby unmatched facets when possible.
- `--fill-holes`: adds triangles across open boundary loops.
- `--normal-directions`: fixes clockwise/counterclockwise face orientation.
- `--normal-values`: recalculates normal vectors.
- `--write-binary-stl`: writes a new STL without overwriting the source.

Validate the result before replacing the main STL. A repaired file should have `0` open boundary edges. Non-manifold edges should also be `0` when possible, but some old signs may still slice if only a few remain.

If `--fill-holes` closes the wrong area, for example filling the counter inside a letter or changing a small detail, do not use that fully repaired file as-is. Instead:

- Keep the repaired large component that needed closure, such as an animal or icon silhouette.
- Keep the original text, plaque, holes, and other small components from the backup.
- Export a hybrid STL, then verify it again.

For difficult cases, rebuild from the original design source rather than patching the STL:

- Open the source `.skp`, `.svg`, `.dxf`, or generator script.
- Make each printed shape a closed filled face, not loose linework.
- Extrude closed faces into solids.
- Boolean-union or intentionally keep separate print-color solids.
- Export a fresh STL and run the validation step.

For visual repair outside SketchUp, Blender is useful:

- Import the STL.
- Enable the `3D Print Toolbox` add-on.
- Use `Select All by Trait > Non Manifold`.
- Run `Merge by Distance`, `Recalculate Outside`, and careful hole filling.
- Export STL and validate before publishing.

## Minimal New Sign Template

Use this object when adding a sign before building the full individual page.

```json
{
  "id": "new-sign-id",
  "signNumber": 24,
  "numberedFolder": "24-new-sign-id",
  "title": "Display Title",
  "englishName": "English Trail Name",
  "creeName": "",
  "creeSyllabics": "",
  "folder": "sourceFolderName",
  "stlPath": "sourceFolderName/production.stl",
  "imagePath": "sourceFolderName/image.png",
  "pagePath": "new-sign-id.html",
  "colors": ["white", "black"],
  "description": "Short description of the trail sign.",
  "status": "draft"
}
```

## Page Content Object

Use `pageContent` to drive the renderer that produces a kiwapamitin-style interactive poster page (`docs/{folder}/index.html`). The renderer lives at `tools/sign_page_renderer.py` and can be invoked from the local editor UI or from the command line.

When `pageContent` is missing or has `pageStatus` of `draft`, the renderer leaves the existing `index.html` untouched. When `pageContent.pageStatus` is `agent-drafted`, `user-reviewed`, or `published`, the renderer overwrites `docs/{folder}/index.html`.

Shape:

```json
{
  "pageContent": {
    "pageStatus": "agent-drafted",
    "accentColor": "#dc3545",
    "themeName": "red",
    "headerTitle": "I See You • kiwâpamitin • ᑭᐚᐸᒥᑎᐣ",
    "photo": {
      "src": "../assets/kiwapamitin/iseeyousign.png",
      "alt": "I See You trail sign showing kiwâpamitin in Cree syllabics",
      "caption": "3D printed trail sign with multi-color design"
    },
    "trailforks": {
      "trailId": "805899",
      "trailUrl": "https://www.trailforks.com/trails/i-see-you/",
      "widgetUrl": "https://www.trailforks.com/widgets/trail/?trailid=805899&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1",
      "displayName": "I See You",
      "mapCoords": { "lat": 53.51605, "lng": -113.53973, "source": "trailforks trailhead 805899" },
      "mapEndCoords": { "lat": 53.51092, "lng": -113.53973, "source": "estimated: 570m southbound descent" },
      "track": [[53.51605, -113.53973], [53.51610, -113.53980]]
    },
    "linguistics": {
      "meaning": "I See You",
      "type": "verb phrase",
      "primarySection": {
        "heading": "The Core Phrase",
        "sro": "ki‑wâpam‑itin",
        "syllabics": "ᑭᐚᐸᒥᑎᐣ",
        "morphemes": [
          { "key": "ki", "sro": "ki‑", "syllabics": "ᑭ", "gloss": "marks 'you' (the person you're talking to)" },
          { "key": "wapam", "sro": "wâpam", "syllabics": "ᐚᐸᒥ", "gloss": "'see (a person)'" },
          { "key": "itin", "sro": "‑itin", "syllabics": "ᑎᐣ", "gloss": "means 'you (one person)'" }
        ]
      },
      "relatedForms": [
        {
          "english": "I See Them",
          "sro": "niwâpamâwak",
          "syllabics": "ᓂᐚᐸᒫᐘᐠ",
          "morphemes": [
            { "key": "ni2", "sro": "ni‑", "syllabics": "ᓂ", "gloss": "marks 'I' (the speaker)" },
            { "key": "wapam2", "sro": "wâpam", "syllabics": "ᐚᐸᒫ", "gloss": "'see (a person)'" },
            { "key": "awak", "sro": "‑âwak", "syllabics": "ᐘᐠ", "gloss": "means 'them'" }
          ],
          "note": ""
        }
      ],
      "quickReference": [
        { "english": "I See You (sg)", "sro": "kiwâpamitin", "syllabics": "ᑭᐚᐸᒥᑎᐣ", "note": "ends with -itin" }
      ],
      "baseWords": [
        { "sro": "wâpiw", "english": "He/She Sees", "syllabics": "ᐚᐱᐤ" }
      ]
    },
    "culturalStory": {
      "heading": "The ICU Connection",
      "body": [
        "The trail builder, an ICU physician, chose a name rich with meaning...",
        "The act of truly seeing each patient—kiwâpamitin—embodies the essence of intensive care."
      ]
    },
    "trailStory": {
      "heading": "",
      "body": []
    },
    "sources": ["itwêwina", "Online Cree Dictionary", "Plains Cree Dictionary"],
    "notes": ["Cree forms read directly from sign image and STL geometry."]
  }
}
```

Field rules:

- `pageStatus` lifecycle: `draft` (renderer skips), `agent-drafted` (agent filled values, awaiting human review), `user-reviewed` (human approved), `published` (locked).
- `accentColor` is a CSS color used for the page's `--accent`. The renderer derives related CSS variables (`--accent2`, `--primary-bg`, `--formula-bg`) from it.
- `photo.src` is relative to `docs/{folder}/index.html`. Use `../assets/{folder}/...` for assets under `docs/assets/`. If `photo` is omitted the renderer falls back to embedding the STL render via three.js.
- `trailforks` is optional. When omitted, the renderer shows a "trail information coming soon" stub.
- `trailforks.mapCoords` is optional. When present, the catalogue map view in `docs/index.html` places a sign-image marker at `{lat, lng}` on an Edmonton map. Copy the trailhead coordinates from the Trailforks trail page FAQ ("The trailhead is located at coordinates ..."). The optional `source` string is a free-form provenance note.
- `trailforks.mapEndCoords` is optional. When present alongside `mapCoords` (and no detailed `track` is set), the catalogue map view draws a dashed rough-estimate line from the trailhead to this point, with green start / blue end dot markers. Use this when you do not have a digitised path but can estimate the end coordinate from the Trailforks length + bearing description. The line tooltip labels it as a rough estimate.
- `trailforks.track` is optional. When present, the catalogue map view draws a solid polyline from the array of `[lat, lng]` points, with green start / blue end dot markers (and takes precedence over `mapEndCoords`). Trailforks does not expose track GeoJSON over its public web (Cloudflare blocks scripted requests, and the JSON API requires `app_id`/`app_secret`), so populate this array manually using one of:
  - Recording a GPX of the trail and converting to `[lat, lng]` pairs.
  - Tracing the trail in [geojson.io](https://geojson.io/) over satellite imagery and exporting the `LineString`.
  - Exporting the trail GPX from inside the Trailforks app on a logged-in account, then downsampling.
- The catalogue map view also renders an STL snapshot per sign as the marker icon. Snapshots are baked on demand inside `docs/index.html` using the same Three.js color-layer pipeline as the catalogue's interactive STL viewer, so the marker styling automatically tracks `colors` / `colorLayers` changes — no separate render PNG is needed.
- The right column's **Map** tab uses [MapLibre GL JS](https://maplibre.org/) with a 3D terrain surface and supports an in-map **Tilt / Top-down** toggle. Tilt is the oblique 3D perspective; Top-down is a flat overhead view of the same map. The tab reads the same `mapCoords` / `mapEndCoords` / `track` fields; no extra data is needed. Tile sources used:
  - Satellite basemap: ESRI World Imagery (free for non-commercial use).
  - Cartoon basemap: CartoDB Voyager (`{a,b,c,d}.basemaps.cartocdn.com/rastertiles/voyager`) — exposed via a second in-map **Satellite / Cartoon** toggle that only appears in Top-down mode. Switching basemaps preserves camera center/zoom/bearing because both rasters live on the same MapLibre map; markers and trail lines never re-render. Tilt mode forces Satellite back on because the cartoon raster does not read well draped over terrain.
  - DEM: AWS Open Data Mapzen Terrarium tiles (`s3.amazonaws.com/elevation-tiles-prod/terrarium`).
  - Terrain exaggeration defaults to 1.8× to make Edmonton's river-valley topography legible at city scale.
- `linguistics.primarySection` is required when status is past `draft`. `morphemes` is allowed to contain a single morpheme for simple noun signs (e.g. `kahkakiw`).
- `linguistics.relatedForms[].morphemes[].key` values must be unique per page so the renderer can wire hover-highlighting between SRO and syllabics. The renderer auto-suffixes duplicates if needed.
- `culturalStory` is optional. The renderer shows the box only when `heading` and at least one `body` paragraph are present.
- `trailStory` is also optional and renders separately from `culturalStory`. Use it for trail-builder backstories like the ICU connection.
- `sources` is a list of label strings; the renderer links the known references (itwêwina, Online Cree Dictionary, Plains Cree Dictionary) to their canonical URLs.

Authoritative content source:

- Cree SRO and syllabics on the page should match the carved/printed text on the physical sign whenever possible. Agents drafting `pageContent` should visually inspect the sign image (`docs/assets/{folder}/*` or crops from `allSigns.jpg`) and the production STL geometry as the primary source, falling back to dictionaries only for related forms and morpheme glosses.

## Card Readiness Checklist

Each catalogue card shows a row of six tiny chips at the top so it's clear at a glance which production steps are still pending for a sign. Each chip is one capital letter; hover for the full label and current state (`done` / `pending`). A green-filled chip means the step is satisfied; a hollow grey chip means it is still pending. The hand-built exemplar (`kiwapamitin`) shows all six chips in purple.

Replaces the older single `pageStatus` corner pill which conflated mesh repair, STL selection, colour layer setup, trail metadata, photo, and human review into one flag and overlapped the card title.

| Chip | Meaning                          | How it is determined                                                                       |
| :--: | -------------------------------- | ------------------------------------------------------------------------------------------ |
| `M`  | Mesh repaired (STL watertight)   | `model.checks.meshRepaired === true`. Auto-set when the editor's `Run mesh closure repair` button calls `/api/repair-stl` and admesh reports `Total disconnected facets … Final: 0`. Also exposed as a manual checkbox in the editor for Blender-repaired meshes or hand-confirmed cases. |
| `S`  | Final STL selected               | Auto: `model.docsStlPath` is set, i.e. the user has run `Set selected STL as final` (or it was hand-authored). |
| `C`  | Colours and print layers         | Auto: `model.colorLayers` is non-empty and every entry has a non-empty `color`.            |
| `T`  | Trailforks linked                | Auto: any of `pageContent.trailforks.trailUrl`, `trailId`, or `widgetUrl` is non-empty.    |
| `P`  | Sign photo set                   | Auto: `pageContent.photo.src` is non-empty.                                                |
| `D`  | Page draft confirmed by user     | Auto: `pageContent.pageStatus` is `user-reviewed` or `published`. `agent-drafted` alone is not enough — the chip stays pending until you explicitly mark the draft reviewed. |

`pageStatus` itself still drives the renderer (only `agent-drafted`, `user-reviewed`, and `published` cause `tools/sign_page_renderer.py` to overwrite `docs/{folder}/index.html`). The `D` chip is the human-confirmation half of that lifecycle.

`checks` shape on a sign object:

```json
{
  "checks": {
    "meshRepaired": true
  }
}
```

Only `meshRepaired` is persisted today because the other five chips read directly from existing fields. If a future check needs a manual toggle (for example a "language reviewed by elder" flag), add another boolean to `checks` rather than overloading `pageStatus`.

The local catalogue editor exposes `checks.meshRepaired` as a checkbox in the Sign Page Content panel; saving the panel sends the new value alongside `pageContent` to `/api/save-sign-content`.

## Page Checklist

Before marking a sign `published`, check:

- The sign appears in `catalogue.json`.
- The `id`, `signNumber`, `numberedFolder`, `folder`, `stlPath`, and `pagePath` resolve or intentionally describe current legacy paths correctly.
- The catalogue card shows sign number, title, English name, SRO, and syllabics.
- The individual page includes a back link to `index.html`.
- The image or render has useful alt text.
- Trailforks information is included when available.
- Language forms have been checked against listed sources or local review.
- SRO, syllabics, and English glosses agree across catalogue, page, and markdown notes.

