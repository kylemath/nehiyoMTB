#!/usr/bin/env python3
"""
build_signs.py — automated draft-sign factory.

Default pipeline (image): for every un-made, non-aliased trail it
  1. uses a real screen-print ICON image  — either one already sitting in
     docs/sign-drafts/icons/<slug>.png, or freshly generated from the trail's
     prompt via the OpenAI image API (--gen-icons, needs a valid key);
  2. composites the finished sign PREVIEW with compose_sign.py — transliteration
     on top, the icon filling the middle, the Cree SYLLABICS overlaid on top of
     the icon, English at the bottom (matches the physical signs);
  3. writes the manifest the Translation Workbench reads for its Preview column.

Legacy pipeline (--procedural): build a coloured OpenSCAD plaque with a simple
procedural motif icon and render an .stl + preview .png (no image API needed).

Usage:
  # compose previews from icons already in docs/sign-drafts/icons/
  python3 tools/sign_factory/build_signs.py --only "Gold Digger,Cowboy"

  # generate the icons via OpenAI first, then compose (needs OPENAI_API_KEY)
  python3 tools/sign_factory/build_signs.py --all --gen-icons

  # old procedural OpenSCAD drafts
  python3 tools/sign_factory/build_signs.py --all --procedural
"""
import argparse, base64, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "plaque_gen"))
sys.path.insert(0, HERE)

import plaque_gen as pg          # noqa: E402
import motifs as mo              # noqa: E402
import compose_sign as cs        # noqa: E402
import icon_to_stl as i2s        # noqa: E402

HTML = os.path.join(REPO_ROOT, "docs", "cree-trail-names.html")
GFX_JS = os.path.join(REPO_ROOT, "docs", "graphics-data.js")
BLANK = os.path.join(REPO_ROOT, "blanks", "blank_plaque_thinner.stl")
SIGNS_DIR = os.path.join(REPO_ROOT, "signs")
DRAFTS_DIR = os.path.join(REPO_ROOT, "docs", "sign-drafts")
ICONS_DIR = os.path.join(DRAFTS_DIR, "icons")
MANIFEST = os.path.join(DRAFTS_DIR, "manifest.json")

# legacy plaque layout (mm) for --procedural
W, H, T = 90.0, 165.0, 1.75
MARGIN = 8.0
AVAIL_W = W - 2 * MARGIN
TRANSLIT_Y = H / 2 - 16
SYLL_Y = H / 2 - 40
ENGLISH_Y = -H / 2 + 14
ICON_Y = -10.0
ICON_W = 58.0
ICON_BASE = 0.6
ICON_STEP = 0.6
TEXT_DEPTH = 1.5
SYLL_DEPTH = 2.6
PLAQUE_COLOR = "#d9d3c4"
TEXT_COLOR = "#2a2a2a"
SYLL_COLOR = "#b23b3b"


# --------------------------------------------------------------------------- #
def load_text_data():
    """en -> {'t': transliteration, 's': syllabics} from the workbench DATA."""
    html = open(HTML, encoding="utf-8").read()
    pat = re.compile(
        r'\{en:"((?:[^"\\]|\\.)*)",.*?cree:\[\s*\{s:"((?:[^"\\]|\\.)*)",'
        r't:"((?:[^"\\]|\\.)*)"', re.S)
    return {m.group(1): {"s": m.group(2), "t": m.group(3)} for m in pat.finditer(html)}


