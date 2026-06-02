# Authoring sign pages (the right way)

**The golden rule: never hand-edit `docs/<slug>/index.html`.** That file is a
**build artifact**. It is regenerated from `catalogue.json` every time a sign is
promoted, saved through the editor, or regenerated. Any change you type directly
into the rendered HTML will be silently overwritten on the next render.

A sign's page is produced by `tools/sign_page_renderer.py` from one place:

```
catalogue.json  →  models[i].pageContent  →  render_page()  →  docs/<slug>/index.html
```

So to change a page **permanently**, you change `pageContent` (and the page
re-renders identically every time). All pages share the same template, so
populating the same fields gives every sign the **same sections, styling, and
interactive features** automatically.

---

## pageStatus — the lifecycle that decides if your edits survive

`pageContent.pageStatus` is one of: `draft`, `agent-drafted`, `user-reviewed`,
`published`.

- **`draft` / `agent-drafted`** — treated as auto-generated. When you
  **Move to production** (`promote-sign`), the server **regenerates**
  `pageContent` from scratch with the *minimal* auto-content, throwing away
  whatever was there. The page renderer also only emits these automatically.
- **`user-reviewed` / `published`** — treated as human-owned. `promote-sign`
  **keeps your `pageContent` as-is** (it does not auto-generate) and just
  re-renders the page + swaps the STL/3MF. **This is the status you want once a
  page is the way you like it.**

> Practical rule: after you've curated a page, set its `pageStatus` to
> `user-reviewed`. Then you can freely re-adjust the sign's 3D components and
> re-promote without ever losing the page.

---

## The `pageContent` schema (every field → what it renders)

Authoritative definition: `_clean_page_content()` in
`tools/catalogue_editor_server.py`. Renderers: `tools/sign_page_renderer.py`.

```jsonc
{
  "pageStatus": "user-reviewed",          // see lifecycle above
  "accentColor": "#2e6eb9",               // page accent (header rule, headings, links)
  "themeName": "",                        // optional label, not rendered
  "headerTitle": "Too Much • osâm mistahi • ᐅᓵᒼ ᒥᐢᑕᐦᐃ",  // big <h1> at top

  "photo": {                              // "Trail Sign Design" block (left column)
    "src": "../assets/too_much/too_much_sign.png",
    "alt": "…",
    "caption": "…"                        // italic line under the image
  },

  "trailforks": {                         // "Trail Information" block (right column)
    "trailSource": "trailforks",          // or "strava"
    "trailUrl": "https://www.trailforks.com/region/…/",  // link shown under the block
    "displayName": "View the … network on Trailforks →", // link text (else the URL)
    "trailId": "",                        // if set, embeds the Trailforks widget iframe
    "widgetUrl": "",                      // explicit widget src (auto-built from trailId)
    "mapEmbedMode": "",                   // "local" → draw uploaded GPX track instead
    "track": []                           // [[lat,lng],…] → renders an SVG mini-map
  },

  "linguistics": {
    "meaning": "Too much — osâm 'too' …", // the quoted gloss under the big word (PLAIN TEXT, gets escaped)
    "type": "",
    "primarySection": {                   // the "The Name on the Plaque" hero block
      "heading": "The Name on the Plaque",
      "sro": "osâm mistahi",
      "syllabics": "ᐅᓵᒼ ᒥᐢᑕᐦᐃ",
      "morphemes": [                      // the interactive part chips + hover tooltips
        { "key": "too_much_0", "sro": "osâm", "syllabics": "ᐅᓵᒼ",
          "gloss": "osâm — 'too, excessively' …" }   // gloss = hover tooltip text
      ]
    },
    "relatedForms": [                     // "Building Other Forms" cards (alt candidates)
      { "english": "more than enough / surplus", "sro": "ayiwâk",
        "syllabics": "ᐊᔨᐗᐠ", "morphemes": [], "note": "italic explanation line" }
    ],
    "quickReference": [                   // the "Quick reference" table rows
      { "english": "…", "sro": "…", "syllabics": "…", "note": "SRO-cell hover tooltip" }
    ],
    "baseWords": [                        // the "Base words" chips with Copy buttons
      { "sro": "osâm", "english": "too, excessively", "syllabics": "ᐅᓵᒼ" }
    ]
  },

  "culturalStory": {                      // a story-box (left column)
    "heading": "Two Words That Both Mean \"A Lot\"",
    "body": [ "para 1 …", "para 2 …" ]    // HTML ALLOWED here (<strong>, <em>, &nbsp;, syllabics)
  },
  "trailStory": {                         // a second story-box (left column); omit to hide
    "heading": "The Trail",
    "body": [ "…" ]                       // HTML ALLOWED
  },

  "sources": [ "itwêwina", "Online Cree Dictionary", "Plains Cree Dictionary" ],
                                          // matched to known dictionary URLs → reference links
  "notes": [ "internal note …" ]          // editorial notes (not shown as a public section)
}
```

