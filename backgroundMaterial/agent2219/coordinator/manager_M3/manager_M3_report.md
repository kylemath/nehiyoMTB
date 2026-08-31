# Manager 2219-M3 Report — Difficulty field in web catalogue editor

## Stream Summary

Added a per-trail "Difficulty" `<select>` (`#content-trail-difficulty`) to the Trailforks panel of the web catalogue editor (`docs/index.html`), and wired it into both the form **load** path (populating from `pageContent.trailforks.difficulty`) and the form **save** path (writing `trailforks.difficulty` when a value is chosen, omitting/deleting it when "Unknown" is selected). No other files were touched; the export tool and `catalogue.json` were left strictly alone, per the brief.

## Files changed

### `docs/index.html` (only file changed)

| Region (post-edit lines) | What | Why |
|---|---|---|
| ~2249–2258 (inside `#content-trailforks-panel`, after the widget-URL field) | New `content-field` div with `<label>` + `<select id="content-trail-difficulty">` containing options `""`→Unknown, `green`→"Green — easy", `blue`→"Blue — intermediate", `black`→"Black diamond — advanced", `dblblack`→"Double black — expert" | The UI control. Markup mirrors neighbouring `content-field` rows and the existing select pattern used by `#content-map-embed-mode`. |
| ~5208 (`CONTENT_INPUT_IDS` array) | Added `'content-trail-difficulty'` after `'content-trail-widget'` | Existing pattern: every form control is listed here so `setContentInputsDisabled()` disables it during saves. |
| ~5731 (`fill...Form` / model-select population, right after `content-trail-widget` is set) | `document.getElementById('content-trail-difficulty').value = content.trailforks.difficulty || '';` | LOAD wiring — same `getElementById(...).value = x || ''` style as adjacent lines. |
| ~5818–5823 (`collectContentFromForm()`, immediately after the `trailforks` object is assembled) | Reads the select; `trailforks.difficulty = value` when non-empty, `delete trailforks.difficulty` when empty | SAVE wiring. Placed after the trailforks/strava ternary so difficulty is persisted regardless of trail source (the hidden select retains its loaded value in strava mode, so the field survives round-trips). |

Note: the brief pointed at "save logic around line 5363". That region turned out to be the GPX upload handler (which mutates `selectedModel.pageContent.trailforks` directly for track geometry only). The actual form→`trailforks` save path is `collectContentFromForm()` (~line 5759+), which builds the object fresh; that is where the save wiring belongs and was added. The upload handler needs no change — it doesn't touch difficulty.

## Acceptance criteria check

- [x] `<select id="content-trail-difficulty">` exists exactly once in the Trailforks panel with the five specified options — verified by grep (one `<select>` occurrence, line 2251).
- [x] Load path sets the select from `trailforks.difficulty || ''` (line 5731).
- [x] Save path writes `trailforks.difficulty` when non-empty and deletes it when empty (lines 5818–5823).
- [x] Matches surrounding markup/JS patterns (`content-field` div, `getElementById` style, `CONTENT_INPUT_IDS` registration).
- [x] No other panels touched; no reformatting; no changes to `tools/export_trails_for_app.py` or `docs/catalogue.json`.
- [x] Verification: `grep -n content-trail-difficulty` shows the id in markup (2250/2251), input-id list (5208), load (5731), and save (5818). `python3 html.parser` feed of the whole file ran without exception. Inline app script extracted and passed `node --check` (the only "failing" script block is the JSON import map, which is expected to fail a JS syntax check and was not modified).

## Issues

- None blocking. One design note: because the difficulty select lives inside `#content-trailforks-panel`, it is hidden when the trail source is Strava — but its value is still loaded and saved, so difficulty round-trips correctly for Strava-sourced trails; it just isn't editable in that mode. This matches the brief's placement instruction; if Strava trails need editable difficulty, the field could later be moved outside the source-specific panels.
- The `delete trailforks.difficulty` branch is technically a no-op (the object is freshly constructed in `collectContentFromForm`), but it is kept for explicitness and robustness against future refactors that might reuse an existing object.

## Self-Assessment

- **Craftsperson says:** The change is small, surgical, and pattern-faithful — every line matches an adjacent idiom in the file (the `content-field` row, the `|| ''` load style, the `CONTENT_INPUT_IDS` registration). I read all three code regions before touching them, and the save placement (after the source ternary) means difficulty survives regardless of trail source.
- **Skeptic says:** The brief's "line 5363" pointer was stale/misleading — I verified it was the GPX upload handler and consciously wired the real save path instead; if the coordinator expected a literal edit there, that should be reconciled. Also, I did not do a live browser round-trip test (the editor requires its local API server); verification is static (grep, HTML parse, `node --check`). The hidden-in-Strava-mode caveat is documented above.
- **Mover says:** Static verification covers the realistic failure modes for a 4-region edit of this kind (typo'd id, broken markup, JS syntax error), and all pass. Shipping now; a live smoke test of load→edit→save in the running editor is the one thing I'd add with more time.
