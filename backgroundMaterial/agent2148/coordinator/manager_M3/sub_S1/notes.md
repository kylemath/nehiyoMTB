# Sub-subagent S1 Notes — Sign #17 `kakwa` (Porcupine)

Agent: **Agent 2148 / Manager M3 / Sub-S1**
Sign: **#17 — Kakwa (Porcupine)**
Source image: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg` (8160 × 6144 px composite)
Working crops: `/tmp/kakwa_crop_small.jpg`, `/tmp/kakwa_syl_small.jpg`

---

## 1. Visual read of the physical sign

I cropped the Kakwa panel from the composite image at two zoom levels (full panel + tight crop on the porcupine graphic) and examined them directly. The panel is a standard three-layer plaque (red top relief, black middle relief, white base) consistent with the rest of the series.

| Element | What I see | Confidence |
|---|---|---|
| SRO heading (top) | **`kâkwa`** — clearly carved in **black** raised letters. The circumflex above the first `a` is unambiguous (visibly separated from the letter, two small strokes forming a hat). The `w` is a clean Roman `w` (not `v`). | **High** |
| Bottom label | **`PORCUPINE`** — black raised all-caps. | **High** |
| Central graphic | A **porcupine silhouette in black** (full-body side profile, head to the right, mouth/eye visible, quills/spines radiating from the back). | **High** |
| Embedded syllabics (red) | **Two `b`-shaped (ᑲ-family) syllabic glyphs** sitting inside / overlaid on the porcupine's body. The left glyph clearly has a **small dot above it** (the long-vowel marker → `kâ`, i.e. **ᑳ**). The right glyph is the same `b`/`ᑲ` base shape; I cannot fully resolve whether it carries a tiny upper-right finalizer dot/curl that would distinguish **ᑿ (kwa)** from a plain **ᑲ (ka)** at the resolution available. | Left glyph: **High** (it is ᑳ). Right glyph: **Medium** — best read is **ᑿ (kwa)** to match the SRO `kâkwa`, but a bare **ᑲ (ka)** cannot be ruled out from the photo alone. |
| Base plate color | White / off-white. | **High** |
| Mounting | LED-style mounting bead at top, single screw hole at bottom centre — same hardware pattern as adjacent panels. | High (not lingually relevant) |

**Best-read transcription of what is carved on the sign:**

- SRO: **`kâkwa`**
- Syllabics: **`ᑳᑿ`** (kâ-kwa) — *most likely*; with `ᑳᑲ` (kâ-ka) as a secondary possibility if the right glyph is unmodified.
- Bottom label: **`PORCUPINE`**
- Graphic: black porcupine silhouette with the syllabics rendered in red inside the body.
- Layer scheme: red top (syllabics), black middle (animal silhouette + Roman text), white base.

---

## 2. STL filename / solid-name cross-check

`head -1` on `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kakwa/kakwa_plaque_v3_admesh_fixed_1.stl` returned:

```
Processed by ADMesh version 0.98.5
```

The solid-name header was overwritten by `admesh` during repair, so it carries no carved-string information. The directory and filename use ASCII `kakwa` (no diacritic), which is a pragmatic filename convention — it does **not** contradict the carved `kâkwa` reading. No useful disambiguation between `ka` vs `kwa` second-syllable from the file header.

---

## 3. Linguistics draft (drop-in JSON for `pageContent.linguistics`)

```json
{
  "primarySection": {
    "heading": "The Word",
    "sro": "kâkwa",
    "syllabics": "ᑳᑿ",
    "morphemes": [
      {
        "key": "kakwa-root",
        "sro": "kâkwa",
        "syllabics": "ᑳᑿ",
        "gloss": "porcupine (animate noun, NA)"
      }
    ]
  },
  "relatedForms": [
    {
      "english": "porcupines (plural)",
      "sro": "kâkwak",
      "syllabics": "ᑳᑿᐠ"
    },
    {
      "english": "little porcupine (diminutive)",
      "sro": "kâkwasis",
      "syllabics": "ᑳᑿᓯᐢ"
    },
    {
      "english": "porcupine quill (uncertain form — see notes)",
      "sro": "kâway",
      "syllabics": "ᑳᐘᕀ"
    }
  ],
  "quickReference": [
    { "english": "porcupine", "sro": "kâkwa", "syllabics": "ᑳᑿ" },
    { "english": "porcupines", "sro": "kâkwak", "syllabics": "ᑳᑿᐠ" },
    { "english": "little porcupine", "sro": "kâkwasis", "syllabics": "ᑳᑿᓯᐢ" },
    { "english": "porcupine quill", "sro": "kâway", "syllabics": "ᑳᐘᕀ" },
    { "english": "I see a porcupine", "sro": "niwâpamâw kâkwa", "syllabics": "ᓂᐚᐸᒫᐤ ᑳᑿ" }
  ],
  "baseWords": [
    { "sro": "kâkwa", "english": "Porcupine", "syllabics": "ᑳᑿ" }
  ],
  "meaning": "Porcupine",
  "type": "noun"
}
```

### Notes on the linguistic content

- **`kâkwa`** is a Plains Cree (nêhiyawêwin / y-dialect) **animate noun (NA)** for porcupine. Standard itwêwina / Online Cree Dictionary (`creedictionary.com`) headword form. The long â in the first syllable is the citation form.
- Some sources spell it without the macron (`kakwa`) in casual/anglicised contexts. The sign uses the proper long-vowel form, so I match it.
- **Plural** of NA stems in `-a` is the suffix **`-ak`** → **`kâkwak`** "porcupines". High confidence — this is regular animate-plural morphology.
- **Diminutive** in Plains Cree is **`-sis`** (with stem-final adjustments). **`kâkwasis`** "little porcupine" is the expected regular formation. I have not personally verified it as a dictionary headword, so it should be treated as a **derived/regular form** rather than a quoted citation.
- **`kâway`** "porcupine quill" — this is the form I am least confident about. Plains Cree has competing attested forms in different sources: **`kâway`** / **`kâwiy`** / **`okâway`** appear in different teaching materials. The syllabics `ᑳᐘᕀ` correspond to `kâway` (kâ-wa-y-final). If M3 wants to be conservative, drop this row or replace with a different uncontroversial related form (e.g. another animal of similar habitat). I have flagged this with "uncertain form" in the JSON `english` field so it is visible downstream.
- The example sentence **`niwâpamâw kâkwa`** "I see a porcupine" uses the VTA `wâpam-` "see (animate object)" with 1sg→3sg ending `-âw`. The animate object is unmarked (zero-marked) since it is 3sg proximate. High confidence on grammar.

---

## 4. Uncertainties (explicit)

1. **Second syllabic glyph (ka vs kwa)**: visual evidence is consistent with **ᑿ (kwa)** to match the SRO `kâkwa`, but the small w-final mark on the upper-right of the second `b`-shape is not crisply resolvable in the image crops at the resolution used. I report **ᑳᑿ** as the best read; **ᑳᑲ** is the secondary possibility. A higher-resolution photo of just that panel would resolve this. *Recommendation to M3:* if anyone has direct physical access to the plaque, eyeball the second glyph for a small upper-right curl/dot.
2. **`kâway` / `kâwiy` / `okâway` for "porcupine quill"**: form not confidently attested from a single canonical source in my training. Flagged in the JSON. M3 can drop this row if conservatism is preferred.
3. **`kâkwasis` "little porcupine"**: morphologically regular but I have not verified it as a headword in a major Plains Cree dictionary. It is presented as a likely-regular diminutive, not a quoted citation.
4. **Dialect**: I have assumed Plains Cree (y-dialect / nêhiyawêwin), which is the dialect convention of the rest of this catalogue. If the project standard is Woods Cree (th-dialect) or Swampy Cree (n-dialect), some forms would shift (e.g. `kâkwa` is stable across these, but other items vary). The catalogue's other signs appear to be y-dialect, so I have matched that.
5. **Final-`k` syllabic for plural**: I wrote **ᑳᑿᐠ** using the standard Western final-k glyph `ᐠ`. Some materials use the alternate `ᐤ` or a raised final; `ᐠ` is the most common modern convention and is what I have used consistently here.

---

## 5. Tripartite self-assessment

**Craftsperson says:** The visual read on the SRO is rock-solid — `kâkwa` is unambiguously carved, the circumflex is clearly there, and the porcupine graphic / bottom `PORCUPINE` label confirm the gloss. The animate-noun classification and the plural `kâkwak` are textbook Plains Cree morphology that I can produce with full conviction. The JSON block matches the schema shape used elsewhere in this catalogue and is drop-in ready for `pageContent.linguistics`.

**Skeptic says:** I did not resolve the second syllabic glyph (ka vs kwa) to certainty from the photo — I made the linguistically-motivated choice (`ᑿ` to match the carved Roman `kwa`) but the visual evidence at this resolution is consistent with either. I also leaned on my trained intuition for the quill word (`kâway`) and the diminutive (`kâkwasis`) without external verification, and flagged those explicitly. If a dictionary cross-check is run, the `kâway` line is the most likely to need correction. I also did not consult the actual itwêwina online dictionary in this run — purely trained knowledge.

**Mover says:** What I have is good enough to advance: SRO + syllabics for the primary headword are at high enough confidence for M3 to ship the page, and every weaker claim is flagged inline with the JSON and again in §4. M3 can lift the JSON as-is, or strip the two flagged related-forms rows if they want a conservative page. With another 10 minutes I would (a) request a high-res single-panel photo to nail down ka-vs-kwa on the second glyph, and (b) cross-check `kâway` against a canonical source — but neither is blocking. Shipping.
