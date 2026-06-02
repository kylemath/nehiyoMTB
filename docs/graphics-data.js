/* =====================================================================
   graphics-data.js  —  Screenprint / 3D-icon design suggestions
   for every trail in the nêhiyaw Trail Names workbench.

   Consumed by cree-trail-names.html (adds the "Graphic / 3D Icon" column)
   and linked from style-guide.html.

   Each entry is keyed by the EXACT English trail name used in DATA.
   Fields:
     type     : "screenprint" | "hueforge" | "object"
                - screenprint : flat, limited-tone stencil icon (default)
                - hueforge    : continuous tonal / gradient image (~10% of signs)
                - object      : screenprint sign PLUS an embedded printable
                                3D object fused into the plaque (~10% of signs)
     concept  : human-readable description shown in the table column
     subject  : the core image-generation SUBJECT phrase. The UI composes
                the final editable prompt = subject + ", " + STYLE_FRAGMENTS[styleKey]
                so every prompt carries a common, extrude-friendly style.
     object   : (object type only) the embedded printable model + source hint
     alias    : (optional) canonical English name — this trail reuses that
                trail's sign; the UI renders "→ see <alias>"
     existing : (optional) folder name under repo root for an already-built
                sign; the UI renders a "built ✓" link instead of a generator

   STYLE_FRAGMENTS is the single source of truth for the "common style"
   appended to every prompt. Keep it in sync with style-guide.html.
   ===================================================================== */

window.STYLE_FRAGMENTS = {
  // Flat, 2–4 spot-colour screenprint. Each colour is a SOLID flat fill (no
  // gradient) bounded by bold black keylines → reads as a sticker/decal and is
  // reducible to a small set of closed regions for extrusion. NOTE: the Cree
  // syllabics are NOT part of the image — they are overlaid on top of the icon
  // afterwards, so the icon must contain no text/lettering.
  screenprint:
    "flat 2D screen-print style icon, bold clean vector shapes, limited palette of 3 flat colours, " +
    "thick confident black outlines, minimal detail, high contrast, single centered subject on a plain solid white background, " +
    "no text, no lettering, no border, vinyl decal / screenprint sticker look, 1024x1024",

  // Continuous-tone image meant to be sliced into stacked translucent
  // filament layers (HueForge). The icon-extruder reads this as a heightmap.
  hueforge:
    "smooth continuous-tone single-subject image optimised for HueForge filament-swap layering, " +
    "soft luminance gradient from light to dark, photographic tonal range, subject fills the frame, " +
    "no hard black outlines, no text, simple uncluttered background, even lighting, 1024x1024",

  // The sign graphic for an object-fused plaque uses the screenprint style;
  // the embedded 3D model is described separately in `object`.
  object:
    "flat 2D screen-print style icon, bold clean vector shapes, limited palette of 3 flat colours, " +
    "thick confident black outlines, minimal detail, high contrast, single centered subject on a plain solid white background, " +
    "no text, no lettering, no border, vinyl decal / screenprint sticker look, 1024x1024"
};

// styleKey used to pick the fragment (object -> uses the "object" fragment)
window.STYLE_KEY_FOR_TYPE = { screenprint: "screenprint", hueforge: "hueforge", object: "object" };

