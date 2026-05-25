#!/usr/bin/env python3
"""Render kiwapamitin-style sign pages from catalogue.json pageContent.

For each sign object whose ``pageContent.pageStatus`` is past ``draft``, this
script regenerates ``docs/{folder}/index.html`` from the structured
``pageContent`` data. The exemplar page ``docs/kiwapamitin/index.html`` is the
visual reference; the renderer reproduces the same DOM and JS for cross-
highlighting between SRO and syllabics.

CLI usage::

    python3 tools/sign_page_renderer.py                 # render every eligible sign
    python3 tools/sign_page_renderer.py kahkakiw kakwa  # render only the listed sign ids
    python3 tools/sign_page_renderer.py --force kahkakiw # render even when status is draft

The script never touches signs whose ``pageContent`` is missing unless
``--force`` is passed, and it never renames or relocates files. It only
overwrites the public ``index.html`` for the sign.
"""

from __future__ import annotations

import argparse
import json
import math
from html import escape
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
# The sign catalogue lives next to docs/index.html so the static page can
# read it with a relative fetch on GitHub Pages. The repo-root catalogue.json
# is an unrelated stub for the author's GitHub-file-organization API.
CATALOGUE_PATH = DOCS_ROOT / "catalogue.json"

RENDERABLE_STATUSES = {"agent-drafted", "user-reviewed", "published"}
DEFAULT_SOURCES = {
    "itwêwina": "https://itwewina.altlab.app/",
    "Online Cree Dictionary": "https://www.creedictionary.com/",
    "Plains Cree Dictionary": "https://dictionary.plainscree.atlas-ling.ca/",
    "Plains Cree Dictionary (ADP)": "https://dictionary.plainscree.atlas-ling.ca/",
}


def load_catalogue() -> dict:
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def model_page_folder(model: dict) -> Path:
    page_path = model.get("pagePath") or f"{model.get('folder', '')}/"
    page_path = page_path.rstrip("/")
    return DOCS_ROOT / page_path


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return (220, 53, 69)
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return (220, 53, 69)


def mix_hex(color: str, towards: str, ratio: float) -> str:
    base = hex_to_rgb(color)
    target = hex_to_rgb(towards)
    mixed = tuple(int(round(base[i] * (1 - ratio) + target[i] * ratio)) for i in range(3))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def darken_hex(color: str, ratio: float = 0.18) -> str:
    return mix_hex(color, "#000000", ratio)


def soften_hex(color: str, ratio: float = 0.82) -> str:
    return mix_hex(color, "#ffffff", ratio)


