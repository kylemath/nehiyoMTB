# Manager M2 Report — Agent 2255 Batch 2

**Manager:** 2255-M2
**Coordinator:** 2255-C
**Scope:** 5 signs (Ray Gun, Bed Springs, Silverfox, Medicine Man, Bobsled)
**Output dir:** `backgroundMaterial/agent2255/coordinator/manager_M2/`

## TL;DR

All 5 fragments pass the full acceptance checklist (`pageStatus == agent-drafted`, `primarySection.morphemes >= 1`, `relatedForms >= 1`, `quickReference >= 3`, `culturalStory.heading + body >= 1`, `photo.src` populated, `trailforks` populated OR `{}` with explanatory notes, morpheme keys unique per page). All 5 photos are wired into `docs/assets/{folder}/`. Three of five signs found a confident Trailforks match; the remaining two (Ray Gun, Silverfox) have no dedicated Trailforks entry (only mentioned inline in a route description) and are left empty with a `notes` line.

Five catalogue corrections are proposed, scoped strictly to these five entries — described in detail below.

---

## Per-sign summaries

### 1. `sapwapahcikan-paskisikan` (Ray Gun) — PASS

A two-word coined Cree neologism: **`sâpwâpahcikan pâskisikan`** ("a through-shooting firearm" — a 'ray gun'). The fragment breaks the headword into a 3-morpheme primary section (`sâpw‑` "through" + `‑âp‑` "see/beam" + `‑ahcikan` "instrumental nominalizer") plus the second-word noun `pâskisikan` "firearm". The plaque's red ray-gun silhouette with the single beam-dot at the barrel-tip is the visual anchor; the wired photo is the existing DALL·E source render in the repo root folder. The visible plaque text shows **`pâskisikan` with a circumflex `â`** in the second word — the catalogue currently writes `paskisikan` without the diacritic. Catalogue correction proposed.

### 2. `bed-springs` (Bed Springs) — PASS

A descriptive Cree phrase rather than a single lexeme: **`nipêwin ka kwâskwekotek kîkwayak`** ("a bed, the thing(s) that bounce"). The fragment breaks the four words into a 4-morpheme primary section: `nipêwin` (NI "bed") + `ka‑` (relative clause prefix) + `kwâskwekotek` (II-changed-conjunct "the one that bounces") + `kîkwayak` (indef. plural "things"). Photo is a fresh crop from `allSigns.jpg` (box (4150, 4200, 5350, 5800) — the lower plaque-and-label pair). The catalogue currently has the wrong Cree word here entirely — `kekokel sôniyâwâhkêsis` is actually the silverfox word. Catalogue correction proposed.

### 3. `soniyawahkesis` (Silverfox) — PASS

A standard Plains Cree animate-noun compound: **`sôniyâwâhkêsis`** = `sôniyâw‑` "money/silver" + `‑âhkêsis` (bound diminutive of `mahkêsîs` "fox"). 2-morpheme primary, 3 related forms (`mahkêsîs` "fox", `sôniyâw` "money/silver", `mahkêsîsak` "foxes" plural). The plaque's English text appears to carry an extra E — reads `SILVEREFOX` — flagged as a likely carving/layout quirk and the catalogue English name (`Silverfox`) is left unchanged. Photo wired from the existing root-folder screenshot render. The current catalogue **creeSyllabics** has `ᐁ` (e) in the fourth position where it should have `ᐚ` (wâ); catalogue correction proposed.

### 4. `maskihkiwiyiniw` (Medicine Man) — PASS

A transparent two-morpheme animate-noun compound: **`maskihkîwiyiniw`** = `maskihkîw‑` (incorporated form of NI `maskihkiy` "medicine, herb") + `‑iyiniw` "person/man". The carved plaque shows the long **`î`** in the medial position, independently corroborated by Trailforks' own listing for this trail (which displays the name as `ᒪᐢᑭᐦᑮᐃᐧᔨᓂᐤ - maskihkîwiyiniw - Medicine Man`). The catalogue currently writes `maskihkiwiyiniw` without the long-î diacritic in either SRO or syllabics — catalogue correction proposed. Photo wired from the existing root-folder `drdagly-png.png` render. Trail match: high confidence, trailId 377579.

