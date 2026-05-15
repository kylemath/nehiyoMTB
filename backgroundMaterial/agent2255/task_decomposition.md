# Task Decomposition — Agent 2255

## Original Task

Following the successful pilot of Agent 2148 (kahkakiw, backbreaker, kakwa), the user said:

> "ok lets now automate the rest of the signs, this is working great"

Batch 2 covers the remaining 19 signs.

## Scope — 19 Signs

| Manager | Signs (id list)                                                                |
|---------|--------------------------------------------------------------------------------|
| M1      | mistapiskihkoman, nicocwasaskanos, nipamayatan-pekiseyahk, lovers-lane, mamahtaw-iskwew |
| M2      | sapwapahcikan-paskisikan, bed-springs, soniyawahkesis, maskihkiwiyiniw, bobsled         |
| M3      | purgatory, deliverance, ewok, farmers-daughter, ocayisinakes                            |
| M4      | oyoyow, nosemanicos, victoria-secret, slinky                                            |

`kahkakiw`, `backbreaker`, `kakwa` (already pilot-completed) and `kiwapamitin` (hand-built exemplar) are out of scope.

## Pattern (proven by Agent 2148)

For each sign:

1. **Visual read** — open `allSigns.jpg` (repo root) and any `docs/assets/{folder}/*` photo and `{folder}/*.png`; read SRO + syllabics off the carved plaque; cross-reference `catalogue.json` `creeName` / `creeSyllabics`.
2. **Trailforks search** — search web for the trail (e.g. "Six Shooter Edmonton mountain bike Trailforks"). Edmonton-area trails. The expected URL form is `https://www.trailforks.com/trails/{slug}-{id}/` (with an embedded trail id). If no confident match, leave `trailforks: {}` and record a note. Build `widgetUrl` from `trailId` using the standard pattern.
3. **Photo** — if `docs/assets/{folder}/sign_render.png` (or any image) exists, set `photo.src` to `../assets/{folder}/{filename}`. If no asset exists, crop the sign from `allSigns.jpg` into `docs/assets/{folder}/sign_render.png` and wire that as `photo.src`. **Photo wiring was the #1 mistake in pilot — do not forget it.**
4. **Cultural story** — 2–3 short paragraphs about the English name + Cree meaning + design choices. Trail-builder personal story stays empty unless a credible one surfaces.
5. **Linguistics** — `primarySection` (1–N morphemes with `key`/`sro`/`syllabics`/`gloss`), 1–3 `relatedForms`, 3–6 `quickReference` rows, 1–3 `baseWords`. Cross-check against itwêwina, Online Cree Dictionary, Plains Cree Dictionary. Where the carved spelling and the dictionary spelling disagree, surface the discrepancy in `notes` and flag for curator review — DO NOT silently rewrite `catalogue.json` top-level fields except in the same surgical pattern the pilot used (correct diacritics with a clear notes paragraph).
6. **Assembly** — write a standalone `pageContent.json` to `coordinator/manager_M{n}/sub_S{k}/pageContent.json` (one per sign). Do NOT touch `catalogue.json` directly — coordinator merges atomically.
7. **Defer rendering** — coordinator runs `python3 tools/sign_page_renderer.py {ids...}` once at the end across all 19 signs.

## Concurrency rule (carried over from Agent 2148)

`catalogue.json` is one shared file. Managers and sub-subagents write fragment JSON only; the coordinator performs the single atomic merge + render at the end.

## Acceptance Per Sign

- `pageContent.pageStatus = "agent-drafted"`
- `pageContent.linguistics.primarySection.morphemes` has ≥ 1 entry
- `pageContent.linguistics.relatedForms` has ≥ 1 entry
- `pageContent.linguistics.quickReference` has ≥ 3 rows
- `pageContent.culturalStory.heading` present and `body` has ≥ 1 paragraph
- `pageContent.photo.src` is set (existing asset wired, or fresh crop from allSigns.jpg)
- `pageContent.trailforks` is either fully populated (`trailId`, `trailUrl`, `widgetUrl`, `displayName`) or `{}` with a `notes` entry explaining why
- Morpheme `key` values are unique within the page

## Files of Reference (read these in every sub-subagent)

- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/sign-object-spec.md` — schema
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kiwapamitin/index.html` — visual exemplar (DO NOT MODIFY)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json` — current data (kahkakiw, backbreaker, kakwa entries are the data shape exemplars)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/tools/sign_page_renderer.py` — renderer used by coordinator at the end
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg` — composite of all physical plaques
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/deliverables/pilot_summary.md` — pilot self-review
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/pageContent.json` — best example of a fully-fleshed pageContent fragment (backbreaker)

## Complexity Estimate

19 signs × ~30 min agent work each, parallelized across 4 managers × 5 signs each = ~2.5 hrs wall clock. Some signs (e.g. `ewok`, `victoria-secret`, `slinky`) have no real Cree word and may need to be lighter-weight: the morpheme breakdown can be a single one-row entry, the story can frame the English name as MTB vernacular borrowed straight into a Plains-Cree-territory plaque without forcing a translation.
