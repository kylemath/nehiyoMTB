# Manager M1 Report: Individual Sign Page Inventory

Manager: 2101-M1  
Coordinator: 2101-C  
Repository: `/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB`

## Sources and Scope

Read sources:

- `catalogue.json`
- `docs/sign-object-spec.md`
- `docs/index.html` page/STL routing snippets
- Exemplar page paths/content as needed: `docs/kahkakiw/index.html`, `docs/kiwapamitin/index.html`
- Public docs STL folders and `docs/assets/**` state

I did not spawn sub-subagents. I did not edit generated pages or exemplar pages. I wrote only coordination artifacts in `backgroundMaterial/agent2101/coordinator/manager_M1/`.

Key global findings:

- Existing individual sign pages under `docs/`: `docs/kahkakiw/index.html` and `docs/kiwapamitin/index.html` only.
- The target inventory excludes `kahkakiw` and `kiwapamitin`.
- `docs/assets/**` currently contains only `docs/assets/kahkakiw/raven_wild.png` and `docs/assets/kiwapamitin/iseeyousign.png`; none of the target models currently has a `docs/assets/{folder}/` image asset.
- `docs/index.html` currently hardcodes `builtOutSignPages` and `viewerSTLFiles` for only the two exemplars. For all new pages, page generation should also add catalogue `pagePath` and `docsStlPath` values or update equivalent routing.
- No root-level `*/production.stl` files were found. Catalogue `stlPath` values such as `backbreaker/production.stl` therefore appear to be placeholders or future source paths, not currently resolvable public links.
- All intended individual page paths below stay in `docs/{folder}/index.html`; no page path is proposed under `docs/assets` or `docs/cree`.

## Per-Model Inventory

### 1. Back Breaker