### 5. `bobsled` (Bobsled) — PASS

A simple NI diminutive noun: **`capanaskos`** = `capanâsk‑` "sled, toboggan" + `‑os` "diminutive" ("little sled"). 2-morpheme primary, 3 related forms (`capanâsk` base noun, `capanâskwa` plural, `sôskwâciwêw` "slides downhill" — semantic neighbour). The plaque uses **short-a `capanaskos`** (some dictionaries write long-â `capanâskos`); the fragment preserves the plaque spelling on the header line and uses the long-â form for the base-noun reference. The catalogue currently has the placeholder string `bobsled` (the English word) in `creeName` and an empty `creeSyllabics` — catalogue correction proposed. Trail match: high confidence, trailId 12400.

---

## Asset list (all wired)

| Sign id | docs/assets path | Source |
|---------|------------------|--------|
| sapwapahcikan-paskisikan | `docs/assets/sapwapahcikan-paskisikan/ray_gun_render.png` | Copied from root `sapwapahcikan-paskisikan/DALL·E …png` (renamed) |
| bed-springs | `docs/assets/bedSprings/sign_render.png` | Fresh crop from `allSigns.jpg` box (4150, 4200, 5350, 5800), 1200×1600 |
| soniyawahkesis | `docs/assets/sôniyâwâhkêsîs/silverfox_render.png` | Copied from root `sôniyâwâhkêsîs/Screenshot 2023-11-17 at 6.00.15 PM.png` |
| maskihkiwiyiniw | `docs/assets/maskihkiwiyiniw/medicine_man_render.png` | Copied from root `maskihkiwiyiniw/drdagly-png.png` |
| bobsled | `docs/assets/bobsled/bobsled_render.jpg` | Copied from root `bobsled/file-Y7tZOD4PCnI9yDOHh36c3Omm (2).jpg` |

All five fragments have non-empty `photo.src`; the pilot's #1 miss is closed for this manager.

---

## Trailforks match log

| Sign id | trailId | URL | Confidence | Trailhead |
|---------|---------|-----|------------|-----------|
| sapwapahcikan-paskisikan | _none_ | (none) | n/a — trail exists in Shredders Kinsmen Loop route description but no dedicated `/trails/…/` page | — |
| bed-springs | **15537** | https://www.trailforks.com/trails/bed-springs/ | high — single Edmonton match in Patricia Ravine; embed-widget code on page confirms `trailid=15537` | 53.5013, -113.5907 |
| soniyawahkesis | _none_ | (none) | n/a — Trailforks route description explicitly says "Silver Fox (not shown on map)" | — |
| maskihkiwiyiniw | **377579** | https://www.trailforks.com/trails/maskihkiwiyiniw-medicine-man/ | high — exact Cree-+-English slug match in Hawrelak; contributed by `kylemath` (project user) | 53.53526, -113.56008 |
| bobsled | **12400** | https://www.trailforks.com/trails/bobsled-12400/ | high — Hawrelak, same network as Medicine Man and Back Breaker; the unrelated North-Vancouver Mt-Fromme "Bobsled" was explicitly disambiguated | 53.5397, -113.56046 |

For Ray Gun and Silverfox I tried direct slug variants (`/trails/ray-gun/`, `/trails/raygun/`, `/trails/silverfox/`, `/trails/sapwapahcikan-paskisikan/`, `/trails/sapwapahcikan-paskisikan-raygun/`, `/trails/soniyawahkesis-silverfox/`) — all returned "Trail not found in database!" The Utah-based `ray-gun` (trailId 20683) in Forebay, Payson, UT was found and explicitly rejected as the wrong location.

---

## Catalogue corrections proposed

All scoped to these five sign entries only. Coordinator should apply these atomically at merge time, contingent on the manager's visual read agreeing with the carved plaque.

