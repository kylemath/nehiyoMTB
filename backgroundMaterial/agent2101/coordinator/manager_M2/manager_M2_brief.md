# Manager M2 Brief

## Assignment

Manager 2101-M2 analyzes the two existing individual sign pages and produces a reusable template/contract for generated pages in the nehiyoMTB repository.

## Inputs

- `docs/kiwapamitin/index.html`
- `docs/kahkakiw/index.html`
- `docs/sign-object-spec.md`
- `catalogue.json`

## Constraints

- Do not edit generated HTML pages or exemplar pages.
- Write coordination artifacts only under `backgroundMaterial/agent2101/coordinator/manager_M2/`.
- Preserve the current exemplar behavior closely enough that Manager M3 can generate new pages without overwriting hand-authored exemplars.
- Treat `catalogue.json` as the source of truth for page data wherever possible.

## Required Analysis

- Distill common page structure, CSS tokens/classes, header and back-link behavior, content sections, quick-reference requirements, sources, fallback language behavior, and hover/copy JavaScript behavior.
- Identify fields that must be data-driven from `catalogue.json`: title, English, SRO, syllabics, colors, description, docs STL path or fallback STL, image path, and color layers.
- Recommend a standalone generated-page template that matches the exemplars but remains generic for partial data and missing images.

## Deliverable

Write `manager_M2_report.md` with implementation guidance, acceptance checks, pitfalls to avoid, and self-assessment using the requested Craftsperson/Skeptic/Mover dialogue.
