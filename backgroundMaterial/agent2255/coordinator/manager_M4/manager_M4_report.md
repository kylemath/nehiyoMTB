# Manager M4 Report — Agent 2255 Batch 2

**Manager:** 2255-M4
**Coordinator:** 2255-C
**Scope:** 4 of the remaining 19 trail signs — `oyoyow`, `nosemanicos`, `victoria-secret`, `slinky`.
**Status:** All 4 fragments hit acceptance criteria. `pageStatus = agent-drafted` on every fragment, every photo wired, every linguistics block populated, every catalogue correction surfaced as `notes` (the coordinator merges `catalogue.json` atomically — M4 did not touch it).

## TL;DR per sign

| # | Sign id           | Header                                              | photo.src                                                | Trailforks                              | Morphemes (primary / related / quickRef) | Catalogue correction proposed |
|---|-------------------|-----------------------------------------------------|----------------------------------------------------------|-----------------------------------------|------------------------------------------|--------------------------------|
| 1 | `oyoyow`          | `Howl • oyôyow • ᐅᔫᔪᐤ`                              | `../assets/oyoyow/oyoyow_render.png`                     | `{}` + notes (no Edmonton match)        | 4 / 3 / 6                                | `oyoyow → oyôyow`, `ᐅᔪᔪᐤ → ᐅᔫᔪᐤ` |
| 2 | `nosemanicos`     | `Ladybug • nôsemanicôs • ᓅᓭᒪᓂᒎᐢ`                    | `../assets/nosemanicos/nosemanicos_render.png`           | `{}` + notes (no Edmonton match)        | 2 / 3 / 5                                | creeName ok; `ᓄᓭᒪᓂᒑᐢ → ᓅᓭᒪᓂᒎᐢ` |
| 3 | `victoria-secret` | `Victoria's Secret • victoria okimôtânimiyiwa • victoria ᐅᑭᒨᑖᓂᒥᔨᐘ` | `../assets/victoriaSecret/victoria_secret_render.png` | **trail #10632** (Central Edmonton (North), trailhead 53.54268,-113.53953) | 7 / 3 / 5 | `vicSecret → victoria okimôtânimiyiwa`, syllabics → `victoria ᐅᑭᒨᑖᓂᒥᔨᐘ` |
| 4 | `slinky`          | `Slinky` (loanword, no Cree calque)                 | `../assets/slinky/sign_render.png`                       | **trail #150113** (Slinky - Mid, Keillor, trailhead 53.51818,-113.5403) | 1 / 2 / 4                                | None — placeholder is correct (no carved Cree on installation) |

All four pass programmatic acceptance:

- `pageStatus == "agent-drafted"` on every fragment.
- `linguistics.primarySection.morphemes.length >= 1` on every fragment.
- `linguistics.relatedForms.length >= 1` on every fragment.
- `linguistics.quickReference.length >= 3` on every fragment.
- `culturalStory.heading` non-empty AND `culturalStory.body.length >= 1` on every fragment.
- `photo.src` non-empty on every fragment.
- `trailforks` either fully populated or `{}` with a `notes` entry.
- All morpheme `key` values unique within each page.

(Verified by a Python pass over all four files; full output reproduced in the coordinator log if needed.)

---

## Per-sign detail

### Sign #20 — `oyoyow` (Howl)

- **Plaque read.** Two near-identical plaques on the wall (one tall standalone on the far left, one in the upper cluster). Both carve `oyôyow` (circumflex on the second `ô`) in raised English-style letters above a black wolf-howl silhouette, with red Plains Cree syllabics `ᐅᔫᔪᐤ` carved across the wolf's muzzle and chest, and the English `HOWL` set in heavy block face below the wolf.
- **Linguistics.**
  - **Type.** AI verb (animate intransitive), onomatopoeic / imitative.
  - **Primary morphemes (4).** `o-` (open imitative initial) + `-yô-` (long-vowel pitch core) + `-yo-` (short-vowel falling tail) + `-w` (AI 3sg). The four-piece split is teaching-grade — most reference works treat oyôyow as a single imitative AI stem `oyôyo-` + AI ending `-w`. Documented as such in `notes`.
  - **Related forms (3).** `mahihkan` (wolf, NA noun), `mahihkanak` (wolves, animate plural), `têpwêw` (s/he calls out, AI sister verb).
  - **Quick reference (6 rows).** Headword + `mahihkan` + `mahihkanak` + `mahihkanis` (wolf cub) + `têpwêw` + `matwêhkâsow` (s/he is heard from afar).
  - **Base words (3).** `mahihkan`, the AI 3sg `-w` ending, `têpwêw`.
