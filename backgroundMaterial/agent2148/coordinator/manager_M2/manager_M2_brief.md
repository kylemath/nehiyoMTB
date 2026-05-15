# Manager M2 Brief — Sign #2 `backbreaker` (Back Breaker)

You are **Manager M2** for Agent 2148. Your sign is `backbreaker` (Back Breaker, sign #2).

## Tripartite Persona

You operate under the Agent 2148 tripartite persona. **Read and embody** the verbatim block at:

`/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/tripartite_persona.md`

When you spawn sub-subagents via the Task tool, **paste the full contents of that file** into each child prompt so the three voices propagate.

## Your Sign At A Glance

| Field          | Value                                                                |
|----------------|----------------------------------------------------------------------|
| `id`           | `backbreaker`                                                        |
| `signNumber`   | 2                                                                    |
| `englishName`  | Back Breaker                                                         |
| `creeName` (catalogue, may be wrong) | `kaskawikanênêw`                                |
| `creeSyllabics` (catalogue, may be wrong) | `ᑲᐢᑲᐏᑲᓀᓀᐤ`                                  |
| `folder`       | `backbreaker`                                                        |
| `colors`       | white, red                                                           |
| Existing photo | None in `docs/assets/`. Must rely on `allSigns.jpg` crop or omit.    |
| Sign STLs      | `docs/backbreaker/backbreaker_plaque.stl`, `5_Vertebrae_Plain.stl`, `Chain.stl` |
| Current state  | NO `pageContent` yet — draft full content from scratch.              |

**Verify the SRO/syllabics against the physical sign before trusting the catalogue values.** The trail builder may have used a different spelling than the catalogue draft.

## Your Mission

Build the **complete** `pageContent` from scratch:

1. **Visual read** of the physical sign:
   - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg` — composite of all signs. Sign #2 is Back Breaker.
   - STL filenames in `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/backbreaker/` (use Shell + `head -1` to check the filename / first solid name; do NOT Read STL bytes).
   - Transcribe what is actually carved/printed on the sign for `creeName` (SRO) and `creeSyllabics`. If the catalogue value `kaskawikanênêw` doesn't match what you see on the sign, **trust the sign**, and add a `notes` entry flagging the discrepancy.

2. **Trailforks lookup**: search the web for the trail. Suggested queries:
   - "Back Breaker Edmonton mountain bike Trailforks"
   - "Back Breaker trail Edmonton" / "Capital City Trails"
   - Pick the most likely Edmonton-area MTB match. Record `trailId`, `trailUrl`, `widgetUrl`, `displayName`. If no confident match, leave `trailforks: {}` and add a `notes` entry.
   - Widget URL pattern: `https://www.trailforks.com/widgets/trail/?trailid={TRAIL_ID}&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1`

3. **Cultural story** (2–3 paragraphs) about the English name + Cree meaning + the visual design (vertebrae spine + chain motif suggested by the STL filenames). Drop into `culturalStory.body` as an array of paragraph strings. Use `<strong>...</strong>` HTML inline for emphasis where useful. Heading example: `"About the Name"` or `"Spine of the Trail"`.

4. **Linguistics**: build `primarySection`, `relatedForms` (1–3 entries), `quickReference` (3–6 rows), `baseWords` (1–3). Each morpheme needs `key`, `sro`, `syllabics`, `gloss`. Use itwêwina, Online Cree Dictionary, Plains Cree Dictionary as secondary references for glosses. Add a `notes` entry flagging anything uncertain. Use circumflexes `â ê î ô` in SRO.

5. **Accent color**: default `#dc3545` (red) to match the sign's red color layer. Set `themeName: "red"`.

6. **Photo**: if you cannot easily produce a placeholder image, **omit the `photo` field entirely** (or set `photo: {}`). The renderer handles missing photo gracefully and falls through. Add a `notes` entry: "Photo placeholder pending — user to provide or crop from allSigns.jpg." Do NOT install Pillow.

7. **Produce** the final pageContent as a standalone JSON file at:

   `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/pageContent.json`

   Top-level keys: `pageStatus`, `accentColor`, `themeName`, `headerTitle`, `photo` (optional), `trailforks`, `linguistics`, `culturalStory`, `trailStory`, `sources`, `notes`. `pageStatus` MUST be `"agent-drafted"`. Use Python `json.dump` with `ensure_ascii=False, indent=2`.

8. **Do NOT edit `catalogue.json` yourself.** The coordinator merges all three pageContent fragments atomically after you finish.

9. **Manager report** at `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/manager_M2_report.md` with:
   - What the physical sign shows (SRO + syllabics actually carved).
   - Trailforks search outcome.
   - Linguistic sources consulted + uncertainties.
   - Cultural story rationale.
   - The tripartite self-assessment block (Craftsperson / Skeptic / Mover).
   - Open questions for the user.

## Sub-subagents You May Spawn

Workspace folders are pre-created:

- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/sub_S1/` — visual read + linguistics draft.
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/sub_S2/` — Trailforks search + cultural story draft.
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/sub_S3/` — (optional) assembly QA before you compile the final `pageContent.json`.

Each sub-subagent prompt MUST include the full tripartite persona. Spawn S1 and S2 in parallel (one Task tool call with two child calls in the same message). Each sub writes its outputs to a notes file inside its own `sub_S*/` folder. You (M2) consolidate their outputs into the final `pageContent.json`.

## Acceptance Criteria (self-check before declaring done)

- [ ] `manager_M2/pageContent.json` exists and is valid JSON.
- [ ] `pageStatus == "agent-drafted"`.
- [ ] `linguistics.primarySection.morphemes` contains ≥1 morpheme with `key`/`sro`/`syllabics`/`gloss`.
- [ ] `linguistics.relatedForms` has ≥1 entry, each with `english`/`sro`/`syllabics` and ideally `morphemes`.
- [ ] `linguistics.quickReference` has 3–6 rows.
- [ ] `linguistics.baseWords` has ≥1 entry.
- [ ] `culturalStory` has `heading` + ≥1 paragraph in `body`.
- [ ] `trailforks` is either fully populated (`trailId`, `trailUrl`, `widgetUrl`, `displayName`) or `{}` with a notes entry.
- [ ] `notes` documents discrepancies vs. catalogue values, uncertainties, and photo-placeholder status.
- [ ] `manager_M2_report.md` written with tripartite self-assessment.

## Repo Reference Pointers

- Spec: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/sign-object-spec.md` (Page Content Object section).
- Exemplar HTML (DO NOT MODIFY): `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kiwapamitin/index.html`.
- Exemplar pageContent JSON: see `kahkakiw` in `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json`.
- Renderer: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/tools/sign_page_renderer.py`.

## Hard Constraints

- ALWAYS use absolute paths in tool calls.
- Do NOT modify `catalogue.json`. Do NOT modify any file outside `backgroundMaterial/agent2148/coordinator/manager_M2/`.
- Do NOT modify `docs/backbreaker/index.html` directly.
- Do NOT delete files. Do NOT run `git add` / `git commit` / `git push`.
- Do NOT install packages.
- Cree text comes from the **physical sign** first, dictionaries second.
- Morpheme `key` values across the page must be unique (renderer hover-pairs by key).
