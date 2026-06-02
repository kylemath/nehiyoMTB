#!/usr/bin/env python3
"""Generate walters_folly_engraving.stl — a SINGLE solid that merges the plaque
backing and the triptych relief: a rounded-corner plaque (150x100) whose face IS
the inverted engraving (dark objects rise out of the recessed sky/water), with
the two screw holes bored straight through. Built as a heightfield column mesh
(no OpenSCAD/CGAL booleans, so it stays high-res and fast). Keep params in sync
with walters_folly.scad."""
import struct, math
import numpy as np
from PIL import Image, ImageOps, ImageFilter

PLQ_W, PLQ_H, PLQ_T = 138.0, 73.0, 1.2      # standard blank (landscape) + thickness
CORNER_R = 3.5                               # rounded corner radius
HOLE_R, HOLE_Y = 2.1, 18.5                   # screw holes: vertical centreline
                                             # (0,+Y)/(0,-Y) to screw onto a tree
TILE_Z = 1.6                                 # relief rise above the backing
RES_W = 360                                  # heightmap sampling columns
LEVELS = 2                                   # 2 = clean CAMEO (bold line-art shapes
                                             # raised over a flat field) — slices
                                             # legibly front-lit. (Photographic tone
                                             # only reads backlit, i.e. IllumiStack.)
BLUR = 0.5                                   # light denoise; keep line edges crisp
YEARS_CROP = 0.15                            # trim the year labels off the top so
                                             # the translit can sit in a clear band
# Bold line-art reads as a front-lit relief; the photographic grayscale
# (walters_folly_triptych_grayscale.png) is kept for the backlit IllumiStack final.
SRC = "walters_folly_triptych_lineart.png"
OUT = "walters_folly_engraving.stl"

# INVERT (black line-art -> tall lines), trim the year labels off the top, then
# centre-crop to the plaque aspect so the triptych fills 138x73 without distortion.
im = ImageOps.invert(Image.open(SRC).convert("L"))
w, h = im.size
im = im.crop((0, int(h * YEARS_CROP), w, h))
w2, h2 = im.size
target = PLQ_W / PLQ_H
if w2 / h2 < target:                               # too tall: trim height (centre)
    nh = int(round(w2 / target)); off = (h2 - nh) // 2
    im = im.crop((0, off, w2, off + nh))
else:                                              # too wide: trim width (centre)
    nw = int(round(h2 * target)); off = (w2 - nw) // 2
    im = im.crop((off, 0, off + nw, h2))
RES_H = round(RES_W * PLQ_H / PLQ_W)
im = im.resize((RES_W, RES_H), Image.LANCZOS)
im = im.filter(ImageFilter.GaussianBlur(radius=BLUR))
val = np.asarray(im, dtype=np.float32) / 255.0     # 0..1 (1 = tall object)
val = np.round(val * (LEVELS - 1)) / (LEVELS - 1)  # 2-level cameo

W, H = RES_W, RES_H
cell = PLQ_W / W
hw, hh = PLQ_W / 2.0, PLQ_H / 2.0

ys, xs = np.mgrid[0:H, 0:W]
mmx = (xs + 0.5) * cell - hw
mmy = (ys + 0.5) * cell - hh
dx, dy = np.abs(mmx), np.abs(mmy)
inside = (dx <= hw) & (dy <= hh)
corner = (dx > hw - CORNER_R) & (dy > hh - CORNER_R)
cdist = (dx - (hw - CORNER_R)) ** 2 + (dy - (hh - CORNER_R)) ** 2
inside &= (~corner) | (cdist <= CORNER_R ** 2)
hole = ((mmx ** 2 + (mmy - HOLE_Y) ** 2) <= HOLE_R ** 2) | \
       ((mmx ** 2 + (mmy + HOLE_Y) ** 2) <= HOLE_R ** 2)
height = np.where(inside & (~hole), PLQ_T + val * TILE_Z, 0.0).astype(np.float32)

tris = []
def quad(a, b, c, d): tris.append((a, b, c)); tris.append((a, c, d))
hgt = height
for y in range(H):
    row = hgt[y]
    for x in range(W):
        z = row[x]
        if z <= 0: continue
        X0, X1 = x * cell, (x + 1) * cell
        Y0, Y1 = (H - y - 1) * cell, (H - y) * cell
        quad((X0, Y0, z), (X1, Y0, z), (X1, Y1, z), (X0, Y1, z))   # top
        quad((X0, Y0, 0), (X0, Y1, 0), (X1, Y1, 0), (X1, Y0, 0))   # bottom
        rh = hgt[y, x + 1] if x + 1 < W else 0
        lh = hgt[y, x - 1] if x - 1 >= 0 else 0
        dh = hgt[y + 1, x] if y + 1 < H else 0
        uh = hgt[y - 1, x] if y - 1 >= 0 else 0
        if rh < z: quad((X1, Y0, rh), (X1, Y1, rh), (X1, Y1, z), (X1, Y0, z))
        if lh < z: quad((X0, Y1, lh), (X0, Y0, lh), (X0, Y0, z), (X0, Y1, z))
        if dh < z: quad((X0, Y0, dh), (X1, Y0, dh), (X1, Y0, z), (X0, Y0, z))
        if uh < z: quad((X1, Y1, uh), (X0, Y1, uh), (X0, Y1, z), (X1, Y1, z))

ox, oy = W * cell / 2.0, H * cell / 2.0
buf = bytearray(84 + len(tris) * 50)
struct.pack_into("<I", buf, 80, len(tris))
o = 84
for (ax, ay, az), (bx, by, bz), (cx3, cy3, cz3) in tris:
    ax -= ox; bx -= ox; cx3 -= ox
    ay -= oy; by -= oy; cy3 -= oy
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx3 - ax, cy3 - ay, cz3 - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    struct.pack_into("<12fH", buf, o, nx / ln, ny / ln, nz / ln,
                     ax, ay, az, bx, by, bz, cx3, cy3, cz3, 0)
    o += 50
open(OUT, "wb").write(buf)
print(f"wrote {OUT}: {len(tris)} tris, {(84+len(tris)*50)/1e6:.1f}MB")
