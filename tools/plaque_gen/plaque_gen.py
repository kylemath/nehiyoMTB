#!/usr/bin/env python3
"""
plaque_gen.py — auto-generate a trail-sign .scad (and a draft .stl) by combining
the blank plaque with extruded English + Cree-transliteration + syllabics text,
and optionally an icon STL fused on top (with the syllabics protruding in front).

The blank STL (`blanks/blank_plaque_thinner.stl`) is authored in arbitrary
SketchUp units, so we read its bounding box and rescale it to real millimetres
(default 90 x 165 x 1.75 mm), recentred with its base on z = 0. Its drilled
mounting holes are preserved because we import the mesh rather than rebuild it.

Text is auto-fit: the largest font size that fits the available width is chosen,
wrapping into multiple centred lines when needed.

Usage:
  python3 tools/plaque_gen/plaque_gen.py \
      --en "I See You" --translit "kiwâpamitin" --syllabics "ᑭᐚᐸᒥᑎᐣ" \
      [--icon path/to/icon.stl] [--icon-height 4] \
      [--out signs/i_see_you] [--name i_see_you] \
      [--width 90 --height 165 --thickness 1.75] [--no-render]

Requires only the Python standard library. If `openscad` is on PATH (or passed
via --openscad) a draft STL is rendered; otherwise just the .scad is written.
"""
import argparse, math, os, re, shutil, struct, subprocess, sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_BLANK = os.path.join(REPO_ROOT, "blanks", "blank_plaque_thinner.stl")

# crude per-glyph advance as a fraction of font size (good enough to auto-fit)
CWF_LATIN = 0.60
CWF_SYLL  = 0.80
LINE_GAP  = 1.22


# --------------------------------------------------------------------------- #
# STL bbox (binary or ASCII), stdlib only
# --------------------------------------------------------------------------- #
def stl_bbox(path):
    with open(path, "rb") as f:
        head = f.read(5)
        f.seek(0)
        if head == b"solid":
            # could still be binary with 'solid' header; sniff for 'facet'
            chunk = f.read(512)
            if b"facet" in chunk:
                return _bbox_ascii(path)
        return _bbox_binary(path)


def _bbox_binary(path):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    with open(path, "rb") as f:
        f.read(80)
        (n,) = struct.unpack("<I", f.read(4))
        for _ in range(n):
            data = f.read(50)
            vals = struct.unpack("<12f", data[:48])
            for vi in range(3):
                for k in range(3):
                    c = vals[3 + vi * 3 + k]
                    lo[k] = min(lo[k], c)
                    hi[k] = max(hi[k], c)
    return lo, hi


