# Task Decomposition — Agent 2148

## Original Task

> "Create a multiagent team to go through each of the other index.html pages and build out their content to match [docs/kiwapamitin/index.html], before starting ask me for any details or info I can provide in a table or web UX to make this easier."

This run is the **pilot phase** of that task. The user chose pilot-first roll-out.

## Pilot Scope (this agent)

Three signs only:

| Sign ID        | English Name | Sign # | Initial state                                                                                              |
|----------------|--------------|--------|------------------------------------------------------------------------------------------------------------|
| `kahkakiw`     | Raven        | 1      | `pageContent` already populated by Main Agent from hand-built `docs/kahkakiw/index.html` (status `agent-drafted`). Manager M1 verifies + refines + re-renders. |
| `backbreaker`  | Back Breaker | 2      | No `pageContent`. Manager M2 drafts everything from scratch (visual sign read, Trailforks search, linguistics, cultural story). |
| `kakwa`        | Kakwa        | 17     | No `pageContent`. Manager M3 drafts everything similarly. Has existing `colorLayers` data. |

## Authoritative Constraints (from user)

1. **Cree text source-of-truth**: agents read SRO + syllabics directly off the **physical sign** as captured in the sign images and/or STL geometry. Dictionaries (itwêwina, Online Cree Dictionary, Plains Cree Dictionary) are **secondary** references used only for morpheme glosses and related forms.
2. **Photos**: `allSigns.jpg` (repo root) is a composite of all signs. Agents may crop / extract per-sign photos from it as **placeholder** images. The user will replace with better photos later. If `docs/assets/{folder}/*` already has a photo (e.g. kahkakiw), use that.
3. **Trailforks**: agents search the web for the trail's Trailforks page. The trails are around Edmonton, Alberta mountain bike trail networks.
4. **Cultural stories**: agents draft a 2–3 paragraph cultural / contextual story based on the English name, Cree meaning, and the sign's visual design. Trail-builder personal stories (like the ICU connection) only appear when the agents find/infer a credible one; otherwise leave `trailStory` empty.
5. **Accent color**: deferred to the human user. Agents set a reasonable default (e.g. `#000000` for kahkakiw because its sign is mostly black, `#dc3545` for backbreaker, etc.) — user can change it later via the new Sign Page Content panel in `docs/index.html`.
6. **`pageStatus` must be set to `agent-drafted`** on save, so the renderer produces output and the user sees the badge in the UI.

## Atomic Subtasks

Per-sign atomic units (the same shape for each of the three pilot signs):

- A. **Visual read**: open the sign image (`allSigns.jpg` crop and/or `docs/assets/{folder}/*` and/or `docs/{folder}/*.png`); cross-reference with the production STL filename and `creeName` / `creeSyllabics` in `catalogue.json`; transcribe the SRO + syllabics that actually appear on the sign.
- B. **Trailforks lookup**: web-search for the trail (e.g. "Back Breaker Edmonton mountain bike Trailforks") and pick the most likely match. Record `trailId`, `trailUrl`, `displayName`. If no match is confident, leave `trailforks` empty and add a `notes` entry.
- C. **Cultural story draft**: 2–3 short paragraphs about the English name + Cree meaning + animal/object significance, suitable for the cultural context box.
- D. **Linguistics draft**: build `primarySection` (morphemes with `key`, `sro`, `syllabics`, `gloss`), 1–3 `relatedForms`, a 3–6 row `quickReference` table, and 1–3 `baseWords`. Use itwêwina + Online Cree Dictionary + Plains Cree Dictionary as secondary references and add a `notes` entry flagging anything uncertain.
- E. **Assemble + persist**: write the `pageContent` object into `catalogue.json` under the matching `models[].id`. Use Python (`json.load` → mutate → `json.dump` with `ensure_ascii=False, indent=2`) so syllabics stay readable. Set `pageStatus` to `agent-drafted`.
- F. **Render + verify**: run `python3 tools/sign_page_renderer.py {sign-id}`; read the resulting `docs/{folder}/index.html` and check that header, photo block, trail block, primary morpheme row, related forms, quick reference, and story render in the expected order without empty fragments.
- G. **Report**: write `sub_S1/S1_report.md` (or appropriate) with assumptions, sources, uncertainties, and a path list of every file touched.

## Dependency Graph

- A, B, C, D for the same sign can run in parallel.
- E depends on A + C + D (and optionally B).
- F depends on E.
- G depends on F.

Across signs: M1, M2, M3 are fully independent and run in parallel.

## Stream Allocation

| Manager | Sign         | Sub-subagents                                                                 | Async? |
|---------|--------------|-------------------------------------------------------------------------------|--------|
| M1      | kahkakiw     | S1 visual-verify + render. S2 (optional) refine relatedForms vs dictionaries. | Yes    |
| M2      | backbreaker  | S1 visual-read + linguistics. S2 trailforks + cultural story. S3 assemble + render. | Yes |
| M3      | kakwa        | S1 visual-read + linguistics. S2 trailforks + cultural story. S3 assemble + render. | Yes |

All three managers launch simultaneously.

## Complexity Estimate

- **Small for kahkakiw** — pageContent already in place, agents only verify and re-render.
- **Medium for backbreaker** — no Cree morpheme analysis yet, need to read sign and draft from scratch.
- **Medium for kakwa** — same as backbreaker; kakwa is a porcupine (kâkwa), so cultural story has a clear animal angle.

Total: ~3 hours of agent work compressed in parallel. Output goes to `docs/kahkakiw/index.html`, `docs/backbreaker/index.html`, `docs/kakwa/index.html` plus updated `catalogue.json`.

## Key References for Sub-subagents

- Spec: `docs/sign-object-spec.md` (especially the new "Page Content Object" section)
- Exemplar HTML: `docs/kiwapamitin/index.html` (do **not** modify)
- Exemplar pageContent in JSON: see `catalogue.json` for `kahkakiw` (the version Main Agent transferred from its existing hand-built page)
- Renderer: `tools/sign_page_renderer.py` — CLI usage `python3 tools/sign_page_renderer.py {sign-id}`
- Server endpoint (optional, if local server is running): `POST /api/save-sign-content` and `POST /api/regenerate-sign-page`. Sub-subagents should use direct file edits + CLI render to avoid depending on a running server.
- Visual: `allSigns.jpg` at repo root, `docs/assets/{folder}/*`, `docs/{folder}/*.stl`, root `{folder}/*.png|*.stl`.
- Linguistics references: <https://itwewina.altlab.app/>, <https://www.creedictionary.com/>, <https://dictionary.plainscree.atlas-ling.ca/>.
