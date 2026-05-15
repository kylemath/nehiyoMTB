# Sub-subagent S2 Notes — Sign #17 `kakwa` (porcupine)

**Agent:** S2 under Manager M3 (Agent 2148)
**Sign:** `kakwa` / `kâkwa` (ᑲᑲᐧ / ᑳᑿ) — Cree word for porcupine
**Date:** 2026-05-14

---

## 1. Trailforks search log

### Queries tried

1. `"Kakwa" trail Edmonton Trailforks mountain bike` — only returned generic Edmonton trail-network landing pages and the unrelated *Kakwa Wildland Provincial Park* (west-central Alberta, ~500 km from Edmonton).
2. `site:trailforks.com Kakwa Edmonton` — same: no Kakwa hits in any Edmonton region/sub-region listing.
3. `Kakwa porcupine trail Edmonton river valley singletrack` — no relevant trail; results pointed back at Kakwa Wildland and the *Cham Wow Epic* meta-route.
4. `"Porcupine" trail Edmonton Trailforks river valley mountain bike` — no Edmonton trail named *Porcupine*; top trails listed for Edmonton are Caddytrack, The Holy Trail, Happy Ending, etc.
5. `trailforks kakwa trail` — only the *Kakwa Falls* alltrails/trailpeak page (an OHV/hike route in Kakwa Wildland, far from Edmonton).
6. `Terwillegar Edmonton trail kakwa porcupine cree name` — surfaces *Maskêkosihk Trail* (the Cree-named roadway) but no MTB trail named Kakwa.

### Pages cross-grepped for `kakwa|porcupine|kâkwa`

- `https://www.trailforks.com/region/edmonton/` — no match
- `https://www.trailforks.com/region/edmonton/trails/` (top trails) — no match
- `https://www.trailforks.com/region/central-edmonton-north` — no match
- `https://www.trailforks.com/region/edmonton/reports` (recent reports) — no match
- `https://www.edmmtnbike.ca/trails` (Edmonton MTB Alliance landing) — no trail names listed at all (overview page only).

### Conclusion

**No confident match.** No Edmonton-area mountain bike trail named *Kakwa*, *Kâkwa*, or *Porcupine* appears on Trailforks or in the Edmonton Mountain Bike Alliance trail discussion. The only "Kakwa" trail-shaped result is **Kakwa Falls Trail** inside *Kakwa Wildland Provincial Park*, located ~160 km southwest of Grande Prairie (i.e. west-central Alberta, not Edmonton) — that is a hike / OHV route, not an Edmonton MTB trail.

**Recommendation to M3:** leave `trailforks: {}` (empty object) for this sign and add a `notes` entry such as:

> No Edmonton-area MTB trail named "Kakwa" or "Porcupine" found on Trailforks (searched 2026-05-14). The only namesake is Kakwa Wildland Provincial Park near Grande Prairie, which is geographically unrelated. The carved sign likely commemorates the Cree word `kâkwa` (porcupine) as cultural/linguistic content rather than naming an existing trail segment.

(Widget URL pattern is therefore not applicable for this sign.)

---

## 2. Cultural story

```json
{
  "heading": "About kâkwa — the Porcupine",
  "body": [
    "<strong>kâkwa</strong> (ᑳᑿ) is the Cree word for porcupine — a slow-moving, deeply self-possessed forest dweller of the boreal woods that stretch across nêhiyaw (Cree) territory. Unhurried and largely solitary, the porcupine is famously well-defended: rather than fight or flee, it lowers its head, raises its quills, and lets any aggressor make the mistake of pressing in. Cree teachings often hold up <strong>kâkwa</strong> as a quiet model of patience and gentle strength — protection through stillness rather than aggression, and the wisdom of knowing when not to move.",
    "Long before glass beads arrived through the fur trade, porcupine quillwork was one of the most refined craft traditions of the Plains and Woodlands peoples, including the Cree. Quills were plucked, soaked, dyed with pigments drawn from roots, berries, lichens and ochres, then softened in the mouth, flattened with the teeth, and woven, wrapped, or sewn onto tanned hide, birchbark, moccasins, pipe stems, and lidded boxes. The geometric and floral patterns that later flourished in beadwork were first carried by quills — making <strong>kâkwa</strong> not only a forest neighbour but a literal source of artistic material, generously offered by an animal that asked only to be approached with care.",
    "The red, black, and white of this trail sign carry an echo of those older quill-dye palettes — earth reds, charcoal blacks, and undyed natural whites that recur across many Indigenous quillwork traditions. (We note this resonance gently, as a visual rhyme rather than a claim about any specific tribal recipe.) Riding past <strong>kâkwa</strong> here in the river valley, it is worth pausing to remember an animal that taught generations of artists how to make beauty out of patience, and how to defend a small life with quiet, deliberate care."
  ]
}
```

