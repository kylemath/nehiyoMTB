#!/usr/bin/env python3
"""
icon_to_stl.py — turn a flat screen-print icon PNG into an extrudable,
multi-height relief STL (the automated equivalent of the browser Icon Extruder).

Pipeline: load -> resize to a working grid -> posterize the luminance into K
tone bands -> map each band to a monotonic layer height (lightest band = the
white background = void) -> mesh each kept cell as a column (heightmap mesher)
-> binary STL, centred in X/Y with its base on z = 0 and scaled to a target
width in millimetres.

CLI:
  python3 tools/sign_factory/icon_to_stl.py --in icon.png --out icon.stl \
      --width 60 --tones 4 --base 0.6 --step 0.5
"""
import argparse, struct
import numpy as np
from PIL import Image


def posterize_levels(img, K, invert=False):
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    if invert:
        lum = 255.0 - lum
    light_bin = np.clip((lum * K / 256.0).astype(np.int32), 0, K - 1)
    return (K - 1) - light_bin     # 0 = lightest .. K-1 = darkest


def build_columns_stl(level, cell_mm, height_of):
    """level: HxW int array; height_of: array len K mm (0 => void)."""
    H, Wd = level.shape
    h = height_of[level]                      # HxW heights in mm
    tris = []

    def quad(a, b, c, d):
        tris.append((a, b, c)); tris.append((a, c, d))

    for y in range(H):
        for x in range(Wd):
            z = h[y, x]
            if z <= 0:
                continue
            X0, X1 = x * cell_mm, (x + 1) * cell_mm
            Y0, Y1 = (H - y - 1) * cell_mm, (H - y) * cell_mm
            quad((X0, Y0, z), (X1, Y0, z), (X1, Y1, z), (X0, Y1, z))      # top
            quad((X0, Y0, 0), (X0, Y1, 0), (X1, Y1, 0), (X1, Y0, 0))      # bottom
            rh = h[y, x + 1] if x + 1 < Wd else 0
            lh = h[y, x - 1] if x - 1 >= 0 else 0
            dh = h[y + 1, x] if y + 1 < H else 0
            uh = h[y - 1, x] if y - 1 >= 0 else 0
            if rh < z: quad((X1, Y0, rh), (X1, Y1, rh), (X1, Y1, z), (X1, Y0, z))
            if lh < z: quad((X0, Y1, lh), (X0, Y0, lh), (X0, Y0, z), (X0, Y1, z))
            if dh < z: quad((X0, Y0, dh), (X1, Y0, dh), (X1, Y0, z), (X0, Y0, z))
            if uh < z: quad((X1, Y1, uh), (X0, Y1, uh), (X0, Y1, z), (X1, Y1, z))
    return tris


def write_binary_stl(tris, path, center=None, offset=(0.0, 0.0, 0.0)):
    """Write triangles to a binary STL.

    center: (cx, cy) subtracted from every vertex so the mesh is centred in X/Y.
    offset: (ox, oy, oz) added to every vertex *after* centring, so the relief
            can be baked into its final plaque position (e.g. seated on the
            plaque top, nudged up the icon band) without round-tripping through
            OpenSCAD/CGAL — which rejects the non-manifold relief and drops it.
    """
    cx, cy = (center or (0.0, 0.0))
    ox, oy, oz = offset
    cx -= ox; cy -= oy            # fold the X/Y offset into the centre subtraction
    buf = bytearray(84 + len(tris) * 50)
    struct.pack_into("<I", buf, 80, len(tris))
    o = 84
    for (ax, ay, az), (bx, by, bz), (cx3, cy3, cz3) in tris:
        ax -= cx; bx -= cx; cx3 -= cx
        ay -= cy; by -= cy; cy3 -= cy
        az += oz; bz += oz; cz3 += oz
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx3 - ax, cy3 - ay, cz3 - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        struct.pack_into("<12fH", buf, o,
                         nx / ln, ny / ln, nz / ln,
                         ax, ay, az, bx, by, bz, cx3, cy3, cz3, 0)
        o += 50
    with open(path, "wb") as f:
        f.write(buf)