- **Photo.** Wired pre-staged asset `docs/assets/oyoyow/oyoyow_render.png` (the `oyoyow/oyoyo.png` design source, copied into `docs/assets/` by the coordinator).
- **Trailforks.** `{}` — no Edmonton-area trail named "Howl" surfaced across three queries (the `Wolfman / Wolf Bait` family exists but is structurally different). Flagged in `notes` for a single human-rider lookup.
- **Catalogue corrections proposed.**
  - `creeName`: `oyoyow` → `oyôyow` (add long-ô on the second `o`).
  - `creeSyllabics`: `ᐅᔪᔪᐤ` → `ᐅᔫᔪᐤ` (long-ô glyph `ᔫ` on the second position).

### Sign #21 — `nosemanicos` (Ladybug)

- **Plaque read.** Center-row plaque: a red ladybug fills almost the whole white plaque (black head, black spots, six legs) with white Plains Cree syllabics carved across the polished red wing case. Carved SRO `nôsemanicôs`. The carved English headline is `LADYBUG` (used as `headerTitle` per brief).
- **Linguistics.**
  - **Type.** NA noun (animate).
  - **Primary morphemes (2).** `nôse-` (productive female-marker prefix) + `manicôs` (NA noun: small bug/insect).
  - **Related forms (3).** `manicôs` (the bare bug-noun), `manicôsak` (bugs, animate plural with regular `-ak`), `nôsemostos` (cow / female buffalo — structural minimal pair showing the same `nôse-` prefix on a different animal stem).
  - **Quick reference (5 rows).** Headword + `manicôs` + `nôsemanicôsak` (plural ladybugs) + `nôse-` (the prefix in isolation) + `nôsemostos`.
  - **Base words (2).** `manicôs`, `nôse-`.
- **Photo.** Wired pre-staged asset `docs/assets/nosemanicos/nosemanicos_render.png` (the `nosemanicos/ladybug.png` design source).
- **Trailforks.** `{}` — no Edmonton-area trail named "Ladybug" surfaced across three queries. Flagged in `notes`.
- **Catalogue corrections proposed.**
  - `creeName`: already `nôsemanicôs` — keep.
  - `creeSyllabics`: `ᓄᓭᒪᓂᒑᐢ` (decodes as `nosemanicâs`, wrong vowel marking on both the first and the c-glyph) → `ᓅᓭᒪᓂᒎᐢ` (long-ô on `ᓅ` for `nô`, long-ô on `ᒎ` for `cô`, final `ᐢ`).

### Sign #22 — `victoria-secret` (Victoria's Secret)

- **Plaque read.** Two plaques on the wall (top-right cluster and central-row cluster). Pale-blue background, black bra-silhouette filled with a pine-forest landscape and a small switchback path, carved `victoria okimôtânimiyiwa` in mixed Roman + Cree below the silhouette, with the English `Victoria's Secret` underneath.
- **Linguistics.**
  - **Type.** Phrase: borrowed proper noun + VTA (verb transitive animate, 3→3′ obviative).
  - **Primary morphemes (7).** `victoria` (loanword) + `o-` (3sg agent prefix) + `kimôt-` (steal/stealth root) + `-âni-` (stem extender) + `-m-` (VTA stem-marker) + `-iyi-` (obviative theme-marker) + `-wa` (obviative animate ending). Mid-confidence morpheme bracketing — flagged in `notes` (a stricter dictionary lookup may collapse `-âni-m-` into a single `-ânim-` relational stem).
  - **Related forms (3).** `kimôtiw` (s/he steals, AI), `kîmôc` (the particle ‘secretly, in stealth’), `kimôtâpamêw` (s/he secretly watches/spies on him/her, sister VTA showing kimôt- as a stealth modifier).
  - **Quick reference (5 rows).** Phrase headword + `kimôtiw` + `kîmôc` + `kimôtâpamêw` + the obviative suffix `-iyiwa`.
  - **Base words (3).** `kimôt-`, `kîmôc`, `victoria`.