def _node_json(expr):
    code = ("global.window={};require(%s);process.stdout.write(JSON.stringify(%s));"
            % (json.dumps(GFX_JS), expr))
    res = subprocess.run(["node", "-e", code], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit("failed to read graphics-data.js via node:\n" + res.stderr)
    return json.loads(res.stdout)


def load_graphics():
    return _node_json("window.TRAIL_GRAPHICS")


def load_style():
    return (_node_json("window.STYLE_FRAGMENTS"),
            _node_json("window.STYLE_KEY_FOR_TYPE"))


def build_prompt(g, frags, keymap):
    key = keymap.get(g.get("type", "screenprint"), "screenprint")
    frag = frags.get(key, "")
    subj = g.get("subject", "")
    return (subj + (", " + frag if frag else "")).strip()


# --------------------------------------------------------------------------- #
def gen_icon_openai(prompt, out_path, key, model="gpt-image-1", size="1024x1024"):
    body = json.dumps({"model": model, "prompt": prompt, "size": size, "n": 1}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=240)
    d = json.load(r)["data"][0]
    raw = base64.b64decode(d["b64_json"]) if d.get("b64_json") else urllib.request.urlopen(d["url"]).read()
    open(out_path, "wb").write(raw)


# ------- image-pipeline 3D assembly (blank + icon STL + text + syllabics) --- #
IMG_T = 1.75            # legacy plaque thickness mm (used by --single path)
IMG_ICON_W = 60.0       # legacy icon width mm
IMG_ICON_Y = 6.0        # legacy icon centre y

# --- real print geometry (matches blanks/blank_plaque_thinner.stl) --------- #
PLQ_W = 73.0            # final print width  (mm)
PLQ_H = 138.0           # final print height (mm)
PLQ_T = 1.2            # plaque base thickness (mm)
# mounting holes measured from the blank, in the centred 73x138 frame (y up):
TOP_HOLE_Y = 37.2
BOT_HOLE_Y = -42.2
# Mounting holes: a 4.2 mm aperture (the bolt shank passes through) ringed by a
# raised rim. Unlike the old recessed countersink, the rim PROTRUDES above the
# plaque face to give the bolt head/washer a solid, stand-off platform to clamp.
HOLE_R = 2.1           # aperture radius (4.2 mm diameter bolt hole)
RIM_W = 1.4            # rim ring width around the aperture (mm)
RIM_H = 0.5            # rim protrusion above the plaque face (mm)
RIM_OUTER_R = HOLE_R + RIM_W   # 3.5 mm — outer radius of the raised rim
EDGE_MARGIN = 3.0      # keep text/icon this far from the plaque edge
HOLE_GAP = 2.5         # keep text this far from a hole

# z-stack (low -> high), total ~3.2 mm (within the 2-5 mm target):
TEXT_DEPTH = 0.6       # english + transliteration relief height
OUTLINE_H = 0.6        # icon black-outline layer height
COLOR_H = 1.2          # icon colour-fill layer height (flat mode)
FILL_STEP = 0.4        # staggered mode: each icon colour sits this much taller
SYLL_FRONT = 0.8       # syllabics protrude this far beyond the icon colour top
EMBED = 0.3            # text/icon parts sink this far INTO the plaque so colour
                       # objects overlap it volumetrically (avoids coplanar-face
                       # slicing artifacts: dropped glyphs, filled counters/holes)

# filament names for the non-icon parts (snapped icon colours come from
# icon_to_stl.FILAMENT_PALETTE). These double as valid CSS colours for the viewer.
PLAQUE_FILAMENT = "white"      # cream/white plaque base
PLAQUE_RGB = (232, 225, 207)
TEXT_FILAMENT = "black"        # english + transliteration + icon outline
TEXT_RGB = (38, 38, 38)
SYLL_FILAMENT = "red"          # syllabics accent (tallest)
SYLL_RGB = (192, 57, 43)


LAND_W = 138.0         # landscape plaque width  (mm)
LAND_H = 73.0          # landscape plaque height (mm)
CORNER_R = 3.5         # plaque corner radius (mm) — matches the blank's soft corners
# landscape holes sit on the horizontal centreline near the two ends, flanking
# the icon (the portrait blank's top/bottom holes don't suit a short wide sign):
LAND_HOLE_X = 62.0


def _param_plaque_snippet(W, H, T, holes, corner=CORNER_R, hole_r=HOLE_R,
                          rim_w=RIM_W, rim_h=RIM_H):
    """A parametric rounded-rectangle plaque (centred, base z=0) with mounting
    holes. Each hole is a ``hole_r`` aperture surrounded by a raised rim that
    protrudes ``rim_h`` above the plaque face (outer radius ``hole_r+rim_w``),
    giving a bolt head/washer a solid stand-off platform to clamp onto. The
    aperture is drilled the full depth through both the plaque and the rim."""
    rims = "\n".join(
        f"      translate([{hx:.3f}, {hy:.3f}, 0]) "
        f"cylinder(h={T+rim_h:.3f}, r={hole_r+rim_w:.3f});"
        for hx, hy in holes)
    bores = "\n".join(
        f"    translate([{hx:.3f}, {hy:.3f}, -1]) "
        f"cylinder(h={T+rim_h+2:.3f}, r={hole_r:.3f});"
        for hx, hy in holes)
    return ("module blank_plaque() {\n"
            "  difference() {\n"
            "    union() {\n"
            f"      linear_extrude(height={T:.3f})\n"
            f"        offset(r={corner:.3f}) offset(r={-corner:.3f})\n"
            f"          square([{W:.3f}, {H:.3f}], center=true);\n"
            f"{rims}\n"
            "    }\n"
            f"{bores}\n"
            "  }\n}\n")


def _plaque_snippet():
    """Import the real blank, rescaled to PLQ_W x PLQ_H x PLQ_T, centred, base z=0.
    Holes are preserved because we import the mesh rather than rebuild it."""
    lo, hi = pg.stl_bbox(BLANK)
    bw, bh, bt = hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]
    sx, sy, sz = PLQ_W/bw, PLQ_H/bh, PLQ_T/bt
    return ("module blank_plaque() {\n"
            f"  translate([{-PLQ_W/2:.3f}, {-PLQ_H/2:.3f}, 0])\n"
            f"    scale([{sx:.6f}, {sy:.6f}, {sz:.6f}])\n"
            f"      translate([{-lo[0]:.3f}, {-lo[1]:.3f}, {-lo[2]:.3f}])\n"
            f'        import("{pg.scad_escape(os.path.abspath(BLANK))}", convexity=10);\n}}\n')


def _img_blank_snippet():
    lo, hi = pg.stl_bbox(BLANK)
    bw, bh, bt = hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]
    sx, sy, sz = 90.0/bw, 165.0/bh, IMG_T/bt
    return ("module blank_plaque() {\n"
            f"  translate([-45, -82.5, 0])\n"
            f"    scale([{sx:.6f}, {sy:.6f}, {sz:.6f}])\n"
            f"      translate([{-lo[0]:.3f}, {-lo[1]:.3f}, {-lo[2]:.3f}])\n"
            f'        import("{pg.scad_escape(os.path.abspath(BLANK))}", convexity=10);\n}}\n')