window.TRAIL_GRAPHICS = {
  /* ---- Already-built physical signs (skip generation, link the folder) ---- */
  "Ray Gun":            { type:"screenprint", existing:"sapwapahcikan-paskisikan", concept:"Built sign — retro ray-gun / blaster.", subject:"a retro 1950s sci-fi ray-gun blaster pistol" },
  "Six Shooter":        { type:"screenprint", existing:"nicocwasaskanos", concept:"Built sign — six-shooter revolver.", subject:"a classic western six-shooter revolver" },
  "Raven":              { type:"screenprint", existing:"kahkakiw", concept:"Built sign — raven in flight.", subject:"a black raven with spread wings" },
  "Machete":            { type:"screenprint", existing:"mistapiskihkoman", concept:"Built sign — machete blade.", subject:"a heavy machete blade" },
  "Lovers Lane":        { type:"object", existing:"loversLane", concept:"Built sign — heart with embedded interactive piece.", subject:"a heart pierced by a winding lane", object:"interactive heart/coil fused into the plaque (already built)" },
  "Wonder Woman":       { type:"screenprint", existing:"mamahtaw_askwew", concept:"Built sign — Wonder Woman emblem.", subject:"a superheroine warrior woman silhouette with tiara and emblem" },
  "Victoria's Secret":  { type:"hueforge", existing:"victoriaSecret", concept:"Built sign — HueForge portrait.", subject:"a glamorous lingerie-brand style portrait" },
  "The Farmer's Daughter": { type:"hueforge", existing:"FarmersDaughter", concept:"Built sign — HueForge portrait.", subject:"a vintage portrait of a farmer's daughter in a field" },
  "Bobsled":            { type:"object", existing:"bobsled", concept:"Built sign — bobsled run.", subject:"a bobsled sled speeding down an icy chute", object:"sled object fused into plaque (already built)" },
  "Bed Springs":        { type:"object", existing:"bedSprings", concept:"Built sign — bed with real printed springs.", subject:"a bed frame with coiled springs", object:"printed coil springs fused into plaque (already built)" },
  "Back Breaker":       { type:"object", existing:"backbreaker", concept:"Built sign — spine / back-breaker.", subject:"a curved spine being bent", object:"printed object fused into plaque (already built)" },
  "Deliverance":        { type:"screenprint", existing:"deliverance", concept:"Built sign — banjo / canoe dread.", subject:"a banjo over a wild river canyon" },
  "Slinky - Mid":       { type:"object", existing:"slinky", concept:"Built sign — real printed slinky coil.", subject:"a coiled slinky spring", object:"print-in-place slinky coil fused into plaque (already built)" },
  "Lower Ewok":         { type:"screenprint", existing:"ewok", concept:"Built sign — Ewok in hood.", subject:"a small hooded forest creature with spear" },

  /* ---- Aliases / co-named trails (one sign reused) ---- */
  "Slinky - South":         { alias:"Slinky - Mid" },
  "Slinky - North":         { alias:"Slinky - Mid" },
  "Upper Ewok":             { alias:"Lower Ewok" },
  "Victoria's Lower Secret":{ alias:"Victoria's Secret" },
  "Lower Back Breaker":     { alias:"Back Breaker" },
  "Machete-climb":          { alias:"Machete" },
  "Flatter Pete":           { type:"screenprint", concept:"An even flatter, more stretched-out happy cat.", subject:"a cartoon cat squashed even flatter and stretched out longer and thinner, grinning wide with its tongue out and paws splayed, comically flattened but blissfully enjoying it" },
  "Mustang - Alt":          { alias:"Mustang" },
  "Mustang Access":         { alias:"Mustang" },
  "Hustler Uphill":         { alias:"Hustler" },
  "GO Trail - alt climb":   { alias:"GO Trail" },
  "Happy Ending Hill":      { alias:"Happy Ending" },
  "Old Timer's Shortcut":   { alias:"Old Timer's" },
  "Emily Murphy Connector": { alias:"Emily Murphy Access" },
  /* Numbered minor-trail groups: each member shares the base icon (iconFrom)
     but stamps its own group number. See build_signs.py render_sign_components. */
  "Canada Cup Network - 2": { iconFrom:"Canada Cup Network - 1", number:2 },
  "Canada Cup Network - 3": { iconFrom:"Canada Cup Network - 1", number:3 },
  "Terwillegar - 19":       { iconFrom:"Terwillegar - 7", number:19 },
  "Terwillegar - 26":       { iconFrom:"Terwillegar - 7", number:26 },
  "Terwillegar - 6":        { iconFrom:"Terwillegar - 7", number:6 },
  "Mill Creek South II":    { alias:"Mill Creek South" },
  "Upper Caddytrack":       { alias:"Caddytrack" },
  "Lower Corkscrew":        { alias:"Upper Corkscrew" },

  /* ---- New screenprint icons ---- */
  "Mark Messier":       { type:"screenprint", concept:"Hockey captain — jersey #11 with a captain's C and crossed sticks.", subject:"a hockey jersey emblem with a large number 11, a captain's C, and crossed hockey sticks behind it" },
  "Capilano Cresent":   { type:"screenprint", concept:"A crescent moon arcing over a curving road.", subject:"a thin crescent moon curving over a winding crescent-shaped road" },
  "The Holy Trail":     { type:"screenprint", concept:"Holy Grail goblet as a Rubin vase/face illusion, biker riding down the base.", subject:"a single centred holy grail goblet, flared and wider at the base than at the rim, drawn as a Rubin vase / face illusion so the symmetrical empty negative space on each side forms a full facing female profile that spans the entire height of the goblet, with no chin, nose or brow lines extending outside the goblet outline (kept subtle); clean evenly-spaced straight radiant light rays beaming upward from the bowl; a small mountain biker silhouette rides down the outside of the flared base" },
  "Sideline":           { type:"screenprint", concept:"A singletrack peeling off the main trail to skirt a clifftop ledge above the river.", subject:"a narrow singletrack trail branching off the side of a wider main trail and tracing the top edge of a steep river-bank cliff, with the river curving along the base of the cliff below, side-on profile view" },
  "Caddytrack":         { type:"screenprint", concept:"Caddyshack homage — red lips biting Carl Spackler's bucket-hat face as the golf ball, trestle bridge behind.", subject:"a bold pair of red lips biting down on a golf ball where the golf ball is the grinning bucket-hatted face of the Caddyshack groundskeeper, with a tall wooden railway trestle bridge silhouette spanning the background" },
  "Hoot and Holler":    { type:"screenprint", concept:"An owl mid-hoot with sound lines.", subject:"an owl with its beak open mid-hoot and curved sound lines" },
  "Moonraker":          { type:"screenprint", concept:"Bond-space-opera homage — astronaut spy on an orange shuttle wing, crescent moon/space-station arc, and the rake hidden as the orbital trail.", subject:"a retro 1970s space-spy movie poster icon: a heroic astronaut in a white space suit standing on a bold orange space-shuttle wing, holding a garden rake like a laser pistol, with the rake teeth forming an orbital trail toward a crescent moon shaped like a space-station arc, small starbursts and a tiny satellite, no actor likeness" },
  "Risky Business":     { type:"screenprint", concept:"A pair of tumbling dice.", subject:"two tumbling dice with motion lines" },
  "Capilano Access":    { type:"screenprint", concept:"Trailhead gateway arch with arrow.", subject:"a trailhead gateway arch with a directional arrow" },
  "Happy Ending":       { type:"screenprint", concept:"A smiling setting sun on the horizon.", subject:"a setting sun with a smile dipping below a horizon line" },
  "Edmonton Queen":     { type:"object", concept:"Paddlewheel riverboat — embed a mini spinning paddlewheel.", subject:"a stern-wheel paddleboat riverboat", object:"a small print-in-place paddlewheel riverboat (model from Printables/Thingiverse, or simple SCAD paddlewheel) inset into the plaque centre" },
  "Birdhouse Trail":    { type:"object", concept:"Birdhouse icon — embed an actual mini birdhouse.", subject:"a classic peaked-roof birdhouse on a post with a round hole", object:"a printable mini birdhouse (search Printables 'mini birdhouse', or our own SCAD box+roof+perch) fused onto the plaque, hole facing out" },
  "E.M.P. Blast":       { type:"screenprint", concept:"Electromagnetic shockwave bursting outward.", subject:"an electromagnetic pulse shockwave bursting outward in concentric rings from a center point" },
  "Old Timer's":        { type:"screenprint", concept:"An antique pocket watch.", subject:"an antique pocket watch on a chain" },
  "Walters Folly":      { type:"screenprint", concept:"A whimsical leaning folly tower.", subject:"a whimsical crooked leaning folly tower" },
  "Dave's Trail":       { type:"screenprint", concept:"Hand-painted wooden trail name marker.", subject:"a rustic hand-painted wooden trail marker sign with an arrow" },
  "Upper Corkscrew":    { type:"screenprint", concept:"A spiral corkscrew.", subject:"a spiral metal corkscrew" },
  "Flat Pete":          { type:"screenprint", concept:"A happy cat squashed flat and stretched out, loving it.", subject:"a cartoon cat lying squashed completely flat and stretched out long across the ground, relaxed with a big content smile and a lolling tongue, clearly enjoying being flat" },
  "Too Much":           { type:"screenprint", concept:"An overflowing measuring cup.", subject:"an overflowing measuring cup spilling over the brim" },
  "Fort Edmonton Park Double Track": { type:"screenprint", concept:"Wooden fort palisade with a flag.", subject:"a wooden fort palisade wall with a flag flying above" },
  "No Horses":          { type:"screenprint", concept:"A crossed-out horse (no-entry).", subject:"a horse silhouette inside a no-entry circle with a diagonal slash" },
  "Walterdale Park Access": { type:"screenprint", concept:"The arched Walterdale bridge.", subject:"the distinctive twin-arch Walterdale bridge silhouette" },
  "Curvin Murvin":      { type:"screenprint", concept:"A wildly curving winding road.", subject:"a wildly curving serpentine winding road" },
  "Emily Murphy Access":{ type:"screenprint", concept:"1920s suffragette portrait (Famous Five).", subject:"a dignified 1920s suffragette woman portrait silhouette with a wide-brim hat" },
  "Canada Cup Network - 1": { type:"screenprint", concept:"Championship cup trophy with a maple leaf.", subject:"a championship cup trophy bearing a maple leaf", number:1 },
  "Terwillegar - 7":    { type:"screenprint", concept:"Numbered trail marker post.", subject:"a numbered wooden trail marker post with a directional arrow", number:7 },
  "Won't Die":          { type:"screenprint", concept:"A flatline that spikes back to life.", subject:"a heart-monitor flatline that suddenly spikes back into a heartbeat" },
  "Low Class":          { type:"screenprint", concept:"A cracked top hat and monocle.", subject:"a cracked tilted top hat with a monocle" },
  "Logarythmic":        { type:"screenprint", concept:"A log with a rhythm/sine wave through it.", subject:"a wooden log with a rhythmic sine wave running through it" },
  "Millcreek Double Track - Curling Club Exit": { type:"screenprint", concept:"A curling stone and broom.", subject:"a curling stone with a curling broom crossed behind it" },
  "Hyperloop":          { type:"screenprint", concept:"A sleek hyperloop pod in a looping tube.", subject:"a sleek hyperloop pod inside a looping vacuum tube" },
  "IMBA Trail":         { type:"screenprint", concept:"A mountain-bike badge.", subject:"a mountain bike silhouette inside a badge" },
  "Sprite":             { type:"screenprint", concept:"A winged forest sprite with a sparkle.", subject:"a small winged woodland sprite fairy with a sparkle trail" },
  "LRT Bridge":         { type:"screenprint", concept:"An LRT train crossing a girder bridge.", subject:"a light-rail train crossing a steel girder bridge" },
  "GO Trail":           { type:"screenprint", concept:"A green GO traffic-signal light.", subject:"a traffic signal showing a glowing green GO light" },
  "The Trap":           { type:"screenprint", concept:"A steel-jaw bear trap.", subject:"an open steel-jaw bear trap" },
  "Hustler":            { type:"screenprint", concept:"A pool cue striking the 8-ball.", subject:"a pool cue striking a billiard 8-ball" },
  "Turtle berms":       { type:"object", concept:"Turtle icon — embed a mini turtle figurine.", subject:"a turtle with a domed segmented shell, top view", object:"a small printable turtle figurine (Printables 'turtle', or SCAD dome + legs) fused on the plaque as a rolling berm bump" },
  "Dancing with the Trees": { type:"screenprint", concept:"A figure dancing intertwined with a tree.", subject:"a person dancing intertwined with a flowing tree" },
  "EM - Traverse":      { type:"screenprint", concept:"A contour line traversing a hillside.", subject:"a contour line traversing across a hillside with an arrow" },
  "Creekside Boogie II":{ type:"screenprint", concept:"A dancing figure beside a wavy creek with notes.", subject:"a dancing figure with music notes beside a wavy creek line" },
  "Oleskiw Meadow":     { type:"screenprint", concept:"A band of meadow wildflowers and grass.", subject:"a band of meadow wildflowers and tall grass" },
  "Root and Roll":      { type:"screenprint", concept:"Gnarled tangled tree roots.", subject:"twisting tangled tree roots spreading across the ground" },
  "Switchback Slicer":  { type:"screenprint", concept:"A zigzag switchback with a blade edge.", subject:"a zigzag switchback trail formed by a sharp knife blade edge" },
  "Dirty Mattress":     { type:"screenprint", concept:"A sagging old mattress with springs.", subject:"a worn sagging old mattress with coil springs poking out" },
  "Gold Digger":        { type:"screenprint", concept:"A gold pan and pickaxe with nuggets.", subject:"a gold prospecting pan with a pickaxe and gold nuggets" },
  "Root Canal":         { type:"screenprint", concept:"A molar tooth whose drilled root canal becomes a twisting trail, framed by two trees whose roots form the path.", subject:"a molar tooth showing its roots with a hole (root canal) drilled through which a twisted path goes, trees on either side and their roots creating the path in and out of the tool hole, scale and orientation of tooth allows large area in root for the path through, the viewer sees the end of the path only as a faint light at the end of the tunnel" },
  "Scona Hill Rip":     { type:"screenprint", concept:"A steep hill ripped with speed lines.", subject:"a steep hill profile with fast downhill speed lines" },
  "Mustang":            { type:"screenprint", concept:"A galloping mustang horse.", subject:"a galloping wild mustang horse with flowing mane" },
  "BDSM":               { type:"screenprint", concept:"Handcuffs crossed with a riding crop (tasteful).", subject:"a pair of handcuffs crossed with a riding crop" },
  "Jasper Ave Traverse - Alt": { type:"screenprint", concept:"Downtown avenue skyline with a traverse arrow.", subject:"a downtown avenue skyline with a horizontal traverse arrow" },
  "Hawrelak Outer Trail": { type:"screenprint", concept:"A lake ringed by a loop trail.", subject:"a lake encircled by a loop trail outline" },
  "Wanyandi Access":    { type:"screenprint", concept:"Trailhead gateway arch with arrow.", subject:"a trailhead gateway arch with a directional arrow" },
  "Higher Edukation":   { type:"screenprint", concept:"A graduation mortarboard cap.", subject:"a graduation mortarboard cap with a tassel" },
  "LOV":                { type:"screenprint", concept:"A bold heart emblem.", subject:"a bold solid heart emblem" },
  "MooseKnuckle":       { type:"screenprint", concept:"A moose head with big antlers.", subject:"a moose head with large palmate antlers" },
  "Fox Drive - Alt":    { type:"screenprint", concept:"A sitting fox silhouette.", subject:"a sitting fox with a bushy tail" },
  "Skoot-n-Shoot":      { type:"screenprint", concept:"A kick scooter with a slingshot.", subject:"a kick scooter with motion lines beside a slingshot" },
  "Master Yoda":        { type:"screenprint", concept:"A small long-eared jedi master with a cane.", subject:"a small wise long-eared jedi master silhouette leaning on a cane" },
  "McClung Connector":  { type:"screenprint", concept:"1920s suffragette portrait (Nellie McClung).", subject:"a 1920s suffragette woman portrait silhouette with hair in a bun" },
  "Moosestang":         { type:"screenprint", concept:"A moose with a galloping mustang's pose/mane.", subject:"a moose with a galloping mustang's flowing mane and running pose" },
  "Gnome Trail":        { type:"screenprint", concept:"Memegwesi — the small hairy Cree/Ojibwe riverbank water-spirit (the 'gnome' of nêhiyaw legend), beside its carved stone canoe.", subject:"a small child-sized hairy Memegwesi forest/water spirit with a large head, a narrow noseless face, two small dot eyes, a tall flame-like tuft of hair, shaggy fur body in layered brown tones, standing beside a small grey stone canoe", object:"a Memegwesi spirit figure with a stone canoe fused onto the plaque" },
  "Up and Down - McKinnon": { type:"screenprint", concept:"Up and down arrows over a hill profile.", subject:"an up arrow and a down arrow over a hill profile" },
  "Snake Back":         { type:"screenprint", concept:"A snake's curving spine zigzag.", subject:"a snake spine curving in a zigzag" },
  "Belgravia Access - South": { type:"screenprint", concept:"Trailhead gateway arch with arrow.", subject:"a trailhead gateway arch with a directional arrow" },
  "Bridge me up Scottie": { type:"object", concept:"Star-Trek beam over a bridge — embed a mini truss bridge.", subject:"a transporter beam-up sparkle column over a small bridge", object:"a small printable truss/arch bridge (SCAD or Printables) fused across the plaque centre" },
  "Hulk Bogan":         { type:"screenprint", concept:"A wrestler flexing and ripping a shirt.", subject:"a muscular pro-wrestler flexing both arms and ripping his shirt" },
  "Westpointe Ravine":  { type:"screenprint", concept:"A forested ravine valley cross-section.", subject:"a forested ravine valley cross-section with a creek at the bottom" },
  "Skyline Trail":      { type:"screenprint", concept:"A city skyline along a ridge.", subject:"a city skyline silhouette along a ridge line" },
  "Rowland Road Upper": { type:"screenprint", concept:"A winding uphill road with marker.", subject:"a winding uphill road with a roadside marker" },
  "Mill Creek Access Alt": { type:"screenprint", concept:"Trailhead gateway arch with arrow.", subject:"a trailhead gateway arch with a directional arrow" },
  "Buenavista Alt Track": { type:"screenprint", concept:"A scenic overlook with sun and hills.", subject:"a scenic overlook viewpoint with a sun rising over rolling hills" },
  "Millcreek IIII":     { type:"screenprint", concept:"A wavy creek with roman numeral IIII.", subject:"a wavy creek line beside a bold roman numeral four (IIII)" },
  "Tear Willy":         { type:"screenprint", concept:"A leaping orca (Free Willy pun).", subject:"an orca whale leaping out of the water" },
  "7-UP HitUP":         { type:"screenprint", concept:"A fizzy soda bottle with bubbles and a 7.", subject:"a fizzy soda bottle with rising bubbles and a number 7" },
  "Bakers Folly":       { type:"screenprint", concept:"A chef's toque and rolling pin.", subject:"a baker's chef toque hat with a crossed rolling pin" },
  "Money $hot":         { type:"screenprint", concept:"A dollar sign bursting with coins.", subject:"a dollar sign bursting outward with coins and motion lines" },
  "Dawson Gravel Multi":{ type:"screenprint", concept:"Scattered gravel stones along a path.", subject:"scattered gravel stones forming a path" },
  "Ass Over Tea Kettle":{ type:"screenprint", concept:"A tumbling figure beside a tipping tea kettle.", subject:"a figure tumbling head over heels next to a tipping tea kettle" },
  "Selkirk Knights":    { type:"screenprint", concept:"A medieval knight's plumed helmet.", subject:"a medieval knight's helmet with a plume" },
  "Andre's Trail":      { type:"screenprint", concept:"Hand-painted wooden trail name marker.", subject:"a rustic hand-painted wooden trail marker sign with an arrow" },
  "Silverberry Dirt Jumps": { type:"screenprint", concept:"A biker launching off a dirt jump.", subject:"a mountain biker launching airborne off a dirt jump" },
  "Bottle Rocket":      { type:"object", concept:"Bottle-rocket icon — embed a mini rocket.", subject:"a firework bottle rocket launching with a flame trail", object:"a small printable rocket (Printables 'mini rocket', or SCAD cone+fins body) fused onto the plaque, nose protruding" },
  "Fireman's Descent":  { type:"screenprint", concept:"A firefighter helmet with a fire pole.", subject:"a firefighter helmet beside a vertical fire pole" },
  "Secret Trail":       { type:"screenprint", concept:"A keyhole with a shushing finger.", subject:"a keyhole with a finger held to lips in a shush" },
  "MacKenzie Ravine":   { type:"screenprint", concept:"A deep forested ravine with a creek.", subject:"a deep forested ravine with a creek winding through the bottom" },
  "Golf Course Trail":  { type:"screenprint", concept:"A golf flag in a hole on the green.", subject:"a golf flag standing in a hole on a putting green with a ball" },
  "Purple Bench":       { type:"screenprint", concept:"A park bench (purple via filament).", subject:"a slatted park bench in side profile" },
  "Camel Humps":        { type:"screenprint", concept:"A two-humped bactrian camel.", subject:"a two-humped bactrian camel in profile" },
  "Belgravia Dirt Jumps - Drop In": { type:"screenprint", concept:"A biker dropping in on a dirt ramp.", subject:"a mountain biker dropping in on a steep dirt ramp" },
  "Justice Training Loop": { type:"screenprint", concept:"Scales of justice formed into a loop.", subject:"the balanced scales of justice with a looping arrow" },
  "Henday Hunge":       { type:"screenprint", concept:"A growling stomach over a highway.", subject:"a growling hungry stomach over a long highway" },
  "A loop through the forest": { type:"screenprint", concept:"A ring of pine trees forming a loop.", subject:"a circle of pine trees forming a loop" },
  "UofA-6":             { type:"screenprint", concept:"A university crest book and grad cap.", subject:"an open book with a graduation cap, university crest style" },
  "Rattlesnake":        { type:"object", concept:"Rattlesnake icon — embed a print-in-place articulated snake.", subject:"a coiled rattlesnake with a raised rattling tail", object:"a print-in-place articulated snake (Printables 'articulated snake') fused along the plaque so it flexes" },
  "Dawson Park":        { type:"screenprint", concept:"A park tree and bench.", subject:"a leafy park tree beside a bench" },
  "Spanish Switchblade":{ type:"object", concept:"Switchblade icon — embed a mini folding knife model.", subject:"a folding switchblade knife flicking open", object:"a small printable folding/flick knife model (Printables 'folding knife', or SCAD pivoting blade) inset into the plaque" },
  "Rundle Park Gravel": { type:"screenprint", concept:"A gravel path with scattered stones.", subject:"a gravel path lined with scattered stones" },
  "Hawrelak Park Access": { type:"screenprint", concept:"Trailhead gateway arch with arrow.", subject:"a trailhead gateway arch with a directional arrow" },
  "Riverside Dr Descent": { type:"screenprint", concept:"A steep road descending toward a river.", subject:"a steep road descending down toward a river" },
  "Kessel Run":         { type:"screenprint", concept:"The Millennium Falcon streaking with speed lines.", subject:"a fast saucer-shaped spaceship streaking with speed lines" },
  "Prime Rib":          { type:"screenprint", concept:"A prime rib roast with bone.", subject:"a thick prime rib roast cut with a bone" },
  "Wolf Willow Access": { type:"screenprint", concept:"A wolf beneath a willow branch.", subject:"a wolf standing beneath a drooping willow branch" },
  "Battle Axe":         { type:"object", concept:"Battle-axe icon — embed a mini battle axe.", subject:"a double-bladed medieval battle axe", object:"a small printable battle-axe model (Printables 'battle axe', or SCAD head+haft) fused onto the plaque" },
  "McAloon R.I.P.":     { type:"screenprint", concept:"A memorial headstone with a maple leaf.", subject:"a rounded memorial headstone with a small maple leaf" },
  "Wayne Gretzky":      { type:"screenprint", concept:"Hockey jersey #99 with crossed sticks.", subject:"a hockey jersey emblem with a large number 99 and crossed hockey sticks" },
  "Mill Creek South":   { type:"screenprint", concept:"A wavy creek with a compass S.", subject:"a wavy creek line beside a compass letter S" },
  "DownTheFunWay":      { type:"screenprint", concept:"A wavy slide going downhill.", subject:"a wavy playground-style slide descending downhill with motion lines" },
  "Farm Frolic":        { type:"screenprint", concept:"A barn with a frolicking figure and hay.", subject:"a red-style barn with a frolicking figure and hay bales" },
  "Patricia Ravine Doubletrack": { type:"screenprint", concept:"Two parallel trail lines through a ravine.", subject:"two parallel double-track trail lines running through a ravine" },
  "Kinnaird Killer":    { type:"screenprint", concept:"A skull with a steep climbing arrow.", subject:"a skull with a steep upward climbing arrow" },
  "Scalpel":            { type:"screenprint", concept:"A surgeon's scalpel.", subject:"a surgeon's scalpel with a fine blade" },
  "Soup Kitchen":       { type:"object", concept:"Cauldron icon — embed a mini pot with ladle.", subject:"a steaming soup pot with a ladle", object:"a small printable cauldron / soup pot with ladle (SCAD revolve or Printables) fused into the plaque" },
  "Drop In":            { type:"screenprint", concept:"A skate/BMX drop-in ramp with an arrow.", subject:"a quarter-pipe drop-in ramp with a downward arrow" },
  "Foxhole":            { type:"screenprint", concept:"A fox peeking from its den hole.", subject:"a fox peeking out of a round den hole" },
  "Two Garths":         { type:"screenprint", concept:"Two headbanging cartoon heads in caps (Wayne's World).", subject:"two cartoon heads wearing caps headbanging side by side" },
  "Knights of Ren":     { type:"screenprint", concept:"A cracked sith knight mask.", subject:"a cracked menacing sith knight helmet mask" },
  "Root Route":         { type:"screenprint", concept:"A tree root forming a winding route.", subject:"a tangled tree root forming a winding route" },
  "North Millcreek Bridge": { type:"screenprint", concept:"A small wooden footbridge over a creek.", subject:"a small wooden footbridge arching over a creek" },
  "Cowboy":             { type:"screenprint", concept:"A cowboy hat and boots with spurs.", subject:"a cowboy hat above a pair of boots with spurs" },
  "Earthshaker":        { type:"screenprint", concept:"Cracking ground with shockwave lines.", subject:"cracking fracturing ground with radiating shockwave lines" },
  "Dirty Cut":          { type:"screenprint", concept:"A rough muddy cut/slash mark.", subject:"a rough muddy diagonal cut slash mark" },
  "There Be Dragons Connector": { type:"screenprint", concept:"A coiled old-map dragon.", subject:"a coiled serpent dragon in old nautical-map style" },
  "Quick Snapper":      { type:"screenprint", concept:"A snapping turtle head.", subject:"a snapping turtle with its jaws open" },
  "Giddy Up":           { type:"screenprint", concept:"A horseshoe with a cowboy spur.", subject:"a horseshoe with a cowboy spur" },
  "Short 'n Sweet":     { type:"screenprint", concept:"A wrapped sweet candy.", subject:"a wrapped twist-end sweet candy" },
  "Cloverdale Detour Alt": { type:"screenprint", concept:"A four-leaf clover with a detour arrow.", subject:"a four-leaf clover with a curving detour arrow" },
  "Vegan Hollow":       { type:"screenprint", concept:"A leafy sprout in a bowl.", subject:"a leafy plant sprout growing from a bowl" },

  /* ---- New batch (Trailforks import) ---- */
  "Peckers Hollow":     { type:"screenprint", concept:"A woodpecker on a hollow tree.", subject:"a woodpecker perched on a hollow tree trunk with a round knot-hole" },
  "Tin Pan Alley":      { type:"screenprint", concept:"A tin pan with a music note in an alley.", subject:"a battered tin cooking pan hanging in a narrow alley with a music note" },
  "Under the End":      { type:"screenprint", concept:"A tunnel beneath the end of a bridge.", subject:"a small tunnel passing underneath the end of an arched bridge" },
  "Love Child":         { type:"screenprint", concept:"A heart cradling a little baby.", subject:"a heart shape cradling a small swaddled baby" },
  "Organ Donor":        { type:"screenprint", concept:"An anatomical heart with a donor ribbon.", subject:"an anatomical heart with a folded medical donor awareness ribbon" },
  "Pet Cemetary":       { type:"screenprint", concept:"A pet gravestone with a paw print.", subject:"a small rounded pet gravestone with a paw print and a dog bone in front" },
  "Lansdown":           { type:"screenprint", concept:"A soft feather drifting down (land-down pun).", subject:"a single soft feather drifting gently down toward the ground" },
  "Outlaw":             { type:"screenprint", concept:"An old-west wanted poster with a masked bandit.", subject:"an old west wanted poster showing a masked bandit face with a cowboy hat" },
  "Sidewinder":         { type:"screenprint", concept:"A sidewinding desert rattlesnake.", subject:"a sidewinder rattlesnake coiled in an S-curve with a raised rattle tail" },
  "Spirit Trail":       { type:"screenprint", concept:"A floating spirit over a winding path.", subject:"a translucent floating spirit ghost drifting above a winding trail" },
  "Svarog":             { type:"screenprint", concept:"A blacksmith's anvil + hammer with forge flames and a sun (Slavic smith/fire god).", subject:"a blacksmith's anvil with a crossed hammer and rising forge flames, with a small radiant sun above" },
  "Serendipity":        { type:"screenprint", concept:"A shooting star over a four-leaf clover.", subject:"a shooting star arcing over a four-leaf clover" },
  "Snow Sally":         { type:"screenprint", concept:"A cheerful snow-woman with a scarf.", subject:"a cheerful snow-woman with a scarf, twig arms and a snowflake" },
  "Honky Tonks":        { type:"screenprint", concept:"A honky-tonk saloon piano with notes.", subject:"an upright honky-tonk saloon piano with a couple of music notes" },
  "Shooter McGavin":    { type:"screenprint", concept:"A smug golfer doing the finger-guns 'shooter' salute.", subject:"a cocky golfer holding a golf club in one hand and pointing finger-guns forward with the other in a smug salute pose" },
  "Bruce Almighty":     { type:"screenprint", concept:"A man with arms raised commanding divine light and lightning.", subject:"a man standing with both arms raised, glowing radiant divine light rays and lightning bolts beaming outward from his open hands, a small halo above his head" },
  "Coalminer's Daughter": { type:"screenprint", concept:"Coal Miner's Daughter (Loretta Lynn nod) — a miner-girl in a headlamp helmet with a pickaxe.", subject:"a confident young woman wearing a coal miner's hard hat with a glowing front headlamp, a pickaxe resting on one shoulder, a chunk of coal beside her" },
  "Farmers Daughter's Cousin": { type:"screenprint", concept:"The farmer's-daughter's cousin — a farm girl by the barn, the cheeky next branch of the family tree.", subject:"a young farm woman in a sun hat and overalls leaning on a pitchfork beside a stacked hay bale, a small barn in the background" },

  /* ---- HueForge (continuous-tone) signs ---- */
  "West Coast Trail":   { type:"hueforge", concept:"Rugged Pacific coast with sea stacks and mist.", subject:"a rugged Pacific coastline with sea stacks, crashing waves, and misty coastal forest" },
  "780-Flow":           { type:"hueforge", concept:"A flowing water-current ribbon (780).", subject:"a smooth flowing water current ribbon with soft tonal depth" },
  "Breathless":         { type:"hueforge", concept:"A breathtaking layered mountain vista at dawn.", subject:"a breathtaking mountain vista at dawn with layered misty ridges receding into haze" },
  "Edge of Tomorrow":   { type:"hueforge", concept:"A lone figure against a rising sun horizon.", subject:"a lone futuristic figure silhouetted against a rising sun on the horizon" },
  "Bohemian Maid":      { type:"hueforge", concept:"Vintage beer-label maiden portrait.", subject:"a vintage Bohemian beer-label portrait of a maiden with soft tonal shading" },
  "Blue Man Group":     { type:"hueforge", concept:"Smooth blue-toned bald performer face.", subject:"a smooth blue-toned bald performer's face with gradient lighting" },
  "Klondike Valley Loop": { type:"hueforge", concept:"Gold-rush river valley, sepia gradient.", subject:"a gold-rush river valley with mountains and a prospector, warm sepia tones" },
  "Riverside Traverse": { type:"hueforge", concept:"Calm river through forested banks at golden hour.", subject:"a calm river winding through forested banks at golden hour with soft tonal gradient" },
  "Crazy Maria":        { type:"hueforge", concept:"A wild-haired dramatic woman's portrait.", subject:"a dramatic portrait of a wild-haired woman with strong tonal contrast" },
  "Steep and Deep":     { type:"hueforge", concept:"A steep snowy mountain face in deep powder.", subject:"a steep snowy mountain face buried in deep powder, cool blue-white tones" },

  /* ---- New Mill Woods batch (Trailforks import) ---- */
  "Alderaan":           { type:"screenprint", concept:"A peaceful ringed planet shattering apart (Star Wars).", subject:"a serene ringed planet breaking apart into fragments, with a thin energy beam striking it from the side" },
  "Endor":              { type:"screenprint", concept:"A forest moon — pine treetops over a curved moon horizon.", subject:"a row of tall pine tree silhouettes standing on the curved horizon of a moon, with a small planet in the sky behind" },
  "Loki":               { type:"screenprint", concept:"A trickster's two-pronged horned helmet (Loki / wîsahkêcâhk).", subject:"a mischievous trickster's curved two-horned helmet with a sly grin motif" },
  "Coyote Corridor":    { type:"screenprint", concept:"A howling coyote silhouette.", subject:"a coyote howling with its head raised, side profile silhouette" },
  "Red Leader":         { type:"screenprint", concept:"A lead X-wing-style starfighter (Red Leader callsign).", subject:"a front-three-quarter X-wing style starfighter with swept wings leading the formation" },
  "Bo and the Gizzy":   { type:"screenprint", concept:"Two buddy silhouettes fist-bumping.", subject:"two friend silhouettes side by side giving a fist bump" },
  "Papaschase":         { type:"screenprint", concept:"A woodpecker on a tree — honours Chief Papaschase (pâpâstêw, 'woodpecker').", subject:"a woodpecker clinging to a vertical tree trunk, head cocked back mid-peck" },
  "Chew-barka":         { type:"screenprint", concept:"A big shaggy Wookiee-style creature with a bandolier (Chewbacca pun).", subject:"a tall shaggy furry creature standing upright wearing a diagonal bandolier strap, friendly expression" },
  "Berm Express 1":     { type:"screenprint", concept:"A bike railing a banked berm with speed lines and a number 1.", subject:"a mountain bike leaning hard through a banked dirt berm turn with motion speed lines and a bold number 1", number:1 },
  "Greenview Path":     { type:"screenprint", concept:"A leafy green path winding into the distance.", subject:"a winding path lined with leafy bushes and a tree, curving into the distance" },
  "Papaschase Extension": { iconFrom:"Papaschase", number:2, type:"screenprint", concept:"Shares the Papaschase woodpecker icon, marked as the extension.", subject:"a woodpecker clinging to a vertical tree trunk, head cocked back mid-peck" },
  "Straggler":          { type:"screenprint", concept:"A lone tired figure lagging behind footprints.", subject:"a single weary walking figure trailing behind a line of footprints leading off ahead" },
  "Jackie Parkaloop":   { type:"screenprint", concept:"A looping trail forming a park-bench shape (Jackie Parker Park).", subject:"a looping trail line that curls into the shape of a park bench, with a single tree" },
  "Jackie Parker Multiuse": { type:"screenprint", concept:"Multi-use icons — a walker, biker and dog sharing a path.", subject:"simple side-by-side icons of a walking person, a bicycle and a dog above a shared path line" },
  "Meadows Path":       { type:"screenprint", concept:"A band of meadow grass and wildflowers along a path.", subject:"a band of tall meadow grass and a few wildflowers beside a gentle path" },
  "No Where Man":       { type:"screenprint", concept:"A lone wandering figure under a question mark / empty signpost (Beatles).", subject:"a lone wandering figure standing beside a blank empty signpost with arrows pointing nowhere" },
  "Magpie":             { type:"screenprint", concept:"A bold black-and-white magpie with a long tail (apistikakakês).", subject:"a magpie bird perched in profile with a long tail and bold black-and-white markings" },
  "Berm Express 2":     { iconFrom:"Berm Express 1", number:2, type:"screenprint", concept:"Shares the Berm Express icon, marked 2.", subject:"a mountain bike leaning hard through a banked dirt berm turn with motion speed lines and a bold number 2" },
  "Fulton Ravine Path": { type:"screenprint", concept:"A creek winding through a forested ravine cross-section.", subject:"a forested ravine valley cross-section with a small creek winding along the bottom" },
  "Party Line":         { type:"screenprint", concept:"A vintage telephone with a tangled cord (party line).", subject:"a vintage rotary wall telephone with a long tangled curling cord" },
  "Tamarack Saplings Path": { type:"screenprint", concept:"A cluster of young tamarack saplings.", subject:"a cluster of three slender young tamarack sapling trees of increasing height" },
  "Tawa Dry Pond Path": { type:"screenprint", concept:"A dry pond basin with cracked mud and cattails.", subject:"a shallow dry pond basin with cracked-mud ground and a few cattails at the edge" },
  "Death Star":         { type:"screenprint", concept:"The spherical Death Star battle station firing its superlaser.", subject:"a large spherical space battle station with a concave dish on one side firing a focused energy beam" },
  "23 Ave 1/8 mile":    { type:"screenprint", concept:"A drag-strip start line with a 1/8 mile marker.", subject:"a straight drag-strip lane with a checkered start line and a roadside distance marker post" },
  "Hillview Path":      { type:"screenprint", concept:"A path cresting a hill with a viewpoint sun.", subject:"a path climbing over a rounded hill toward a rising sun viewpoint" },
  "B.F.T.":             { type:"screenprint", concept:"A bold blank trail blaze marker (mystery initials).", subject:"a single bold rectangular trail blaze marker on a post" },
  "Howdy neighbour":    { type:"screenprint", concept:"A friendly waving hand over a picket fence.", subject:"a friendly waving hand rising above a short picket fence" }
};