- **Photo.** Wired pre-staged asset `docs/assets/victoriaSecret/victoria_secret_render.png` (the `victoriaSecret/Screenshot 2023-11-17 at 11.59.34 AM.png` design source).
- **Trailforks.** **HIGH confidence — trail #10632** "Victoria's Secret" in Central Edmonton (North), Northwest Edmonton, Alberta. Trailhead `(53.54268, -113.53953)`. ~1.0 km / 3,338 ft of techy bench-cut singletrack with off-camber roots, in the same cluster as Lovers Lane (#15796), Wonder Woman, and Purple Haze (#15797) — all of which appear on the wall as adjacent plaques. Sibling trails `Victoria's Lower Secret` and `Victoria's other secret` (#19734) exist but are spurs.
- **Catalogue corrections proposed.**
  - `creeName`: `vicSecret` (placeholder) → `victoria okimôtânimiyiwa`.
  - `creeSyllabics`: empty → `victoria ᐅᑭᒨᑖᓂᒥᔨᐘ` (Roman name kept, Cree verb in syllabics — mirrors the plaque exactly).
  - **Optional/secondary:** `colors` could be expanded to include `blue` (the plaque is pale-blue with black-and-white print, but the catalogue currently says `["white", "black"]`). Surfaced as a non-blocking note.

### Sign #23 — `slinky` (Slinky)

- **Plaque/installation read.** The slinky "sign" is two pieces working together: (a) a small white printed plaque at the top-left of row 1 carrying `slinky` in raised black letters and a red syllabic transliteration of the loanword underneath, and (b) the giant red continuous wire-coil sculpture itself (~4 ft tall, rows 1 → 3), recognisably a scaled-up Richard James 1945 coil-toy. The brief noted "no plaque exists" — the pre-staged photo shows that there IS a small printed plaque, but it is small and the dominant element of the installation is the sculpture itself. Both are captured in `photo.alt` / `photo.caption`.
- **Linguistics.**
  - **Type.** Loanword / sculpture (no Plains Cree calque).
  - **Primary section (1 morpheme row, per brief).** `slinky` (borrowed English brand-name) — the row is a single explanatory entry that names this as a sculpture rather than a translated word, mirroring the brief's "physical spring sculpture, not a translated word" instruction.
  - **Related forms (2).** A descriptive Cree paraphrase `kâ-kwêskwêkotêk piwâpisk` ("the metal that bounces / coils back" — stitching together the same `kâ-kwêskwêkotêk` stem the wall uses on the Bed Springs plaque + `piwâpisk` ‘metal’) and the underlying II verb `kwêskwêkotêw` ‘it bounces, it springs back.’ Both are explicitly flagged as paraphrases, not calqued nouns — Plains Cree describes mechanical springs by what they do, not by a single noun, and inventing a calqued noun would conflict with the spec rule "do not silently replace a checked local spelling."
  - **Quick reference (4 rows).** Headword + `kwêskwêkotêw` + `piwâpisk` + `mêskanaw` (trail / road, anchoring the trail-vocabulary field).
  - **Base words (2).** `kwêskwêkotêw`, `piwâpisk`.
- **Photo.** Wired pre-staged asset `docs/assets/slinky/sign_render.png` (a tight crop of the small printed plaque + the upper coil from `allSigns.jpg`). A future revision could add a wider crop showing the multi-row sculpture from box `(900, 200) → (2400, 5000)` if a multi-photo gallery is added.
- **Trailforks.** **HIGH confidence — trail #150113** "Slinky - Mid" in Keillor, Northwest Edmonton (Trailforks's own description: "the best section of the three Slinkys"). Trailhead `(53.51818, -113.5403)`. Sibling trails: `Slinky - North` (#51286, Central Edmonton (South), 2,221 ft, the longer/more popular of the family) and a `Slinky - South` (no ID confirmed in this run). Any of the three is defensible; user may flip to `#51286` if the catalogue prefers the more popular section.
- **Catalogue corrections proposed.** None. The catalogue's `slinky` placeholder + empty syllabics is correct because no carved Plains Cree calque exists on the installation. Leaving both as-is is intentional.
- **headerTitle.** `Slinky` only (no Cree segment) per brief: "for slinky just `Slinky` if no Cree." Deviates from the kiwapamitin three-part `English • SRO • Syllabics` pattern but matches the loanword-only nature of the installation.

