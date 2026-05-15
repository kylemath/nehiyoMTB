# Manager M3 Report — Sign #17 `kakwa` (Agent 2148)

**Manager:** M3
**Sign:** #17 — Kakwa (Porcupine)
**Date:** 2026-05-14
**Deliverable:** `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/pageContent.json` (`pageStatus: "agent-drafted"`)

---

## 1. Headline answer — what is actually carved on the sign?

**SRO:** `kâkwa` (circumflex on first `a`, **high confidence**).
**Syllabics:** `ᑳᑿ` (kâ-kwa) — **best read, medium-high confidence**.

- Left syllabic glyph `ᑳ`: confirmed by a clearly-visible long-vowel dot above the `b`-shape (S1 visual read).
- Right syllabic glyph `ᑿ` (kwa): chosen to match the carved Roman `kwa`. A bare `ᑲ` (ka) cannot be fully ruled out from the composite-image crop, but `ᑿ` is the linguistically-consistent read and is the form M3 has shipped.
- Bottom label: `PORCUPINE` (English, all caps, black).
- Graphic: black porcupine silhouette with the red syllabics embedded in its body.
- Layer scheme: red top (syllabics), black middle (silhouette + Roman text), white base. Confirms `accentColor: "#dc3545"`, `themeName: "red"`.

**This disagrees with the current `catalogue.json` value** of `creeName: "kakwa"` and `creeSyllabics: "ᑲᑲᐧ"`. Per the brief ("trust the sign"), `pageContent` uses the carved forms and the discrepancy is documented in the `notes` array. **Recommendation:** when the coordinator merges, also update the catalogue's `creeName` to `kâkwa` and `creeSyllabics` to `ᑳᑿ` so the summary record matches the carved plaque. (I did not edit `catalogue.json` myself, per hard constraint.)

---

## 2. Trailforks outcome

**No confident match.** S2 ran six distinct search queries plus direct page-greps of:

- `https://www.trailforks.com/region/edmonton/`
- `https://www.trailforks.com/region/edmonton/trails/`
- `https://www.trailforks.com/region/central-edmonton-north`
- `https://www.trailforks.com/region/edmonton/reports`
- `https://www.edmmtnbike.ca/trails`

…with no hits for `kakwa`, `kâkwa`, or `porcupine`. The only namesake is **Kakwa Wildland Provincial Park** (~160 km SW of Grande Prairie — an OHV/hike area, geographically unrelated to Edmonton).

**Action taken:** `trailforks: {}` in `pageContent`, with a `notes` entry explaining the negative search outcome. The sign most likely commemorates the Cree word as cultural/linguistic content rather than naming an existing Trailforks-indexed trail. Search was web-based (not Trailforks API-direct); confidence ~90%.

---

## 3. Linguistic sources and uncertainties

**Sources** (also recorded in `pageContent.sources`):
- itwêwina / Online Cree Dictionary (`creedictionary.com`).
- Plains Cree Dictionary conventions.
- Standard Plains Cree (y-dialect / nêhiyawêwin) morphology training knowledge for plural `-ak` and diminutive `-sis`.

**High-confidence claims:**
- `kâkwa` (ᑳᑿ) — animate noun (NA), "porcupine", Plains Cree citation form.
- `kâkwak` (ᑳᑿᐠ) — animate plural, regular `-ak` suffix.
- Example sentence `niwâpamâw kâkwa` ("I see a porcupine") — VTA `wâpam-` with 1sg→3sg `-âw`, animate object unmarked.

**Flagged uncertainties (also in `notes`):**
- `kâkwasis` "little porcupine" — morphologically regular `-sis` diminutive, not independently verified as a headword in a major dictionary in this run. Flagged in `relatedForms.note`.
- `kâway` "porcupine quill" — competing forms (`kâwiy`, `okâway`) appear across teaching materials; treat as tentative. Flagged inline.
- Coordinator/curator may drop either of these two `relatedForms` rows if a more conservative page is desired.

---

## 4. Cultural story rationale

Three paragraphs were written by S2:

1. **kâkwa as forest teacher** — patience, gentle strength, protection-by-stillness. Non-tribe-specific framing intentionally; no specific community story is appropriated.
2. **Quillwork as foundational craft** — quill prep (pluck/soak/dye/soften/flatten/weave), supports for hide/birchbark/moccasins/pipe stems, predating glass-bead trade. Frames kâkwa as a literal source of artistic material.
3. **Color-palette resonance** (gentle hedge) — red/black/white sign palette as a visual rhyme with earth-pigment quill-dye traditions. Marked explicitly as resonance, not claim of intent.

