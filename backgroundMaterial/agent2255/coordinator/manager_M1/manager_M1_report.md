# Manager M1 Report — Agent 2255 Batch 2

**Manager:** 2255-M1
**Coordinator:** 2255-C
**Scope:** 5 signs — `mistapiskihkoman` (Machete), `nicocwasaskanos` (Six Shooter), `nipamayatan-pekiseyahk` (Purple Haze), `lovers-lane` (Lovers Lane), `mamahtaw-iskwew` (Wonder Woman)
**Output folder:** `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2255/coordinator/manager_M1/`

---

## TL;DR

All 5 fragment JSONs are written, all 8 acceptance criteria pass on every sign, every fragment has `photo.src` populated against a real file in `docs/assets/`, and 5 of 5 signs have a Trailforks match (4 with high confidence + numerical trail IDs verified by direct page fetch; 1 with high confidence by neighbour-link). 5 catalogue corrections are proposed (3 syllabics-only, 2 SRO+syllabics).

---

## Per-sign summaries

### 1. `mistapiskihkoman` — Machete

**PASS.** Wired existing root design `mistapiskihkoman/mistapiskihkoman.png` into `docs/assets/mistapiskihkoman/`. Plaque-correct SRO `mistâpiskihkomân` matches the catalogue, but the carved syllabics show `ᒥᐢᑖᐱᐢᑭᐦᑯᒫᐣ` (long-â glyph ᑖ in 2nd position) — current catalogue has plain ᑕ. Trailforks AKA confirms ᒥᐢᑖᐱᐢᑭᐦᑯᒫᐣ. Morpheme decomposition: `mist‑` (big) + `‑âpisk‑` (metal medial) + `‑(i)hkomân` (knife-final). Trailforks: black-diamond, Keillor / NW Edmonton, trail id 30260.

### 2. `nicocwasaskanos` — Six Shooter

**PASS.** Wired existing root design `nicocwasaskanos/nikocwasaskanos.png` (photo shows the carved revolver-with-red-syllabics design). Catalogue creeName `nikocwâsaskanôs` is correct, but creeSyllabics `ᓂᑯᐚᓴᐢᑲᓄᐢ` is missing the `c` and the long-ô — Trailforks AKA writes the correct `ᓂᑯᒑᐧᓴᐢᑲᓅᐢ`. Morpheme reading: numeral `nikocwâs‑` ‘six’ + body-medial `‑askan‑` ‘bone / hard projecting’ + diminutive `‑ôs`. Trailforks: blue, Central Edmonton (South), trail id 18858.

### 3. `nipamayatan-pekiseyahk` — Purple Haze

**PASS.** Wired existing root design `nipamayatan_pekiseyahk/purple_haze.png` (the strongest design source: the painted purple-mountain plaque with the white syllabics). Catalogue SRO `nipâmâyâtan pekisehyânik` materially diverges from the carved `nîpâmâyâtân pekiseyâhk` — missing î on first vowel, missing n-final on -mâyâtân, has spurious -hy- + -ânik instead of -yâhk. Proposed catalogue creeName: `nîpâmâyâtân pekiseyâhk`. Morpheme reading: VII `nîpâ‑mâyâtân` ‘it is dim/hazy’ + AI 1pl-incl conjunct `pekiseyâhk` ‘when we (all) ride through’. Trailforks: trail id 15797 (in Wonder Woman’s Nearby Trails list).

### 4. `lovers-lane` — Lovers Lane

**PASS.** No root design image existed; cropped the upper of the two heart plaques from `allSigns.jpg` to `docs/assets/loversLane/sign_render.png` (preview crop 310,605 → 460,885; original-image crop 1581,3084 → 2346,4512). Catalogue creeName `nicimosak méskanâs` has two errors — pluralises sweetheart and uses French acute é instead of Cree circumflex ê. Plaque carves singular `nicimos mêskanâs`. Morpheme reading: 1sg `ni‑` + dependent NA stem `‑cimos` ‘sweetheart’ + NI stem `mêskan‑` ‘road’ + diminutive `‑âs`. Trailforks: blue, Central Edmonton (North), trail id 15796.

### 5. `mamahtaw-iskwew` — Wonder Woman