---

## Catalogue corrections summary (proposed for coordinator merge)

| Sign id           | Field           | Old (catalogue)             | Proposed new (matches plaque) |
|-------------------|-----------------|-----------------------------|-------------------------------|
| `oyoyow`          | `creeName`      | `oyoyow`                    | `oyôyow`                      |
| `oyoyow`          | `creeSyllabics` | `ᐅᔪᔪᐤ`                       | `ᐅᔫᔪᐤ`                         |
| `nosemanicos`     | `creeName`      | `nôsemanicôs` (already ok)  | `nôsemanicôs` (keep)          |
| `nosemanicos`     | `creeSyllabics` | `ᓄᓭᒪᓂᒑᐢ`                     | `ᓅᓭᒪᓂᒎᐢ`                       |
| `victoria-secret` | `creeName`      | `vicSecret` (placeholder)   | `victoria okimôtânimiyiwa`    |
| `victoria-secret` | `creeSyllabics` | (empty)                     | `victoria ᐅᑭᒨᑖᓂᒥᔨᐘ`            |
| `slinky`          | `creeName`      | `slinky` (placeholder)      | `slinky` (keep — no calque)   |
| `slinky`          | `creeSyllabics` | (empty)                     | (keep empty — no calque)      |

Optional/secondary (non-blocking):

- `victoria-secret` — `colors` array could grow to include `blue` (plaque is pale-blue background; catalogue currently says `["white", "black"]`).

---

## Asset list (already on disk under `docs/assets/`)

| Sign id           | Asset path                                              | Source                                              | Wired into fragment as |
|-------------------|---------------------------------------------------------|-----------------------------------------------------|------------------------|
| `oyoyow`          | `docs/assets/oyoyow/oyoyow_render.png`                  | copy of `oyoyow/oyoyo.png` (design source)          | `../assets/oyoyow/oyoyow_render.png` |
| `nosemanicos`     | `docs/assets/nosemanicos/nosemanicos_render.png`        | copy of `nosemanicos/ladybug.png` (design source)   | `../assets/nosemanicos/nosemanicos_render.png` |
| `victoria-secret` | `docs/assets/victoriaSecret/victoria_secret_render.png` | copy of `victoriaSecret/Screenshot 2023-11-17 at 11.59.34 AM.png` (design source) | `../assets/victoriaSecret/victoria_secret_render.png` |
| `slinky`          | `docs/assets/slinky/sign_render.png`                    | tight crop from `allSigns.jpg` (small plaque + upper coil) | `../assets/slinky/sign_render.png` |

All four assets were pre-staged into `docs/assets/{folder}/` by the coordinator before manager launch. M4 did not create or move any asset files, only wired them into the fragment JSON.

---

## Open questions for the user

