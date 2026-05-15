# Pilot Summary — Agent 2148

**Coordinator:** 2148-C
**Run window:** 2026-05-14 22:05 → 22:28 (~23 minutes wall clock, three managers in parallel)
**Pilot scope:** 3 of 23 signs (`kahkakiw`, `backbreaker`, `kakwa`)

## TL;DR

Three kiwapamitin-style sign pages now render from structured `pageContent` data in `catalogue.json`:

- `docs/kahkakiw/index.html`
- `docs/backbreaker/index.html`
- `docs/kakwa/index.html`

All three signs have `pageContent.pageStatus == "agent-drafted"` and `catalogue.json` is still valid JSON (23 models, same collection-level metadata). The `pageContent` → renderer pipeline is validated end-to-end. Two catalogue-level Cree-spelling errors were found and corrected from the physical signs (`kaskâwikanênêw` and `kâkwa`).

---

## Per-sign deliverable highlights

### Sign #1 — `kahkakiw` (Raven)

| Field           | Value                                                                                  |
|-----------------|----------------------------------------------------------------------------------------|
| pageStatus      | `agent-drafted`                                                                        |
| accentColor     | `#000000` (theme `black`) — matches the sign's mostly-black palette                    |
| headerTitle     | `Raven • kahkakiw • ᑲᐦᑲᑭᐤ`                                                              |
| Photo           | `../assets/kahkakiw/raven_wild.png` (already in repo) — rendered                       |
| Trailforks      | **Match:** Trail ID `146421` "Raven" in Buena Vista (Edmonton river valley)            |
| Morphemes       | 1 primary (`kahkakiw` = raven, animate noun)                                            |
| Related forms   | 2 — `kahkakiwak` (plural, stem + `-ak`), `kahkakiwisis` (diminutive, stem + `-isis`)   |
| Quick reference | 3 rows                                                                                  |
| Base words      | 1                                                                                       |
| Cultural story  | "About the Raven" — 2 paragraphs                                                       |
| Sources         | itwêwina, Online Cree Dictionary, Plains Cree Dictionary                               |
| Catalogue corrections applied | none (catalogue already matched the sign)                                |

**Manager M1 refined (vs. the prior Main-Agent-seeded draft):**

- Split single-morpheme related forms into stem + suffix morphemes so the renderer's hover-pairing works for `-ak` and `-isis`.
- Set `linguistics.type` from `"noun"` → `"noun (animate)"` (so the `-ak` animate plural is explained, not just shown).
- Tightened `photo.alt` for screen readers; tightened `photo.caption`.
- Added a verification log to `notes` (replacing the prior single-line transfer note while preserving the curator-history intent).

### Sign #2 — `backbreaker` (Back Breaker)

