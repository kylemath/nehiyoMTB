# S2 Report — Trailforks Difficulty Research (batch 2 of 2)

**Sub-subagent:** S2, under Manager M1 (Data & Backend), Coordinator 2219-C
**Date:** 2026-06-10
**Task:** Determine official Trailforks difficulty ratings for 19 Edmonton river-valley MTB trails via direct WebFetch of each trail's Trailforks page.

## Results

| id | title | difficulty | source | confidence |
|---|---|---|---|---|
| victoria-secret | Victoria's Secret | blue | direct fetch of https://www.trailforks.com/trails/victoria-s-secret-10632/ | high |
| slinky | Slinky | blue | direct fetch of https://www.trailforks.com/trails/slinky-mid/ | high |
| scalpel | Scalpel | blue | direct fetch of https://www.trailforks.com/trails/scalpel/ | high |
| too_much | Too Much | blue | direct fetch of https://www.trailforks.com/trails/too-much/ | high |
| gnome_trail | Gnome Trail | blue | direct fetch of https://www.trailforks.com/trails/gnome-trail/ | high |
| sideline | Sideline | black | direct fetch of https://www.trailforks.com/trails/sideline/ | high |
| no_horses | No Horses | green | direct fetch of https://www.trailforks.com/trails/no-horses-10636/ | high |
| caddytrack | Caddytrack | blue | direct fetch of https://www.trailforks.com/trails/caddytrack-17761/ | high |
| the_holy_trail | The Holy Trail | blue | direct fetch of https://www.trailforks.com/trails/the-holy-trail-12414/ | high |
| flat_pete | Flat Pete | blue | direct fetch of https://www.trailforks.com/trails/flat-pete/ | high |
| walters_folly | Walters Folly | blue | direct fetch of https://www.trailforks.com/trails/walters-folly/ | high |
| moonraker | Moonraker | blue | direct fetch of https://www.trailforks.com/trails/moonraker-40151/ | high |
| go_trail | GO Trail | blue | direct fetch of https://www.trailforks.com/trails/go-trail/ | high |
| gold_digger | Gold Digger | blue | direct fetch of https://www.trailforks.com/trails/gold-digger-31547/ | high |
| peckers_hollow | Peckers Hollow | blue | direct fetch of https://www.trailforks.com/trails/peckers-hollow/ | high |
| coalminer_s_daughter | Coalminer's Daughter | null | no Trailforks URL provided; web searches found no Edmonton trail by this name; trailforks.com/trails/coalminer-s-daughter/ returns "Trail not found in database" | low |
| root_canal | Root Canal | blue | direct fetch of https://www.trailforks.com/trails/root-canal-10628/ | high |
| selkirk_knights | Selkirk Knights | black | direct fetch of https://www.trailforks.com/trails/selkirk-knights/ | high |
| flatter_pete | Flatter Pete | green | direct fetch of https://www.trailforks.com/trails/flatter-pete/ | high |

**Tally:** 18/19 resolved non-null (14 blue, 2 green, 2 black; 0 dblblack). 18 high confidence, 1 low (the null).

## Methodology

- Per the user directive, every trail with a URL was fetched DIRECTLY with the WebFetch tool. The fetched page body contained both an explicit "Difficulty Rating" field and the FAQ line "X is rated as <Y> difficulty"; the rating was read off both, and they agreed in every case.
- The official "Difficulty Rating" field was used, NOT "Voted Difficulty" (user votes) and NOT "Climb Difficulty". Notable divergences where this distinction mattered:
  - **Sideline**: official Black Diamond; voted Blue (5 votes). The page itself explains the black rating is for exposure risk above the river, not technicality. Recorded **black** (official).
  - **Flat Pete**: official Blue; voted Green (4 votes). Recorded **blue**.
  - **Walters Folly**: official Blue; voted Green (3 votes). Recorded **blue**.
  - **GO Trail**: official Blue; voted Black Diamond (1 vote). Recorded **blue**.
  - **Gold Digger**: official Blue; climb difficulty Black Diamond. Recorded **blue** (trail rating, not climb rating).
- Token mapping applied: Green → `green`, Blue → `blue`, Black Diamond → `black`, Double Black Diamond → `dblblack`.

## Page accessibility / failures

- **No pages were login-gated or hidden.** All 18 provided Trailforks URLs ultimately returned full public pages.
- Transient timeouts occurred on first attempt for 8 pages (victoria-s-secret, scalpel, too-much, the-holy-trail, moonraker, peckers-hollow, selkirk-knights, flatter-pete); all succeeded on retry (scalpel and peckers-hollow needed two retries). These were fetch timeouts, not Cloudflare blocks or auth gates.
- **coalminer_s_daughter** (no URL provided, marked `-`): fallback WebSearch found no Edmonton trail by this name on Trailforks, MTB Project, or local club sources (only the Loretta Lynn album/film and an unrelated Iowa trail). A guessed slug `coalminer-s-daughter` on Trailforks returned "Trail not found in database!". The repo's own docs (`docs/coalminer_s_daughter/index.html`) indicate this is a custom/locally-named trail (a Loretta Lynn nod), so no authoritative external rating exists. Recorded **null** per the never-guess rule.

## Tripartite self-assessment

- **Craftsperson says:** The 18 non-null values are as solid as this kind of research gets — each was read verbatim from the trail's own Trailforks page, cross-confirmed by two independent fields on the same page (the Details "Difficulty Rating" and the FAQ sentence), with zero disagreement between them. The direct-fetch method worked exactly as the user predicted; no inference was needed anywhere.
- **Skeptic says:** Three residual risks. (1) Trailforks ratings are crowd-maintained and can change; these values are a snapshot of 2026-06-10. (2) For trails where voted difficulty diverges from official (Sideline especially), a downstream consumer might actually want the community consensus rather than the official rating — I followed the spec (official rating) but flag the divergences above so M1 can decide. (3) The `slinky` id maps to the "Slinky - Mid" Trailforks page per the provided URL; there are also North/South Slinky segments that could in principle differ, but I treated the given URL as authoritative as instructed.
- **Mover says:** 18/19 at high confidence with documented sources meets all acceptance criteria; the one null is genuinely unresolvable from external sources (the trail name appears to be the user's own invention, like other Loretta Lynn-themed names in this repo). Nothing left to iterate — shipping. With more time I would only re-verify the Sideline black rating against EMBA's own materials for the downstream sign-color decision.