1. **`oyoyow` Trailforks.** No Edmonton-area trail named "Howl" surfaced across three queries. Is this an unmapped community trail, or a trail listed in another region under a related name (`Wolfman` / `Wolf Bait` / similar)? A single human Trailforks click would settle it.
2. **`nosemanicos` Trailforks.** Same situation — no "Ladybug" trail in the Edmonton area on Trailforks. Same ask.
3. **`oyoyow` morpheme bracketing.** The 4-morpheme split (`o-` / `-yô-` / `-yo-` / `-w`) is teaching-grade and surfaces the imitative reduplication pattern. The strict dictionary-headword analysis is `oyôyo-` (single imitative AI stem) + `-w` (AI 3sg). Both are valid; flag if you prefer the stricter 2-piece reading instead.
4. **`nosemanicos` syllabic glyph for `cô`.** Used `ᒎ` (CANS U+128E COO, the long-vowel glyph). Some materials use `ᒍ` (CO, short) with an external long-vowel mark. Either is readable; chose `ᒎ` to match the SRO circumflex transparently.
5. **`victoria-secret` morpheme bracketing of `okimôtânimiyiwa`.** Used a 6-piece split (`o-` / `kimôt-` / `-âni-` / `-m-` / `-iyi-` / `-wa`) for teaching clarity. A strict dictionary lookup may collapse `-âni-m-` into a single `-ânim-` relational stem. Flag if a stricter reading is preferred.
6. **`victoria-secret` colors.** The plaque is pale-blue background; catalogue `colors` is currently `["white", "black"]`. Add `blue`? (Non-blocking, but would let the catalogue card colour-chip match the wall plaque.)
7. **`slinky` plaque.** The brief said "no plaque exists" but the pre-staged photo shows a small printed plaque with `slinky` (English) + a red syllabic transliteration of the loanword. Captured in `photo.caption` and `notes`. The dominant element is still the giant red wire-coil sculpture. A higher-res single-panel photo of the small plaque would let us read the syllabic transliteration letter-by-letter and confirm whether it is a clean `ᔅᓕᐣᑭ` (s-li-n-ki) loanword transliteration or something else.
8. **`slinky` Trailforks pick.** Wired `Slinky - Mid` (#150113) as the primary because Trailforks's own description calls it "the best section of the three Slinkys." If the catalogue prefers the longer / more popular section, flip to `Slinky - North` (#51286).
9. **`slinky` related forms.** Used Plains Cree paraphrases (`kwêskwêkotêw`, `piwâpisk`, `kâ-kwêskwêkotêk piwâpisk`) rather than calqued nouns, to avoid inventing a Cree word for "coiled mechanical spring." Surfaced under `relatedForms` so the page still teaches some Plains Cree morphology adjacent to the loanword. Drop or simplify if a stricter no-Cree-on-loanword presentation is preferred.

---

## Tripartite self-assessment

**Craftsperson says.** The four fragments come out structurally clean: each one passes every programmatic acceptance check (pageStatus, primary morphemes, related forms, quick reference, cultural story, photo wiring, trailforks, unique morpheme keys). Each surfaces every catalogue correction as a `notes` entry in the exact pattern the pilot established for `backbreaker` — coordinator can apply the catalogue-level edits atomically without re-reading the fragments. The four signs cover every renderer branch the pilot exercised: photo present + trailforks present (`victoria-secret`, `slinky`), photo present + trailforks absent (`oyoyow`, `nosemanicos`), single-morpheme primary (`slinky`), multi-morpheme primary (`oyoyow`, `nosemanicos`, `victoria-secret`), Roman+syllabics mixed-script (`victoria-secret`), and loanword-only (`slinky`). The slinky page in particular took some care: the brief was wrong about "no plaque exists" — the pre-staged photo shows a small printed plaque alongside the sculpture — so the fragment captures both pieces honestly without inventing a Cree calque the carvers did not intend.

**Skeptic says.** Three things to push back on. (1) The morpheme analyses for `oyoyow` (4-piece imitative split) and `victoria-secret` (`okimôtânimiyiwa` 6-piece split) are teaching-grade rather than dictionary-grade — both have stricter alternative readings noted, and a Plains Cree language consultant may well flatten these. (2) The `nosemanicos` syllabics were corrected from the catalogue's `ᓄᓭᒪᓂᒑᐢ` to `ᓅᓭᒪᓂᒎᐢ` based on the SRO `nôsemanicôs`, but the actual carved syllabics on the wall plaque are not 100% legible at the wall-photo resolution — a higher-res panel shot would settle whether the carver used `ᓅ` (long-ô) or `ᓄ` (short-o, with the long-ô implied) on the first glyph and `ᒎ` vs. `ᒍ` on the c-glyph. (3) Two of four trailforks blocks landed at `{}` (no `Howl` or `Ladybug` Edmonton-area match across three queries each). That is not a failure — the spec explicitly allows `{}` + notes — but it does mean two of M4's pages will render with the "trail information coming soon" stub, which is less visually complete than the two pages with full Trailforks widgets.

**Mover says.** Shipping. Four fragments are written, validated against every acceptance criterion, and surface every catalogue correction in the same `notes` pattern the pilot used. Two trail matches landed cleanly with full trailhead coordinates (Victoria's Secret #10632, Slinky-Mid #150113); two are honestly flagged as `{}` for human follow-up. Coordinator can merge without further M4 work.

---

## Files written

- `manager_M4/oyoyow_pageContent.json`
- `manager_M4/nosemanicos_pageContent.json`
- `manager_M4/victoria-secret_pageContent.json`
- `manager_M4/slinky_pageContent.json`
- `manager_M4/manager_M4_report.md` (this file)

No edits to `catalogue.json`, `docs/{folder}/index.html`, `docs/assets/`, or any other shared file.