- id: `backbreaker`
- folder: `backbreaker`
- intended page path: `docs/backbreaker/index.html`
- existing page: no
- language status: complete from catalogue (`kaskawikanênêw` / `ᑲᐢᑲᐏᑲᓀᓀᐤ`)
- image availability: none under `docs/assets/backbreaker/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `backbreaker/Chain.stl`; `backbreaker/backbreaker_plaque.stl`; `backbreaker/5_Vertebrae_Plain.stl`
- recommended STL link: `backbreaker/backbreaker_plaque.stl`
- recommended image behavior: STL-first page; use generated 3D preview or no-image placeholder rather than inventing an image path.
- broken-link risk: catalogue `stlPath` points to missing `backbreaker/production.stl`; component files `Chain.stl` and `5_Vertebrae_Plain.stl` should not be used as the primary page STL unless the page intentionally exposes parts.

### 2. Machete

- id: `mistapiskihkoman`
- folder: `mistapiskihkoman`
- intended page path: `docs/mistapiskihkoman/index.html`
- existing page: no
- language status: complete from catalogue (`mistâpiskihkomân` / `ᒥᐢᑕᐱᐢᑭᐦᑯᒫᐣ`)
- image availability: none under `docs/assets/mistapiskihkoman/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `mistapiskihkoman/mistâpiskihkomân_plaque.stl`; `mistapiskihkoman/mistâpiskihkomân_plaque_v3.stl`; `mistapiskihkoman/v2_mistâpiskihkomân_plaque_v2.stl`
- recommended STL link: `mistapiskihkoman/mistâpiskihkomân_plaque_v3.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: non-ASCII filename requires careful URL encoding in generated `href`/viewer paths; catalogue `stlPath` points to missing `mistapiskihkoman/production.stl`.

### 3. Six Shooter

- id: `nicocwasaskanos`
- folder: `nicocwasaskanos`
- intended page path: `docs/nicocwasaskanos/index.html`
- existing page: no
- language status: complete from catalogue (`nikocwâsaskanôs` / `ᓂᑯᐚᓴᐢᑲᓄᐢ`)
- image availability: none under `docs/assets/nicocwasaskanos/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `nicocwasaskanos/nicocwâsaskanôs_plaque.stl`; `nicocwasaskanos/nikocwasaskanos.stl`
- recommended STL link: `nicocwasaskanos/nicocwâsaskanôs_plaque.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: catalogue id/folder are ASCII but recommended STL filename has diacritics; catalogue `stlPath` points to missing `nicocwasaskanos/production.stl`.

### 4. Purple Haze

- id: `nipamayatan-pekiseyahk`
- folder: `nipamayatan_pekiseyahk`
- intended page path: `docs/nipamayatan_pekiseyahk/index.html`
- existing page: no
- language status: complete from catalogue (`nipâmâyâtan pekisehyânik` / `ᓂᐹᒫᔭᑕᐣ ᐯᑭᓭᐦᔮᓂᐠ`)
- image availability: none under `docs/assets/nipamayatan_pekiseyahk/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `nipamayatan_pekiseyahk/nipamayatan_pekiseyahk_plaque.stl`; `nipamayatan_pekiseyahk/nipamayatan_pekiseyahk_plaque_v2.stl`; `nipamayatan_pekiseyahk/nipamayatan_pekiseyahk_plaque_v3.stl`
- recommended STL link: `nipamayatan_pekiseyahk/nipamayatan_pekiseyahk_plaque_v3.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: id uses hyphens while folder uses underscores; page generation must route from `id` to `folder`, not infer one from the other.

### 5. Lovers Lane

- id: `lovers-lane`
- folder: `loversLane`
- intended page path: `docs/loversLane/index.html`
- existing page: no
- language status: complete from catalogue (`nicimosak méskanâs` / `ᓂᒋᒧᓴᐠ ᒣᐢᑲᓈᐢ`)
- image availability: none under `docs/assets/loversLane/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `loversLane/lovers_lane_plaque_v2.stl`; `loversLane/lovers_lane_plaque_v3.stl`; `loversLane/lovers_lane_plaque_v4.stl`; `loversLane/lovers_lane_plaque_v5_bk.stl`; `loversLane/lovers_lane_plaque_v6.stl`; `loversLane/backbreaker_plaque.stl`; plus several `OTHER GEARS__UrbanAtWork_*` heart/gear source STLs
- recommended STL link: `loversLane/lovers_lane_plaque_v6.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: folder is camelCase and many candidate STLs are source/alternate gear parts; avoid backup file `lovers_lane_plaque_v5_bk.stl` and unrelated `backbreaker_plaque.stl`.

### 6. Wonder Woman

- id: `mamahtaw-iskwew`
- folder: `mamahtaw_askwew`
- intended page path: `docs/mamahtaw_askwew/index.html`
- existing page: no
- language status: complete from catalogue (`mamahtaw iskwew` / `ᒪᒪᐦᑕᐤ ᐃᐢᑲᐧᐤ`)
- image availability: none under `docs/assets/mamahtaw_askwew/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `mamahtaw_askwew/mamahtaw_askwew.stl`; `mamahtaw_askwew/mamahtâw_iskwew_plaque.stl`; `mamahtaw_askwew/mamahtâw_iskwew_plaque_v2.stl`
- recommended STL link: `mamahtaw_askwew/mamahtâw_iskwew_plaque_v2.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: id says `iskwew`, folder says `askwew`, and recommended STL uses diacritics; use catalogue `folder` literally.

### 7. Ray Gun

- id: `sapwapahcikan-paskisikan`
- folder: `sapwapahcikan-paskisikan`
- intended page path: `docs/sapwapahcikan-paskisikan/index.html`
- existing page: no
- language status: complete from catalogue (`sâpwâpahcikan paskisikan` / `ᓵᐚᐸᐦᒋᑲᐣ ᐸᐢᑭᓯᑲᐣ`)
- image availability: none under `docs/assets/sapwapahcikan-paskisikan/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `sapwapahcikan-paskisikan/sapwapahcikan-paskisikan-plaque.stl`; `sapwapahcikan-paskisikan/sapwapahcikan-paskisikan-plaque_v2.stl`
- recommended STL link: `sapwapahcikan-paskisikan/sapwapahcikan-paskisikan-plaque_v2.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: catalogue `stlPath` points to missing `sapwapahcikan-paskisikan/production.stl`.

### 8. Bed Springs

- id: `bed-springs`
- folder: `bedSprings`
- intended page path: `docs/bedSprings/index.html`
- existing page: no
- language status: complete from catalogue (`kekokel sôniyâwâhkêsis` / `ᑫᑯᑫᓬ ᓲᓂᔮᐁᐦᑫᓯᐢ`)
- image availability: none under `docs/assets/bedSprings/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `bedSprings/bed_springs_plaque.stl`; `bedSprings/bed_springs_plaque 2.stl`; `bedSprings/bed_springs_creeBed.stl`; `bedSprings/bed_springs_creeBed 2.stl`; `bedSprings/spring (6.2mm inner, 9mm outer, 10mm height, with rings at top and bottom) - 2588116__files__spring_with_rings_at_top_and_bottom_6.2mm_inner_hole.stl`
- recommended STL link: `bedSprings/bed_springs_plaque 2.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: recommended filename contains a space; consider copying/renaming to a URL-safe public STL before final catalogue wiring. Spring component STL should not be the primary sign STL.

### 9. Silverfox

- id: `soniyawahkesis`
- folder: `sôniyâwâhkêsîs`
- intended page path: `docs/sôniyâwâhkêsîs/index.html`
- existing page: no
- language status: complete from catalogue (`sôniyâwâhkêsis` / `ᓲᓂᔮᐁᐦᑫᓯᐢ`)
- image availability: none under `docs/assets/sôniyâwâhkêsîs/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `sôniyâwâhkêsîs/sôniyâwâhkêsîs.stl`; `sôniyâwâhkêsîs/sôniyâwâhkêsîs_plaque.stl`
- recommended STL link: `sôniyâwâhkêsîs/sôniyâwâhkêsîs_plaque.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: folder and STL filenames contain diacritics; catalogue id is ASCII. Use explicit `folder`, `pagePath`, and `docsStlPath`.

### 10. Medicine Man

- id: `maskihkiwiyiniw`
- folder: `maskihkiwiyiniw`
- intended page path: `docs/maskihkiwiyiniw/index.html`
- existing page: no
- language status: complete from catalogue (`maskihkiwiyiniw` / `ᒪᐢᑭᐦᑭᐏᔨᓂᐤ`)
- image availability: none under `docs/assets/maskihkiwiyiniw/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `maskihkiwiyiniw/maskihkiwiyiniw_new.stl`; `maskihkiwiyiniw/maskihkiwiyiniw_new_v2.stl`; `maskihkiwiyiniw/maskihkiwiyiniw_new_v3.stl`; `maskihkiwiyiniw/maskihkiwiyiniw_new_v4.stl`; `maskihkiwiyiniw/maskihkiwiyiniw_new_v5.stl`; `maskihkiwiyiniw/maskihkiwiyiniw_new_v6.stl`; `maskihkiwiyiniw/maskihkîwiyiniw_plaque_multicolour_rulers_v4.stl`; many `bk__maskihkîwiyiniw_*` backup/intermediate STLs
- recommended STL link: `maskihkiwiyiniw/maskihkîwiyiniw_plaque_multicolour_rulers_v4.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: many backups and alternate component files exist; avoid `bk__*` unless intentionally preserving a backup. Recommended filename contains `î`.

### 11. Bobsled

- id: `bobsled`
- folder: `bobsled`
- intended page path: `docs/bobsled/index.html`
- existing page: no
- language status: pending review (`creeName` is `bobsled`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/bobsled/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `bobsled/bobsled_plaque.stl`; `bobsled/bobsled_plaque_v2.stl`; `bobsled/bobsled_plaque_v3.stl`; `bobsled/bobsled_plaque_v4.stl`
- recommended STL link: `bobsled/bobsled_plaque_v4.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: do not display `bobsled` as a confirmed Cree form; keep language section clearly pending until reviewed.