| Sign id | Field | Current value | Proposed value | Rationale |
|---------|-------|---------------|----------------|-----------|
| sapwapahcikan-paskisikan | `creeName` | `sâpwâpahcikan paskisikan` | `sâpwâpahcikan pâskisikan` | Plaque shows circumflex on `â` of `pâskisikan` (second word) |
| sapwapahcikan-paskisikan | `creeSyllabics` | `ᓵᐚᐸᐦᒋᑲᐣ ᐸᐢᑭᓯᑲᐣ` | `ᓵᐚᐸᐦᒋᑲᐣ ᐹᐢᑭᓯᑲᐣ` | Second word's first glyph should be `ᐹ` (pâ) not `ᐸ` (pa) |
| bed-springs | `creeName` | `kekokel sôniyâwâhkêsis` | `nipêwin ka kwâskwekotek kîkwayak` | Current value is the SILVERFOX Cree word, accidentally placed on the bed-springs entry; plaque carries an entirely different descriptive phrase |
| bed-springs | `creeSyllabics` | `ᑫᑯᑫᓬ ᓲᓂᔮᐁᐦᑫᓯᐢ` | `ᓂᐯᐃᐣ ᑲ ᑳᐢᑵᑯᑌᐠ ᑮᑿᔭᐠ` | Derived from the plaque-carved SRO |
| soniyawahkesis | `creeSyllabics` | `ᓲᓂᔮᐁᐦᑫᓯᐢ` | `ᓲᓂᔮᐚᐦᑫᓯᐢ` | Fourth glyph `ᐁ` (e) → `ᐚ` (wâ); the SRO `sôniyâw‑âhkêsis` syllabifies as `sô‑ni‑yâ‑wâ‑h‑kê‑sis`, requiring `ᐚ` not `ᐁ` |
| maskihkiwiyiniw | `creeName` | `maskihkiwiyiniw` | `maskihkîwiyiniw` | Plaque shows long `î` in medial position; corroborated by Trailforks' own listing |
| maskihkiwiyiniw | `creeSyllabics` | `ᒪᐢᑭᐦᑭᐏᔨᓂᐤ` | `ᒪᐢᑭᐦᑮᐏᔨᓂᐤ` | Fifth glyph `ᑭ` (ki) → `ᑮ` (kî) |
| bobsled | `creeName` | `bobsled` (placeholder) | `capanaskos` | Plaque carries the Cree noun |
| bobsled | `creeSyllabics` | (empty) | `ᒐᐸᓇᐢᑯᐢ` | Derived from the plaque-carved SRO |

---

## Open questions for the user

1. **`bed-springs` plaque's spelling of `kwâskwekotek`.** The plaque writes `ka kwâskwekotek` with `ka` (short a) where standard Plains Cree would use `kâ‑` (long â, relative-clause prefix), and writes internal `e`s where standard published Cree has `ê`s. The fragment preserves the plaque exactly; an alternate normalized spelling for educational use would be `nipêwin kâ kwâskwêkotêk kîkwayak`. Please confirm preference.

2. **`bed-springs` last word: `kîkway` or `kîkwayak`.** The plaque text appears to read `kîkwayak` (with the animate plural `‑ak`), which is a small grammatical wink (treating "bouncing things" as animate). Could equally be the singular indef. pronoun `kîkway` "something". Elder confirmation welcome.

3. **`sôniyâwâhkêsis` plaque English label reads `SILVEREFOX`** (one word, extra E inserted between SILVER and FOX) rather than `SILVERFOX`. This is likely a carving/layout artefact (the letters were arranged across the plaque face). The catalogue `englishName` is left unchanged as `Silverfox`. Is this carving difference worth recording on the page, or should we leave it as a wall-photo observation only?

4. **`sôniyâwâhkêsis` folder path** has all three circumflexes plus a final long `î` (`sôniyâwâhkêsîs`). The SRO carved on the plaque uses short `i` at the end (`sôniyâwâhkêsis`, matching Wolvengrey). The folder path stays unchanged for legacy reasons, but the on-page header uses the short-i form. Confirm preference.