| Field           | Value                                                                                  |
|-----------------|----------------------------------------------------------------------------------------|
| pageStatus      | `agent-drafted`                                                                        |
| accentColor     | `#dc3545` (theme `red`) — matches the sign's red accents                               |
| headerTitle     | `Back Breaker • kaskâwikanênêw • ᑲᐢᑳᐏᑲᓀᓀᐤ`                                              |
| Photo           | Omitted (renderer skips block) — user to crop from `allSigns.jpg`                      |
| Trailforks      | **Match:** Trail ID `10634` "Back Breaker" in Hawrelak / MacKinnon Ravine (NW Edmonton) |
| Morphemes       | 5 — `kaskâ-` (snap/break) + `-wikan-` (back, medial) + `-ê-` + `-n-` (by hand) + `-êw` (VTA 3→3′) |
| Related forms   | 3 — `wîkan` (back, noun), `pîkonêw` (break it apart), `kaskâwikanisin` (one's back is broken) |
| Quick reference | 6 rows                                                                                  |
| Base words      | 3                                                                                       |
| Cultural story  | "Spine of the Trail" — 3 paragraphs tying mountain-bike vernacular → vertebra+chain visual pun → Cree morpheme reading → Nêhiyaw-Askiy territory acknowledgement |
| Sources         | itwêwina, Online Cree Dictionary, Plains Cree Dictionary                               |
| Catalogue corrections applied | **`creeName` `kaskawikanênêw` → `kaskâwikanênêw`** (added long-â circumflex); **`creeSyllabics` `ᑲᐢᑲᐏᑲᓀᓀᐤ` → `ᑲᐢᑳᐏᑲᓀᓀᐤ`** (added long-â dot on third glyph). The physical plaque carries the circumflex; itwêwina headword `kaskâwikanênêw` "s/he breaks s.o.'s back by hand" matches. |

### Sign #17 — `kakwa` (Porcupine)

| Field           | Value                                                                                  |
|-----------------|----------------------------------------------------------------------------------------|
| pageStatus      | `agent-drafted`                                                                        |
| accentColor     | `#dc3545` (theme `red`) — matches the sign's red top layer                             |
| headerTitle     | `Porcupine • kâkwa • ᑳᑿ`                                                                |
| Photo           | Omitted (renderer skips block) — user to crop from `allSigns.jpg`                      |
| Trailforks      | **No match in Edmonton-area regions** (six queries + direct region-page greps). Block renders the "Trail information coming soon" stub. |
| Morphemes       | 1 primary (`kâkwa` = porcupine, animate noun)                                          |
| Related forms   | 3 — `kâkwak` (plural, confident), `kâkwasis` (diminutive, regular but not independently dictionary-confirmed), `kâway` (quill, competing attestations — flagged tentative) |
| Quick reference | 5 rows                                                                                  |
| Base words      | 1                                                                                       |
| Cultural story  | "About kâkwa — the Porcupine" — 3 paragraphs (patient forest dweller; pre-bead quillwork craft tradition; gently-hedged note on the sign's red/black/white palette echoing earth-pigment quill-dye traditions) |
| Sources         | itwêwina, Online Cree Dictionary, Plains Cree Dictionary                               |
| Catalogue corrections applied | **`creeName` `kakwa` → `kâkwa`** (added long-â circumflex); **`creeSyllabics` `ᑲᑲᐧ` → `ᑳᑿ`** (long-â glyph + `ᑿ` kwa). Visual read of the carved plaque is the authority. |

---

## Catalogue-level corrections applied (all scoped to pilot signs)

| Sign         | Field           | Old (pre-pilot)         | New (carved on sign)       |
|--------------|-----------------|-------------------------|----------------------------|
| backbreaker  | `creeName`      | `kaskawikanênêw`        | `kaskâwikanênêw`           |
| backbreaker  | `creeSyllabics` | `ᑲᐢᑲᐏᑲᓀᓀᐤ`               | `ᑲᐢᑳᐏᑲᓀᓀᐤ`                 |
| kakwa        | `creeName`      | `kakwa`                 | `kâkwa`                    |
| kakwa        | `creeSyllabics` | `ᑲᑲᐧ`                    | `ᑳᑿ`                        |

A pre-merge backup of `catalogue.json` is preserved at `backgroundMaterial/agent2148/coordinator/catalogue_pre_merge_backup.json`.

A `kahkakiw` description is also worth noting: the catalogue's `description` for `backbreaker` says "red gear-like graphic" but the plaque actually shows a vertebra (single lumbar-style vertebra in white, with red accents). This was NOT changed in catalogue.json this pass (out of strict scope) but is flagged for user review.

---

## Open questions for the user

1. **`kahkakiwisis` syllabics carry-over.** M1 preserved the curator-reviewed form `ᑲᐦᑲᑭᐏᓯᓯᐢ` even though a strict mapping of `kahkakiwisis` would yield `ᑲᐦᑲᑭᐏᓯᐢ` (one fewer `ᓯ`). M1 erred on the side of the spec rule "do not silently replace a checked local spelling." Please confirm with an elder / itwêwina cross-check.
2. **`kakwa` second syllabic glyph at higher resolution.** M3's best read is `ᑿ` (kwa) — internally consistent with the carved Roman `kwa` — but at the composite-image crop resolution a bare `ᑲ` (ka) cannot be 100% ruled out. A higher-res single-panel photo would settle this.
3. **Diminutive / quill related forms on `kakwa`.** `kâkwasis` (regular `-sis` diminutive but not independently dictionary-attested in this run) and `kâway` (competing forms `kâwiy`, `okâway` in teaching materials) are flagged tentative on the page. Drop either if a stricter linguistics presentation is preferred.
4. **`kakwa` header line says `Porcupine • kâkwa • ᑳᑿ` while the catalogue card title is `Kakwa`.** M3 chose to put the meaning in the page header; the catalogue card still uses the loanword "Kakwa" as the English trail name. Decide which presentation you prefer and either change `model.title` to `Porcupine` or change `pageContent.headerTitle` to `Kakwa • kâkwa • ᑳᑿ`.
5. **Trailforks confidence — `Back Breaker`.** There is also a `Lower Back Breaker` sibling trail in the same Hawrelak / MacKinnon Ravine network. M2 selected the main `Back Breaker` (trailId `10634`) at ~95% confidence. Confirm before flipping `pageStatus` past `agent-drafted`.
6. **Trailforks confidence — `Raven` (kahkakiw).** M1's S2 sub-subagent found trailId `146421` via two internal Trailforks listings, but a live fetch timed out (rate limit). Worth a single human click before promoting `pageStatus`.
7. **`backbreaker` plaque description.** Catalogue says "red gear-like graphic" — the plaque shows a vertebra. Want this corrected in the next batch?
8. **`backbreaker` extra STL geometry.** `5_Vertebrae_Plain.stl` and `Chain.stl` exist in `docs/backbreaker/` but only one vertebra and no chain are visible on the actual mounted plaque in `allSigns.jpg`. Larger composite installation? Future revision?
9. **Photos for `backbreaker` and `kakwa`.** Both omitted (renderer falls through gracefully). Please either crop from `allSigns.jpg` or supply better photos when ready. Putting them at `docs/assets/backbreaker/sign.jpg` and `docs/assets/kakwa/sign.jpg` and updating `pageContent.photo.src` in the Sign Page Content panel is the easiest path.
10. **Accent color choices.** M2 chose `#dc3545` for `backbreaker` and M3 chose `#dc3545` for `kakwa` because both signs have red layers. Both are placeholders; adjust via the panel.

---

## Coordinator self-assessment

**Craftsperson says:** The three pages render cleanly, structurally identical to the kiwapamitin exemplar (modulo content). The fragment-merge pattern (each manager produces `pageContent.json`, coordinator merges atomically) eliminated the `catalogue.json` race condition while preserving parallel manager execution. The two diacritic catalogue corrections (`kaskâwikanênêw`, `kâkwa`) are well-justified — they came from direct visual reads of the carved plaques and are corroborated by itwêwina — and they are scoped exclusively to the three pilot models, satisfying the "only modify the three pilot signs' entries" constraint. Every manager produced a substantive report with a real Craftsperson / Skeptic / Mover self-assessment, and every fragment survived merge unchanged.

**Skeptic says:** Three things I'd revisit with more time. (1) `kahkakiwisis` syllabics — preserved per spec but flagged uncertain to end users. (2) `kakwa` second syllabic glyph at low image resolution. (3) `kakwa` page `h1` says "Porcupine" while the catalogue card title says "Kakwa" — minor inconsistency the user may want to align. None of these are blockers; all are flagged here for review. A fourth, broader doubt: the tripartite persona block was pasted verbatim into every subagent prompt, but I have no way to observe whether the sub-subagents actually internalized it vs. just acknowledged its presence — the proof would be in their *reports*, not their compliance.

**Mover says:** Shipping. Three pages render correctly, catalogue.json is valid, the open questions are explicit and the user can address each via the Sign Page Content panel without further agent work. The pipeline (visual read → pageContent → fragment merge → renderer → verify) is now proven and ready for the remaining 19 signs.

---

## Next steps

### Remaining 19 signs (suggested batching)

| Batch | Sign IDs                                                                                 | Notes |
|-------|------------------------------------------------------------------------------------------|-------|
| B1 (simple noun signs) | `nicocwasaskanos` (Six Shooter), `sapwapahcikan-paskisikan` (Ray Gun), `soniyawahkesis` (Silverfox), `nosemanicos` (Nosemanicos / ladybug), `oyoyow` (Oyoyow), `ocayisinakes` (Ocayisinakes), `mistapiskihkoman` (Machete) | Single-noun morpheme pattern like `kahkakiw` / `kakwa`. ~30 min/sign with one manager + one sub. |
| B2 (multi-word / verb-phrase signs) | `lovers-lane`, `nipamayatan-pekiseyahk` (Purple Haze), `mamahtaw-iskwew` (Wonder Woman), `purgatory`, `maskihkiwiyiniw` (Medicine Man), `bed-springs` | More morphemes; pattern follows `backbreaker` (multi-morpheme primary section). ~45 min/sign. |
| B3 (English-loanword signs / no Cree yet) | `bobsled`, `deliverance`, `ewok`, `farmers-daughter`, `victoria-secret`, `slinky` | Cree forms not yet set in catalogue. Linguistic research needed before pageContent. Lower priority OR mark `pageStatus: draft` and skip until a Cree name is chosen. |

Suggested rollout pattern (same shape as this pilot, scaled):

1. **Batch B1 (7 signs).** Spawn one coordinator-level agent with 7 managers in parallel. Each manager spawns 2 sub-subagents (S1 visual+linguistics, S2 Trailforks+story). Coordinator merges + renders + verifies.
2. **Batch B2 (6 signs).** Same pattern but each manager probably wants the full 3-sub-subagent split (S1 linguistics, S2 Trailforks, S3 cultural story) because phrase-level signs need more research.
3. **Batch B3 (6 signs).** Decide first whether to (a) commission Cree forms before drafting `pageContent`, or (b) leave their `pageStatus` as `draft` so the renderer skips them.

### Tooling improvements suggested by this run

1. **Catalogue.json concurrent-write guard.** Add a small helper at `tools/update_page_content.py` that takes `--sign {id}` + `--input pageContent.json` and atomically merges with `fcntl` file locking, so future batches can let managers write directly to the catalogue without a coordinator-level merge step. This pilot worked around the race by doing all merges at the coordinator, but a helper would simplify the pattern for the larger batches.
2. **Photo placeholder pipeline.** Pre-crop sign-by-sign rectangles from `allSigns.jpg` (one-time, scripted in PIL) into `docs/assets/{folder}/sign.jpg` so future managers don't have to skip the photo block. Even rough crops (the user said placeholders are fine) would mean the rendered page is more visually complete out of the gate.
3. **Renderer dry-run mode.** Add a `--dry-run --stdin` flag to `tools/sign_page_renderer.py` that takes a `pageContent` JSON on stdin + a model id, and prints the rendered HTML to stdout without touching `catalogue.json` or any file. Lets sub-subagents validate their own JSON before declaring done. (Pilot worked without this, but it would cut iteration loops.)
4. **Sign Page Content panel UI.** Surface the `notes` array prominently — most of the user's actionable review items end up in `notes`, and the panel should make those one-click-resolvable instead of buried in JSON.
5. **`renderable` check in catalogue editor.** When a `pageContent` is saved with `pageStatus: agent-drafted`, run the renderer immediately as part of the save (the catalogue editor server already has this endpoint per the spec, but the local editor UI's save button could be wired to call both `/api/save-sign-content` and `/api/regenerate-sign-page` in sequence).
6. **Catalogue Cree-text validation.** A one-time script that flags every catalogue `creeName` whose syllabics don't decode to the same SRO (or vice versa) — this pilot caught two such errors by reading the physical signs, but a static check could surface them faster.

### Pilot validation declaration

The kiwapamitin-style page pattern is now proven for three distinct sign types:

- A **simple animate-noun, well-known trail with photo** (`kahkakiw`).
- A **complex multi-morpheme VTA verb-phrase, plain plaque without photo, with Trailforks match** (`backbreaker`).
- A **simple animate-noun, plain plaque without photo, no Trailforks match** (`kakwa`).

These three cases together exercise all the renderer's branches (photo present / photo absent, trailforks present / trailforks absent, single-morpheme primary section / multi-morpheme primary section, related forms with morphemes / related forms without morphemes). The remaining 19 signs should fit one of these shapes; no further renderer changes are anticipated.