def build_css(accent: str) -> str:
    accent2 = darken_hex(accent, 0.18)
    primary_bg = soften_hex(accent, 0.85)
    secondary_bg = soften_hex(accent, 0.92)
    formula_bg = soften_hex(accent, 0.96)
    return f"""    :root{{
      --bg:#f8f9fa;--panel:#ffffff;--muted:#6c757d;--text:#000000;--accent:{accent};--accent2:{accent2};--line:#dee2e6;--chip:#e9ecef;--ok:{accent};--primary-bg:{primary_bg};--primary-text:#000000;--formula-bg:{formula_bg};--formula-border:{accent};--secondary-bg:{secondary_bg};--secondary-border:{soften_hex(accent, 0.7)}
    }}
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";background:var(--bg);color:var(--text);line-height:1.6}}
    a{{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}}
    a:hover{{border-bottom-color:var(--accent)}}
    .container{{max-width:1100px;margin:0 auto;padding:16px}}
    header{{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:center;padding:20px;border-bottom:3px solid var(--accent);margin-bottom:16px;background:linear-gradient(135deg, var(--primary-bg) 0%, #ffffff 100%);border-radius:12px 12px 0 0;text-align:center}}
    .title{{display:flex;flex-direction:column;gap:8px;align-items:center;width:100%}}
    .tag{{background:rgba(255,255,255,0.9);border:1px solid var(--accent);padding:6px 14px;border-radius:999px;color:var(--primary-text);font-size:13px;font-weight:600}}
    h1{{font-size:32px;margin:0;color:var(--primary-text);font-weight:900;letter-spacing:-0.02em}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}}
    .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
    .panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05);height:100%}}
    .panel h2{{font-size:18px;margin:0 0 14px 0;color:var(--primary-text);font-weight:800;padding-bottom:8px;border-bottom:3px solid var(--primary-bg)}}
    .panel h3{{font-size:17px;margin:14px 0 10px 0;color:#000000;font-weight:800;padding-left:10px;border-left:4px solid var(--accent)}}
    .row{{display:flex;flex-wrap:nowrap;align-items:center;gap:8px}}
    .sro{{font-weight:700;font-size:20px;color:#000000;padding:8px 12px;background:var(--primary-bg);border-radius:8px;border:2px solid var(--secondary-border);white-space:nowrap}}
    .syll{{font-size:20px;color:#000000;background:var(--primary-bg);padding:6px 12px;border-radius:8px;font-weight:600;border:2px solid var(--secondary-border)}}
    .muted{{color:var(--muted);font-size:15px}}
    .chips{{display:flex;flex-wrap:wrap;gap:8px}}
    .chip{{background:var(--chip);border:1px solid var(--line);padding:7px 11px;border-radius:8px;font-weight:600;font-size:15px}}
    .copy{{background:#ffffff;color:#000000;border:2px solid var(--line);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:11px;font-weight:600;transition:all 0.15s;white-space:nowrap;flex-shrink:0}}
    .copy:hover{{background:var(--accent);color:white;border-color:var(--accent)}}
    .formula{{font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;background:var(--formula-bg);border:2px solid var(--formula-border);padding:12px 14px;border-radius:10px;font-weight:500;box-shadow:0 2px 4px rgba(0,0,0,0.05);display:flex;align-items:center;flex-wrap:wrap;gap:4px}}
    .parts{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}}
    .part{{padding:7px 11px;border-radius:8px;border:2px solid var(--line);background:#ffffff;cursor:pointer;font-weight:600;transition:all 0.15s}}
    .part:hover{{border-color:var(--accent);transform:translateY(-1px)}}
    .part[data-active="true"]{{outline:2px solid var(--accent);background:var(--primary-bg);border-color:var(--accent)}}
    .syll-part{{padding:7px 11px;border-radius:8px;border:2px solid var(--line);background:#ffffff;cursor:pointer;font-weight:600;transition:all 0.15s;font-size:18px}}
    .syll-part:hover{{border-color:var(--accent);transform:translateY(-1px)}}
    .syll-part[data-active="true"]{{outline:2px solid var(--accent);background:var(--primary-bg);border-color:var(--accent)}}
    .hint{{font-size:13px;color:var(--muted);font-weight:500;font-style:italic}}
    .syllabics-emphasis{{font-size:20px;font-weight:700;color:#000000;margin-top:8px;padding:8px 12px;background:var(--primary-bg);border-radius:8px;border:2px solid var(--secondary-border);display:flex;align-items:center;flex-wrap:wrap;gap:4px}}
    .trail-iframe{{width:100%;height:600px;border:2px solid var(--line);border-radius:12px;margin-top:12px}}
    .trail-mini-map-link{{display:block;color:inherit;text-decoration:none;border-bottom:0}}
    .trail-mini-map-link:hover{{border-bottom:0}}
    .trail-mini-map{{margin:12px 0;border:2px solid var(--line);border-radius:12px;overflow:hidden;background:linear-gradient(135deg, var(--secondary-bg), #ffffff);box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:transform 0.15s, box-shadow 0.15s}}
    .trail-mini-map-link:hover .trail-mini-map{{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,0.16)}}
    .trail-mini-map svg{{display:block;width:100%;height:auto}}
    .trail-mini-map-tile{{image-rendering:auto}}
    .trail-mini-map-halo{{fill:none;stroke:#ffffff;stroke-width:9;stroke-linecap:round;stroke-linejoin:round;opacity:0.95}}
    .trail-mini-map-track{{fill:none;stroke:var(--accent);stroke-width:5;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 1px 1px rgba(0,0,0,0.28))}}
    .trail-mini-map-dot{{stroke:#ffffff;stroke-width:3}}
    .trail-mini-map-attrib{{font-size:10px;fill:#5f6368;paint-order:stroke;stroke:#ffffff;stroke-width:3px;stroke-linejoin:round}}
    .trail-mini-map-caption{{padding:8px 10px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;text-align:left;background:rgba(255,255,255,0.82)}}
    .kvs{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}}
    .kv{{background:var(--secondary-bg);border:2px solid var(--secondary-border);border-radius:10px;padding:10px;box-shadow:0 1px 2px rgba(0,0,0,0.05)}}
    .kv strong{{color:#000000}}
    .table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.05)}}
    .table th,.table td{{padding:12px 14px;border-bottom:1px solid var(--line);font-size:15px}}
    .table th{{background:var(--secondary-bg);text-align:left;color:#000000;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.025em}}
    .table tr:hover{{background:#f8fafc}}
    .table tr:last-child td{{border-bottom:none}}
    .badge{{padding:3px 10px;border-radius:999px;border:1px solid var(--accent);background:rgba(255,255,255,0.9);color:var(--primary-text);font-size:12px;font-weight:600}}
    footer{{margin:24px 0 8px;color:var(--muted);text-align:center;font-size:13px}}
    @media (max-width: 960px){{.grid{{grid-template-columns:1fr}}}}
    @media (max-width: 640px){{.grid-2{{grid-template-columns:1fr}}}}
    .tooltip{{position:relative}}
    .tooltip:hover::after{{content:attr(data-tip);position:absolute;left:50%;transform:translateX(-50%);bottom:calc(100% + 8px);white-space:nowrap;background:#111827;color:#e5e7eb;font-size:12px;padding:6px 8px;border-radius:6px;border:1px solid #374151;pointer-events:none;z-index:100}}
    .primary-content{{background:#ffffff;border:3px solid var(--accent);border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05)}}
    .story-box{{background:linear-gradient(135deg, var(--formula-bg) 0%, #ffffff 100%);border:2px solid var(--accent);border-radius:12px;padding:16px;margin-top:16px}}"""