def _load_autocropped(in_path, max_res, white_thresh=238):
    """Load an icon, trim the flat background margins, downsample to a working
    grid. Returns (rgb float array HxWx3, luminance HxW)."""
    img = Image.open(in_path).convert("RGB")
    a = np.asarray(img, dtype=np.float32)
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    fg = lum <= white_thresh                       # non-background pixels
    if fg.any():
        ys, xs = np.where(fg)
        pad = 2
        y0, y1 = max(0, ys.min() - pad), min(a.shape[0], ys.max() + 1 + pad)
        x0, x1 = max(0, xs.min() - pad), min(a.shape[1], xs.max() + 1 + pad)
        a = a[y0:y1, x0:x1]
    h, w = a.shape[:2]
    s = min(1.0, max_res / max(h, w))
    if s < 1.0:
        img2 = Image.fromarray(a.astype(np.uint8)).resize(
            (max(2, int(w * s)), max(2, int(h * s))), Image.LANCZOS)
        a = np.asarray(img2, dtype=np.float32)
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    return a, lum


def mask_to_scad_2d(mask, cell_mm, simplify_px=0.75, min_area_px=8):
    """Trace a boolean mask into smooth OpenSCAD 2D polygons (with holes).

    Uses OpenCV contour tracing instead of per-pixel columns, so the icon
    extrudes with crisp vector edges like the text — and the result is a clean,
    watertight, manifold solid that OpenSCAD can Render (F6) and export. Points
    are returned centred about the icon's own origin (mm); the caller applies
    the plaque translate + linear_extrude.
    """
    import cv2
    H, W = mask.shape
    m = (mask.astype(np.uint8)) * 255
    contours, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return ""
    hier = hier[0] if hier is not None else []
    ox, oy = W * cell_mm / 2.0, H * cell_mm / 2.0   # centre the icon at origin

    def to_mm(cnt):
        pts = cnt.reshape(-1, 2)
        return [(c * cell_mm - ox, (H - r) * cell_mm - oy) for c, r in pts]

    polys = []
    for i, cnt in enumerate(contours):
        if hier[i][3] != -1:                        # skip holes here; handled w/ parent
            continue
        if cv2.contourArea(cnt) < min_area_px:
            continue
        eps = simplify_px
        outer = to_mm(cv2.approxPolyDP(cnt, eps, True))
        if len(outer) < 3:
            continue
        holes = []
        child = hier[i][2]
        while child != -1:
            hc = contours[child]
            if cv2.contourArea(hc) >= min_area_px:
                h = to_mm(cv2.approxPolyDP(hc, eps, True))
                if len(h) >= 3:
                    holes.append(h)
            child = hier[child][0]
        polys.append((outer, holes))

    if not polys:
        return ""
    out = []
    for outer, holes in polys:
        rings = [outer] + holes
        pts, paths, idx = [], [], 0
        for ring in rings:
            paths.append(list(range(idx, idx + len(ring))))
            pts.extend(ring); idx += len(ring)
        pts_s = "[" + ",".join("[%.3f,%.3f]" % (x, y) for x, y in pts) + "]"
        paths_s = "[" + ",".join("[" + ",".join(str(j) for j in p) + "]" for p in paths) + "]"
        out.append(f"    polygon(points={pts_s}, paths={paths_s});")
    # A tiny ROUNDED offset() runs the polygons through Clipper, welding the
    # single-point "pinch" junctions left by diagonally-touching pixels (which
    # make a raw extrude non-manifold under CGAL). Rounded (r=) — not delta= —
    # so sharp tips (e.g. star/ray points) don't shoot out a long miter spike.
    return "offset(r=0.06, $fn=8) {\n" + "\n".join(out) + "\n}"