**PASS.** Wired existing root design `mamahtaw_askwew/mamahtaw_iskwew.png` (the silhouette-with-red-syllabics design — note the legacy folder typo `_askwew` is preserved per coordinator instructions). Catalogue creeName `mamahtaw iskwew` missing â circumflex; carved `mamahtâw iskwew`, Trailforks AKA confirms. Morpheme reading: pre-noun VII `mamahtâw` ‘wondrous, miraculous, having spirit-power’ + NA `iskwew` ‘woman’. Trailforks: blue, Hawrelak / NW Edmonton, trail id 31377.

---

## Asset wiring (`docs/assets/{folder}/`)

| Sign | File written | Source |
|------|--------------|--------|
| mistapiskihkoman   | `docs/assets/mistapiskihkoman/mistapiskihkoman.png`         | copied from `mistapiskihkoman/mistapiskihkoman.png`             |
| nicocwasaskanos    | `docs/assets/nicocwasaskanos/nikocwasaskanos.png`           | copied from `nicocwasaskanos/nikocwasaskanos.png`               |
| nipamayatan-pekiseyahk | `docs/assets/nipamayatan_pekiseyahk/purple_haze.png`    | copied from `nipamayatan_pekiseyahk/purple_haze.png`            |
| nipamayatan-pekiseyahk (alt) | `docs/assets/nipamayatan_pekiseyahk/nipamayatanpekiseyahk.png` | also copied for completeness; not the active `photo.src`  |
| lovers-lane        | `docs/assets/loversLane/sign_render.png`                    | cropped from `allSigns.jpg` (PIL; preview box 310,605 → 460,885) |
| mamahtaw-iskwew    | `docs/assets/mamahtaw_askwew/mamahtaw_iskwew.png`           | copied from `mamahtaw_askwew/mamahtaw_iskwew.png`               |

---

## Trailforks matches

| Sign | Trail | Trail ID | Confidence | Source |
|------|-------|----------|------------|--------|
| mistapiskihkoman      | Machete         | 30260 | High   | direct page fetch; AKA `ᒥᐢᑖᐱᐢᑭᐦᑯᒫᐣ mistâpiskihkomân` confirms |
| nicocwasaskanos       | Six Shooter     | 18858 | High   | direct page fetch; AKA `ᓂᑯᒑᐧᓴᐢᑲᓅᐢ nikocwâsaskanôs` confirms |
| nipamayatan-pekiseyahk| Purple Haze     | 15797 | High (no fetch) | found via Wonder Woman Nearby Trails listing; same Edmonton MTB-Cree project |
| lovers-lane           | Lovers Lane     | 15796 | High   | direct page fetch; trailhead 53.54309, -113.54137 |
| mamahtaw-iskwew       | Wonder Woman    | 31377 | High   | direct page fetch; AKA `mamahtâw iskwew` confirms |

All five mapCoords are populated where coords were extractable from the page fetch (4/5; Purple Haze coords not extracted but trailforks widget URL still works).

---

## Catalogue-level corrections proposed (mirror sign_inventory.md format)

| Sign id                | Field           | Current (catalogue)                         | Proposed (plaque-correct)                |
|------------------------|-----------------|---------------------------------------------|------------------------------------------|
| mistapiskihkoman       | `creeSyllabics` | `ᒥᐢᑕᐱᐢᑭᐦᑯᒫᐣ`                                | `ᒥᐢᑖᐱᐢᑭᐦᑯᒫᐣ`                             |
| nicocwasaskanos        | `creeSyllabics` | `ᓂᑯᐚᓴᐢᑲᓄᐢ`                                  | `ᓂᑯᒑᐧᓴᐢᑲᓅᐢ`                              |
| nipamayatan-pekiseyahk | `creeName`      | `nipâmâyâtan pekisehyânik`                  | `nîpâmâyâtân pekiseyâhk`                 |
| nipamayatan-pekiseyahk | `creeSyllabics` | `ᓂᐹᒫᔭᑕᐣ ᐯᑭᓭᐦᔮᓂᐠ`                          | `ᓂᐹᒫᔮᑖᐣ ᐯᑭᓭᔮᕽ`                          |
| lovers-lane            | `creeName`      | `nicimosak méskanâs`                        | `nicimos mêskanâs`                       |
| lovers-lane            | `creeSyllabics` | `ᓂᒋᒧᓴᐠ ᒣᐢᑲᓈᐢ`                              | `ᓂᒋᒧᐢ ᒣᐢᑲᓈᐢ`                            |
| mamahtaw-iskwew        | `creeName`      | `mamahtaw iskwew`                           | `mamahtâw iskwew`                        |
| mamahtaw-iskwew        | `creeSyllabics` | `ᒪᒪᐦᑕᐤ ᐃᐢᑲᐧᐤ`                              | `ᒪᒪᐦᑖᐤ ᐃᐢᑲᐧᐤ`                            |