def collect_morpheme_keys(content: dict) -> set[str]:
    keys: set[str] = set()
    linguistics = content.get("linguistics") or {}
    for section in [linguistics.get("primarySection") or {}]:
        for morpheme in section.get("morphemes") or []:
            if morpheme.get("key"):
                keys.add(morpheme["key"])
    for form in linguistics.get("relatedForms") or []:
        for morpheme in form.get("morphemes") or []:
            if morpheme.get("key"):
                keys.add(morpheme["key"])
    return keys


def render_morpheme_row(
    morphemes: list[dict],
    section_id: str,
    final_word_sro: str | None = None,
    final_word_syll: str | None = None,
    include_arrow: bool = True,
) -> str:
    """Render the SRO row + syllabics row for a single morpheme breakdown."""
    sro_parts = []
    syll_parts = []
    for index, morpheme in enumerate(morphemes):
        key = escape(str(morpheme.get("key") or f"{section_id}-m{index}"))
        sro = escape(str(morpheme.get("sro") or ""))
        syll = escape(str(morpheme.get("syllabics") or ""))
        gloss = escape(str(morpheme.get("gloss") or ""))
        syll_id = f"{key}-syll"
        sro_parts.append(
            f'<span class="part tooltip" data-key="{key}" data-tip="{gloss}" data-syll-id="{syll_id}">{sro}</span>'
        )
        syll_parts.append(
            f'<span class="syll-part tooltip" data-key="{key}" data-tip="{escape(str(morpheme.get("sro") or ""))}" id="{syll_id}">{syll}</span>'
        )

    sro_row = "\n              ".join(sro_parts)
    syll_row = "\n              ".join(syll_parts)

    if final_word_sro and include_arrow:
        sro_row += f'\n              <span style="margin:0 8px">→</span>\n              <strong style="font-size:20px">{escape(final_word_sro)}</strong>'

    return sro_row, syll_row


def render_primary_section(content: dict, model: dict) -> str:
    linguistics = content.get("linguistics") or {}
    primary = linguistics.get("primarySection") or {}
    heading = escape(primary.get("heading") or "The Word")
    sro_combined = escape(primary.get("sro") or model.get("creeName") or "")
    syll_combined = escape(primary.get("syllabics") or model.get("creeSyllabics") or "")
    meaning = escape(linguistics.get("meaning") or model.get("englishName") or "")

    morphemes = primary.get("morphemes") or []
    if not morphemes and sro_combined:
        morphemes = [{
            "key": (model.get("id") or "word").replace("-", "_"),
            "sro": primary.get("sro") or model.get("creeName") or "",
            "syllabics": primary.get("syllabics") or model.get("creeSyllabics") or "",
            "gloss": meaning,
        }]

    sro_row, syll_row = render_morpheme_row(
        morphemes,
        section_id="primary",
        final_word_sro=sro_combined if len(morphemes) > 1 else None,
    )

    return f"""
        <div class="primary-content">
          <div style="font-size:36px;font-weight:900;color:var(--accent);margin-bottom:20px;text-align:center;letter-spacing:-0.02em">{sro_combined or meaning}</div>
          <div class="formula" style="justify-content:center;font-size:18px;margin-bottom:16px">
              {sro_row}
          </div>
          <div class="syllabics-emphasis" style="justify-content:center;font-size:22px">
              {syll_row}
          </div>
          <p style="text-align:center;margin:16px 0 0 0;color:#000000;font-size:17px;line-height:1.6;font-weight:600">&quot;{meaning}&quot;</p>
        </div>"""


