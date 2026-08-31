# Main Agent Guidance — 2219 → 2219-C

**Date:** 2026-06-10 22:40
**Re:** Difficulty research method (user directive)

The user has directed: instead of web search, fetch each trail's Trailforks page DIRECTLY using the `trailUrl` stored in `docs/catalogue.json` (the same URLs shown in the docs index editor).

Main Agent verified this works: the WebFetch tool successfully retrieves e.g. `https://www.trailforks.com/trails/bobsled-12400/` (curl from this machine is Cloudflare-403-blocked, but the agent web-fetch tool is not). The fetched page contains an explicit "Difficulty Rating" field and an FAQ line of the form "**X is rated as Blue difficulty**" — authoritative, no inference needed.

Instructions for M1:

1. Remaining trails (S2's half): fetch each `trailUrl` directly with the web-fetch tool; parse "Difficulty Rating" / "rated as ... difficulty". Fall back to search only if the page is login-gated/hidden.
2. Verify any S1 entries with confidence below high by direct fetch of their `trailUrl`.
3. Record `"source": "direct fetch of <url>"` and confidence high for values read off the page.

Token mapping reminder: Green→`green`, Blue→`blue`, Black Diamond→`black`, Double Black Diamond→`dblblack`.
