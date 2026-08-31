#!/usr/bin/env python3
"""Export the sign catalogue into app + database trail datasets.

Reads docs/catalogue.json (the source of truth for the sign set) and writes:
  - mobile/src/data/trails.json        bundled offline trail data for the app
  - mobile/assets/trail-icons/         STL-rendered sign icons (small, fast)
  - mobile/src/data/trail-assets.ts    static require() map for the assets
  - supabase/seed.sql                  trails + signs reference rows

Run from the repo root:  python3 tools/export_trails_for_app.py
Whenever the docs catalogue changes, re-run this and the app picks it up.
"""

import glob
import json
import math
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE = os.path.join(ROOT, "docs", "catalogue.json")
DOCS_DIR = os.path.join(ROOT, "docs")
APP_OUT = os.path.join(ROOT, "mobile", "src", "data", "trails.json")
ASSETS_TS_OUT = os.path.join(ROOT, "mobile", "src", "data", "trail-assets.ts")
ICONS_DIR = os.path.join(ROOT, "mobile", "assets", "trail-icons")
SEED_OUT = os.path.join(ROOT, "supabase", "seed.sql")

MAX_TRACK_POINTS = 200  # keep the bundled polylines light
# The STL sign icon is the only artwork the app ships per trail; it is used
# for map markers, list rows, and trail pages. Heavily downsampled + quantized
# so render/decode stays fast on device.
ICON_SIZE = 96


def haversine_m(a, b):
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


def track_length_m(track):
    return sum(haversine_m(track[i], track[i + 1]) for i in range(len(track) - 1))


def decimate(track, max_points):
    if len(track) <= max_points:
        return track
    step = (len(track) - 1) / (max_points - 1)
    return [track[round(i * step)] for i in range(max_points)]


def sql_str(value):
    if value is None or value == "":
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def resolve_docs_path(src):
    """Catalogue paths look like '../assets/<folder>/...' relative to a docs page."""
    if not src:
        return None
    path = os.path.normpath(os.path.join(DOCS_DIR, src.lstrip("./").replace("../", "")))
    return path if os.path.exists(path) else None


# Trails without an STL map-icon render yet (generate one in the catalogue
# editor to replace these): best available sign art as an interim icon.
ICON_FALLBACKS = {
    "mistapiskihkoman": "assets/mistapiskihkoman/mistapiskihkoman.png",
    "nicocwasaskanos": "assets/nicocwasaskanos/nikocwasaskanos.png",
    "oyoyow": "assets/oyoyow/oyoyow_render.png",
    "coalminer_s_daughter": "assets/coalminer_s_daughter/coalminer_s_daughter_sign.png",
}


def find_icon_source(model):
    """Prefer the page's explicit STL-icon override, else newest map-icon PNG,
    else a hand-picked fallback render."""
    tf = (model.get("pageContent") or {}).get("trailforks") or {}
    explicit = resolve_docs_path(tf.get("iconSrc"))
    if explicit:
        return explicit
    folder = model.get("folder") or model["id"]
    candidates = glob.glob(os.path.join(DOCS_DIR, "assets", folder, "map-icons", "*.png"))
    if candidates:
        return max(candidates, key=os.path.getmtime)
    fallback = ICON_FALLBACKS.get(model["id"])
    if fallback:
        path = os.path.join(DOCS_DIR, fallback)
        if os.path.exists(path):
            return path
    return None


def export_icon(src, dest, size):
    """Trim transparent borders so the sign fills the image, keep the sign's
    real aspect ratio, downsample, quantize. Returns width/height ratio."""
    im = Image.open(src).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    if w >= h:
        nw, nh = size, max(1, round(size * h / w))
    else:
        nw, nh = max(1, round(size * w / h)), size
    im = im.resize((nw, nh), Image.LANCZOS)
    # Palette quantization (with alpha) roughly halves PNG size again.
    im = im.quantize(colors=128, method=Image.FASTOCTREE)
    im.save(dest, "PNG", optimize=True)
    return round(nw / nh, 3)