def render_photo_block(content: dict) -> str:
    photo = content.get("photo") or {}
    src = photo.get("src")
    if not src:
        return ""
    alt = escape(photo.get("alt") or "Trail sign photo")
    caption = escape(photo.get("caption") or "")
    caption_html = (
        f'<p style="margin-top:8px;color:var(--muted);font-size:14px;font-style:italic">{caption}</p>'
        if caption
        else ""
    )
    return f"""
        <h2 style="margin-top:16px">Trail Sign Design</h2>
        <div style="text-align:center;margin-bottom:16px">
            <img src="{escape(src)}" alt="{alt}" style="max-width:100%;height:auto;border-radius:8px;border:2px solid var(--line);box-shadow:0 2px 4px rgba(0,0,0,0.1)">
            {caption_html}
        </div>"""


def render_story_block(story: dict | None) -> str:
    if not story:
        return ""
    heading = (story.get("heading") or "").strip()
    body = [p.strip() for p in (story.get("body") or []) if isinstance(p, str) and p.strip()]
    if not heading or not body:
        return ""
    paragraphs = "\n          ".join(
        f'<p style="margin:0 0 12px 0;font-size:15px;line-height:1.6">{p}</p>' for p in body
    )
    return f"""
        <div class="story-box">
          <h3 style="margin:0 0 12px 0;border:none;padding:0;font-size:18px">{escape(heading)}</h3>
          {paragraphs}
        </div>"""


def _has_trailforks_link(trail: dict) -> bool:
    return bool(
        str(trail.get("trailUrl") or "").strip()
        or str(trail.get("trailId") or "").strip()
        or str(trail.get("widgetUrl") or "").strip()
    )


def _strava_segment_id(trail: dict) -> str:
    segment_id = str(trail.get("stravaSegmentId") or "").strip()
    if segment_id:
        return segment_id
    display_name = str(trail.get("displayName") or "").strip()
    if display_name.isdigit() and len(display_name) >= 5 and not _has_trailforks_link(trail):
        return display_name
    return ""


def _trail_map_source(trail: dict) -> str:
    source = (trail.get("trailSource") or "").strip().lower()
    if source in {"trailforks", "strava"}:
        return source
    if trail.get("stravaSegmentUrl") or _strava_segment_id(trail):
        return "strava"
    return "trailforks"


def _track_points(trail: dict) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for point in trail.get("track") or []:
        if not isinstance(point, list) or len(point) != 2:
            continue
        lat, lng = point
        if isinstance(lat, bool) or isinstance(lng, bool):
            continue
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            continue
        points.append((float(lat), float(lng)))
    return points


def _mercator_pixel(lat: float, lng: float, zoom: int, tile_size: int = 256) -> tuple[float, float]:
    lat = max(-85.05112878, min(85.05112878, lat))
    lat_rad = math.radians(lat)
    scale = tile_size * (2**zoom)
    x = (lng + 180.0) / 360.0 * scale
    y = (
        1.0
        - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi
    ) / 2.0 * scale
    return x, y


