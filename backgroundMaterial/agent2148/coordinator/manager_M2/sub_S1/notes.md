# Sub-S1 (Manager M2, Agent 2148) — Back Breaker (`kaskâwikanênêw`)

Sign #2 of nehiyoMTB. Author: sub-subagent S1.

---

## 1. Physical sign transcription

Source images:
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/sub_S1/backbreaker_crop.jpg` (full plaque crop)
- `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/backgroundMaterial/agent2148/coordinator/manager_M2/sub_S1/backbreaker_syllabics_zoom.jpg` (2× upscale of the syllabics row)

The plaque is a black rectangular board, oriented portrait, mounted to a white/off-white wall. Reading top to bottom:

| Element | Carved text / form | Colour |
| --- | --- | --- |
| SRO (top) | `kaskâwikanênêw` | white |
| Cree syllabics (mid-upper) | `ᑲᐢᑳᐏᑲᓀᓀᐤ` | red |
| Sculpted graphic (centre) | A 3-D lumbar-style **vertebra** in white with red accents along the spinous and transverse processes; the body of the vertebra has a small central hole/foramen. A red drip/streak runs down the side of the vertebra body, evoking blood/injury. | white + red |
| English caption (bottom) | `Back Breaker` (two lines: "Back" / "Breaker") | white on black |

I did **not** see a chain element actually attached to the Back Breaker plaque in this crop — the chain that appears in the project STLs (`Chain.stl`) and the catalogue render is either a separate sculpt below the visible area or omitted from this particular mount. A small fragment of red text/sign for the *next* plaque (`oyoyow`, the porcupine) is visible at the bottom-left of the crop and should be ignored.

### Syllabics — character-by-character read

Reading the upscaled zoom left → right (8 glyphs total):

| # | Glyph | Value | Notes |
| --- | --- | --- | --- |
| 1 | ᑲ | `ka` | bare "b"-form, no diacritic |
| 2 | ᐢ | `s` | small superscript / final |
| 3 | **ᑳ** | **`kâ`** | b-form **with a clear small dot above** — this is the long-â dot, NOT a screw head (the screw is offset higher and to the right, plus there is a separate visible dot above the glyph itself) |
| 4 | ᐏ | `wi` | triangle with the w-dot above |
| 5 | ᑲ | `ka` | bare b-form (no dot) — confirms #3 is intentionally different |
| 6 | ᓀ | `nê` | |
| 7 | ᓀ | `nê` | identical twin of #6 |
| 8 | ᐤ | `w` | small superscript final circle |

### Discrepancies vs. `catalogue.json`

The current catalogue entry for this sign carries:

- SRO: `kaskawikanênêw` (no circumflex on the third `a`)
- Syllabics: `ᑲᐢᑲᐏᑲᓀᓀᐤ` (third character is plain `ᑲ`)

The **physically carved sign** has:

- SRO: `kaskâwikanênêw` (circumflex on third `a`)
- Syllabics: `ᑲᐢᑳᐏᑲᓀᓀᐤ` (third character is `ᑳ`, with the long-â dot)

The plaque is **internally consistent** (SRO long-â on `kâ` ↔ syllabics dot on `ᑳ`); the catalogue is the one that is missing the diacritic, in both orthographies, in matched positions. Recommend M2 update the catalogue + page to match the plaque, and treat `kaskâwikanênêw` / `ᑲᐢᑳᐏᑲᓀᓀᐤ` as canonical.

This also matches **itwêwina** (Wolvengrey / CW), which lists `kaskâwikanênêw` as a dictionary headword with the gloss *"s/he breaks s.o.'s back by hand"*.

---

## 2. Morpheme draft (for `primarySection.morphemes`)

The verb is **VTA** (Verb Transitive Animate), with body-part incorporation via the medial `-wikan-` "back/spine". Parallel-construction reference: `pîkonêw` "s/he breaks him/her by hand" (`pîkon-` + `-êw`), where the same `-n-ê-w` tail surfaces.

```json
[
  {
    "key": "kaskaa-init",
    "sro": "kaskâ-",
    "syllabics": "ᑲᐢᑳ",
    "gloss": "initial: snap, break across, break in two (the same initial occurs in many ‘snap/break-rigidly’ verbs, e.g. kaskâcihtin ‘it breaks right off’, kaskâwikanisin ‘s/he breaks his/her own back falling’)"
  },
  {
    "key": "wikan-med",
    "sro": "-wikan-",
    "syllabics": "ᐏᑲᐣ",
    "gloss": "body-part medial: back, spine, backbone (incorporated form of the noun wîkan ‘back’; the long î shortens in medial position)"
  },
  {
    "key": "e-connect",
    "sro": "-ê-",
    "syllabics": "ᐁ",
    "gloss": "connective / thematic vowel"
  },
  {
    "key": "n-manual",
    "sro": "-n-",
    "syllabics": "ᐣ",
    "gloss": "VTA manual final: ‘by hand, by direct manipulation’ (same -n- as in pîkonêw ‘breaks him by hand’)"
  },
  {
    "key": "ew-3to3p",
    "sro": "-êw",
    "syllabics": "ᐁᐤ",
    "gloss": "VTA 3→3′ indicative suffix: ‘he/she does it to him/her (animate object)’"
  }
]
```

Surface-segmentable as `kaskâ-wikan-ê-n-ê-w`.

Free translation: **"S/he breaks his/her back (by hand)."** The English place-name caption *Back Breaker* is the agent-noun-ish gloss ("the one that breaks the back").

---

## 3. `relatedForms` draft

```json
[
  {
    "english": "back, spine, backbone (the body-part itself)",
    "sro": "wîkan",
    "syllabics": "ᐑᑲᐣ",
    "morphemes": [
      {
        "key": "wiikan-noun",
        "sro": "wîkan",
        "syllabics": "ᐑᑲᐣ",
        "gloss": "NI noun: back, spine, backbone (itwêwina/CW). The medial -wikan- inside kaskâwikanênêw is the incorporated form of this root."
      }
    ],
    "note": "The simplest underlying body-part noun. Inside the headword it shortens to -wikan- (short i)."
  },
  {
    "english": "s/he breaks him/her by hand (generic, no body-part)",
    "sro": "pîkonêw",
    "syllabics": "ᐲᑯᓀᐤ",
    "morphemes": [
      {"key": "piikon-stem", "sro": "pîkon-", "syllabics": "ᐲᑯᐣ", "gloss": "VTA stem: break (by hand)"},
      {"key": "ew-rel", "sro": "-êw", "syllabics": "ᐁᐤ", "gloss": "VTA 3→3′ indicative suffix"}
    ],
    "note": "Same -ê-w VTA tail as the headword, but without back-incorporation — useful as a structural minimal pair showing what the -wikan- medial adds semantically."
  },
  {
    "english": "s/he has a broken back (from falling)",
    "sro": "kaskâwikanisin",
    "syllabics": "ᑲᐢᑳᐏᑲᓂᓯᐣ",
    "morphemes": [
      {"key": "kaskaa-rel2", "sro": "kaskâ-", "syllabics": "ᑲᐢᑳ", "gloss": "initial: break across, snap"},
      {"key": "wikan-rel2", "sro": "-wikan-", "syllabics": "ᐏᑲᐣ", "gloss": "body-part medial: back"},
      {"key": "isin-fall", "sro": "-isin", "syllabics": "ᐃᓯᐣ", "gloss": "AI final: ‘by falling / by bodily impact’"}
    ],
    "note": "Sister AI verb in the same paradigm: same kaskâ-…-wikan- spine but the ‘by falling’ final -isin instead of the manual -n-êw. Listed in Wolvengrey via itwêwina under kaskâ- (‘s/he has a broken back from falling, s/he lies with a broken back’)."
  }
]
```

---

## 4. `quickReference` draft

```json
[
  {
    "english": "Back Breaker — s/he breaks s.o.’s back by hand",
    "sro": "kaskâwikanênêw",
    "syllabics": "ᑲᐢᑳᐏᑲᓀᓀᐤ",
    "note": "Headword on the plaque; VTA, 3→3′."
  },
  {
    "english": "back, spine, backbone",
    "sro": "wîkan",
    "syllabics": "ᐑᑲᐣ",
    "note": "NI noun. Source of the -wikan- medial in the headword."
  },
  {
    "english": "someone’s back (his/her back)",
    "sro": "mispiskwan",
    "syllabics": "ᒥᐢᐱᐢᑲᐧᐣ",
    "note": "More common everyday word for ‘back of the body’ (possessed-stem paradigm: nispiskwan ‘my back’, kispiskwan ‘your back’, ospiskwan ‘his/her back’)."
  },
  {
    "english": "s/he breaks it by hand (inanimate object)",
    "sro": "pîkonam",
    "syllabics": "ᐲᑯᓇᒼ",
    "note": "VTI generic ‘break it’."
  },
  {
    "english": "s/he breaks him/her by hand (animate object)",
    "sro": "pîkonêw",
    "syllabics": "ᐲᑯᓀᐤ",
    "note": "VTA generic ‘break him/her’. Same -n-êw tail as the headword."
  },
  {
    "english": "bone",
    "sro": "oskan",
    "syllabics": "ᐅᐢᑲᐣ",
    "note": "General word for bone — extends the body / break semantic field."
  },
  {
    "english": "s/he feels pain, s/he is in pain",
    "sro": "wîsakêyihtam",
    "syllabics": "ᐑᓴᑫᔨᐦᑕᒼ",
    "note": "VTI ‘to feel pain’ — useful pain-semantic anchor."
  }
]
```

---

## 5. `baseWords` draft

```json
[
  {"sro": "wîkan",   "english": "back, spine, backbone (NI noun)",                    "syllabics": "ᐑᑲᐣ"},
  {"sro": "kaskâ-",  "english": "(verb initial) to snap, to break across, to break in two", "syllabics": "ᑲᐢᑳ"},
  {"sro": "pîkonêw", "english": "s/he breaks him/her by hand (VTA)",                  "syllabics": "ᐲᑯᓀᐤ"}
]
```

---

## 6. Sources consulted

- itwêwina (Plains Cree Dictionary, ALTLab) — headword lookup:
  - https://itwewina.altlab.app/search?q=kask%C3%A2wikan%C3%AAn%C3%AAw — returns `kaskâwikanênêw` "s/he breaks s.o.'s back by hand" (CW = Wolvengrey).
  - https://itwewina.altlab.app/search?q=wikan — returns `wîkan` "back, spine; backbone; an entire spine; backbone of a canoe".
  - https://itwewina.altlab.app/word/mispiskwan/ — `mispiskwan` "back, back of the body" with possessor paradigm (nispiskwan / kispiskwan / ospiskwan).
  - https://itwewina.altlab.app/search?q=p%C3%AEkon%C3%AAw — `pîkonêw` "s/he breaks s.o. by hand" + extended senses (tames, disrupts, etc.).
  - https://itwewina.altlab.app/search?q=p%C3%AEkonam — `pîkonam` "s/he breaks s.t. by hand".
  - https://itwewina.altlab.app/search?q=kask%C3%A2- — long results listing showing the productive `kaskâ-` initial across many verbs (`kaskâwikanênêw`, `kaskâwikanisin` "broken back from falling", `kaskâwikanahwêw`-style "by shot" form, `kaskâcihtin` "it breaks right off", `kaskâcoskan` "broken tooth", etc.). The semantic core of `kaskâ-` here is *snap / break across a rigid object*.

(Other Cree dictionaries — Online Cree Dictionary, Plains Cree Dictionary — were not separately needed since itwêwina indexes the Wolvengrey, Maskwacîs, and Alberta Elders' Cree dictionaries and returned the headword directly. They remain available cross-checks for downstream work.)

---

## 7. Uncertainties

1. **Manual final `-n-` segmentation.** I have split the surface `-nêw` into `-n-` (manual final) + `-ê-w` (VTA 3→3′ suffix) on the basis of the obvious parallel with `pîkon-êw`. Some descriptive grammars treat `-êw` itself as the full VTA suffix and absorb the `-n-` into the preceding stem (so they would parse the headword as `kaskâ-wikan-ê-n` + `-êw`). The boundary is theoretical; the morphemes I've listed are correct, just the bracketing is mildly disputable. M2 may want to collapse `-ê-`, `-n-`, `-ê-w` into a single `-ênêw` "VTA 3→3′, by hand" gloss line if the page prefers a simpler 3-morpheme breakdown (`kaskâ-` + `-wikan-` + `-ênêw`). Both stories are linguistically defensible.
2. **Vowel length on the medial.** I've written `-wikan-` (short i) in the medial slot because that's what the plaque has and what the dictionary form `kaskâwikanênêw` requires; the underlying free noun is `wîkan` (long î). The shortening is the standard medial-incorporation behavior in Plains Cree, but worth flagging.
3. **`kaskâwikanisin` exact spelling.** The kaskâ- result page lists a "has-a-broken-back from falling" form; I've reconstructed the spelling as `kaskâwikanisin` (`kaskâ-` + `-wikan-` + AI `-isin`). The itwêwina headword for that exact form was not separately confirmed in a single-word lookup, so this related-form spelling carries ~80% confidence. If M2 wants to be conservative they can drop relatedForm #3 or replace it with the plain noun `mispiskwan` (rock-solid).
4. **`mispiskwan` syllabics rendering.** I used `ᒥᐢᐱᐢᑲᐧᐣ` (k + w-medial + a + n) for "kwa". The unified-syllabics combining form `ᒁ` is also valid. M2's existing pages should be checked for which convention is preferred site-wide; I have followed the more decomposed/portable form.
5. **Whether a chain element belongs on this plaque.** The visible crop shows vertebra + English + Cree text, but no chain. The project's STL set includes `Chain.stl` and `5_Vertebrae_Plain.stl`, suggesting the original design had multiple vertebrae and a chain. The mounted physical plaque appears to display only one vertebra and no chain. This is a physical-design note for the page author, not a linguistic issue.

---

## 8. Tripartite self-assessment

**Craftsperson says:** The transcription is solid. The third syllabics glyph clearly carries the long-â dot in the upscaled crop, and the SRO printed above it on the same plaque agrees (`kaskâ-`). itwêwina returns the exact headword `kaskâwikanênêw` as a Wolvengrey entry meaning "s/he breaks s.o.'s back by hand", and independently confirms `wîkan` "back, spine" — so the morpheme spine `kaskâ-wikan-` + VTA-manual-3→3′ tail is not speculative, it's the actual analysis embedded in the dictionary. The related forms (`wîkan`, `pîkonêw`, `mispiskwan`) are all real dictionary entries; the parallel with `pîkonêw` is structurally clean and makes the morpheme story easy to teach on the page.

**Skeptic says:** The morpheme-boundary call between `-n-` (manual final) and `-êw` (VTA tail) is a grammarian's choice rather than a dictionary fact — listed as Uncertainty 1. The reconstructed sister form `kaskâwikanisin` (Uncertainty 3) is ~80% confident; I'm reading it off the gloss-list page rather than a clean direct lookup. The `mispiskwan` syllabics convention may need normalizing to whatever the rest of the site uses. And critically — I'm treating the plaque carving as authoritative on diacritics over the catalogue, which is correct **for this sign** but means downstream code/JSON must actually be updated; this is M2's call to ship.

**Mover says:** Ship it. The headword spelling correction (`kaskâ-` with circumflex, syllabics `ᑳ`) is the most important deliverable and it's locked in by both the physical sign and the itwêwina entry. The morpheme block has the right pieces — even if M2 collapses the tail differently, the labels, glosses and syllabics are reusable. The related forms and quick-reference rows are dictionary-grounded. Outstanding uncertainties are clearly flagged with backout options. Hand off to M2 for renumbering keys and merging with the page.
