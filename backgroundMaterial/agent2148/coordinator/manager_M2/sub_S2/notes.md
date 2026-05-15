# Sub-S2 Notes — Back Breaker (Sign #2)

Agent 2148 / Manager M2 / Sub-subagent S2
Sign slug: `backbreaker` · SRO: `kaskâwikanênêw` · Theme color: `#dc3545` (red)

---

## 1. Trailforks Search Results

### Queries tried
- `"Back Breaker" Edmonton mountain bike Trailforks`
- `"back-breaker" trailforks Hawrelak trail id`
- Direct fetch of `https://www.trailforks.com/region/hawrelak-33290/`
- Direct fetch of `https://www.trailforks.com/trails/back-breaker/`
- Sanity check via widget URL `?trailname=back-breaker` (Trailforks rejected — confirms `trailid` is required, not slug)

### Candidate trails
Only one strong match surfaced for "Back Breaker" in the Edmonton region:

| Match | Region | Slug | Trail ID | Notes |
|---|---|---|---|---|
| **Back Breaker** | Hawrelak, Northwest Edmonton, AB | `back-breaker` | **10634** | Companion to Root Canal in MacKinnon Ravine; Blue difficulty; XC singletrack; downhill primary; built by `mtnbikermitch` & contributors. This is the canonical pick. |
| Lower Back Breaker | Hawrelak, Edmonton | `lower-back-breaker` | (not retrieved) | A nearby, beginner-rated companion trail. Almost certainly NOT what the plaque refers to — "Back Breaker" (no "Lower") is the named, more aggressive trail and the one a sign would commemorate. |

### Final pick

```json
{
  "trailforks": {
    "trailId": 10634,
    "trailUrl": "https://www.trailforks.com/trails/back-breaker/",
    "widgetUrl": "https://www.trailforks.com/widgets/trail/?trailid=10634&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1",
    "displayName": "Back Breaker"
  }
}
```

### Trail facts (for use by the page author if helpful)
- Riding area: **Hawrelak**, Northwest Edmonton, Alberta
- Trailhead coordinates: **53.53816, -113.56543** (under the 142nd Street Bridge, MacKinnon Ravine)
- Length: ~549 m (1,801 ft); descent ~27 m; avg time ~3:45
- Difficulty: **Blue**; Physical rating: Moderate; TTFs: Drop
- Direction: Downhill primary, XC singletrack
- Description (from Trailforks): *"The companion to Root Canal this trail continues to traverse the rooty Mckinnon Ravine. Large berms help increase the flow on this technical trail."*
- Trail association: **Edmonton Mountain Bike Alliance** (EMBA)
- Builder / contributor of record: **mtnbikermitch** & contributors
- Trailforks views: 6,294 · Ride check-ins: 8,087 · All-time rides: 1,174 (popular trail)
- Indigenous land acknowledgement listed on the trail page: **ᓀᐦᐃᔭᐤ ᐊᐢᑭᕀ Nêhiyaw-Askiy (Plains Cree)**, Tsuu T'ina, Michif Piyii (Métis), Cree

---

## 2. Cultural Story Draft (`culturalStory`)

```json
{
  "heading": "Spine of the Trail",
  "body": [
    "In mountain-bike vernacular, a trail earns the name <strong>Back Breaker</strong> by feel — by the rooty, rattling sections that hammer your spine through the bars, by the line that punishes a lazy posture and rewards a loose grip. The trail of that name drops through MacKinnon Ravine on Edmonton's west side as the rooty companion to Root Canal: short, sharp, and unforgiving enough that the name has stuck for years among the local riders who built and maintain it.",
    "The plaque leans into that joke literally. A single white vertebra dangles like a charm against the black field, ringed with red the way a sore spine glows after a hard run. The accompanying parts in this sign's set — a five-vertebra column and a length of chain — push the pun further: a backbone built like a bike chain, each link a vertebra, the rider's spine and the bike's drivetrain merged into one rattling assembly. Red on black is the working-shop palette of grease, rust, and warning tape; the white SRO and English text keep the language clearly legible against it.",
    "The Cree reading <strong>kaskâwikanênêw</strong> carries the same idea in its own register — it points toward the act of breaking the back, or the one who breaks it — and the syllabics above the SRO are picked out in the same red as the vertebra's accents, so the language and the image read as a single gesture. The sign sits on <strong>ᓀᐦᐃᔭᐤ ᐊᐢᑭᕀ Nêhiyaw-Askiy</strong> (Plains Cree territory), and is part of an Edmonton-area effort to put Plains Cree names back on the everyday landscape of trails that riders here have known by their English nicknames for a long time."
  ]
}
```

### Inline-tag check
- All `<strong>...</strong>` are inline. No block-level tags. Safe for `culturalStory.body`.
- 3 paragraphs, all under ~120 words each.

---

## 3. `trailStory` Draft (optional)

Most builder/history detail surfaced is thin (single contributor handle `mtnbikermitch`, EMBA as the association). Rather than overcommit to a builder narrative I cannot verify, I'm leaving this empty and letting `culturalStory` carry the weight.

