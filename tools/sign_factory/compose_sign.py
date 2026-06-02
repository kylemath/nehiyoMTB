#!/usr/bin/env python3
"""
compose_sign.py — composite a finished sign PREVIEW (PNG) the way the physical
signs look: transliteration on top, the screen-print icon filling the middle,
the Cree SYLLABICS overlaid on top of the icon, and the English name at the
bottom. Pure Pillow + numpy.

Used by the sign factory for the Workbench's Draft-sign column, and runnable
standalone:

  python3 tools/sign_factory/compose_sign.py \
      --icon icon.png --en "Gold Digger" \
      --translit "osâwâ-sôniyâw omonahikêw" --syllabics "ᐅᓵᐚ ᓲᓂᔮᐤ" --out out.png
"""
import argparse, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---- fonts (macOS) -------------------------------------------------------- #
def _first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

LATIN_FONT = _first([
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Bold.ttf",
])
SYLL_FONT = _first([
    "/System/Library/Fonts/Supplemental/EuphemiaCAS.ttc",
    "/System/Library/Fonts/Supplemental/NotoSansCanadianAboriginal-Regular.otf",
])

PLAQUE = (243, 239, 230)     # cream
INK = (38, 38, 38)           # near-black text
SYLL_COLOR = (193, 59, 59)   # red syllabics
SYLL_HALO = (255, 255, 255)  # white outline behind syllabics