def _bbox_ascii(path):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    with open(path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("vertex"):
                _, x, y, z = line.split()[:4]
                for k, c in enumerate((float(x), float(y), float(z))):
                    lo[k] = min(lo[k], c)
                    hi[k] = max(hi[k], c)
    return lo, hi


# --------------------------------------------------------------------------- #
# text fitting / wrapping
# --------------------------------------------------------------------------- #
def wrap_words(text, max_chars):
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if len(cand) <= max_chars or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def fit_text(text, avail_w, avail_h, cwf, fs_max, fs_min=4.0):
    fs = fs_max
    while fs >= fs_min:
        cpl = max(1, int(avail_w / (cwf * fs)))
        lines = wrap_words(text, cpl)
        longest = max(len(l) for l in lines)
        w = longest * cwf * fs
        h = len(lines) * fs * LINE_GAP
        if w <= avail_w and h <= avail_h:
            return fs, lines
        fs -= 0.5
    cpl = max(1, int(avail_w / (cwf * fs_min)))
    return fs_min, wrap_words(text, cpl)


# --------------------------------------------------------------------------- #
# SCAD emit
# --------------------------------------------------------------------------- #
def scad_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def text_block(lines, fs, band_center_y, z, depth, font, comment, depth_boost=0.0):
    out = [f"  // {comment}"]
    lineh = fs * LINE_GAP
    top = band_center_y + (len(lines) - 1) / 2.0 * lineh
    for i, ln in enumerate(lines):
        y = top - i * lineh
        out.append(
            f'  translate([0, {y:.3f}, {z:.3f}]) linear_extrude(height={depth+depth_boost:.3f}) '
            f'text("{scad_escape(ln)}", size={fs:.3f}, halign="center", valign="center", '
            f'font="{font}");'
        )
    return "\n".join(out)


def build_scad(args, blank_lo, blank_hi):
    W, H, T = args.width, args.height, args.thickness
    bw = blank_hi[0] - blank_lo[0]
    bh = blank_hi[1] - blank_lo[1]
    bt = blank_hi[2] - blank_lo[2]
    sx, sy, sz = W / bw, H / bh, T / bt
    # recentre: move blank min->origin, scale to mm, then centre in X/Y, base at z=0
    cx = blank_lo[0]
    cy = blank_lo[1]
    cz = blank_lo[2]

    margin = 8.0
    avail_w = W - 2 * margin

    # bands (y measured from plaque centre)
    translit_y = H / 2 - 16
    syll_y = H / 2 - 40
    english_y = -H / 2 + 14
    icon_y = (syll_y - 24 + english_y + 12) / 2.0  # middle dead-space

    fs_en, en_lines = fit_text(args.en, avail_w, 26, CWF_LATIN, fs_max=16)
    fs_tl, tl_lines = fit_text(args.translit, avail_w, 18, CWF_LATIN, fs_max=13)
    fs_sy, sy_lines = fit_text(args.syllabics, avail_w, 30, CWF_SYLL, fs_max=20)

    text_depth = args.text_depth
    syll_depth = args.syllabics_depth

    blank_abs = os.path.abspath(args.blank)

    parts = []
    parts.append("// Auto-generated by tools/plaque_gen/plaque_gen.py — edit freely.")
    parts.append(f'// "{scad_escape(args.en)}" / {scad_escape(args.translit)} / {scad_escape(args.syllabics)}')
    parts.append(f"$fn = {args.fn};")
    parts.append("")
    parts.append("module blank_plaque() {")
    parts.append(f'  // import blank, rescale arbitrary units -> {W}x{H}x{T} mm, centre, base at z=0')
    parts.append(f"  translate([{-W/2:.3f}, {-H/2:.3f}, 0])")
    parts.append(f"    scale([{sx:.6f}, {sy:.6f}, {sz:.6f}])")
    parts.append(f"      translate([{-cx:.3f}, {-cy:.3f}, {-cz:.3f}])")
    parts.append(f'        import("{scad_escape(blank_abs)}", convexity=10);')
    parts.append("}")
    parts.append("")

    have_icon = bool(args.icon)
    if have_icon:
        icon_abs = os.path.abspath(args.icon)
        ilo, ihi = stl_bbox(args.icon)
        iw = ihi[0] - ilo[0]
        ih = ihi[1] - ilo[1]
        it = max(1e-6, ihi[2] - ilo[2])
        target_iw = args.icon_width if args.icon_width else (W - 2 * margin)
        isc = target_iw / iw if iw else 1.0
        # height the icon will reach on the plaque (for syllabics clearance)
        icon_top = T + it * isc
        parts.append("module icon_model() {")
        parts.append(f'  // icon scaled to {target_iw:.1f} mm wide, seated on plaque top (z={T})')
        parts.append(f"  translate([0, {icon_y:.3f}, {T:.3f}])")
        parts.append(f"    scale([{isc:.6f}, {isc:.6f}, {isc:.6f}])")
        parts.append(f"      translate([{-(ilo[0]+iw/2):.3f}, {-(ilo[1]+ih/2):.3f}, {-ilo[2]:.3f}])")
        parts.append(f'        import("{scad_escape(icon_abs)}", convexity=10);')
        parts.append("}")
        parts.append("")
    else:
        icon_top = T

    # syllabics extrude tall enough to protrude in front of the icon
    syll_z = T
    syll_clear = max(syll_depth, (icon_top - T) + args.syllabics_front)

    parts.append("module lettering() {")
    parts.append(text_block(en_lines, fs_en, english_y, T, text_depth,
                            "Raleway:style=Bold", "English (bottom)"))
    parts.append(text_block(tl_lines, fs_tl, translit_y, T, text_depth,
                            "Raleway:style=Bold", "transliteration (top)"))
    parts.append("}")
    parts.append("")
    parts.append("module syllabics_text() {")
    parts.append(text_block(sy_lines, fs_sy, syll_y, syll_z, syll_clear,
                            "Euphemia UCAS:style=Bold",
                            "syllabics (protrude in front of icon)"))
    parts.append("}")
    parts.append("")
    parts.append("// ===== assembly =====")
    parts.append("union() {")
    parts.append("  blank_plaque();")
    parts.append("  lettering();")
    if have_icon:
        parts.append("  icon_model();")
    parts.append("  syllabics_text();")
    parts.append("}")
    parts.append("")
    parts.append(f'echo("Plaque: {scad_escape(args.en)}  {W}x{H}x{T}mm");')
    parts.append(f'echo("English fs={fs_en}, translit fs={fs_tl}, syllabics fs={fs_sy}");')
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "plaque"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--en", required=True, help="English trail name")
    ap.add_argument("--translit", default="", help="Cree transliteration (SRO)")
    ap.add_argument("--syllabics", default="", help="Cree syllabics")
    ap.add_argument("--icon", default="", help="optional icon STL to fuse on top")
    ap.add_argument("--icon-width", type=float, default=0.0, help="icon target width mm (default: fit)")
    ap.add_argument("--icon-height", dest="icon_height", type=float, default=0.0, help="(reserved)")
    ap.add_argument("--blank", default=DEFAULT_BLANK, help="blank plaque STL")
    ap.add_argument("--width", type=float, default=90.0)
    ap.add_argument("--height", type=float, default=165.0)
    ap.add_argument("--thickness", type=float, default=1.75)
    ap.add_argument("--text-depth", dest="text_depth", type=float, default=1.5)
    ap.add_argument("--syllabics-depth", dest="syllabics_depth", type=float, default=2.5)
    ap.add_argument("--syllabics-front", dest="syllabics_front", type=float, default=1.5,
                    help="extra mm the syllabics protrude beyond the icon top")
    ap.add_argument("--fn", type=int, default=48)
    ap.add_argument("--out", default="", help="output directory (default: signs/<name>)")
    ap.add_argument("--name", default="", help="base filename (default: slug of --en)")
    ap.add_argument("--openscad", default=shutil.which("openscad") or "openscad")
    ap.add_argument("--no-render", action="store_true", help="write .scad only")
    args = ap.parse_args()

    if not os.path.exists(args.blank):
        sys.exit(f"blank STL not found: {args.blank}")

    name = args.name or slug(args.en)
    out_dir = args.out or os.path.join(REPO_ROOT, "signs", name)
    os.makedirs(out_dir, exist_ok=True)
    scad_path = os.path.join(out_dir, name + ".scad")
    stl_path = os.path.join(out_dir, name + ".stl")

    lo, hi = stl_bbox(args.blank)
    scad = build_scad(args, lo, hi)
    with open(scad_path, "w", encoding="utf-8") as f:
        f.write(scad)
    print(f"wrote {scad_path}")

    if args.no_render:
        return
    if not shutil.which(args.openscad) and not os.path.exists(args.openscad):
        print(f"openscad not found ({args.openscad}); skipping STL render. "
              f"Open the .scad in OpenSCAD to export.")
        return
    print(f"rendering {stl_path} (this can take a moment)…")
    try:
        subprocess.run([args.openscad, "-o", stl_path, scad_path], check=True)
        print(f"wrote {stl_path}")
    except subprocess.CalledProcessError as e:
        print(f"openscad render failed: {e}. The .scad is still usable.")


if __name__ == "__main__":
    main()