def icon_layer_scad(in_path, box_w_mm, box_h_mm, max_res=360,
                    dark_thresh=80, white_thresh=238, simplify_px=0.75):
    """Return smooth 2D OpenSCAD polygon code for the icon's black-outline layer
    and colour-fill layer, contain-fitted into the given box. The caller wraps
    each with translate()+linear_extrude() at the desired heights."""
    a, lum = _load_autocropped(in_path, max_res, white_thresh)
    Hc, Wc = lum.shape
    white = lum > white_thresh
    dark = lum < dark_thresh
    color = (~white) & (~dark)
    cell = min(box_w_mm / Wc, box_h_mm / Hc)
    return {
        "outline_2d": mask_to_scad_2d(dark, cell, simplify_px),
        "color_2d": mask_to_scad_2d(color, cell, simplify_px),
        "cell_mm": cell, "width_mm": Wc * cell, "height_mm": Hc * cell,
    }


def icon_aspect(in_path, max_res=200, white_thresh=238):
    """Width/height aspect of the icon's non-background content (after autocrop).
    >1 means wider than tall (a landscape candidate)."""
    _, lum = _load_autocropped(in_path, max_res, white_thresh)
    h, w = lum.shape
    return (w / h) if h else 1.0


# A small SHARED filament palette every icon colour is snapped to, so the whole
# catalogue reuses a limited set of filaments (the "minimize colour changes"
# goal). Black (outline/text) and white (plaque/void) are handled separately.
FILAMENT_PALETTE = {
    "red":    (196,  54,  44),
    "blue":   ( 46, 110, 185),
    "navy":   ( 32,  54, 104),
    "teal":   ( 40, 150, 150),
    "green":  ( 60, 140,  75),
    "grey":   (150, 150, 150),
    "silver": (200, 202, 205),
    "tan":    (205, 170, 110),
    "lightbrown": (195, 150,  85),
    "midbrown":   (165, 100,  45),
    "brown":  (120,  78,  46),
    "orange": (226, 122,  55),
    "yellow": (234, 198,  58),
    "purple": (132,  72, 160),
    "pink":   (221, 123, 162),
}


def icon_color_layers(in_path, box_w_mm, box_h_mm, max_res=560, dark_thresh=80,
                      white_thresh=238, simplify_px=0.4, max_colors=3,
                      min_frac=0.03):
    """Separate a flat screen-print icon into its distinct printable colours.

    White stays void (plaque shows through); the darkest pixels become the black
    OUTLINE. The remaining fill pixels are snapped to the nearest entries in the
    shared FILAMENT_PALETTE, the largest ``max_colors`` are kept (tiny ones are
    folded into the nearest kept colour so no holes appear), and each kept colour
    is traced into smooth 2D polygons. The caller assigns heights and extrudes.

    Returns: { cell_mm, width_mm, height_mm, outline_2d, fills: [ {name, rgb,
    poly2d, area} ... ] } ordered largest-area first.
    """
    a, lum = _load_autocropped(in_path, max_res, white_thresh)
    Hc, Wc = lum.shape
    white = lum > white_thresh
    dark = lum < dark_thresh
    fill = (~white) & (~dark)
    cell = min(box_w_mm / Wc, box_h_mm / Hc)
    res = {"cell_mm": cell, "width_mm": Wc * cell, "height_mm": Hc * cell,
           "outline_2d": mask_to_scad_2d(dark, cell, simplify_px), "fills": []}
    if not fill.any():
        return res

    names = list(FILAMENT_PALETTE.keys())
    pal = np.array([FILAMENT_PALETTE[n] for n in names], dtype=np.float32)
    ys, xs = np.where(fill)
    px = a[ys, xs, :3].astype(np.float32)
    dist = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    lab = dist.argmin(1)                               # nearest palette idx per pixel
    counts = np.bincount(lab, minlength=len(names))
    total = int(lab.shape[0])
    order = [i for i in np.argsort(counts)[::-1] if counts[i] > 0]
    kept = [i for i in order if counts[i] >= max(min_frac * total, 24)][:max_colors]
    if not kept:
        kept = order[:1]
    # fold every fill pixel onto the nearest KEPT palette colour (no voids)
    keptpal = pal[kept]
    lab2 = ((px[:, None, :] - keptpal[None, :, :]) ** 2).sum(2).argmin(1)

    fills = []
    for kpos, pal_i in enumerate(kept):
        mask = np.zeros((Hc, Wc), dtype=bool)
        sel = lab2 == kpos
        if not sel.any():
            continue
        mask[ys[sel], xs[sel]] = True
        poly = mask_to_scad_2d(mask, cell, simplify_px)
        if not poly:
            continue
        fills.append({"name": names[pal_i], "rgb": [int(c) for c in pal[pal_i]],
                      "poly2d": poly, "area": float(sel.sum()) / total})
    fills.sort(key=lambda f: -f["area"])
    res["fills"] = fills
    return res