def _font(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.truetype(path, size)


def _wrap(draw, text, font, max_w):
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def _fit(draw, text, font_path, max_w, max_h, size_max, index=0, size_min=12):
    size = size_max
    while size >= size_min:
        f = _font(font_path, size, index)
        lines = _wrap(draw, text, f, max_w)
        widest = max(draw.textlength(l, font=f) for l in lines)
        asc, desc = f.getmetrics()
        lh = (asc + desc) * 1.12
        if widest <= max_w and lh * len(lines) <= max_h:
            return f, lines, lh
        size -= 2
    f = _font(font_path, size_min, index)
    return f, _wrap(draw, text, f, max_w), (sum(f.getmetrics())) * 1.12


def _draw_block(draw, lines, font, lh, cx, cy_center, fill, halo=None, halo_w=0):
    total = lh * len(lines)
    y = cy_center - total / 2
    for ln in lines:
        w = draw.textlength(ln, font=font)
        kw = dict(font=font, fill=fill)
        if halo and halo_w:
            kw.update(stroke_width=halo_w, stroke_fill=halo)
        draw.text((cx - w / 2, y), ln, **kw)
        y += lh


def key_white(icon, thresh=236):
    """make near-white background transparent."""
    icon = icon.convert("RGBA")
    a = np.array(icon)
    white = (a[:, :, 0] > thresh) & (a[:, :, 1] > thresh) & (a[:, :, 2] > thresh)
    a[:, :, 3] = np.where(white, 0, a[:, :, 3])
    return Image.fromarray(a)


def compose(icon_path, en, translit, syllabics, out_path,
            plaque_w=720, transparent_icon=True, number=None, orient="portrait"):
    W = plaque_w
    if orient == "landscape":
        # wide short plaque (matches the 138x73 landscape print); proportionally
        # taller text strips and a full-width icon band in the middle.
        H = int(round(W * 73 / 138))
        margin = int(W * 0.035)
        rad = int(W * 0.03)
        tl_top_f, tl_h_f, tl_font_f = 0.10, 0.20, 0.052
        en_bot_f, en_h_f, en_font_f = 0.90, 0.22, 0.078
        hole_top_f, hole_bot_f = 0.10, 0.90
        syll_font_f = 0.11
    else:
        H = int(round(W * 165 / 90))     # tall portrait plaque
        margin = int(W * 0.06)
        rad = int(W * 0.055)
        tl_top_f, tl_h_f, tl_font_f = 0.085, 0.10, 0.072
        en_bot_f, en_h_f, en_font_f = 0.915, 0.13, 0.11
        hole_top_f, hole_bot_f = 0.055, 0.945
        syll_font_f = 0.14

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, W - 2, H - 2], radius=rad, fill=PLAQUE,
                           outline=(170, 162, 148), width=3)
    # mounting holes (top/bottom on the vertical centreline)
    hr = int(W * 0.018)
    for hy in (int(H * hole_top_f), int(H * hole_bot_f)):
        draw.ellipse([W / 2 - hr, hy - hr, W / 2 + hr, hy + hr],
                     fill=(255, 255, 255), outline=(150, 145, 132), width=2)

    avail_w = W - 2 * margin
    # --- transliteration (top) ---
    # treat hyphens in compounds (e.g. "âhkamê-meskanaw") as wrap points so the
    # transliteration can break onto two lines and render at a larger size.
    tl_text = (translit or en).replace("-", " ")
    tl_top = int(H * tl_top_f)
    f_tl, tl_lines, lh_tl = _fit(draw, tl_text, LATIN_FONT, avail_w,
                                 H * tl_h_f, int(W * tl_font_f))
    _draw_block(draw, tl_lines, f_tl, lh_tl, W / 2,
                tl_top + lh_tl * len(tl_lines) / 2, INK)

    # --- English (bottom) ---
    en_bottom = int(H * en_bot_f)
    f_en, en_lines, lh_en = _fit(draw, en, LATIN_FONT, avail_w,
                                 H * en_h_f, int(W * en_font_f))
    _draw_block(draw, en_lines, f_en, lh_en, W / 2,
                en_bottom - lh_en * len(en_lines) / 2, INK)

    # --- icon (fills middle) ---
    icon_top = tl_top + lh_tl * len(tl_lines) + int(H * 0.02)
    icon_bot = en_bottom - lh_en * len(en_lines) - int(H * 0.02)
    box_w, box_h = avail_w, icon_bot - icon_top
    icon = Image.open(icon_path).convert("RGBA")
    if transparent_icon:
        icon = key_white(icon)
    iw, ih = icon.size
    s = min(box_w / iw, box_h / ih)
    icon = icon.resize((max(1, int(iw * s)), max(1, int(ih * s))), Image.LANCZOS)
    ix = int(W / 2 - icon.width / 2)
    iy = int(icon_top + (box_h - icon.height) / 2)
    img.alpha_composite(icon, (ix, iy))

    # --- syllabics OVERLAID on the icon (centered) ---
    icx, icy = W / 2, icon_top + box_h / 2
    f_sy, sy_lines, lh_sy = _fit(draw, syllabics or "", SYLL_FONT, avail_w * 0.92,
                                 box_h * 0.7, int(W * syll_font_f), index=0)
    halo = max(3, int(f_sy.size * 0.08))
    _draw_block(draw, sy_lines, f_sy, lh_sy, icx, icy, SYLL_COLOR,
                halo=SYLL_HALO, halo_w=halo)

    # --- group number badge (numbered minor-trail groups), top-right corner --- #
    if number is not None and str(number).strip():
        ntxt = str(number).strip()
        f_n = _font(LATIN_FONT, int(W * 0.13))
        nw = draw.textlength(ntxt, font=f_n)
        nasc, ndesc = f_n.getmetrics()
        nx = ix + icon.width - nw / 2 - int(W * 0.02)
        nx = min(nx, W - margin - nw / 2)
        ny = icon_top + (nasc + ndesc) / 2 + int(H * 0.005)
        nhalo = max(4, int(f_n.size * 0.10))
        draw.text((nx - nw / 2, ny - (nasc + ndesc) / 2), ntxt, font=f_n,
                  fill=SYLL_COLOR, stroke_width=nhalo, stroke_fill=SYLL_HALO)

    img.convert("RGB").save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--icon", required=True)
    ap.add_argument("--en", required=True)
    ap.add_argument("--translit", default="")
    ap.add_argument("--syllabics", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--number", default="", help="group number badge (top-right)")
    ap.add_argument("--orient", choices=["portrait", "landscape"], default="portrait")
    ap.add_argument("--no-key", action="store_true", help="don't key out white bg")
    a = ap.parse_args()
    compose(a.icon, a.en, a.translit, a.syllabics, a.out,
            transparent_icon=not a.no_key, number=a.number or None, orient=a.orient)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