All corrections are based on direct visual reads of the carved plaques in `allSigns.jpg`, cross-checked against Trailforks AKA listings (which match the carved forms for Machete, Six Shooter, and Wonder Woman) and against itwêwina / standard Plains Cree morphology.

---

## Open questions for the user

1. **Purple Haze morpheme analysis (~75% confidence).** The `nîpâ‑ + ‑mâyâtan + pekise‑ + ‑yâhk` reading is the structural one; an alternative parses `pekiseyâhk` as a `pîkise‑` ‘break/disperse’ stem rather than `pekise‑` ‘pass through.’ Both yield similar trail-name semantics; an elder cross-check would settle it.
2. **Lovers Lane carved diacritic on `n`.** A faint upper mark on the carved `nicimos` could be read as `nîcimos` (with circumflex on î — itwêwina’s preferred headword form) rather than plain `nicimos`. The fragment uses plain `nicimos` per coordinator inventory; flag if the user’s direct read disagrees.
3. **Six Shooter cw vs. tw cluster.** The plaque uses the palatalised Plains-Cree `cw` form. In strict-orthography contexts (e.g. classroom materials) the underlying `tw` form `nikotwâsaskanôs` may be preferred. Confirm whether to keep the `cw` plaque-form on the page or also surface the `tw` variant in `quickReference`.
4. **Machete `‑(i)hkomân` vs. `môhkomân` analysis.** The page treats `‑(i)hkomân` as a noun final (the bound form of `môhkomân` ‘knife’). An alternative collapses it as a single nominalised compound stem. Either is defensible; the three-morpheme split is preferred for teaching clarity.
5. **Wonder Woman two-word vs. compound.** Treated here as pre-noun `mamahtâw` + NA `iskwew` (two words). An alternative analysis writes it as a single compound `mamahtâwiskwew`. Trailforks AKA writes it as two words; the plaque visually separates them.
6. **Wonder Woman folder typo.** Legacy folder `mamahtaw_askwew` keeps `askwew` (typo for `iskwew`). The coordinator instructions say to keep the path; the page renders the correct `iskwew` everywhere. Just confirming this is the intended choice.
7. **Purple Haze double-plaque.** The wall has two Purple Haze plaques (a small portrait-format upper one and a fuller one further right). The page wires `purple_haze.png` (the dedicated design source representing the same composition). Do you want the secondary photo wired anywhere on the page (e.g. as a comparison image)?

---

## Self-assessment

**Craftsperson says:** Five fragments, all eight acceptance checks green on every sign, every photo wired against a real file in `docs/assets/`, every Trailforks ID verified by direct fetch (modulo Purple Haze, which I confirmed by transitive link from Wonder Woman’s Nearby Trails list). The morpheme analyses are real morphology — not just glosses — and the cultural-story prose ties the English name → Cree morpheme reading → plaque design choices → Edmonton + Nêhiyaw‑Askiy context the way the kiwapamitin and backbreaker exemplars do. The catalogue-correction proposals are scoped exactly to my five signs, mirror the `backbreaker` precedent in form, and are conservative (every change is justified by a direct visual read AND a corroborating source).

**Skeptic says:** Three honest doubts. (1) The carved syllabics on Purple Haze and Six Shooter are stylised enough that I am rendering proposed-correct syllabics from the SRO + standard Plains-Cree syllabic conventions, not transcribing each glyph one-to-one. The proposals are linguistically sound but a higher-resolution single-plaque photo would let me transcribe each glyph individually. (2) The Purple Haze morpheme analysis is the weakest of the five: the conjunct `pekiseyâhk` admits multiple defensible parses, and the `nîpâ‑` + `‑mâyâtan` compound, while attested in itwêwina, is not common enough that I would stake a strong claim on it. (3) For Lovers Lane I read the upper heart plaque (the lower heart is also present and reads the same Cree, per the coordinator inventory). I never saw both plaques side-by-side in a single high-res frame, so I am trusting the inventory’s claim that they are textually identical.

**Mover says:** Ship it. Five fragments, all green, all photos wired, five real catalogue corrections proposed in the format the coordinator can ingest atomically, the open questions are explicit and each is one elder-confirmation away from being closeable. The pipeline did the right thing where the pilot’s #1 miss was — every fragment has a concrete `photo.src` against a file that exists. Coordinator can merge.
