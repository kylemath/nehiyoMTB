# Task Decomposition — Agent 2101

## Original Task
Create a multiagent team to make pages like `docs/kiwapamitin/index.html` and raven: `docs/kahkakiw/index.html` for all the other folders in `docs`, using `allSigns.jpg`.

## Atomic Subtasks
1. Inventory `docs/` folders and identify which sign folders still need an `index.html`.
2. Compare the two exemplar pages, `docs/kiwapamitin/index.html` and `docs/kahkakiw/index.html`, to derive the required structure, interactions, and styling.
3. Extract authoritative metadata from `catalogue.json` and `docs/sign-object-spec.md`.
4. Use `allSigns.jpg` as a visual reference for sign artwork/theme cues, while avoiding fabricated language details.
5. Generate a reusable page template that can handle complete Cree data, partial Cree data, and placeholder cases.
6. Create `docs/{folder}/index.html` for every sign folder in `catalogue.json` that does not already have a page.
7. Preserve the existing hand-authored `docs/kiwapamitin/index.html` and `docs/kahkakiw/index.html`.
8. Check links, relative paths, page titles, back links, copied interaction behavior, and fallback text.
9. Update `docs/index.html` only if needed for links to new pages, without disturbing unrelated catalogue behavior.
10. Write a final integration report listing generated pages, assumptions, and follow-up data gaps.

## Dependency Graph
- Subtasks 1-4 can run in parallel.
- Subtask 5 depends on understanding the exemplars and metadata shape.
- Subtask 6 depends on the template and page inventory.
- Subtasks 8-10 depend on generated pages.
- Updating `docs/index.html` is conditional and must happen after page paths are known.

## Stream Allocation
| Manager | Stream Type | Subtasks | Dependencies | Async? |
|---------|-------------|----------|--------------|--------|
| M1 | parallel | Inventory folders, metadata, and assets | None | Yes |
| M2 | parallel | Exemplar/template analysis | None | Yes |
| M3 | serial | Generate missing pages | M1 and M2 outputs | After M1/M2 |
| M4 | serial | Integration and verification | M3 output | After M3 |

## Complexity Estimate
Large but mechanically tractable. There are roughly twenty sign folders with enough catalogue metadata to create useful pages, but some have incomplete Cree data or no image assets. The team should produce consistent pages with transparent placeholders rather than inventing language details. The main risks are overwriting hand-authored pages, generating broken relative links, and treating `assets/` or empty support folders as signs.

## Known Inputs
- Workspace root: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB`
- Exemplars:
  - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kiwapamitin/index.html`
  - `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/kahkakiw/index.html`
- Catalogue metadata: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/catalogue.json`
- Page/object spec: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/docs/sign-object-spec.md`
- Wall reference photo: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/allSigns.jpg`

## Target Sign Folders
Generate pages for catalogue folders other than `kahkakiw` and `kiwapamitin`, including:
`backbreaker`, `mistapiskihkoman`, `nicocwasaskanos`, `nipamayatan_pekiseyahk`, `loversLane`, `mamahtaw_askwew`, `sapwapahcikan-paskisikan`, `bedSprings`, `sôniyâwâhkêsîs`, `maskihkiwiyiniw`, `bobsled`, `purgatory`, `deliverance`, `ewok`, `FarmersDaughter`, `kakwa`, `ocayisinakes`, `oyoyow`, `nosemanicos`, `victoriaSecret`, and `slinky`.

Do not create sign pages for `docs/assets` or empty support folders such as `docs/cree` unless a corresponding catalogue model requires it.

## Acceptance Criteria
- Each generated sign page lives at `docs/{folder}/index.html`.
- Existing exemplar pages are not overwritten.
- Every generated page has `English • SRO • Syllabics` in the header when data exists, and honest fallback text when Cree data is missing.
- Every generated page includes a back link to `../index.html`.
- Generated pages include sections for word/phrase, sign design, trail information, related forms or data status, quick reference, and sources.
- Hover/copy interactions from the exemplars work for generated SRO/syllabics parts.
- Pages do not invent unchecked Cree forms. Missing language data is marked for review.
- Reports are written under `backgroundMaterial/agent2101/`.