def assemble_scad(en, translit, syllabics, icon_stl, icon_ztop):
    avail = 90.0 - 16.0
    fs_en, en_l = pg.fit_text(en, avail, 26, pg.CWF_LATIN, fs_max=16)
    fs_tl, tl_l = pg.fit_text((translit or en).replace("-", " "), avail, 16, pg.CWF_LATIN, fs_max=12)
    fs_sy, sy_l = pg.fit_text(syllabics or "—", avail, 26, pg.CWF_SYLL, fs_max=17)
    syll_h = icon_ztop + 1.4          # protrude ~1.4 mm in front of the icon
    out = ["// Auto image-pipeline draft (tools/sign_factory/build_signs.py)",
           f'// "{pg.scad_escape(en)}"  icon={pg.scad_escape(os.path.basename(icon_stl))}',
           "$fn = 36;\n", _img_blank_snippet(),
           "module icon_model() {",
           f'  translate([0, {IMG_ICON_Y}, {IMG_T}]) import("{pg.scad_escape(os.path.abspath(icon_stl))}", convexity=10);',
           "}\n",
           "module lettering() {",
           pg.text_block(en_l, fs_en, -82.5+14, IMG_T, 1.5, "Raleway:style=Bold", "English (bottom)"),
           pg.text_block(tl_l, fs_tl, 82.5-15, IMG_T, 1.5, "Raleway:style=Bold", "translit (top)"),
           "}\n",
           "module syllabics_text() {",
           pg.text_block(sy_l, fs_sy, IMG_ICON_Y, IMG_T, syll_h,
                         "Euphemia UCAS:style=Bold", "syllabics (overlaid, protruding)"),
           "}\n",
           "union() { blank_plaque(); icon_model(); lettering(); syllabics_text(); }"]
    return "\n".join(out) + "\n"


LATIN_FONT = "Helvetica Neue:style=Bold"   # Raleway isn't installed; this is clean + available
SYLL_FONT = "Euphemia UCAS:style=Bold"

# trails that read best as a wide landscape sign regardless of icon bbox aspect
LANDSCAPE_NAMES = {
    "scalpel", "machete", "six shooter", "spanish switchblade", "switchback slicer",
    "battle axe", "ray gun", "snake back", "bottle rocket", "bobsled",
    "flat pete", "flatter pete",
}


def ensure_square_icon(icon_path):
    """Center-crop an icon to a 1:1 square in place.

    HueForge (continuous-tone) art is generated landscape (e.g. 1536x1024) but
    the plaque's icon band is taller than it is wide, so a landscape image
    contain-fits by width and leaves large empty bands above/below. Squaring the
    source lets it fill the band's height far better. Best-effort: a missing
    file or already-square image is a no-op."""
    try:
        from PIL import Image
    except Exception:
        return
    if not os.path.exists(icon_path):
        return
    try:
        im = Image.open(icon_path)
        w, h = im.size
        if w == h:
            return
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        im.crop((left, top, left + side, top + side)).save(icon_path)
    except Exception as e:
        print(f"    ! square-crop failed ({os.path.basename(icon_path)}): {str(e)[:80]}")


def choose_orient(en, icon_path, mode="auto", aspect_thresh=1.6):
    """Decide portrait vs landscape for a sign."""
    if mode in ("portrait", "landscape"):
        return mode
    if en.strip().lower() in LANDSCAPE_NAMES:
        return "landscape"
    try:
        if i2s.icon_aspect(icon_path) >= aspect_thresh:
            return "landscape"
    except Exception:
        pass
    return "portrait"


