# S1 Report — Trailforks Difficulty Research (Batch 1 of 2)

**Sub-subagent:** S1 (Trailforks Difficulty Research) · **Manager:** M1 (Data & Backend) · **Coordinator:** 2219-C
**Date:** 2026-06-10
**Scope:** 19 Edmonton river-valley MTB trails

## Results

| id | title | difficulty | source | confidence |
|---|---|---|---|---|
| kahkakiw | Kahkakiw (Raven) | blue | Trailforks trail-page FAQ snippet (raven-146421) | high |
| backbreaker | Back Breaker | blue | Trailforks trail-page FAQ snippet (back-breaker) | high |
| mistapiskihkoman | Machete | black | Trailforks trail-page FAQ snippet (machete) | high |
| nicocwasaskanos | Six Shooter | blue | Trailforks trail-page FAQ snippet (six-shooter) | high |
| nipamayatan-pekiseyahk | Purple Haze | blue | Direct fetch of trailforks.com/trails/purple-haze-15797/ | high |
| lovers-lane | Lovers Lane | blue | Trailforks trail-page FAQ snippet (lovers-lane-15796) | high |
| mamahtaw-iskwew | Wonder Woman | blue | Trailforks trail-page FAQ snippet (wonder-woman) | high |
| sapwapahcikan-paskisikan | Ray Gun | blue | Trailforks trail-page FAQ snippet (ray-gun-201396) | high |
| bed-springs | Bed Springs | black | Direct fetch of trailforks.com/trails/bed-springs/ | high |
| soniyawahkesis | Silverfox | null | Not on Trailforks (see notes) | low |
| maskihkiwiyiniw | Medicine Man | black | Trailforks trail-page FAQ snippet (maskihkiwiyiniw-medicine-man) | high |
| bobsled | Bobsled | blue | Trailforks trail-page FAQ snippet (bobsled-12400) | high |
| purgatory | Purgatory | dblblack | Secondary source: toronto.com Edmonton MTB feature ("a double black diamond trail") | medium |
| deliverance | Deliverance | black | Trailforks trail-page FAQ snippet (deliverance-13244) + crankys.ca mirror | high |
| farmers-daughter | Farmer's Daughter | black | Direct fetch of trailforks.com/trails/the-farmer-s-daughter-60234/ | high |
| kakwa | Kakwa (Porcupine) | black | Trailforks trail-page FAQ snippet (kakwa-porcupine-322561) | high |
| kiwapamitin | I See You | blue | Direct fetch of trailforks.com/trails/i-see-you/ | high |
| oyoyow | Oyoyow (Howl) | black | Direct fetch of trailforks.com/trails/oyoyow-howl/ | high |
| nosemanicos | Nosemanicos (Ladybug) | black | Trailforks trail-page FAQ snippet (nosemanicos-ladybug-703615) | high |

**Totals:** 18/19 resolved non-null · 17 high confidence · 1 medium (Purgatory) · 1 null (Silverfox).
**Breakdown:** 9 blue, 8 black, 1 dblblack, 1 null. No green trails in this batch.

## Methodology

1. **Primary method — WebSearch with Trailforks FAQ phrasing.** Trailforks trail pages embed a "How hard is X?" FAQ ("X is rated as <Color> difficulty"), which surfaces reliably in search snippets. Searches of the form `trailforks "<name>" Edmonton mountain bike trail difficulty` resolved 11 trails with explicit, exact-trail snippet text.
2. **Fallback — direct WebFetch of Trailforks trail pages.** Contrary to expectation, direct fetches of trailforks.com succeeded intermittently (some timeouts, ~50% success after retries). This resolved Purple Haze, I See You, Oyoyow/Howl, Bed Springs, and The Farmer's Daughter with first-party page data, upgrading them to high confidence. The Purple Haze page also confirmed the Cree alias "nîpâmâyâtân pekiseyâhk", validating the id mapping.
3. **Disambiguation care.** Several names collide with other trails: "Six Shooter to Machete Access" (a paved access path, easy) vs. "Six Shooter" proper (blue); "Lower Back Breaker" (green) vs. "Back Breaker" (blue); "Lower Bed Springs" (blue) vs. "Bed Springs" (black); Wonder Woman in Canberra, Silver Fox in Colorado/Pennsylvania. In every case I matched on the exact slug from the assigned Trailforks URL and the Edmonton/Hawrelak/Keillor/Whitemud region context.
4. **Secondary sources.** crankys.ca (an Edmonton bike shop that mirrors Trailforks descriptions) corroborated Deliverance and Bed Springs as black diamond. toronto.com's Edmonton MTB feature supplied the Purgatory rating.

## Unresolved / problem trails

- **soniyawahkesis (Silverfox) — null.** No Trailforks URL was provided (`-`) and searches confirm no Trailforks trail page exists under either name. The name "Silver Fox" appears only in user trail reports attached to the permanently closed/decommissioned "EM Descent" trail (Central Edmonton South), suggesting locals use the name for that corridor, and in a Pacer walking-app route (no MTB difficulty). Recording null per the no-guessing rule.
- **purgatory — medium confidence.** The Trailforks page (purgatory-81341) returns "Login required" on fetch — it appears to be a hidden/unsanctioned trail on Trailforks, and no search snippet exposes its FAQ rating. The only explicit rating found is a toronto.com travel feature about Edmonton river-valley riding that calls Purgatory "a double black diamond trail." Recorded `dblblack` at medium confidence; M1 may wish to verify with a logged-in Trailforks account.

## Tripartite Self-Assessment

- **Craftsperson says:** 17 of 19 ratings come from exact-trail, first-party Trailforks FAQ text ("X is rated as ... difficulty") — either from a direct page fetch or a verbatim search snippet of the trail's own page, matched against the exact slug assigned to me. The disambiguation traps (Lower Back Breaker, Lower Bed Springs, Six Shooter Access, out-of-province name twins) were identified and avoided. The JSON validates and uses only the permitted tokens.
- **Skeptic says:** Search-synthesis text sometimes asserted ratings the visible snippets didn't support (early syntheses claimed Bed Springs was blue and attributed Farmer's Daughter's rating to a neighboring trail's page) — I refused those and escalated to direct fetches, but it's a reminder that synthesized answers can hallucinate; only verbatim FAQ text was trusted. Purgatory rests on a single journalist's characterization, and there are multiple Purgatory trails in the world — though the article is unambiguously about Edmonton's river valley. Trailforks ratings also drift over time as users vote; these values are a snapshot as of 2026-06-10.
- **Mover says:** 18/19 resolved with a defensible evidence trail is a strong result; the remaining null (Silverfox) genuinely has no Trailforks presence, so further searching has diminishing returns. Shipping now with Purgatory flagged at medium confidence for optional logged-in verification by M1.