This third paragraph is the prose's softest claim; the hedge is preserved verbatim in the JSON and should be retained on any edit pass.

---

## 5. Acceptance criteria check

- [x] `manager_M3/pageContent.json` exists, valid JSON, `pageStatus == "agent-drafted"`.
- [x] `linguistics.primarySection.morphemes` has 1 morpheme (`kakwa-root`) with `key`/`sro`/`syllabics`/`gloss`.
- [x] `linguistics.relatedForms` has 3 entries (`kâkwak`, `kâkwasis`, `kâway`), each with its own morpheme.
- [x] `linguistics.quickReference` has 5 rows (within 3–6).
- [x] `linguistics.baseWords` has 1 entry.
- [x] `culturalStory` has heading + 3 paragraphs.
- [x] `trailforks: {}` plus `notes` entry explaining negative search.
- [x] `notes` documents the `kakwa` vs `kâkwa` spelling discrepancy, the second-syllabic-glyph uncertainty, the photo placeholder, and linguistic uncertainties.
- [x] Morpheme `key` values are unique across the page (`kakwa-root`, `kakwak-plural`, `kakwasis-diminutive`, `kaway-quill`).
- [x] `manager_M3_report.md` written with tripartite self-assessment (below).

No changes were made to `catalogue.json`, `docs/kakwa/index.html`, or any file outside `manager_M3/`. No git operations were run. No packages installed.

---

## 6. Files written

- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/pageContent.json`
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/_build_pagecontent.py` (helper script used to dump JSON with `ensure_ascii=False, indent=2`)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/sub_S1/notes.md` (S1 visual + linguistics)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/sub_S2/notes.md` (S2 Trailforks + cultural story)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/manager_M3_report.md` (this file)

---

## 7. Open questions for the coordinator / user

1. **Catalogue update**: should `catalogue.json` `creeName` / `creeSyllabics` be updated to `kâkwa` / `ᑳᑿ` to match the carved sign? (Recommended.)
2. **Second syllabic glyph confirmation**: a higher-resolution single-panel photo would settle `ᑳᑿ` vs `ᑳᑲ`. Best read used is `ᑳᑿ`.
3. **Photo asset**: nothing exists at `docs/assets/kakwa/`. Will the user crop sign #17 from `allSigns.jpg`, or supply a separate photo? `photo: {}` left as placeholder.
4. **Conservative trim of `relatedForms`?** `kâkwasis` (regular but unverified) and `kâway` (competing attestations) could be dropped if a stricter linguistics page is preferred. Both are flagged inline.
5. **Cultural story tone**: the color/quill-dye paragraph is the softest claim. Keep, soften further, or remove?

---

## 8. Tripartite self-assessment

**Craftsperson says:**
The page draft is solid where it counts. The carved SRO `kâkwa` is unambiguous in the image, the long-vowel diacritic on the first `a` is visibly present, and the porcupine silhouette + `PORCUPINE` English label confirms the gloss without ambiguity. Linguistics morphology (animate noun, `-ak` plural, `-sis` diminutive) is textbook Plains Cree. The cultural prose is respectful, factually grounded in widely-attested craft history, and the right length for a sign-page blurb. The JSON is schema-clean, morpheme keys are unique, and the Trailforks negative result is methodically supported. This is publishable agent-drafted output.

**Skeptic says:**
Three real risks remain, all flagged in `notes`. (1) The second syllabic glyph could not be resolved to certainty from the composite-image resolution — `ᑳᑿ` is the best read but `ᑳᑲ` is not impossible. (2) `kâway` "quill" and `kâkwasis` "little porcupine" rest on trained morphology rather than independently verified dictionary citations; a careful Cree-language reviewer may want one or both removed. (3) The Trailforks negative is a strong web-search negative, not an API-confirmed one — a small/private/recently-added trail named Kakwa could in principle exist and have escaped six queries. (4) The catalogue currently disagrees with the carved sign on both the SRO and the syllabics, and I am asking the coordinator to fix that rather than fixing it myself per the hard constraint. The page will look inconsistent against the catalogue summary until that merge happens.

**Mover says:**
None of those risks is blocking, and all are clearly documented downstream. The brief explicitly said to trust the sign over the catalogue, draft the linguistics, and flag uncertainties — that is exactly what was done. The page is ready for the coordinator's atomic catalogue merge and the renderer pass. With another 30 minutes I would (a) request a high-res single-panel photo of #17 to nail down the second syllabic glyph, (b) cross-check `kâway` against itwêwina directly, and (c) consider hitting Trailforks's internal search API to upgrade the negative from ~90% to ~99% confidence. None of these is on the critical path. Shipping.
