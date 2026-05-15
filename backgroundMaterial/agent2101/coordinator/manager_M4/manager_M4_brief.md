# Manager M4 Brief: Integration and Verification

## Assignment

Verify integration and catalogue wiring for the generated individual sign pages in `docs/{folder}/index.html`, excluding the hand-authored `kahkakiw` and `kiwapamitin` pages from generation acceptance while confirming they remain preserved.

## Target Pages

`backbreaker`, `mistapiskihkoman`, `nicocwasaskanos`, `nipamayatan_pekiseyahk`, `loversLane`, `mamahtaw_askwew`, `sapwapahcikan-paskisikan`, `bedSprings`, `sôniyâwâhkêsîs`, `maskihkiwiyiniw`, `bobsled`, `purgatory`, `deliverance`, `ewok`, `FarmersDaughter`, `kakwa`, `ocayisinakes`, `oyoyow`, `nosemanicos`, `victoriaSecret`, and `slinky`.

## Inputs

- `catalogue.json`
- `docs/sign-object-spec.md`
- `docs/index.html`
- Generated target page files under `docs/`
- Existing exemplar pages `docs/kahkakiw/index.html` and `docs/kiwapamitin/index.html`
- `backgroundMaterial/agent2101/coordinator/manager_M3/manager_M3_report.md`

## Verification Plan

1. Confirm each target page exists and no stray generated page exists at `docs/assets/index.html` or `docs/cree/index.html`.
2. Confirm exemplar pages remain present and retain hand-authored content.
3. Check generated page structure for required sections, back link, source section, quick reference, language display, and design/trail/status sections.
4. Check SRO/syllabics pages for matching `data-key` hover/copy wiring, and missing-syllabics pages for a pending-review fallback.
5. Check generated pages for broken `<img>` references and verify STL download links resolve under each page folder where possible.
6. Check `docs/index.html` page-link wiring and preferred viewer STL paths against existing `docs/stl-manifest.json` entries.
7. Run a lightweight syntax/static pass where practical.
8. Write `manager_M4_report.md` with results, fixes, residual risks, and tripartite self-assessment.

## Delegation Decision

No sub-subagents are planned initially. The task is broad but mechanically verifiable, and keeping the checks in one local pass reduces coordination overhead. If a systemic issue appears, sub-subagents may be used for focused follow-up under this folder.