def _run_oscad_export(scad_text, scad_path, stl_path, oscad):
    """Write a tiny scad and export it to STL via OpenSCAD. Returns True on success."""
    open(scad_path, "w", encoding="utf-8").write(scad_text)
    r = subprocess.run([oscad, "-o", stl_path, scad_path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ! export failed ({os.path.basename(stl_path)}): {r.stderr.strip()[:120]}")
        return False
    return True


def _fit_export_text(text, band_w, band_h, y, depth, font, comment,
                     scad_path, stl_path, oscad, fs_max=24, fs_min=4.0):
    """Render text, measure the real mesh, then rescale so it fills the band as
    large as possible without overhanging — font-metric independent (works even
    when the requested font is substituted)."""
    text = text or "—"
    fs, lines = pg.fit_text(text, band_w, band_h, 0.66, fs_max=fs_max, fs_min=fs_min)
    rel = None
    block = ""
    for _ in range(2):
        # extrude from EMBED below the plaque face so the text digs into the plaque
        block = pg.text_block(lines, fs, y, PLQ_T - EMBED, depth + EMBED, font, comment)
        if not _run_oscad_export("$fn = 48;\n" + block + "\n", scad_path, stl_path, oscad):
            return None, fs, lines, block
        rel = os.path.relpath(stl_path, REPO_ROOT)
        lo, hi = pg.stl_bbox(stl_path)
        w, h = hi[0] - lo[0], hi[1] - lo[1]
        if w <= 0 or h <= 0:
            return rel, fs, lines, block
        scale = min(band_w / w, band_h / h) * 0.98
        if abs(scale - 1.0) <= 0.03:
            break
        fs = max(fs_min, fs * scale)   # measured rescale; keep existing line breaks
    return rel, fs, lines, block


def _layout(orient):
    """Return the orientation-specific plaque size, hole list, text bands and
    icon box. Portrait keys off the real blank holes; landscape uses a
    parametric plaque with holes flanking the icon on the centreline."""
    if orient == "landscape":
        W, H = LAND_W, LAND_H
        # holes stay on the VERTICAL centreline (x=0), one above + one below the
        # icon, so the sign screws to a pole/tree just like the Machete sign.
        strip = 10.5                                   # text strip height (mm)
        tl_top = H / 2 - EDGE_MARGIN
        tl_bot = tl_top - strip
        en_bot = -H / 2 + EDGE_MARGIN
        en_top = en_bot + strip
        hole_y = tl_bot - RIM_OUTER_R - 1.0            # just below the top text strip
        holes = [(0.0, hole_y), (0.0, -hole_y)]
        ic_top = hole_y - RIM_OUTER_R - 1.0            # icon sits between the holes
        ic_bot = -ic_top
        ic_box_w = W - 2 * EDGE_MARGIN                 # icon spans nearly full width
        text_w = W - 2 * EDGE_MARGIN
        plaque_scad = _param_plaque_snippet(W, H, PLQ_T, holes)
    else:  # portrait — parametric plaque so the new 4.2 mm aperture + raised
           # rim apply here too (the imported blank baked in the old recessed
           # holes); hole positions still match the measured blank.
        W, H = PLQ_W, PLQ_H
        holes = [(0.0, TOP_HOLE_Y), (0.0, BOT_HOLE_Y)]
        tl_top = H / 2 - EDGE_MARGIN
        tl_bot = TOP_HOLE_Y + RIM_OUTER_R + HOLE_GAP
        en_top = BOT_HOLE_Y - RIM_OUTER_R - HOLE_GAP
        en_bot = -H / 2 + EDGE_MARGIN
        ic_top = TOP_HOLE_Y - RIM_OUTER_R - 1.0
        ic_bot = BOT_HOLE_Y + RIM_OUTER_R + 1.0
        ic_box_w = W                                   # full width; relief may kiss edges
        text_w = W - 2 * EDGE_MARGIN
        plaque_scad = _param_plaque_snippet(W, H, PLQ_T, holes)
    return {
        "W": W, "H": H, "holes": holes, "plaque_scad": plaque_scad,
        "tl_y": (tl_top + tl_bot) / 2.0, "tl_h": max(6.0, tl_top - tl_bot),
        "en_y": (en_top + en_bot) / 2.0, "en_h": max(6.0, en_top - en_bot),
        "ic_y": (ic_top + ic_bot) / 2.0, "ic_box_h": ic_top - ic_bot,
        "ic_box_w": ic_box_w, "text_w": text_w,
    }


def _scad_color(rgb):
    return "color([%.3f, %.3f, %.3f])" % (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def _bundle_3mf(name, sdir, part_rgb):
    """Bundle a sign's per-part STLs into ONE multicolour .3mf — each part stays
    a separate, coloured object that shares the same coordinates, so the user
    opens a single file in the slicer (Creality Print / Orca) and assigns a
    filament per object (or it carries the colour). Best-effort: needs trimesh.
    """
    try:
        import trimesh
    except Exception:
        return None
    geoms = {}
    for key, rgb in part_rgb.items():
        p = os.path.join(sdir, f"{name}_{key}.stl")
        if not os.path.exists(p):
            continue
        try:
            m = trimesh.load(p, process=False)
        except Exception:
            continue
        if getattr(m, "is_empty", False) or len(getattr(m, "faces", [])) == 0:
            continue
        m.visual.face_colors = list(rgb) + [255]
        geoms[key] = m
    if not geoms:
        return None
    out = os.path.join(sdir, name + ".3mf")
    try:
        trimesh.Scene(geoms).export(out)
    except Exception as e:
        print(f"    ! 3mf bundle failed ({name}): {str(e)[:100]}")
        return None
    return os.path.relpath(out, REPO_ROOT)


def render_sign_components(en, td, icon_path, oscad, orient="portrait",
                           color_mode="staggered", max_colors=3, number=None):
    """Emit each sign element as its own STL in a *shared* coordinate frame.

    The icon is separated into its distinct flat colours (each snapped to the
    shared filament palette) plus a black outline; every colour is its own
    object so the K2 Plus can assign a filament per part. In "staggered" mode
    each icon colour sits on its own thin z-band so a single-nozzle printer can
    reproduce the colours by height-swap with no mid-layer change; "flat" keeps
    them coplanar for pure multi-material use. A native, F6-renderable assembly
    (coloured) and an auto ``colorLayers`` band list (for preview + production)
    are produced too. `orient` is "portrait" or "landscape".

    Returns a dict of repo-relative component paths (or None on hard failure).
    """
    name = slug(en)
    sdir = os.path.join(SIGNS_DIR, name); os.makedirs(sdir, exist_ok=True)
    L = _layout(orient)
    comps = {"orient": orient}

    # 1) icon -> distinct colour objects + black outline --------------------- #
    geo = i2s.icon_color_layers(icon_path, box_w_mm=L["ic_box_w"],
                                box_h_mm=L["ic_box_h"], max_colors=max_colors)
    ztop_dark = PLQ_T + OUTLINE_H
    # icon_parts: (key, poly2d, ztop_mm, rgb, filament, is_fill)
    icon_parts = []
    if geo["outline_2d"]:
        icon_parts.append(("icon_outline", geo["outline_2d"], ztop_dark,
                           TEXT_RGB, TEXT_FILAMENT, False))
    for i, f in enumerate(geo["fills"]):
        ztop = (ztop_dark + (i + 1) * FILL_STEP) if color_mode == "staggered" \
            else (PLQ_T + COLOR_H)
        icon_parts.append(("icon_" + f["name"], f["poly2d"], ztop,
                           tuple(f["rgb"]), f["name"], True))

    icon_base = PLQ_T - EMBED                 # sink icon parts into the plaque
    for key, poly2d, ztop, rgb, fil, _is in icon_parts:
        istl = os.path.join(sdir, name + "_" + key + ".stl")
        scad = (f"$fn = 24;\n"
                f"translate([0, {L['ic_y']:.3f}, {icon_base:.3f}])\n"
                f"  linear_extrude(height={ztop - icon_base:.3f}) {{\n{poly2d}\n}}\n")
        if _run_oscad_export(scad, os.path.join(sdir, name + "_" + key + ".scad"),
                             istl, oscad):
            comps[key] = os.path.relpath(istl, REPO_ROOT)

    max_top = max([p[2] for p in icon_parts], default=ztop_dark)
    syll_h = (max_top - PLQ_T) + SYLL_FRONT     # syllabics protrude past everything

    # 2) plaque base
    plaque_stl = os.path.join(sdir, name + "_plaque.stl")
    if _run_oscad_export("$fn = 64;\n" + L["plaque_scad"] + "\nblank_plaque();\n",
                         os.path.join(sdir, name + "_plaque.scad"), plaque_stl, oscad):
        comps["plaque"] = os.path.relpath(plaque_stl, REPO_ROOT)

    # 3) English (bottom)  4) transliteration (top)  5) syllabics (overlaid) - #
    text_jobs = [
        ("english", en, L["text_w"], L["en_h"], L["en_y"], TEXT_DEPTH, LATIN_FONT,
         "English (below bottom hole)", 24),
        ("translit", (td.get("t", "") or en).replace("-", " "), L["text_w"], L["tl_h"], L["tl_y"], TEXT_DEPTH,
         LATIN_FONT, "transliteration (above top hole)", 22),
        ("syllabics", td.get("s", "") or "—", L["text_w"], L["ic_box_h"] * 0.46, L["ic_y"],
         syll_h, SYLL_FONT, "syllabics (overlaid on icon, tallest)", 30),
    ]
    text_native = {}    # key -> native text_block scad (for the source assembly)
    syll_rows = 0
    for key, text, bw, bh, yy, depth, font, comment, fsmax in text_jobs:
        cstl = os.path.join(sdir, f"{name}_{key}.stl")
        rel, fs, lines, block = _fit_export_text(text, bw, bh, yy, depth, font, comment,
                                                 os.path.join(sdir, f"{name}_{key}.scad"), cstl,
                                                 oscad, fs_max=fsmax)
        # The syllabics overlay is exported as ONE STL PER ROW (syllabics,
        # syllabics_2, …) — each line becomes its own movable piece, so the rider
        # can space the rows apart with the normal nudge control in the editor
        # WITHOUT scaling the glyphs. Single-line syllabics stays one part. The
        # font size + line layout come from the fitted whole block, so the rows
        # line up exactly as before until intentionally moved.
        if key == "syllabics" and len(lines) > 1:
            lineh = fs * pg.LINE_GAP
            top = yy + (len(lines) - 1) / 2.0 * lineh
            for i, ln in enumerate(lines):
                ly = top - i * lineh
                rk = "syllabics" if i == 0 else f"syllabics_{i + 1}"
                rblock = pg.text_block([ln], fs, ly, PLQ_T - EMBED, depth + EMBED, font,
                                       f"{comment} — row {i + 1}")
                rstl = os.path.join(sdir, f"{name}_{rk}.stl")
                if _run_oscad_export("$fn = 48;\n" + rblock + "\n",
                                     os.path.join(sdir, f"{name}_{rk}.scad"), rstl, oscad):
                    comps[rk] = os.path.relpath(rstl, REPO_ROOT)
                text_native[rk] = rblock
            syll_rows = len(lines)
        else:
            if rel:
                comps[key] = rel
            text_native[key] = block
    if syll_rows:
        comps["syllabics_rows"] = syll_rows

    # 6) group number badge (numbered minor-trail groups) ------------------- #
    # Members of a numbered group (e.g. Terwillegar - 6/7/19, Canada Cup
    # Network - 1/2/3) share ONE base icon but each carries its own number,
    # rendered in a consistent style + position so a rider can tell which trail
    # in the group they're on. The number sits in the icon's top-right corner,
    # raised + red like the syllabics (so it reuses the red filament/colour band
    # rather than introducing a new colour). It is its own STL part for slicing.
    number_native = None
    if number is not None and str(number).strip():
        ntxt = str(number).strip()
        nfs = 13.0                                  # mm, fixed so the group matches
        npad = EDGE_MARGIN + 1.5
        nx = L["ic_box_w"] / 2.0 - npad - nfs / 2.0
        ny = L["ic_y"] + L["ic_box_h"] / 2.0 - npad - nfs / 2.0
        nscad = (f'  translate([{nx:.3f}, {ny:.3f}, {PLQ_T - EMBED:.3f}])\n'
                 f'    linear_extrude(height={syll_h + EMBED:.3f})\n'
                 f'      text("{pg.scad_escape(ntxt)}", size={nfs:.3f}, '
                 f'halign="center", valign="center", font="{LATIN_FONT}");')
        nstl = os.path.join(sdir, name + "_number.stl")
        if _run_oscad_export("$fn = 48;\n" + nscad + "\n",
                             os.path.join(sdir, name + "_number.scad"), nstl, oscad):
            comps["number"] = os.path.relpath(nstl, REPO_ROOT)
        number_native = nscad
        comps["number_value"] = ntxt

    # Native, renderable + COLOURED source assembly: plaque + icon polygons +
    # text, all inline and unioned. F6 Renders/exports cleanly (colour() is
    # preview-only and ignored by CGAL export). The per-colour STLs stay for
    # slicing. This is the file to open in OpenSCAD.
    def _extrude(poly2d, ztop):
        return (f"  translate([0, {L['ic_y']:.3f}, {icon_base:.3f}])\n"
                f"    linear_extrude(height={ztop - icon_base:.3f}) {{\n{poly2d}\n  }}")
    body = ["// Source for \"%s\" (%s). Render/Export here; the *_<part>.stl files"
            % (pg.scad_escape(en), orient),
            "// are the same pieces split per colour for multi-material slicing.",
            "$fn = 48;", "", L["plaque_scad"], "union() {",
            f"  {_scad_color(PLAQUE_RGB)} blank_plaque();"]
    for key, poly2d, ztop, rgb, fil, _is in icon_parts:
        body.append(f"  {_scad_color(rgb)}\n{_extrude(poly2d, ztop)}")
    for k in ("english", "translit"):
        if k in text_native:
            body.append(f"  {_scad_color(TEXT_RGB)} {{\n{text_native[k]}\n  }}")
    for k in sorted(text_native):
        if k == "syllabics" or k.startswith("syllabics_"):
            body.append(f"  {_scad_color(SYLL_RGB)} {{\n{text_native[k]}\n  }}")
    if number_native:
        body.append(f"  {_scad_color(SYLL_RGB)} {{\n{number_native}\n  }}")
    body.append("}")
    asm_path = os.path.join(sdir, name + "_assembly.scad")
    open(asm_path, "w", encoding="utf-8").write("\n".join(body) + "\n")

    # auto colorLayers (bottom -> top) for preview + production -------------- #
    layers = [{"color": PLAQUE_FILAMENT, "maxZ": round(PLQ_T, 3), "label": "plaque base"},
              {"color": TEXT_FILAMENT, "maxZ": round(ztop_dark, 3),
               "label": "text + icon outline"}]
    for key, poly2d, ztop, rgb, fil, is_fill in sorted(
            [p for p in icon_parts if p[5]], key=lambda p: p[2]):
        layers.append({"color": fil, "maxZ": round(ztop, 3), "label": "icon " + fil})
    layers.append({"color": SYLL_FILAMENT, "label": "syllabics accent"})

    colors, seen = [], set()
    for ly in layers:
        if ly["color"] not in seen:
            seen.add(ly["color"]); colors.append(ly["color"])

    # bundle all parts into one multicolour .3mf (separate coloured objects)
    part_rgb = {"plaque": PLAQUE_RGB, "english": TEXT_RGB,
                "translit": TEXT_RGB, "syllabics": SYLL_RGB, "number": SYLL_RGB}
    # extra syllabic-row parts (syllabics_2, …) share the red syllabics filament
    for k in comps:
        if isinstance(k, str) and k.startswith("syllabics_") and k != "syllabics_rows":
            part_rgb[k] = SYLL_RGB
    for key, poly2d, ztop, rgb, fil, _is in icon_parts:
        part_rgb[key] = rgb
    threemf = _bundle_3mf(name, sdir, part_rgb)
    if threemf:
        comps["threemf"] = threemf

    comps["assembly_scad"] = os.path.relpath(asm_path, REPO_ROOT)
    comps["color_ztop"] = round(max_top, 3)
    comps["icon_size_mm"] = [round(geo["width_mm"], 1), round(geo["height_mm"], 1)]
    comps["colorLayers"] = layers
    comps["colors"] = colors
    comps["color_mode"] = color_mode
    return comps


def render_assembly_preview(en, oscad, orient="portrait"):
    """Render the import-only assembly scad to a 3D PNG (preview mode shows the
    non-manifold icon that a CGAL export would drop). Returns rel-path or None."""
    name = slug(en)
    sdir = os.path.join(SIGNS_DIR, name)
    asm = os.path.join(sdir, name + "_assembly.scad")
    if not os.path.exists(asm):
        return None
    png = os.path.join(sdir, name + "_assembly.png")
    imgsize = "1180,760" if orient == "landscape" else "760,1180"
    cmd = [oscad, "-o", png, f"--imgsize={imgsize}", "--autocenter", "--viewall",
           "--camera=0,0,40,60,0,20,360", "--projection=perspective",
           "--colorscheme=Tomorrow", asm]
    if subprocess.run(cmd, capture_output=True, text=True).returncode == 0:
        return os.path.relpath(png, REPO_ROOT)
    return None


def render_sign_stl(en, td, icon_path, oscad):
    """icon PNG -> icon STL -> assembled plaque STL. returns stl rel-path or None."""
    name = slug(en)
    sdir = os.path.join(SIGNS_DIR, name); os.makedirs(sdir, exist_ok=True)
    icon_stl = os.path.join(sdir, name + "_icon.stl")
    scad_path = os.path.join(sdir, name + ".scad")
    stl_path = os.path.join(sdir, name + ".stl")
    info = i2s.convert(icon_path, icon_stl, width_mm=IMG_ICON_W, tones=4,
                       base=0.6, step=0.5, max_res=140)
    open(scad_path, "w", encoding="utf-8").write(
        assemble_scad(en, td.get("t", ""), td.get("s", ""), icon_stl, info["z_top"]))
    r = subprocess.run([oscad, "-o", stl_path, scad_path], capture_output=True, text=True)
    if r.returncode == 0:
        return os.path.relpath(stl_path, REPO_ROOT)
    print(f"  ! stl render failed for {en}: {r.stderr.strip()[:140]}")
    return None


# --------------------------------------------------------------------------- #
def slug(s):
    return pg.slug(s)


def select_targets(gfx, args):
    if args.only:
        return [n.strip() for n in args.only.split(",") if n.strip()]
    out = [en for en, g in gfx.items() if not g.get("alias") and not g.get("existing")]
    return out[:args.limit] if args.limit else out


# ------- legacy procedural pipeline ---------------------------------------- #
def _blank_snippet():
    lo, hi = pg.stl_bbox(BLANK)
    bw, bh, bt = hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]
    sx, sy, sz = W/bw, H/bh, T/bt
    return ("module blank_plaque() {\n"
            f"  translate([{-W/2:.3f}, {-H/2:.3f}, 0])\n"
            f"    scale([{sx:.6f}, {sy:.6f}, {sz:.6f}])\n"
            f"      translate([{-lo[0]:.3f}, {-lo[1]:.3f}, {-lo[2]:.3f}])\n"
            f'        import("{pg.scad_escape(os.path.abspath(BLANK))}", convexity=10);\n}}\n')


def _icon_module(motif):
    layers = mo.render_motif(motif); s = ICON_W/92.0
    parts = ["module icon_model() {"]
    for ly in layers:
        h = ICON_BASE + ly["z"]*ICON_STEP
        parts.append(f'  color("{ly["color"]}") translate([0, {ICON_Y:.3f}, {T:.3f}]) '
                     f'linear_extrude(height={h:.3f}) scale([{s:.4f},{s:.4f},1]) {{ {ly["code"]} }}')
    parts.append("}")
    return "\n".join(parts)


def _procedural_scad(en, translit, syllabics, motif):
    fs_en, en_l = pg.fit_text(en, AVAIL_W, 26, pg.CWF_LATIN, fs_max=16)
    fs_tl, tl_l = pg.fit_text((translit or en).replace("-", " "), AVAIL_W, 16, pg.CWF_LATIN, fs_max=12)
    fs_sy, sy_l = pg.fit_text(syllabics or "—", AVAIL_W, 30, pg.CWF_SYLL, fs_max=20)
    out = ["// Auto procedural draft (tools/sign_factory --procedural)",
           f"$fn = 40;\n", _blank_snippet(), _icon_module(motif)+"\n", "module lettering() {",
           pg.text_block(en_l, fs_en, ENGLISH_Y, T, TEXT_DEPTH, "Raleway:style=Bold", "English"),
           pg.text_block(tl_l, fs_tl, TRANSLIT_Y, T, TEXT_DEPTH, "Raleway:style=Bold", "translit"),
           "}\n", "module syllabics_text() {",
           pg.text_block(sy_l, fs_sy, SYLL_Y, T, SYLL_DEPTH, "Euphemia UCAS:style=Bold", "syll"),
           "}\n", "union() {", f'  color("{PLAQUE_COLOR}") blank_plaque();',
           f'  color("{TEXT_COLOR}") lettering();', "  icon_model();",
           f'  color("{SYLL_COLOR}") syllabics_text();', "}"]
    return "\n".join(out)+"\n"


def _render(scad, out, kind, oscad):
    cmd = ([oscad, "-o", out, "--imgsize=560,780", "--autocenter", "--viewall",
            "--camera=0,0,0,0,0,0,0", "--colorscheme=Tomorrow", scad] if kind == "png"
           else [oscad, "-o", out, scad])
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--gen-icons", action="store_true",
                    help="generate missing icons via the OpenAI image API")
    ap.add_argument("--regen", action="store_true", help="regenerate icons even if present")
    ap.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--model", default="gpt-image-1")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--plaque-w", type=int, default=720, help="preview width px")
    ap.add_argument("--stl", action="store_true", help="also render a printable STL per sign (needs OpenSCAD)")
    ap.add_argument("--no-stl", dest="stl", action="store_false")
    ap.set_defaults(stl=True)
    ap.add_argument("--single", action="store_true",
                    help="legacy: CGAL-union everything into one STL (drops the non-manifold "
                         "icon relief). Default is the component pipeline: one STL per part.")
    ap.add_argument("--orient", choices=["auto", "portrait", "landscape"], default="auto",
                    help="sign orientation. 'auto' picks landscape for wide icons "
                         "(and names in the landscape override list), else portrait.")
    ap.add_argument("--landscape-aspect", type=float, default=1.6,
                    help="icon width/height above which 'auto' chooses landscape")
    ap.add_argument("--color-mode", choices=["staggered", "flat"], default="staggered",
                    help="staggered: each icon colour on its own height band (single-nozzle "
                         "height-swap friendly); flat: coplanar fills (pure multi-material)")
    ap.add_argument("--max-colors", type=int, default=3,
                    help="max distinct icon fill colours kept per sign (plus black outline)")
    ap.add_argument("--translit", default=None,
                    help="override the transliteration text (use with a single --only sign)")
    ap.add_argument("--syllabics", default=None,
                    help="override the syllabics text (use with a single --only sign)")
    ap.add_argument("--assembly-preview", dest="asm_preview", action="store_true", default=True,
                    help="also render a combined 3D preview PNG of the components (default on)")
    ap.add_argument("--no-assembly-preview", dest="asm_preview", action="store_false")
    ap.add_argument("--procedural", action="store_true", help="legacy OpenSCAD pipeline")
    ap.add_argument("--openscad", default=shutil.which("openscad") or "openscad")
    args = ap.parse_args()

    text_data = load_text_data()
    gfx = load_graphics()
    targets = select_targets(gfx, args)
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    os.makedirs(ICONS_DIR, exist_ok=True)
    manifest = {}
    if os.path.exists(MANIFEST):
        try: manifest = json.load(open(MANIFEST, encoding="utf-8"))
        except Exception: manifest = {}

    if args.procedural:
        return run_procedural(targets, gfx, text_data, manifest, args)

    frags, keymap = load_style()
    have_oscad = bool(shutil.which(args.openscad) or os.path.exists(args.openscad))
    do_stl = args.stl and have_oscad
    if args.stl and not have_oscad:
        print("openscad not found; composing previews only (no STL).")
    ok = comp = gen = miss = stls = 0
    for en in targets:
        g = gfx.get(en, {})
        if g.get("alias") or g.get("existing"):
            continue
        td = dict(text_data.get(en, {}))
        if args.translit is not None:
            td["t"] = args.translit
        if args.syllabics is not None:
            td["s"] = args.syllabics
        name = slug(en)
        png_path = os.path.join(DRAFTS_DIR, name + ".png")
        prompt = build_prompt(g, frags, keymap)

        # numbered minor-trail group: `iconFrom` borrows a sibling's icon (so the
        # whole group shares one motif) and `number` is the value stamped on this
        # member. `iconFrom` falls back to a parsed trailing number when present.
        number = g.get("number")
        icon_from = g.get("iconFrom")
        if icon_from:
            icon_path = os.path.join(ICONS_DIR, slug(icon_from) + ".png")
        else:
            icon_path = os.path.join(ICONS_DIR, name + ".png")

        if (args.gen_icons and not icon_from and (args.regen or not os.path.exists(icon_path))):
            if not args.api_key:
                print(f"  ! {en}: --gen-icons but no API key"); 
            else:
                try:
                    gen_icon_openai(prompt, icon_path, args.api_key, args.model, args.size)
                    gen += 1; print(f"  gen icon: {en}")
                except urllib.error.HTTPError as e:
                    print(f"  ! {en}: image API {e.code}: {e.read().decode()[:140]}")
                except Exception as e:
                    print(f"  ! {en}: image API {type(e).__name__}: {str(e)[:140]}")

        rec = manifest.get(en, {})
        rec.update({"en": en, "slug": name, "type": g.get("type", "screenprint"),
                    "motif": None, "prompt": prompt})
        if number is not None:
            rec["number"] = str(number)
        if icon_from:
            rec["iconFrom"] = icon_from
        # HueForge art is continuous-tone and generated landscape; square it so
        # it fills the tall icon band instead of leaving empty space.
        if g.get("type") == "hueforge" and os.path.exists(icon_path):
            ensure_square_icon(icon_path)
        # orientation chosen once so the PREVIEW and the STL components agree
        prev_orient = (choose_orient(en, icon_path, args.orient, args.landscape_aspect)
                       if os.path.exists(icon_path) and not args.single else "portrait")
        if os.path.exists(icon_path):
            cs.compose(icon_path, en, td.get("t", ""), td.get("s", ""), png_path,
                       plaque_w=args.plaque_w, number=number, orient=prev_orient)
            rec["icon"] = "sign-drafts/icons/" + slug(icon_from or en) + ".png"
            rec["png"] = "sign-drafts/" + name + ".png"
            rec["source"] = "image"
            comp += 1; ok += 1
            tag = "composed"
            if do_stl:
                if args.single:
                    stl_rel = render_sign_stl(en, td, icon_path, args.openscad)
                    if stl_rel:
                        rec["stl"] = stl_rel; stls += 1; tag = "composed + stl(single)"
                else:
                    orient = prev_orient
                    comps = render_sign_components(en, td, icon_path, args.openscad, orient,
                                                   color_mode=args.color_mode,
                                                   max_colors=args.max_colors, number=number)
                    if comps:
                        rec["components"] = comps
                        rec["stl"] = comps.get("plaque", rec.get("stl"))
                        stls += 1; tag = f"composed + components [{orient}]"
                        if args.asm_preview:
                            ap_rel = render_assembly_preview(en, args.openscad, orient)
                            if ap_rel:
                                rec["assembly_png"] = ap_rel
            print(f"✓ {en:32s} {tag}   [{g.get('type','screenprint')}]")
        else:
            rec.setdefault("png", None)
            rec["needs_icon"] = True
            miss += 1
            print(f"· {en:32s} no icon yet (run with --gen-icons or drop a PNG in {os.path.relpath(ICONS_DIR, REPO_ROOT)})")
        # stamp the build time so the workbench can cache-bust the preview PNG and
        # the per-part STLs even on a text-only change (new Cree name), where the
        # icon geometry — and thus the old colour/size token — stays identical.
        rec["built"] = int(time.time())
        manifest[en] = rec

    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nmanifest: {os.path.relpath(MANIFEST, REPO_ROOT)} ({len(manifest)} entries)  "
          f"composed={comp} generated={gen} stl={stls} missing_icon={miss}")


