# Manager M2 Report: Generated Individual Sign Page Contract

## Scope And Inputs

Manager M2 analyzed:

- `docs/kiwapamitin/index.html`
- `docs/kahkakiw/index.html`
- `docs/sign-object-spec.md`
- `catalogue.json`
- a focused read of `docs/index.html` catalogue field bindings

No generated HTML page or exemplar page was edited. The deliverable here is a contract for Manager M3 to generate new individual pages while leaving the current hand-authored exemplars intact.

## Executive Recommendation

Build generated individual pages from a standalone template that mirrors the two exemplars' visual shell and JavaScript interactions, but treats the deep language/story content as optional. The generated page should always include the required page sections, fill them from `catalogue.json` and future extended fields when present, and show explicit "data pending" language instead of inventing Cree forms, related terms, trail embeds, or cultural notes.

Generated output must skip existing exemplar destinations:

- `docs/kahkakiw/index.html`
- `docs/kiwapamitin/index.html`

For every other model, generate only into its own `docs/{pageFolder}/index.html` or the normalized `pagePath` destination. Never use a bulk overwrite that touches existing hand-authored pages.

## Common Exemplar Structure

Both exemplar pages share the same overall shell:

- HTML document with `<html lang="en">`, UTF-8 charset, responsive viewport, inline `<style>`, and inline `<script>`.
- Page title shaped as `{English} • {SRO} • Interactive Poster`.
- `.container` max-width wrapper.
- Centered `header` containing:
  - `h1` shaped as `{English} • {SRO} • {Syllabics}` when all are available.
  - `.tag` text: `Interactive Poster • Plains Cree (nēhiyawēwin)`.
  - Back link to `../index.html`, `target="_top"`, visible text `← Back to Catalogue`.
- Main content in `<section class="grid">` with two `.panel` columns.
- Left panel:
  - word/phrase section
  - trail sign design section
  - optional story/context box
- Right panel:
  - trail information section
  - related forms or data status section
  - examples/quick reference and sources
- Footer shaped as `{English} • {SRO} • Interactive Poster`.

The generated template should keep this skeleton exactly enough that generated pages look like siblings of the exemplars.

## CSS Contract

Use the common class vocabulary from both exemplars:

- Layout: `.container`, `.grid`, `.grid-2`, `.panel`, `.row`, `.kvs`, `.kv`.
- Language display: `.formula`, `.part`, `.syllabics-emphasis`, `.syll-part`, `.sro`, `.syll`.
- Metadata and small UI: `.tag`, `.muted`, `.chips`, `.chip`, `.badge`, `.copy`, `.tooltip`, `.hint`, `.table`, `.primary-content`.
- Optional context box: use a generic class such as `.story-box`; do not hard-code exemplar-only names like `.icu-box` or `.raven-box` in generated pages.

Keep these root tokens data-driven where possible:

- `--accent`
- `--accent2`
- `--primary-bg`
- `--primary-text`
- `--formula-bg`
- `--formula-border`
- `--secondary-bg`
- `--secondary-border`

Recommended fallback theme if `model.theme` is absent:

- `--accent`: first non-white print color mapped to a hex value, else `#000000`
- `--accent2`: darker or same-color fallback
- `--primary-bg`: light tint derived from the accent when easy, else `#f0f0f0`
- `--formula-bg`: `#fafafa`
- `--secondary-bg`: `#f5f5f5`
- `--secondary-border`: `#cccccc`

The colour palette in `docs/index.html` already maps names such as `black`, `white`, `red`, `blue`, `purple`, `orange`, `brown`, and `multicolor`; M3 should reuse that mapping rather than introducing conflicting color names.

## Data-Driven Fields From `catalogue.json`

Minimum page data must come from each `models[]` item:

| Page Need | Field | Required Behavior |
|---|---|---|
| stable identity | `id` | Use for DOM-safe default keys, destination fallback, and generated comments/metadata. |
| display title | `title` | Use when a compact display title is needed; do not assume it equals English. |
| English text | `englishName` | Use in header, word/phrase gloss, quick reference, image alt, footer. |
| SRO | `creeName` | Use as the main romanized Cree form when non-empty. |
| syllabics | `creeSyllabics` | Use as the main syllabics form when non-empty. |
| source folder | `folder` | Use to derive destination and asset fallbacks. Preserve exact casing/diacritics for file paths. |
| STL | `docsStlPath || stlPath` | Prefer `docsStlPath` because generated public pages live under `docs/`; fall back to `stlPath` only as data status/download information if no docs STL exists. |
| image | `imagePath` | Use if present; normalize for page-relative display. If absent or unresolved, render a no-image fallback panel. |
| colors | `colors` | Render color chips and use to derive theme if no explicit theme exists. |
| color layers | `colorLayers` | Render print-layer notes when present; otherwise render colors only. |
| description | `description` | Use in Trail Sign Design and/or story fallback. |
| status | `status` | Show a small data/status badge; if not `published`, add review warning language. |

Recommended future/extended fields from `docs/sign-object-spec.md` should be supported when present:

- `pagePath`
- `trailforksUrl`
- `trailforksWidgetUrl`
- `theme`
- `language.languageName`, `language.nativeName`, `language.meaning`, `language.type`
- `language.parts`
- `language.relatedForms`
- `language.notes`
- `story.heading`, `story.body`
- `trail.name`
- `sources`

## Path Normalization Guidance

Generated pages live one folder below `docs/`, so most public paths should be relative to the page folder.

Recommended page destination:

1. If `pagePath` exists and ends in `/`, write `docs/{pagePath}/index.html`.
2. If `pagePath` exists and ends in `index.html`, write that exact path under `docs/`.
3. Otherwise write `docs/{id}/index.html` unless the source folder convention demands `docs/{folder}/index.html`.
4. Skip if the destination is one of the hand-authored exemplars.

Recommended asset handling:

- `docsStlPath`: link as `../{docsStlPath}` from an individual page if used for a download/link.
- `stlPath`: show as repository source path only when no docs STL exists; do not assume it is web-loadable under `docs/`.
- `imagePath` examples differ between spec and current catalogue. The spec example uses `assets/kahkakiw/raven_wild.png`, while current `catalogue.json` has `kahkakiw/raven_wild.png` for the raven. Normalize in this order:
  - If it starts with `assets/`, render `../{imagePath}`.
  - If it starts with `docs/`, strip `docs/` and render `../{strippedPath}`.
  - If it starts with `{folder}/`, first try `../assets/{folder}/{basename}` for generated page markup because public images are intended to live under `docs/assets/{folder}/`.
  - If no image exists, do not render a broken `<img>`; render the no-image fallback.

## Required Page Sections

### 1. Word/Phrase

Purpose: show the core language item clearly.

Render:

- Heading: `The Word` for known single lexical items, `The Core Phrase` for known phrases, or generic `The Word/Phrase` when only catalogue fields exist.
- Large primary display using `creeName` if present, otherwise `englishName`.
- `.formula` row containing SRO parts.
- `.syllabics-emphasis` row containing matching syllabics parts when `creeSyllabics` exists.
- English gloss below, quoted, from `englishName` or `language.meaning`.

Minimal generated part behavior:

- If `language.parts` exists, render each part with its own `key`, `sro`, `syllabics`, and `gloss`.
- If only `creeName` and `creeSyllabics` exist, render one part using `key = id`, `sro = creeName`, `syllabics = creeSyllabics`, `gloss = englishName`.
- If `creeName` is empty, render a data status message: `Cree SRO form pending review`.
- If `creeSyllabics` is empty, render: `Syllabics pending review` and do not create empty `.syll-part` elements.

### 2. Trail Sign Design

Purpose: connect the language item to the physical sign.

Render:

- Heading: `Trail Sign Design`.
- If `imagePath` resolves, an image with useful alt text: `{English} trail sign showing {SRO or title} in Cree syllabics`.
- Caption from `description`, or fallback `3D printed trail sign`.
- Color chips from `colors`.
- STL line:
  - `Public STL: {docsStlPath}` when available.
  - `Source STL: {stlPath}` when no public STL exists.
- Print layer list from `colorLayers` when present, preserving bottom-to-top order and labels.

No-image fallback:

- Use a `.kv` or `.primary-content` block saying `Image/render not available yet`.
- Still show description, colors, and STL status.