### 12. Purgatory

- id: `purgatory`
- folder: `purgatory`
- intended page path: `docs/purgatory/index.html`
- existing page: no
- language status: complete from catalogue (`kâsenamâkew iskotew` / `ᑳᓭᓇᒫᑫᐤ ᐃᐢᑯᑌᐤ`)
- image availability: none under `docs/assets/purgatory/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `purgatory/purgatory_plaque.stl`; `purgatory/purgatory_plaque_v2-5.stl`; `purgatory/purgatory_plaque_v3.stl`
- recommended STL link: `purgatory/purgatory_plaque_v3.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: version naming includes both `v2-5` and `v3`; choose one explicit `docsStlPath` to avoid accidental fallback to an older file.

### 13. Deliverance

- id: `deliverance`
- folder: `deliverance`
- intended page path: `docs/deliverance/index.html`
- existing page: no
- language status: pending review (`creeName` is `deliverance`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/deliverance/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `deliverance/deliverance_plaque.stl`; `deliverance/deliverance_plaque_v2.stl`; `deliverance/deliverance_plaque_v3.stl`
- recommended STL link: `deliverance/deliverance_plaque_v3.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: language fields are placeholders; page should not imply a verified Cree translation.

### 14. Ewok

- id: `ewok`
- folder: `ewok`
- intended page path: `docs/ewok/index.html`
- existing page: no
- language status: pending review (`creeName` is `ewok`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/ewok/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `ewok/Screenshot 2023-12-11 at 7.14.23 PM.pngW100H89T2V4B0A0C0NS.stl`; `ewok/Screenshot 2023-12-11 at 7.14.23 PM.pngW100H89T2V4B0A0C0NS (1).stl`
- recommended STL link: `ewok/Screenshot 2023-12-11 at 7.14.23 PM.pngW100H89T2V4B0A0C0NS.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: filename includes spaces, punctuation, timestamp text, and a `.png...stl` stem; best candidate is usable but brittle for URLs unless encoded or renamed. Language data is pending.

### 15. Farmer's Daughter

- id: `farmers-daughter`
- folder: `FarmersDaughter`
- intended page path: `docs/FarmersDaughter/index.html`
- existing page: no
- language status: pending review (`creeName` is `farmers-daughter`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/FarmersDaughter/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `FarmersDaughter/toPrintV4.pngW100H100T2V4B0A0C0PS.stl`; `FarmersDaughter/toPrintV3.pngW100H100T2V4B0A0C0PS.stl`; `FarmersDaughter/FarmersDaughter_Plaque_blank.stl`; `FarmersDaughter/farmerDaughterPrint.pngW100H100T2V4B0A0C0PS (8).stl`; many `printDev__farmerDaughter*` intermediate STLs
- recommended STL link: `FarmersDaughter/toPrintV4.pngW100H100T2V4B0A0C0PS.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: folder is capitalized; filenames are print-development exports with image-like stems, spaces, and parentheses. Human confirmation is recommended before treating `toPrintV4...` as final.

### 16. Kakwa

- id: `kakwa`
- folder: `kakwa`
- intended page path: `docs/kakwa/index.html`
- existing page: no
- language status: complete from catalogue (`kakwa` / `ᑲᑲᐧ`)
- image availability: none under `docs/assets/kakwa/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `kakwa/kakwa_plaque.stl`; `kakwa/kakwa_plaque_v2.stl`; `kakwa/kakwa_plaque_v3.stl`
- recommended STL link: `kakwa/kakwa_plaque_v3.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: catalogue `stlPath` points to missing `kakwa/production.stl`.

### 17. Ocayisinakes

- id: `ocayisinakes`
- folder: `ocayisinakes`
- intended page path: `docs/ocayisinakes/index.html`
- existing page: no
- language status: complete from catalogue (`ocayisinâkês` / `ᐅᒐᔨᓯᓈᑫᐢ`)
- image availability: none under `docs/assets/ocayisinakes/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `ocayisinakes/ocayisinâkês_plaque.stl`; `ocayisinakes/ocayisinâkês_plaque_v2.stl`; `ocayisinakes/ocâyisanakes.stl`
- recommended STL link: `ocayisinakes/ocayisinâkês_plaque_v2.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: two romanizations appear in filenames (`ocayisinâkês`, `ocâyisanakes`); do not infer language spelling from filename.

### 18. Oyoyow

- id: `oyoyow`
- folder: `oyoyow`
- intended page path: `docs/oyoyow/index.html`
- existing page: no
- language status: complete from catalogue (`oyoyow` / `ᐅᔪᔪᐤ`)
- image availability: none under `docs/assets/oyoyow/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `oyoyow/oyoyo.stl`; `oyoyow/oyoyo_plaque.stl`; `oyoyow/oyoyo_plaque_moveholes.stl`; `oyoyow/oyoyo_plaque_moveholes_v3_multicolour.stl`; `oyoyow/oyoyo_plaque_moveholes_v4_multicolour.stl`; `oyoyow/NBBDPorcupine.stl`
- recommended STL link: `oyoyow/oyoyo_plaque_moveholes_v4_multicolour.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: catalogue id is `oyoyow` while filenames use `oyoyo`; explicit `docsStlPath` prevents mismatch. `NBBDPorcupine.stl` appears to be a source/component asset.

### 19. Nosemanicos

- id: `nosemanicos`
- folder: `nosemanicos`
- intended page path: `docs/nosemanicos/index.html`
- existing page: no
- language status: complete from catalogue (`nôsemanicôs` / `ᓄᓭᒪᓂᒑᐢ`)
- image availability: none under `docs/assets/nosemanicos/`
- catalogue `docsStlPath`: `nosemanicos/nôsemanicôs_plaque_v4.stl`
- plausible docs STLs: `nosemanicos/nôsemanicôs_plaque.stl`; `nosemanicos/nôsemanicôs_plaque_v2.stl`; `nosemanicos/v3_nôsemanicôs_plaque_v3.stl`; `nosemanicos/nôsemanicôs_plaque_v4.stl`; `nosemanicos/nôsemanicôs.stl`
- recommended STL link: `nosemanicos/nôsemanicôs_plaque_v4.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: lowest STL risk because catalogue already has `docsStlPath` and the file exists. Page route is still absent until `docs/nosemanicos/index.html` exists or `pagePath` is added after generation.

### 20. Victoria's Secret

- id: `victoria-secret`
- folder: `victoriaSecret`
- intended page path: `docs/victoriaSecret/index.html`
- existing page: no
- language status: pending review (`creeName` is `vicSecret`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/victoriaSecret/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `victoriaSecret/vicSecret_plaque.stl`
- recommended STL link: `victoriaSecret/vicSecret_plaque.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: id and folder differ, and language fields are placeholders.

### 21. Slinky

- id: `slinky`
- folder: `slinky`
- intended page path: `docs/slinky/index.html`
- existing page: no
- language status: pending review (`creeName` is `slinky`; `creeSyllabics` is empty)
- image availability: none under `docs/assets/slinky/`
- catalogue `docsStlPath`: absent
- plausible docs STLs: `slinky/slinky_plaque.stl`; `slinky/Slinky.stl`; `slinky/Slinky_Remix.stl`; `slinky/Slinky_Remix 2.stl`; `slinky/classicspringo.stl`
- recommended STL link: `slinky/slinky_plaque.stl`
- recommended image behavior: STL-first page; no current image asset.
- broken-link risk: language fields are placeholders; non-plaque spring/remix STLs should not be used as primary sign plaque unless intentionally exposing variants.

## Recommended STL Links

- `backbreaker`: `backbreaker/backbreaker_plaque.stl`
- `mistapiskihkoman`: `mistapiskihkoman/mistâpiskihkomân_plaque_v3.stl`
- `nicocwasaskanos`: `nicocwasaskanos/nicocwâsaskanôs_plaque.stl`
- `nipamayatan-pekiseyahk`: `nipamayatan_pekiseyahk/nipamayatan_pekiseyahk_plaque_v3.stl`
- `lovers-lane`: `loversLane/lovers_lane_plaque_v6.stl`
- `mamahtaw-iskwew`: `mamahtaw_askwew/mamahtâw_iskwew_plaque_v2.stl`
- `sapwapahcikan-paskisikan`: `sapwapahcikan-paskisikan/sapwapahcikan-paskisikan-plaque_v2.stl`
- `bed-springs`: `bedSprings/bed_springs_plaque 2.stl`
- `soniyawahkesis`: `sôniyâwâhkêsîs/sôniyâwâhkêsîs_plaque.stl`
- `maskihkiwiyiniw`: `maskihkiwiyiniw/maskihkîwiyiniw_plaque_multicolour_rulers_v4.stl`
- `bobsled`: `bobsled/bobsled_plaque_v4.stl`
- `purgatory`: `purgatory/purgatory_plaque_v3.stl`
- `deliverance`: `deliverance/deliverance_plaque_v3.stl`
- `ewok`: `ewok/Screenshot 2023-12-11 at 7.14.23 PM.pngW100H89T2V4B0A0C0NS.stl`
- `farmers-daughter`: `FarmersDaughter/toPrintV4.pngW100H100T2V4B0A0C0PS.stl`
- `kakwa`: `kakwa/kakwa_plaque_v3.stl`
- `ocayisinakes`: `ocayisinakes/ocayisinâkês_plaque_v2.stl`
- `oyoyow`: `oyoyow/oyoyo_plaque_moveholes_v4_multicolour.stl`
- `nosemanicos`: `nosemanicos/nôsemanicôs_plaque_v4.stl`
- `victoria-secret`: `victoriaSecret/vicSecret_plaque.stl`
- `slinky`: `slinky/slinky_plaque.stl`

## Recommended Image Behavior

No target model currently has an image under `docs/assets/{folder}/`. For page generation, use the STL viewer/render as the primary visual and omit image sections or show a neutral no-image state. Do not point target pages at `docs/assets/kahkakiw`, `docs/assets/kiwapamitin`, old root images, or guessed filenames.

If future image assets are added, place them under `docs/assets/{folder}/` and set catalogue `imagePath` according to `docs/sign-object-spec.md`. Until then, generated target pages should not depend on images.

## Data Gap Summary

Language pending review because Cree or syllabics are missing/placeholder:

- `bobsled`: `creeName` is English placeholder; `creeSyllabics` empty.
- `deliverance`: `creeName` is English placeholder; `creeSyllabics` empty.
- `ewok`: `creeName` is English placeholder; `creeSyllabics` empty.
- `farmers-daughter`: `creeName` is English/id placeholder; `creeSyllabics` empty.
- `victoria-secret`: `creeName` is `vicSecret`; `creeSyllabics` empty.
- `slinky`: `creeName` is English placeholder; `creeSyllabics` empty.

Catalogue routing gaps:

- All targets except `nosemanicos` lack `docsStlPath`.
- All targets lack explicit `pagePath`.
- `docs/index.html` currently only knows built-out page/STL routes for `kahkakiw` and `kiwapamitin`.
- Root catalogue `stlPath` values point to `production.stl` files that were not found in the repository scan.

Asset gaps:

- No target-specific image assets exist under `docs/assets/{folder}/`.
- Several recommended STL filenames have URL fragility: spaces, parentheses, diacritics, uppercase folder names, or image-like filename stems.

High-risk choices needing human confirmation before final publication:

- `FarmersDaughter`: many print-development exports; `toPrintV4...` is the best provisional choice but not confirmed.
- `ewok`: only screenshot-derived STL filenames exist; consider renaming/copying to a stable public STL name.
- `bedSprings`: recommended plaque filename contains a space; a URL-safe copy would reduce breakage.
- `maskihkiwiyiniw`: many backup/intermediate files; selected non-`bk__` multicolour rulers v4 file appears strongest.

## Self-Assessment

- **Craftsperson says:** This inventory is grounded in the current catalogue, docs spec, public docs folder state, and the actual STL/assets discovered. The per-model recommendations distinguish catalogue ids from folders and avoid inventing language or image assets.
- **Skeptic says:** Several STL recommendations infer "latest" or "plaque" intent from filenames rather than geometry inspection or print history. Filename fragility, diacritics, and inconsistent folder/id conventions remain real risks for generated links.
- **Mover says:** The report is specific enough for the page-generation manager to proceed with explicit `docsStlPath` choices, image fallbacks, and pending language flags. With more time, I would validate STL geometry/previews and ask for human confirmation on the few high-risk folders before publishing.