```json
{
  "trailStory": {
    "heading": "",
    "body": []
  }
}
```

If the page author wants a short, factual `trailStory` block instead, a safe minimal draft would be:

```json
{
  "trailStory": {
    "heading": "Where It Runs",
    "body": [
      "Back Breaker drops through MacKinnon Ravine on Edmonton's northwest side, in the Hawrelak network of trails along the river valley. Riders typically pick it up under the 142nd Street Bridge and ride it as the natural follow-on to <strong>Root Canal</strong> — a short (~550 m), rooty, blue-rated descent with bermed corners and a single drop feature. It is a popular and well-loved trail, with thousands of recorded rides logged by the local community.",
      "The trail is maintained by the <strong>Edmonton Mountain Bike Alliance</strong> and the riders who show up with rakes and shovels each spring. If this sign reads to you on the trail, consider giving back to the people who keep the dirt rideable."
    ]
  }
}
```

(Use or discard at the page author's discretion. Keeping the primary recommendation as the empty `trailStory` to keep the page tight.)

---

## 4. Sources Consulted

- `https://www.trailforks.com/region/edmonton/trails/` — confirmed `Back Breaker` lives in Hawrelak region.
- `https://www.trailforks.com/region/hawrelak-33290/` — confirmed Hawrelak hosts both `Back Breaker` and `Lower Back Breaker`, plus the Cree-named neighbor `ᓅᓭᒪᓂᒎᐢ - nôsemanicôs - Ladybug` (consistent with this sign series).
- `https://www.trailforks.com/trails/back-breaker/` — primary source: confirmed trail ID **10634** (via `embed Back Breaker trail on your website` link `?trailid=10634` and `#10634 - 6,294 views`), description, builder, riding area, indigenous land listing.
- `https://www.trailforks.com/region/edmonton/reports` — corroborated `Back Breaker` is in `Hawrelak`.

---

## 5. Uncertainties

- **Cree morphology / gloss.** I leaned on the meaning "the one that breaks / breaks the back" without committing to specific morphemes. M2 is running the linguistic analysis of `kaskâwikanênêw` in parallel; if M2's reading differs (e.g., "*it* breaks the back" or a more specific kinetic sense), the third paragraph of `culturalStory` should be adjusted to match.
- **Trail-builder narrative.** Trailforks lists `mtnbikermitch & contributors` as the trail's author of record, but I have no independent source on who built it or when, so I did not name them in the prose. EMBA is mentioned as the trail association in the optional `trailStory` only because that is straightforwardly verifiable on Trailforks.
- **`Lower Back Breaker` ambiguity.** There is a `Lower Back Breaker` trail in the same network. I am 95%+ confident the sign refers to the main `Back Breaker` (the named, harder, more iconic line), not the lower variant. If the sign installation site is actually at the entrance to the *Lower* variant, this should be revisited.
- **Vertebra-as-chain pun.** I am inferring the design intent from the filenames (`5_Vertebrae_Plain.stl`, `Chain.stl`) plus the dangling-vertebra graphic on the plaque. If the artist's intent is documented elsewhere (e.g., a different metaphor — chain as bicycle drivetrain *only*, not spine-as-chain), the second paragraph should be softened.
- **"Edmonton-area" framing.** Specifically northwest Edmonton / MacKinnon Ravine / Hawrelak network — the cultural story stays general ("Edmonton's west side") to avoid pinning to one bridge crossing.

---

## 6. Tripartite Self-Assessment

**Craftsperson says:**
The Trailforks pick is unambiguous — trail ID `10634` came directly from two independent fingerprints on the trail's own page (the `embed` widget config URL and the trail number footer). The widget URL is built strictly from the template M2 supplied, with only the trail ID substituted. The cultural story keeps the visible design (black/red/white palette, vertebra graphic, chain motif, paired STLs) tightly anchored to the trail name, names the Cree word and lets it speak without overreaching on morphology, and acknowledges the territory in the same language the trail page itself does. Inline `<strong>` tags only; no block tags.

**Skeptic says:**
The Cree gloss is the weakest link. I'm trusting M2's running translation ("back breaker / the one that breaks the back") and softening with "carries the same idea" / "points toward" hedges, but if M2's morphemic breakdown comes back narrower (e.g., a specific verb stem or transitive/intransitive distinction), the paragraph will need a quick rewrite. The `Lower Back Breaker` sibling trail is a small risk vector I cannot fully eliminate without seeing where the physical sign is installed. I also did not verify the builder identity beyond the Trailforks handle, so I deliberately omitted any name attribution from the prose to avoid getting it wrong.

**Mover says:**
Shipping. Trail ID `10634` is verified, the widget URL is template-correct, and the cultural story is conservative enough to survive M2's linguistic refinement without a full rewrite — at worst, the third paragraph gets a one-sentence patch. Page author can drop these blocks straight into `pageContent.json`. Items to revisit with more time: the `Lower Back Breaker` disambiguation, M2's final morpheme analysis for `kaskâwikanênêw`, and a one-line builder credit if EMBA or `mtnbikermitch` can be independently verified.