### 3. Trail Information

Purpose: link to trail map/details without inventing unavailable data.

Render:

- Heading: `Trail Information`.
- Standard intro: `Explore the trail on Trailforks for maps, conditions, and details.`
- If `trailforksWidgetUrl` exists, render an iframe like the `kiwapamitin` exemplar.
- If only `trailforksUrl` exists, render a link to Trailforks.
- If neither exists, render muted text `Trail information coming soon`, matching the `kahkakiw` exemplar.

### 4. Related Forms/Data Status

Purpose: show richer language data when present, and make incompleteness explicit when absent.

Render:

- Heading:
  - `Word Forms & Related Terms` for noun/simple entries.
  - `Building Other Forms` for phrase/verb paradigms.
  - `Related Forms & Data Status` as a generic generated fallback.
- For each `language.relatedForms[]`, render a `.kv` with label, English, SRO formula, syllabics row when present, and notes/gloss where present.
- If no related forms exist, render a `.kv` data status panel listing:
  - SRO present/missing.
  - Syllabics present/missing.
  - Related forms not yet added.
  - Status value from `model.status`.
  - Any `language.notes` or model `notes` that are public-safe.

Do not fabricate plural, diminutive, verb, or phrase variants from the base word.

### 5. Quick Reference

Purpose: provide a compact table for copying/checking the displayed language data.

Render:

- Heading block can remain `Examples & Sources`, with subheading `Quick reference`.
- Table columns: `English`, `SRO`, `Syllabics`.
- First row is always the main item.
- Additional rows come from `language.relatedForms[]`.
- If SRO or syllabics are missing, use visible fallback text such as `Pending review`, not an empty cell.
- Keep table text consistent with the Word/Phrase and Related Forms sections.

### 6. Sources

Purpose: cite language and trail/design references shown on the page.

Render:

- Subheading: `Sources`.
- Always include language caveats when any Cree text is displayed:
  - `SRO uses ê î ô â.`
  - `Syllabics match the SRO shown.`
  - `Dialectal preferences may affect minor spelling choices; check local norms for signage.`
- Preferred default references:
  - itwêwina: `https://itwewina.altlab.app/`
  - Online Cree Dictionary: `https://www.creedictionary.com/`
  - Plains Cree Dictionary: `https://dictionary.plainscree.atlas-ling.ca/`
- If `sources[]` exists, render those instead of or in addition to defaults, grouped only if the data supports grouping.
- Include a local consultant/elder/community source only when explicitly present and approved in data.

## Hover And Copy JavaScript Contract

The exemplars implement cross-highlighting by matching SRO `.part` spans to syllabics `.syll-part` spans.

Generated pages must use matching `data-key` values whenever both SRO and syllabics data exist:

```html
<span class="part tooltip" data-key="kahkakiw" data-tip="raven" data-syll-id="kahkakiw-syll">kahkakiw</span>
<span class="syll-part tooltip" data-key="kahkakiw" data-tip="kahkakiw" id="kahkakiw-syll">ᑲᐦᑲᑭᐤ</span>
```

Rules:

- `data-key` must be identical on the SRO and syllabics spans for the same part.
- The SRO `.part` should set `data-syll-id` to the syllabics element id when syllabics exists.
- The syllabics element id should be stable and DOM-safe, for example `${key}-syll`.
- If related forms reuse the same morpheme key in more than one row, suffix keys deterministically (`wapam`, `wapam-2`, `wapam-3`) to avoid accidental cross-highlighting across unrelated forms.
- If syllabics is missing, render the SRO `.part` without `data-syll-id` and do not render a matching `.syll-part`.
- The existing `const pairs = [...]` array in the exemplars is not actually consumed by the event handlers. A generated page may omit it, or generate it for readability, but the real matching must work through `data-key` and `data-syll-id`.

Use the same event behavior:

- On `.part` mouseenter, set `data-active="true"` on the SRO part and on the syllabics element referenced by `data-syll-id`.
- On `.part` mouseleave, remove `data-active`.
- On `.syll-part[data-key]` mouseenter, select all `.part` elements with the same `data-key` and mark them active.
- On `.syll-part[data-key]` mouseleave, remove active state.

Copy behavior:

- Render `.copy` buttons where useful for base SRO and related forms.
- Prefer `data-copy-text="{literal text}"` for generated pages; use `data-copy` only if selecting from the DOM is intentional.
- Keep the tiny toast behavior (`Copied` / `Copy failed`) from the exemplars.

## Standalone Template Shape

Recommended implementation unit for M3:

- A generator script reads `catalogue.json`.
- A pure render function accepts a normalized sign model and returns one complete HTML string.
- A write step creates destination folders and writes only missing/non-exemplar generated pages.

Suggested render contract:

```js
renderSignPage({
  model,
  pageRelativeBackHref: '../index.html',
  normalizedImageSrc,
  normalizedDocsStlHref,
  theme,
  languageParts,
  relatedForms,
  sources
})
```

Normalization should happen before rendering:

- `displayEnglish = model.englishName || model.title`
- `displaySro = model.creeName || ''`
- `displaySyllabics = model.creeSyllabics || ''`
- `mainLanguagePart = language.parts?.length ? language.parts : fallback single part if SRO exists`
- `publicStl = model.docsStlPath || null`
- `sourceStl = model.stlPath || null`
- `pageStatus = model.status || 'draft'`

The template should not require all fields. It should render complete, truthful pages for:

- full data with image, SRO, syllabics, related forms, Trailforks widget, sources
- no image
- no syllabics
- no Cree form
- no related forms
- no public STL

## Acceptance Checks For M3

Before considering generation complete:

- Existing `docs/kahkakiw/index.html` and `docs/kiwapamitin/index.html` are unchanged.
- Every generated page has sections for word/phrase, trail sign design, trail information, related forms/data status, quick reference, and sources.
- Header and footer use available English, SRO, and syllabics without empty separators.
- Back link points to `../index.html`.
- Missing data is shown as pending/review text, not silently omitted where a required section would become empty.
- If SRO and syllabics spans both exist, matching spans share identical `data-key` values.
- SRO spans with matching syllabics set `data-syll-id` to the syllabics span id.
- Hovering SRO highlights syllabics, and hovering syllabics highlights SRO.
- Copy buttons use valid `data-copy-text` or `data-copy` targets and trigger the toast.
- Image paths do not produce broken images for missing or differently rooted `imagePath` values.
- `docsStlPath` is preferred over `stlPath` for public links.
- `colorLayers` are displayed in catalogue order without re-sorting.
- Sources include the standard language references unless explicit source data replaces them.

## Pitfalls To Avoid

- Do not overwrite the two exemplar pages. They contain richer hand-authored content than the current catalogue model.
- Do not infer Cree translations, syllabics, plurals, or diminutives from English or filenames.
- Do not assume `folder` is kebab-case or ASCII; several folders use camelCase, underscores, or diacritics.
- Do not assume `imagePath` currently points directly under `docs/assets`; normalize carefully and provide a no-image fallback.
- Do not use `stlPath` as a web path when it points to a source-folder production file outside `docs/`.
- Do not create empty table cells, empty hover spans, or dangling separators in the header.
- Do not hard-code story boxes named for a specific sign; use a generic optional story/context component.
- Do not depend on the exemplar `pairs` array for hover behavior unless the generated script actually consumes it.

## Self-Assessment

**Craftsperson says:** The report captures the actual shared structure of both exemplar pages, the object contract in `docs/sign-object-spec.md`, and the catalogue's current use of `pagePath`, `docsStlPath`, `colorLayers`, SRO, syllabics, and colors. The hover/copy contract is specific enough for implementation and explicitly names the `data-key` matching requirement.

**Skeptic says:** The largest risk is path normalization for images, because current `catalogue.json` and the spec do not yet fully agree on whether `imagePath` is rooted at `docs/assets`, a source folder, or repository root. Another risk is that catalogue entries currently lack extended `language`, `story`, `trail`, and `sources` objects, so generated pages will be structurally complete but less rich than exemplars unless M3 adds clear pending-data fallbacks.

**Mover says:** This is sufficient for Manager M3 to generate useful, non-destructive pages now. With more time I would add a small path-resolution test matrix and a sample generated page fixture, but the core contract, acceptance checks, and pitfalls are ready to hand off.
