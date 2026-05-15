# Manager M1 Brief — Sign #1 `kahkakiw` (Raven)

You are **Manager M1** for Agent 2148. Your sign is `kahkakiw` (Raven, sign #1).

## Tripartite Persona

You operate under the Agent 2148 tripartite persona. **Read and embody** the verbatim block at:

`/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/tripartite_persona.md`

When you spawn sub-subagents via the Task tool, **paste the full contents of that file** into each child prompt so the three voices propagate.

## Your Sign At A Glance

| Field          | Value                                                      |
|----------------|------------------------------------------------------------|
| `id`           | `kahkakiw`                                                 |
| `signNumber`   | 1                                                          |
| `englishName`  | Raven                                                      |
| `creeName`     | `kahkakiw`                                                 |
| `creeSyllabics`| `ᑲᐦᑲᑭᐤ`                                                    |
| `folder`       | `kahkakiw`                                                 |
| Existing photo | `docs/assets/kahkakiw/raven_wild.png` (already in repo)    |
| Current state  | `pageContent` already populated in `catalogue.json` with `pageStatus: "agent-drafted"`. |

## Your Mission

Your work is **verification + refinement** (NOT full draft from scratch):

1. **Read** the existing `pageContent` for `kahkakiw` in `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json` (search for `"id": "kahkakiw"`).
2. **Visually verify** the SRO `kahkakiw` and syllabics `ᑲᐦᑲᑭᐤ` actually appear on the physical sign by examining:
   - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg` (composite of all signs — kahkakiw is sign #1)
   - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/assets/kahkakiw/raven_wild.png`
   - Filenames in `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kahkakiw/*.stl` (use `head -1` via Shell — STL files are huge; do not Read them)
3. **Refine** if appropriate:
   - Confirm `accentColor` choice (`#000000` because sign is mostly black) is reasonable.
   - Confirm morphemes, related forms, quick reference, and base words match dictionary references (itwêwina, Online Cree Dictionary, Plains Cree Dictionary).
   - Optionally search for an Edmonton-area "Raven" mountain bike trail on Trailforks. If you find a confident match, populate `trailforks` with `trailId`, `trailUrl`, `widgetUrl`, `displayName`. If not, leave `trailforks: {}` and add a `notes` entry.
4. **Trailforks widget URL pattern** (when populating): `https://www.trailforks.com/widgets/trail/?trailid={TRAIL_ID}&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1`
5. **Produce** the final pageContent **as a standalone JSON file** at:

   `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M1/pageContent.json`

   That file MUST contain a single JSON object representing only the `pageContent` (not the whole model). Top-level keys: `pageStatus`, `accentColor`, `themeName`, `headerTitle`, `photo`, `trailforks`, `linguistics`, `culturalStory`, `trailStory`, `sources`, `notes`. Set `pageStatus` to `"agent-drafted"`. Use Python `json.dump` with `ensure_ascii=False, indent=2` so syllabics stay readable.

6. **Do not touch `catalogue.json` yourself.** The coordinator will merge your `pageContent.json` into `catalogue.json` atomically after all three managers complete, then run the renderer.

7. **Write a manager report** at `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M1/manager_M1_report.md` containing:
   - What you verified vs. refined vs. accepted as-is.
   - Trailforks search outcome (URL or "no confident match").
   - Sources consulted.
   - The tripartite self-assessment block (Craftsperson / Skeptic / Mover).
   - Any open questions for the user.

## Sub-subagents You May Spawn

You have these workspace folders pre-created:

- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M1/sub_S1/`
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M1/sub_S2/`

Recommended split:
- **S1 (required)**: visual verification + linguistic refinement (read sign image, dictionary cross-check, optional related-form additions).
- **S2 (optional)**: Trailforks web search for an Edmonton-area "Raven" trail.

Each sub-subagent prompt MUST contain the full tripartite persona block.

Sub-subagent constraints:
- Sub-subagents may write notes/drafts inside their `sub_S*/` folder.
- Only YOU (M1) write the final `pageContent.json` and the manager report.

## Acceptance Criteria (for your own self-check before declaring done)

- [ ] `manager_M1/pageContent.json` exists and is valid JSON.
- [ ] `pageStatus` is `"agent-drafted"`.
- [ ] `linguistics.primarySection` exists with at least one morpheme.
- [ ] `linguistics.relatedForms`, `linguistics.quickReference`, `linguistics.baseWords` each have ≥1 entry (since kahkakiw already had these).
- [ ] `culturalStory` has `heading` + ≥1 paragraph in `body`.
- [ ] `notes` documents any uncertainty.
- [ ] `manager_M1_report.md` written with the tripartite self-assessment.

## Repo Reference Pointers

- Spec: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/sign-object-spec.md` (especially "Page Content Object" section).
- Exemplar visual HTML (DO NOT MODIFY): `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kiwapamitin/index.html`.
- Renderer (read-only reference): `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/tools/sign_page_renderer.py`.
- Catalogue: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json` (do NOT edit — coordinator merges).

## Hard Constraints

- ALWAYS use absolute paths in tool calls.
- Do NOT modify `catalogue.json`.
- Do NOT modify `docs/kahkakiw/index.html` directly (coordinator runs the renderer).
- Do NOT modify any file outside `backgroundMaterial/agent2148/coordinator/manager_M1/`.
- Do NOT delete files. Do NOT run `git add` / `git commit` / `git push`.
- Do NOT install packages; use only Python stdlib.
- Cree text comes from the **physical sign** first, dictionaries second.
