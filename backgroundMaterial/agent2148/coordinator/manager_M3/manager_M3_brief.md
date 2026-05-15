# Manager M3 Brief — Sign #17 `kakwa`

You are **Manager M3** for Agent 2148. Your sign is `kakwa` (sign #17).

## Tripartite Persona

You operate under the Agent 2148 tripartite persona. **Read and embody** the verbatim block at:

`/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/tripartite_persona.md`

When you spawn sub-subagents via the Task tool, **paste the full contents of that file** into each child prompt so the three voices propagate.

## Your Sign At A Glance

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| `id`           | `kakwa`                                                                |
| `signNumber`   | 17                                                                     |
| `englishName`  | Kakwa                                                                  |
| `creeName` (catalogue) | `kakwa`                                                       |
| `creeSyllabics` (catalogue) | `ᑲᑲᐧ`                                                    |
| `folder`       | `kakwa`                                                                |
| `colors`       | white, black, red                                                      |
| `colorLayers`  | already present in catalogue (white → black → red)                     |
| `docsStlPath`  | `kakwa/kakwa_plaque_v3_admesh_fixed_1.stl` (already in `docs/kakwa/`)  |
| Existing photo | None in `docs/assets/`. Must rely on `allSigns.jpg` crop or omit.      |
| Current state  | NO `pageContent` yet — draft full content from scratch.                |

**Important linguistic note:** the task decomposition notes "kakwa is a porcupine (`kâkwa`)". The catalogue's `creeName: "kakwa"` and `creeSyllabics: "ᑲᑲᐧ"` may differ from the spelling carved on the physical sign. **Read the sign image first** and trust what is actually carved. If the carved form uses `kâkwa` / `ᑳᑿ` (with the long-a circumflex and the `ᑿ` final), document that discrepancy and use the carved form as authoritative.

Common dictionary forms to cross-check:
- Plains Cree for porcupine is often given as `kâkwa` or `kakwa` depending on source/dialect.
- Syllabics for `kâkwa`: `ᑳᑿ` (long-a + kwa). For `kakwa`: `ᑲᑿ` or `ᑲᑲᐧ` (the catalogue's existing form).

## Your Mission

Build the **complete** `pageContent` from scratch:

1. **Visual read** of the physical sign:
   - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg` — composite of all signs. Sign #17 is Kakwa.
   - STL filename `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kakwa/kakwa_plaque_v3_admesh_fixed_1.stl` (use Shell + `head -1` only; do NOT Read STL bytes).
   - Transcribe what's actually carved/printed on the sign for `creeName` (SRO) and `creeSyllabics`. Trust the sign. Add a `notes` entry if it differs from the catalogue value.

2. **Trailforks lookup**: search the web for the trail. Suggested queries:
   - "Kakwa Edmonton mountain bike Trailforks"
   - "Kakwa trail Edmonton porcupine"
   - Edmonton-area trail networks include Capital City Trails, Mill Creek, Terwillegar.
   - If no confident match, leave `trailforks: {}` and add a notes entry.
   - Widget URL pattern: `https://www.trailforks.com/widgets/trail/?trailid={TRAIL_ID}&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1`

3. **Cultural story** (2–3 paragraphs) about the porcupine in Cree / Indigenous tradition: traits like resourcefulness, quill-work craft tradition, animal symbolism. Tie into the sign's red+black design if appropriate. Drop into `culturalStory.body` as an array of paragraph strings. Heading suggestion: `"About the Porcupine"` (or whatever matches the carved name).

4. **Linguistics**: build `primarySection` (with `morphemes` — for a single-morpheme noun like `kâkwa` you can use a single morpheme entry mirroring `kahkakiw`'s pattern). Provide `relatedForms` (e.g. plural `kâkwak` / quill `kâwiy`), `quickReference` (3–6 rows), `baseWords` (1–3). Use itwêwina, Online Cree Dictionary, Plains Cree Dictionary for glosses.

5. **Accent color**: default `#dc3545` (red) since the sign has a red top layer. Set `themeName: "red"`. (User will adjust later.)

6. **Photo**: omit the `photo` field (or `photo: {}`) and add a notes entry: "Photo placeholder pending — user to provide or crop from allSigns.jpg." Do NOT install Pillow.

7. **Produce** the final pageContent as a standalone JSON file at:

   `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/pageContent.json`

   Top-level keys: `pageStatus`, `accentColor`, `themeName`, `headerTitle`, `photo` (optional), `trailforks`, `linguistics`, `culturalStory`, `trailStory`, `sources`, `notes`. `pageStatus == "agent-drafted"`. Use Python `json.dump` with `ensure_ascii=False, indent=2`.

8. **Do NOT edit `catalogue.json` yourself.** The coordinator merges all three pageContent fragments atomically after you finish.

9. **Manager report** at `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/manager_M3_report.md` with:
   - What the physical sign shows (SRO + syllabics actually carved). Specifically: does it say `kakwa` or `kâkwa`? Which syllabics form?
   - Trailforks search outcome.
   - Linguistic sources + uncertainties.
   - Cultural story rationale.
   - Tripartite self-assessment block.
   - Open questions for the user.

## Sub-subagents You May Spawn

Workspace folders pre-created:

- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/sub_S1/` — visual read + linguistics draft.
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/sub_S2/` — Trailforks + cultural story.
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M3/sub_S3/` — (optional) assembly QA.

Each sub-subagent prompt MUST include the full tripartite persona. Spawn S1 + S2 in parallel where possible. Sub-subagents write only inside their own `sub_S*/`. M3 consolidates into the final `pageContent.json`.

## Acceptance Criteria

- [ ] `manager_M3/pageContent.json` exists, valid JSON, `pageStatus == "agent-drafted"`.
- [ ] `linguistics.primarySection.morphemes` has ≥1 morpheme with `key`/`sro`/`syllabics`/`gloss`.
- [ ] `linguistics.relatedForms` has ≥1 entry.
- [ ] `linguistics.quickReference` has 3–6 rows.
- [ ] `linguistics.baseWords` has ≥1 entry.
- [ ] `culturalStory` has `heading` + ≥1 paragraph.
- [ ] `trailforks` fully populated OR `{}` with notes entry.
- [ ] `notes` documents discrepancies and uncertainties, including the `kakwa` vs `kâkwa` spelling question.
- [ ] `manager_M3_report.md` written with tripartite self-assessment.

## Repo Reference Pointers

- Spec: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/sign-object-spec.md`.
- Exemplar HTML (DO NOT MODIFY): `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kiwapamitin/index.html`.
- Exemplar pageContent JSON: `kahkakiw` entry in `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json`.
- Renderer: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/tools/sign_page_renderer.py`.

## Hard Constraints

- ALWAYS use absolute paths.
- Do NOT modify `catalogue.json`. Do NOT modify any file outside `backgroundMaterial/agent2148/coordinator/manager_M3/`.
- Do NOT modify `docs/kakwa/index.html` directly.
- Do NOT delete files. Do NOT run `git add` / `git commit` / `git push`.
- Do NOT install packages.
- Cree text comes from the **physical sign** first, dictionaries second.
- Morpheme `key` values must be unique per page.