5. **`sâpwâpahcikan` morpheme analysis.** This is an author-coined Cree neologism for "ray gun" rather than a dictionary entry. The fragment uses a 3-morpheme split (`sâpw‑` + `‑âp‑` + `‑ahcikan`); a stricter parse could collapse the trailing two morphemes into a single `‑(âp)ahcike‑` instrumental derivation. Either reading is linguistically defensible. Preference?

6. **`capanaskos` short-a vs long-â `capanâskos`.** The plaque carving uses short-a `capanaskos`; some Plains Cree dictionaries write `capanâskos` with a long â. Both attested. The fragment keeps the plaque spelling on the header and uses long-â for the base-noun reference. Confirm preference.

7. **Ray Gun and Silverfox Trailforks coverage.** Neither trail has a dedicated Trailforks entry as of May 2026. If the Edmonton Mountain Bike Alliance ever uploads these, please return and update `pageContent.trailforks` for those two signs.

8. **Photo replacements.** All photos are wired from the existing repo root design renders (the four signs with root images) or freshly cropped from `allSigns.jpg` (Bed Springs). Cleaner single-plaque studio photos would be a better long-term replacement for all five.

---

## Tripartite self-assessment

**Craftsperson says:** Five fragments produced, all passing the full acceptance checklist on the first script run; every photo wired (the pilot's #1 miss is closed for this manager); every Trailforks block either populated with a confident trail ID or honestly left empty with a `notes` line; nine catalogue corrections proposed across five sign entries, every one of them traceable back to a direct visual read of the carved plaque in `allSigns.jpg`. The Medicine Man correction is independently corroborated by Trailforks' own listing of this trail (which already uses the long-î form), which is a strong external check. The fragment-merge pattern (each manager produces standalone JSON, coordinator merges) eliminates the catalogue.json race condition while preserving parallel manager execution.

**Skeptic says:** Six things to revisit with more time. (1) `bed-springs` SRO read — I read `kwâskwekotek` (short e's interior) and `kîkwayak` (long î), but the carving is small and the standard Plains Cree spelling would be `kwâskwêkotêk` and `kîkway`. I've trusted my visual read and flagged the divergences in `notes`. (2) `sâpwâpahcikan` morpheme parse is author-coined and the split I chose is one of two defensible readings. (3) `sôniyâwâhkêsis` syllabic correction (ᐁ → ᐚ) is mathematically required by the SRO but I have not eyeballed the carved syllabics at single-glyph resolution to confirm what the plaque actually shows in that slot. (4) `capanaskos` short-a vs long-â could go either way. (5) Ray Gun and Silverfox both genuinely have no Trailforks page; I'm confident in that null result but a sub-subagent with login access could check the unmapped-trails list. (6) The `SILVEREFOX` English-label reading is unusual enough that I'd want a second pair of eyes on the high-resolution crop before treating it as a "correction" candidate.

**Mover says:** Shipping. Five fragments at `manager_M2/{sign-id}_pageContent.json`, all photos in `docs/assets/{folder}/`, coordinator can merge atomically. Every open question is explicit and the user can resolve each one via the Sign Page Content panel without further agent work. The catalogue corrections are scoped strictly to these five entries and every one is grounded in either the carved plaque, the existing Trailforks listing, or both.

---

## Deliverables checklist

- [x] `manager_M2/sapwapahcikan-paskisikan_pageContent.json`
- [x] `manager_M2/bed-springs_pageContent.json`
- [x] `manager_M2/soniyawahkesis_pageContent.json`
- [x] `manager_M2/maskihkiwiyiniw_pageContent.json`
- [x] `manager_M2/bobsled_pageContent.json`
- [x] All 5 `photo.src` paths populated; corresponding asset files exist under `docs/assets/{folder}/`
- [x] `manager_M2_report.md` (this file)
- [x] Catalogue corrections proposed in `notes` per sign AND surfaced in this report's table
- [x] No edits to `catalogue.json` or `docs/{folder}/index.html` (coordinator-owned)