### Where HTML is allowed vs escaped
- **HTML allowed** (use `<strong>`, `<em>`, `&nbsp;`, syllabics): `culturalStory.body[]`,
  `trailStory.body[]`.
- **Escaped to plain text** (don't put tags here — they'll show literally):
  `meaning`, every `heading`, `gloss`, `note`, `photo.caption`, `headerTitle`,
  `baseWords[].english`, table cells.

### Sections auto-hide when empty
Leave a field empty/absent and its section simply doesn't render. So a page only
shows what you fill in — and every page that fills the same field looks and
behaves the same.

---

## Recommended workflow

**New sign:** promote from the workbench (creates `agent-drafted` minimal page) →
open the sign in the `index.html` editor → fill in the `pageContent` fields →
**save** (writes `pageContent`, re-renders) → set `pageStatus` to
`user-reviewed` when happy.

**Editing an already-promoted sign's geometry (size/arrangement) without touching
the page:** make sure `pageStatus` is `user-reviewed`/`published`, then use the
workbench 3D viewer → adjust → *build print-ready (server)* → *Move to
production*. The STL/3MF update; the page is preserved.

**If you must add a section the schema doesn't have:** add the field + render
logic to `tools/sign_page_renderer.py` (and `_clean_*` in
`tools/catalogue_editor_server.py`) so it becomes a reusable, consistent feature
for *all* signs — don't bolt it onto one page's HTML.

---

## Auto-drafting content with a Cursor agent (the "✦ Flesh out details" button)

`tools/flesh_out_sign.py` authors a rich `pageContent` for a sign by running a
**Cursor agent** headless (via the `cursor-agent` CLI — it uses your Cursor
desktop login, so **no API key**). The catalogue editor exposes it as the
**✦ Flesh out details (AI)** button (endpoint `/api/flesh-out-sign`).

It gathers the sign's 3 Cree options (from the translation workbench DATA), the
icon concept, the trail stats, the Trailforks/GPX you entered, and the
neighbouring trails; asks the agent for a schema-valid JSON `pageContent`;
validates it; and writes it back at **`pageStatus: agent-drafted`** — a draft
for you to review and bump to `user-reviewed`.

One-time setup:

```bash
curl https://cursor.com/install -fsS | bash   # installs cursor-agent
cursor-agent login                             # one-time, uses your Cursor account
```

CLI usage (the button just calls this server-side):

```bash
# preview the exact prompt, no calls, no writes
python3 tools/flesh_out_sign.py --model caddytrack --dry-run

# run the agent and apply the draft
python3 tools/flesh_out_sign.py --model caddytrack

# apply a pageContent JSON you authored elsewhere (e.g. in chat) — same
# validate + render + agent-drafted path, no agent needed
python3 tools/flesh_out_sign.py --model caddytrack --from-json draft.json
```

The agent is only allowed to author content fields (`linguistics`,
`culturalStory`, `trailStory`, `sources`, `headerTitle`, photo caption); the
`trailforks` block, `photo.src`, and `accentColor` you set in the editor are
preserved, and the status is forced to `agent-drafted` (the LLM can't publish).

## Worked example
`too_much` (sign #25) was migrated from a hand-edited `docs/too_much/index.html`
into a fully schema-driven `pageContent` and marked `user-reviewed`. Its rich
content — morpheme tooltips, the "Two Words That Both Mean 'A Lot'" cultural
story, the alternate-candidate cards, the 5-row quick-reference table, the four
base-word chips, and the Trailforks region link — all live in `pageContent` now,
so re-promoting reproduces the page exactly. A snapshot of the original
hand-edited HTML is kept at `docs/too_much/index.html.handedited.bak`.