def main():
    with open(CATALOGUE) as f:
        catalogue = json.load(f)

    os.makedirs(ICONS_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(ICONS_DIR, "*.png")):
        os.remove(old)
    icon_ids = []
    icon_aspect = {}

    trails = []
    for model in catalogue.get("models", []):
        page = model.get("pageContent", {}) or {}
        tf = page.get("trailforks", {}) or {}
        track = tf.get("track") or []
        start = tf.get("mapCoords") or {}
        end = tf.get("mapEndCoords") or {}

        if not start and track:
            start = {"lat": track[0][0], "lng": track[0][1]}
        if not end and track:
            end = {"lat": track[-1][0], "lng": track[-1][1]}

        trail_id = model["id"]
        icon_src = find_icon_source(model)
        if icon_src:
            icon_aspect[trail_id] = export_icon(
                icon_src, os.path.join(ICONS_DIR, f"{trail_id}.png"), ICON_SIZE)
            icon_ids.append(trail_id)

        track = [[round(p[0], 6), round(p[1], 6)] for p in track]
        trails.append({
            "id": trail_id,
            "signNumber": model.get("signNumber"),
            "title": model.get("title") or trail_id,
            "englishName": model.get("englishName"),
            "creeName": model.get("creeName"),
            "creeSyllabics": model.get("creeSyllabics"),
            "description": model.get("description"),
            "status": model.get("status", "published"),
            "accentColor": page.get("accentColor") or "#1f6f54",
            "colors": model.get("colors") or [],
            "hasIcon": bool(icon_src),
            "trailforksUrl": tf.get("trailUrl"),
            "difficulty": tf.get("difficulty"),
            "start": {"lat": start.get("lat"), "lng": start.get("lng")} if start else None,
            "end": {"lat": end.get("lat"), "lng": end.get("lng")} if end else None,
            "lengthM": round(track_length_m(track), 1) if len(track) > 1 else None,
            "track": decimate(track, MAX_TRACK_POINTS),
        })

    mapped = [t for t in trails if t["start"] and t["start"]["lat"] is not None]
    os.makedirs(os.path.dirname(APP_OUT), exist_ok=True)
    with open(APP_OUT, "w") as f:
        json.dump({"generatedFrom": "docs/catalogue.json", "trails": trails}, f,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {APP_OUT}: {len(trails)} trails ({len(mapped)} with map data)")

    # Static require() map — Metro needs literal paths, so we generate them.
    ts = [
        "// Generated by tools/export_trails_for_app.py — do not edit by hand.",
        "// STL-rendered sign icons from docs/assets, shared with the web app.",
        "",
        "export const trailIcons: Record<string, number> = {",
    ]
    ts += [f"  '{tid}': require('@/assets/trail-icons/{tid}.png')," for tid in icon_ids]
    ts += [
        "};",
        "",
        "/** width / height of each trimmed sign icon. */",
        "export const trailIconAspect: Record<string, number> = {",
    ]
    ts += [f"  '{tid}': {icon_aspect[tid]}," for tid in icon_ids]
    ts += ["};", ""]
    with open(ASSETS_TS_OUT, "w") as f:
        f.write("\n".join(ts))
    print(f"wrote {ASSETS_TS_OUT}: {len(icon_ids)} icons")

    lines = [
        "-- Generated by tools/export_trails_for_app.py — do not edit by hand.",
        "begin;",
        "delete from public.signs;",
        "delete from public.trails;",
    ]
    for t in trails:
        s, e = t["start"] or {}, t["end"] or {}
        track_json = json.dumps(t["track"], separators=(",", ":"))
        lines.append(
            "insert into public.trails (id, sign_number, title, english_name, cree_name,"
            " cree_syllabics, start_lat, start_lng, end_lat, end_lng, length_m, track, status,"
            " difficulty)"
            f" values ({sql_str(t['id'])}, {t['signNumber'] or 'null'}, {sql_str(t['title'])},"
            f" {sql_str(t['englishName'])}, {sql_str(t['creeName'])}, {sql_str(t['creeSyllabics'])},"
            f" {s.get('lat') or 'null'}, {s.get('lng') or 'null'},"
            f" {e.get('lat') or 'null'}, {e.get('lng') or 'null'},"
            f" {t['lengthM'] or 'null'}, {sql_str(track_json)}::jsonb, {sql_str(t['status'])},"
            f" {sql_str(t['difficulty'])});"
        )
        for kind, coords in (("start", s), ("end", e)):
            if coords.get("lat") is not None:
                lines.append(
                    "insert into public.signs (id, trail_id, kind, lat, lng) values"
                    f" ({sql_str(t['id'] + ':' + kind)}, {sql_str(t['id'])}, {sql_str(kind)},"
                    f" {coords['lat']}, {coords['lng']});"
                )
    lines.append("commit;")
    with open(SEED_OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {SEED_OUT}")


if __name__ == "__main__":
    main()