def _build_map_preview(
    points: list[tuple[float, float]],
    *,
    width: int = 640,
    height: int = 260,
    padding: int = 36,
) -> dict[str, str]:
    if len(points) < 2:
        return {}

    chosen_zoom = 11
    chosen_pixels: list[tuple[float, float]] = []
    for zoom in range(17, 10, -1):
        pixels = [_mercator_pixel(lat, lng, zoom) for lat, lng in points]
        span_x = max(x for x, _y in pixels) - min(x for x, _y in pixels)
        span_y = max(y for _x, y in pixels) - min(y for _x, y in pixels)
        if span_x <= width - padding * 2 and span_y <= height - padding * 2:
            chosen_zoom = zoom
            chosen_pixels = pixels
            break

    if not chosen_pixels:
        chosen_pixels = [_mercator_pixel(lat, lng, chosen_zoom) for lat, lng in points]

    min_x = min(x for x, _y in chosen_pixels)
    max_x = max(x for x, _y in chosen_pixels)
    min_y = min(y for _x, y in chosen_pixels)
    max_y = max(y for _x, y in chosen_pixels)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    top_left_x = center_x - width / 2
    top_left_y = center_y - height / 2

    # Keep the SVG compact when a dense GPX has thousands of points.
    step = max(1, len(chosen_pixels) // 350)
    sampled = chosen_pixels[::step]
    if sampled[-1] != chosen_pixels[-1]:
        sampled.append(chosen_pixels[-1])

    coords = [
        f"{(x - top_left_x):.1f},{(y - top_left_y):.1f}"
        for x, y in sampled
    ]
    start_x, start_y = chosen_pixels[0]
    end_x, end_y = chosen_pixels[-1]

    tile_size = 256
    tile_count = 2**chosen_zoom
    tile_min_x = math.floor(top_left_x / tile_size)
    tile_max_x = math.floor((top_left_x + width) / tile_size)
    tile_min_y = max(0, math.floor(top_left_y / tile_size))
    tile_max_y = min(tile_count - 1, math.floor((top_left_y + height) / tile_size))

    tile_html = []
    for tile_y in range(tile_min_y, tile_max_y + 1):
        for tile_x in range(tile_min_x, tile_max_x + 1):
            wrapped_x = tile_x % tile_count
            x = tile_x * tile_size - top_left_x
            y = tile_y * tile_size - top_left_y
            href = f"https://a.basemaps.cartocdn.com/light_all/{chosen_zoom}/{wrapped_x}/{tile_y}.png"
            tile_html.append(
                f'<image class="trail-mini-map-tile" href="{href}" x="{x:.1f}" y="{y:.1f}" width="{tile_size}" height="{tile_size}" />'
            )

    return {
        "points": " ".join(coords),
        "tiles": "\n                ".join(tile_html),
        "startX": f"{start_x - top_left_x:.1f}",
        "startY": f"{start_y - top_left_y:.1f}",
        "endX": f"{end_x - top_left_x:.1f}",
        "endY": f"{end_y - top_left_y:.1f}",
    }


def render_track_mini_map(
    trail: dict,
    *,
    link_url: str = "",
    link_label: str = "linked trail page",
) -> str:
    points = _track_points(trail)
    preview = _build_map_preview(points)
    if not preview:
        return ""

    point_count = len(points)
    mini_map = f"""
            <div class="trail-mini-map" aria-label="Uploaded GPX trail preview on a basemap">
              <svg viewBox="0 0 640 260" role="img" aria-label="Trail preview from uploaded GPX">
                <defs>
                  <linearGradient id="trailPreviewBg" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0%" stop-color="#f7f8fa" />
                    <stop offset="100%" stop-color="#eef1f5" />
                  </linearGradient>
                </defs>
                <rect x="0" y="0" width="640" height="260" fill="url(#trailPreviewBg)" />
                {preview["tiles"]}
                <rect x="0" y="0" width="640" height="260" fill="rgba(255,255,255,0.08)" />
                <polyline class="trail-mini-map-halo" points="{preview["points"]}" />
                <polyline class="trail-mini-map-track" points="{preview["points"]}" />
                <circle class="trail-mini-map-dot" cx="{preview["startX"]}" cy="{preview["startY"]}" r="6" fill="#22c55e" />
                <circle class="trail-mini-map-dot" cx="{preview["endX"]}" cy="{preview["endY"]}" r="6" fill="#ef4444" />
                <text class="trail-mini-map-attrib" x="632" y="250" text-anchor="end">© OpenStreetMap © CARTO</text>
              </svg>
              <div class="trail-mini-map-caption">Uploaded GPX over map context: {point_count} track points. Click to open the {escape(link_label)}.</div>
            </div>"""
    if link_url:
        return (
            f'<a class="trail-mini-map-link" href="{escape(link_url)}" '
            f'target="_blank" rel="noopener noreferrer">{mini_map}</a>'
        )
    return mini_map


def render_trailforks_block(content: dict) -> str:
    trail = content.get("trailforks") or {}
    trail_source = _trail_map_source(trail)
    display_name = trail.get("displayName") or ""

    if trail_source == "strava":
        segment_id = _strava_segment_id(trail)
        segment_url = str(trail.get("stravaSegmentUrl") or "").strip()
        if not segment_url and segment_id:
            segment_url = f"https://www.strava.com/segments/{segment_id}"

        if not segment_url:
            return """
        <h2>Trail Information</h2>
        <p style="margin:0 0 12px 0">Explore the trail segment on Strava for maps, efforts, and details.</p>
        <div style="text-align:center;margin-bottom:24px">
            <p class="muted" style="margin:2rem 0">Trail information coming soon</p>
        </div>"""

        link_html = (
            f'<div style="margin-top:8px"><a href="{escape(segment_url)}" style="font-size: 0.7em;">'
            f"{escape(display_name) if display_name else escape(segment_url)}</a></div>"
        )
        mini_map_html = render_track_mini_map(
            trail,
            link_url=segment_url,
            link_label="Strava segment",
        )
        track_note = ""
        if not mini_map_html and trail.get("track"):
            track_note = (
                '<p class="muted" style="margin:1rem 0 0;font-size:0.85em">'
                "Trail line on the site map comes from your uploaded GPX.</p>"
            )
        return f"""
        <h2>Trail Information</h2>
        <p style="margin:0 0 12px 0">Explore the trail segment on Strava, with a local preview from the uploaded GPX.</p>
        <div style="text-align:center;margin-bottom:24px">
            {mini_map_html}
            {link_html}
            {track_note}
        </div>"""

    widget_url = trail.get("widgetUrl")
    trail_url = trail.get("trailUrl")
    map_embed_mode = str(trail.get("mapEmbedMode") or "").strip().lower()
    use_local_map = map_embed_mode == "local" or (not widget_url and bool(trail.get("track")))

    mini_map_html = ""
    if use_local_map:
        mini_map_html = render_track_mini_map(
            trail,
            link_url=trail_url,
            link_label="Trailforks trail page",
        )

    if not widget_url and not trail_url and not mini_map_html:
        return """
        <h2>Trail Information</h2>
        <p style="margin:0 0 12px 0">Explore the trail on Trailforks for maps, conditions, and details.</p>
        <div style="text-align:center;margin-bottom:24px">
            <p class="muted" style="margin:2rem 0">Trail information coming soon</p>
        </div>"""

    widget_html = ""
    if widget_url and not mini_map_html:
        widget_html = f'<iframe width="100%" height="350" frameborder="0" src="{escape(widget_url)}"></iframe>'

    link_html = ""
    if trail_url:
        link_html = (
            f'<div style="margin-top:8px"><a href="{escape(trail_url)}" style="font-size: 0.7em;">'
            f"{escape(display_name) if display_name else escape(trail_url)}</a></div>"
        )

    return f"""
        <h2>Trail Information</h2>
        <p style="margin:0 0 12px 0">Explore the trail on Trailforks{', with a local preview from the uploaded GPX' if mini_map_html else ' for maps, conditions, and details'}.</p>
        <div style="text-align:center;margin-bottom:24px">
            {mini_map_html}
            {widget_html}
            {link_html}
        </div>"""


def render_related_form(form: dict, suffix: str) -> str:
    english = escape(form.get("english") or "")
    sro = escape(form.get("sro") or "")
    syll = escape(form.get("syllabics") or "")
    note = (form.get("note") or "").strip()

    morphemes = form.get("morphemes") or []
    if morphemes:
        sro_row, syll_row = render_morpheme_row(
            morphemes,
            section_id=f"form{suffix}",
            final_word_sro=sro if len(morphemes) > 1 else None,
        )
        body = f"""
          <div class="formula">
              {sro_row}
          </div>
          <div class="syllabics-emphasis">
              {syll_row}
          </div>"""
    else:
        body = f"""
          <div class="formula" style="justify-content:flex-start"><strong>{sro}</strong></div>
          <div class="syllabics-emphasis"><span class="syll-part">{syll}</span></div>"""

    note_html = (
        f'<p style="margin-top:8px;color:var(--accent);font-size:15px;font-weight:600;font-style:italic">{escape(note)}</p>'
        if note
        else ""
    )

    return f"""
          <div class="kv" style="margin-top:12px">
            <div style="font-size:17px;font-weight:800;color:#000000;margin-bottom:8px">English: &quot;{english}&quot;</div>{body}
            {note_html}
          </div>"""


def render_related_forms_section(content: dict) -> str:
    linguistics = content.get("linguistics") or {}
    forms = linguistics.get("relatedForms") or []
    if not forms:
        return ""

    primary = linguistics.get("primarySection") or {}
    has_breakdown = bool((primary.get("morphemes") or [])) and len(primary.get("morphemes") or []) > 1
    heading = "Building Other Forms" if has_breakdown else "Word Forms & Related Terms"

    rendered = "\n".join(render_related_form(form, str(index)) for index, form in enumerate(forms))
    return f"""
        <h2>{heading}</h2>
{rendered}"""


def render_quick_reference(content: dict) -> str:
    linguistics = content.get("linguistics") or {}
    rows = linguistics.get("quickReference") or []
    if not rows:
        # Fall back to assembling from primary + related
        primary = linguistics.get("primarySection") or {}
        derived: list[dict] = []
        if primary.get("sro"):
            derived.append({
                "english": linguistics.get("meaning") or "",
                "sro": primary.get("sro"),
                "syllabics": primary.get("syllabics") or "",
            })
        for form in linguistics.get("relatedForms") or []:
            derived.append({
                "english": form.get("english") or "",
                "sro": form.get("sro") or "",
                "syllabics": form.get("syllabics") or "",
            })
        rows = derived

    if not rows:
        return ""

    body_rows = []
    for row in rows:
        english = escape(row.get("english") or "")
        sro = escape(row.get("sro") or "")
        syll = escape(row.get("syllabics") or "")
        note = (row.get("note") or "").strip()
        sro_cell = (
            f'<td class="tooltip" data-tip="{escape(note)}">{sro}</td>' if note else f"<td>{sro}</td>"
        )
        body_rows.append(f"<tr><td>{english}</td>{sro_cell}<td>{syll}</td></tr>")

    body = "\n              ".join(body_rows)
    return f"""
        <h2 style="margin-top:24px">Examples &amp; Sources</h2>
        <h3 style="margin:0 0 12px 0">Quick reference</h3>
        <table class="table">
          <thead>
            <tr><th>English</th><th>SRO</th><th>Syllabics</th></tr>
          </thead>
          <tbody>
              {body}
          </tbody>
        </table>"""


def render_base_words(content: dict) -> str:
    linguistics = content.get("linguistics") or {}
    base_words = linguistics.get("baseWords") or []
    if not base_words:
        return ""
    rows = []
    for word in base_words:
        sro = escape(word.get("sro") or "")
        english = escape(word.get("english") or "")
        syll = escape(word.get("syllabics") or "")
        rows.append(
            f'<div class="row" style="margin-top:6px"><span class="chip">{sro}</span>'
            f'<span class="muted">= &quot;{english}&quot;</span><span class="chip">{syll}</span>'
            f'<button class="copy" data-copy-text="{sro}">Copy</button></div>'
        )
    body = "\n          ".join(rows)
    return f"""
        <h3 style="margin:18px 0 12px 0">Base words</h3>
        {body}"""


def render_sources(content: dict) -> str:
    sources = content.get("sources") or list(DEFAULT_SOURCES.keys())[:3]
    links = []
    for source in sources:
        url = DEFAULT_SOURCES.get(source)
        if url:
            links.append(
                f'<a href="{escape(url)}" target="_blank" rel="noreferrer">{escape(source)}</a>'
            )
        else:
            links.append(escape(source))
    refs_html = ", ".join(links)
    return f"""
        <h3 style="margin:18px 0 12px 0">Sources</h3>
        <p class="muted">SRO uses ê î ô â. Syllabics match the SRO shown.</p>
        <p class="muted">Dialectal preferences may affect minor spelling choices; check local norms for signage.</p>
        <p class="muted">References: {refs_html}</p>"""


def build_pairs_script(content: dict) -> str:
    keys = collect_morpheme_keys(content)
    if not keys:
        return ""
    pair_objs = ",\n        ".join(
        f"{{sro: '[data-key=\"{key}\"]', syll: '#{key}-syll'}}" for key in sorted(keys)
    )
    return f"const pairs = [\n        {pair_objs}\n      ];"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{title_text} • Interactive Poster</title>
    <style>
{css}
    </style>
  </head>
  <body>
    <div class=\"container\">
      <header>
        <div class=\"title\">
          <h1>{header_title}</h1>
          <span class=\"tag\">Interactive Poster • Plains Cree (nēhiyawēwin)</span>
          <div style=\"margin-top:12px\">
            <a href=\"../index.html\" target=\"_top\" style=\"color:var(--accent);font-size:14px;font-weight:600;text-decoration:none;border-bottom:1px solid var(--accent)\">← Back to Catalogue</a>
          </div>
        </div>
      </header>

      <section class=\"grid\">
        <div class=\"panel\">
          <h2>{primary_heading}</h2>
{primary_section}
{photo_block}
{cultural_story}
{trail_story}
        </div>

        <div class=\"panel\">
{trailforks}
{related_forms}
{quick_reference}
{base_words}
{sources}
        </div>
      </section>

      <footer>
        {footer_text}
      </footer>
    </div>

    <script>
      {pairs_script}

      document.querySelectorAll('.part').forEach(p=>{{
        p.addEventListener('mouseenter',()=>{{
          const key = p.getAttribute('data-key');
          const syllId = p.getAttribute('data-syll-id');
          if (syllId) {{
            const syllElem = document.getElementById(syllId);
            if (syllElem) {{
              syllElem.setAttribute('data-active', 'true');
            }}
          }}
          p.setAttribute('data-active','true');
        }});
        p.addEventListener('mouseleave',()=>{{
          const syllId = p.getAttribute('data-syll-id');
          if (syllId) {{
            const syllElem = document.getElementById(syllId);
            if (syllElem) {{
              syllElem.removeAttribute('data-active');
            }}
          }}
          p.removeAttribute('data-active');
        }});
      }});

      document.querySelectorAll('.syll-part[data-key]').forEach(s=>{{
        s.addEventListener('mouseenter',()=>{{
          const key = s.getAttribute('data-key');
          document.querySelectorAll(`[data-key=\"${{key}}\"].part`).forEach(p=>{{
            p.setAttribute('data-active', 'true');
          }});
          s.setAttribute('data-active','true');
        }});
        s.addEventListener('mouseleave',()=>{{
          const key = s.getAttribute('data-key');
          document.querySelectorAll(`[data-key=\"${{key}}\"].part`).forEach(p=>{{
            p.removeAttribute('data-active');
          }});
          s.removeAttribute('data-active');
        }});
      }});

      function copyText(text){{
        navigator.clipboard.writeText(text).then(()=>{{
          toast('Copied');
        }}).catch(()=>toast('Copy failed'));
      }}
      document.querySelectorAll('.copy').forEach(btn=>{{
        const sel = btn.getAttribute('data-copy');
        const direct = btn.getAttribute('data-copy-text');
        btn.addEventListener('click',()=>{{
          if (direct) return copyText(direct);
          const el = document.querySelector(sel);
          if (el) copyText(el.textContent.trim());
        }});
      }});

      function toast(msg){{
        const t = document.createElement('div');
        t.textContent = msg;
        t.style.position='fixed';t.style.bottom='14px';t.style.left='50%';
        t.style.transform='translateX(-50%)';t.style.background='#111827';
        t.style.color='#e5e7eb';t.style.padding='8px 12px';t.style.border='1px solid #374151';
        t.style.borderRadius='8px';t.style.zIndex='9999';t.style.opacity='0';
        t.style.transition='opacity .15s ease';
        document.body.appendChild(t);
        requestAnimationFrame(()=>t.style.opacity='1');
        setTimeout(()=>{{t.style.opacity='0';setTimeout(()=>t.remove(),200)}},1200);
      }}
    </script>
  </body>
</html>
"""


def render_page(model: dict) -> str | None:
    content = model.get("pageContent")
    if not content:
        return None

    english = model.get("englishName") or model.get("title") or model.get("id") or ""
    cree = model.get("creeName") or ""
    syllabics = model.get("creeSyllabics") or ""
    parts = [escape(english)]
    if syllabics:
        parts.append(escape(syllabics))
    if cree:
        parts.append(escape(cree))
    header_title = content.get("headerTitle") or " • ".join(parts)
    title_text = english or model.get("title") or "Trail Sign"

    primary = (content.get("linguistics") or {}).get("primarySection") or {}
    primary_heading = primary.get("heading") or "The Word"

    accent = content.get("accentColor") or "#dc3545"

    return PAGE_TEMPLATE.format(
        title_text=escape(title_text),
        header_title=header_title,
        css=build_css(accent),
        primary_heading=escape(primary_heading),
        primary_section=render_primary_section(content, model),
        photo_block=render_photo_block(content),
        cultural_story=render_story_block(content.get("culturalStory")),
        trail_story=render_story_block(content.get("trailStory")),
        trailforks=render_trailforks_block(content),
        related_forms=render_related_forms_section(content),
        quick_reference=render_quick_reference(content),
        base_words=render_base_words(content),
        sources=render_sources(content),
        footer_text=escape(
            f"{english} • {syllabics} • {cree} • Interactive Poster"
            if syllabics and cree
            else f"{english} • {cree or syllabics} • Interactive Poster"
            if (cree or syllabics)
            else f"{english} • Interactive Poster"
        ),
        pairs_script=build_pairs_script(content),
    )


def render_for_ids(ids: Iterable[str] | None, force: bool) -> list[dict]:
    catalogue = load_catalogue()
    target_ids = set(ids) if ids else None
    summaries: list[dict] = []

    for model in catalogue.get("models", []):
        model_id = model.get("id")
        if target_ids is not None and model_id not in target_ids:
            continue

        content = model.get("pageContent")
        status = (content or {}).get("pageStatus", "draft") if content else None
        if not content:
            summaries.append({"id": model_id, "skipped": True, "reason": "no pageContent"})
            continue
        if status not in RENDERABLE_STATUSES and not force:
            summaries.append({
                "id": model_id,
                "skipped": True,
                "reason": f"pageStatus is {status!r} (use --force to render anyway)",
            })
            continue

        html = render_page(model)
        if html is None:
            summaries.append({"id": model_id, "skipped": True, "reason": "render returned None"})
            continue

        folder = model_page_folder(model)
        folder.mkdir(parents=True, exist_ok=True)
        out_path = folder / "index.html"
        out_path.write_text(html, encoding="utf-8")
        summaries.append({"id": model_id, "skipped": False, "path": str(out_path.relative_to(REPO_ROOT))})

    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Render sign index.html pages from pageContent in catalogue.json")
    parser.add_argument("ids", nargs="*", help="Sign ids to render (defaults to all eligible)")
    parser.add_argument("--force", action="store_true", help="Render even when pageStatus is draft or missing")
    args = parser.parse_args()

    summaries = render_for_ids(args.ids or None, args.force)
    for entry in summaries:
        if entry.get("skipped"):
            print(f"skip  {entry['id']}: {entry['reason']}")
        else:
            print(f"wrote {entry['id']}: {entry['path']}")


if __name__ == "__main__":
    main()