---

## 3. Sources

- Trailforks Edmonton region — https://www.trailforks.com/region/edmonton/
- Trailforks Edmonton trails — https://www.trailforks.com/region/edmonton/trails/
- Trailforks Central Edmonton (North) — https://www.trailforks.com/region/central-edmonton-north
- Edmonton MTB Alliance — https://www.edmmtnbike.ca/trails
- Kakwa Wildland Provincial Park — https://www.albertaparks.ca/parks/north/kakwa-wpp/
- AllTrails: Kakwa Falls Trail — https://www.alltrails.com/trail/canada/alberta/kakwa-falls-trail
- City of Edmonton: Indigenous Place Names — https://data.edmonton.ca/api/views/59sa-iw7i/rows.pdf
- Edmonton Journal: "Major Edmonton road first to bear Cree name" (Maskêkosihk Trail) — https://edmontonjournal.com/business/local-business/major-edmonton-road-first-to-bear-cree-name

General cultural background on porcupine quillwork drawn from accumulated knowledge of Plains/Woodlands Indigenous craft traditions; no single online source was lifted for the prose. If M3 wants verifiable citations for the cultural body, recommended next steps: Royal Alberta Museum / Glenbow porcupine-quillwork exhibit pages, or the *Encyclopedia of Saskatchewan* entry on quillwork.

---

## 4. Uncertainties / flags

- **Trailforks negative result is search-based, not API-confirmed.** I did not call the Trailforks search API directly, so it is *possible* a small/private/recently-added trail named *Kakwa* exists and simply does not surface in web search. Confidence in "no Edmonton MTB Kakwa trail" is roughly 90%, not 100%. M3 may want to manually check trailforks.com search if a higher-confidence answer is needed.
- **Color-palette / quill-dye link is speculative.** The third paragraph notes that red/black/white echoes traditional quill-dye palettes. This is true in the broad sense (those colors recur in many Indigenous craft traditions across North America), but I have not verified that the sign's specific palette was *intended* to reference quillwork. The paragraph flags this explicitly with "We note this resonance gently…" — please preserve that hedge if the text is edited.
- **No tribe-specific sacred story is included.** I deliberately avoided attributing a particular trickster/teaching narrative to a specific nation, since I cannot verify any single version. If M3 has a verified Cree teaching about `kâkwa` from a community source, it could be substituted into paragraph 1 or appended.
- **Spelling.** Catalogue lists `creeName: "kakwa"` and `creeSyllabics: "ᑲᑲᐧ"`. The more common SRO spelling for porcupine is `kâkwa` (with macron/circumflex on first `a`) and the more common syllabics are `ᑳᑿ`. The cultural story uses the macron form; M3 may want to either (a) keep the catalogue's bare-vowel spelling for consistency or (b) update the catalogue to the macron form. I recommend (b) for linguistic correctness, but it is M3's call.

---

## 5. Tripartite self-assessment

**Craftsperson says:**
The cultural-story prose is solid: it stays grounded in widely-attested facts (porcupine biology, quillwork as a pre-bead craft tradition, the symbolic register of patience/protection), uses correct Cree orthography, and weaves in the sign's color palette in a way that feels natural rather than forced. The Trailforks negative result is well-supported by six distinct queries and direct grep checks of the Edmonton region pages — I'm confident in that conclusion.

**Skeptic says:**
The "no Edmonton MTB Kakwa trail" finding rests on web-search visibility; I did not hit Trailforks' internal search API directly, and a small or private trail could in principle have been missed. The color/quill-dye paragraph is the weakest link in the cultural story — it's a plausible visual rhyme, not a verified intent, and even with the hedge ("We note this resonance gently") a reviewer steeped in quill traditions might find it presumptuous. The cultural prose also lacks named primary sources; it leans on accumulated general knowledge, which is appropriate for a sign blurb but would not survive an academic citation review. Finally, the catalogue spelling `kakwa` vs. the more orthographically standard `kâkwa` is a real inconsistency I am punting to M3.

**Mover says:**
These risks are clearly flagged and tractable for downstream review. The Trailforks finding is firm enough to ship as `trailforks: {}` with a notes entry; if anyone wants stronger evidence, a 30-second manual check on trailforks.com search will confirm. The cultural body is good enough to publish on the sign page — respectful, factually grounded, hedged where it speculates, and the right length for a plaque-side blurb. I am proceeding to deliver this output to M3 now rather than spinning further on the color-symbolism wording or trying to chase down a primary quillwork citation; M3 can elect to tighten either if they wish.