def run_procedural(targets, gfx, text_data, manifest, args):
    have = bool(shutil.which(args.openscad) or os.path.exists(args.openscad))
    if not have:
        print("openscad not found; cannot run --procedural."); return
    ok = 0
    for en in targets:
        g = gfx.get(en, {})
        if g.get("alias") or g.get("existing"):
            continue
        td = text_data.get(en, {})
        motif = mo.pick_motif(en, g.get("concept", ""), g.get("subject", ""))
        name = slug(en)
        sdir = os.path.join(SIGNS_DIR, name); os.makedirs(sdir, exist_ok=True)
        scad_path = os.path.join(sdir, name + ".scad")
        stl_path = os.path.join(sdir, name + ".stl")
        png_path = os.path.join(DRAFTS_DIR, name + ".png")
        open(scad_path, "w", encoding="utf-8").write(
            _procedural_scad(en, td.get("t", ""), td.get("s", ""), motif))
        rec = manifest.get(en, {})
        rec.update({"en": en, "slug": name, "motif": motif, "type": g.get("type"),
                    "scad": os.path.relpath(scad_path, REPO_ROOT), "source": "procedural"})
        if _render(scad_path, stl_path, "stl", args.openscad):
            rec["stl"] = os.path.relpath(stl_path, REPO_ROOT)
        if _render(scad_path, png_path, "png", args.openscad):
            rec["png"] = "sign-drafts/" + name + ".png"; ok += 1
        rec["built"] = int(time.time())
        manifest[en] = rec
        print(f"✓ {en:32s} icon={motif}")
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nmanifest ({len(manifest)} entries)  ok={ok}")


if __name__ == "__main__":
    main()