def convert_layers(in_path, outline_out, color_out, box_w_mm, box_h_mm,
                   center=(0.0, 0.0), plaque_top=1.2, outline_h=0.6,
                   color_h=1.2, max_res=200, dark_thresh=80, white_thresh=238):
    """Split a flat screen-print icon into two printable colour objects.

    Writes a black-OUTLINE STL (dark pixels, lower band) and a COLOUR STL (the
    mid-tone fills, taller band) as separate solids, both baked into their final
    plaque position so they line up in the slicer with no CGAL union. The icon
    is auto-cropped and scaled "contain" to fill the given middle box as large
    as possible. Returns geometry info incl. the colour layer's absolute z-top.
    """
    a, lum = _load_autocropped(in_path, max_res, white_thresh)
    Hc, Wc = lum.shape
    white = lum > white_thresh
    dark = lum < dark_thresh
    color = (~white) & (~dark)
    # contain-fit the working grid into the middle box (as large as possible)
    cell = min(box_w_mm / Wc, box_h_mm / Hc)
    cx, cy = center
    grid_cx = Wc * cell / 2.0
    grid_cy = Hc * cell / 2.0
    off = (cx, cy, plaque_top)

    def _flat(mask, height, out):
        level = mask.astype(np.int32)
        tris = build_columns_stl(level, cell, np.array([0.0, height], dtype=np.float32))
        write_binary_stl(tris, out, center=(grid_cx, grid_cy), offset=off)
        return len(tris)

    n_out = _flat(dark, outline_h, outline_out)
    n_col = _flat(color, color_h, color_out)
    return {
        "cell_mm": cell,
        "width_mm": Wc * cell,
        "height_mm": Hc * cell,
        "outline_tris": n_out,
        "color_tris": n_col,
        "outline_ztop": plaque_top + outline_h,
        "color_ztop": plaque_top + color_h,
    }


def convert(in_path, out_path, width_mm=60.0, tones=4, base=0.6, step=0.5,
            max_res=150, invert=False, min_frac=0.0, offset=(0.0, 0.0, 0.0)):
    img = Image.open(in_path)
    w, h = img.size
    s = min(1.0, max_res / max(w, h))
    img = img.resize((max(2, int(w * s)), max(2, int(h * s))), Image.LANCZOS)
    level = posterize_levels(img, tones, invert)
    # lightest band (0) is the white background -> void
    height_of = np.array([0.0] + [base + i * step for i in range(1, tones)], dtype=np.float32)
    Hc, Wc = level.shape
    cell = width_mm / Wc
    tris = build_columns_stl(level, cell, height_of)
    if not tris:
        # fallback: treat everything below mid as solid
        level = np.where(level == 0, 0, tones - 1)
        tris = build_columns_stl(level, cell, height_of)
    cx = Wc * cell / 2.0
    cy = Hc * cell / 2.0
    write_binary_stl(tris, out_path, center=(cx, cy), offset=offset)
    z_top = float(height_of[level].max()) if tris else 0.0
    return {"tris": len(tris), "width_mm": Wc * cell, "height_mm": Hc * cell,
            "z_top": z_top, "z_top_abs": z_top + offset[2]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=float, default=60.0)
    ap.add_argument("--tones", type=int, default=4)
    ap.add_argument("--base", type=float, default=0.6)
    ap.add_argument("--step", type=float, default=0.5)
    ap.add_argument("--max-res", type=int, default=150)
    ap.add_argument("--invert", action="store_true")
    a = ap.parse_args()
    info = convert(a.inp, a.out, a.width, a.tones, a.base, a.step, a.max_res, a.invert)
    print("wrote", a.out, info)


if __name__ == "__main__":
    main()
