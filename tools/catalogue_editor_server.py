#!/usr/bin/env python3
"""Local-only catalogue editor server for nehiyoMTB.

Run from the repository root:

    python3 tools/catalogue_editor_server.py

Then open http://127.0.0.1:8765/docs/index.html. The static catalogue keeps
working without this server, but save buttons are enabled only when this API is
available locally.
"""

from __future__ import annotations

import argparse
import base64
import filecmp
import json
import mimetypes
import os
import posixpath
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sign_page_renderer import render_for_ids as render_pages_for_ids  # noqa: E402

# Boolean-union helper. The mesh-fix pipeline runs admesh first (cheap, fixes
# disconnected facets) and then this union pass to fold all disjoint shells
# into a single solid so slicers like Creality Print don't treat embedded
# silhouettes as hollow vases. The import is best-effort: if the optional
# trimesh / manifold3d / shapely deps aren't installed we fall back to
# admesh-only repair instead of failing the request.
try:
    from stl_union import union_stl as _union_stl  # noqa: E402
    from stl_union import build_layered_3mf as _build_layered_3mf  # noqa: E402
    _UNION_IMPORT_ERROR: str | None = None
except Exception as _exc:  # pragma: no cover - optional dependency
    _union_stl = None  # type: ignore[assignment]
    _build_layered_3mf = None  # type: ignore[assignment]
    _UNION_IMPORT_ERROR = str(_exc)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
# The real sign catalogue lives under docs/ so the static GitHub Pages site at
# docs/index.html can load it via a relative `fetch('catalogue.json')` and so
# that publishing the docs/ folder does not require any path rewriting. The
# tiny `./catalogue.json` stub at the repo root is a separate file used by the
# author's external GitHub-file-organization API and is intentionally left
# alone by this server.
CATALOGUE_PATH = DOCS_ROOT / "catalogue.json"
MANIFEST_PATH = DOCS_ROOT / "stl-manifest.json"
EDITOR_API_VERSION = 8
EDITOR_API_FEATURES = [
    "savePrintSetup",
    "repairStl",
    "saveSignContent",
    "regenerateSignPage",
    "uploadSignPhoto",
    "uploadTrailSource",
    "uploadMapIcon",
    "parseTrailTrack",
    "buildSign",
    "promoteSign",
    "buildAssembled",
    "buildAdjusted",
    "fleshOutSign",
    "saveAdjustments",
]


def load_catalogue() -> dict:
    with CATALOGUE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def find_model(catalogue: dict, model_id: str) -> dict:
    for model in catalogue.get("models", []):
        if model.get("id") == model_id:
            return model
    raise ValueError(f"Unknown model id: {model_id}")


def ensure_inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"Path escapes repository: {path}")
    return resolved


def safe_join(root: Path, *parts: str) -> Path:
    if any(part in {"", ".", ".."} or "/" in part or "\\" in part for part in parts):
        raise ValueError("Invalid path component")
    return ensure_inside(root.joinpath(*parts), root)


def stl_files(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    return sorted(
        [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".stl"],
        key=lambda path: path.name.lower(),
    )


def build_manifest() -> dict[str, list[str]]:
    manifest: dict[str, list[str]] = {}
    if not DOCS_ROOT.exists():
        return manifest

    for folder in sorted(DOCS_ROOT.iterdir(), key=lambda path: path.name.lower()):
        if folder.is_dir():
            files = [path.name for path in stl_files(folder)]
            if files:
                manifest[folder.name] = files

    return manifest


def regenerate_manifest() -> dict[str, list[str]]:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    return manifest


# --- draft sign factory + promotion ---------------------------------------- #
SIGNS_DIR = REPO_ROOT / "signs"
BUILD_SIGNS = REPO_ROOT / "tools" / "sign_factory" / "build_signs.py"
DRAFTS_MANIFEST = DOCS_ROOT / "sign-drafts" / "manifest.json"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_") or "sign"


def _load_drafts() -> dict:
    if DRAFTS_MANIFEST.exists():
        try:
            return json.loads(DRAFTS_MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


# Filament colour-name -> hex, mirrors the icon palette + viewer FILL_HEX so the
# generated page's accent colour can track the sign's dominant icon colour.
_FILAMENT_HEX = {
    "red": "#c4362c", "blue": "#2e6eb9", "navy": "#203668", "teal": "#289696",
    "green": "#3c8c4b", "grey": "#969696", "silver": "#c8cacd", "tan": "#cdaa6e",
    "lightbrown": "#c39655", "midbrown": "#a5642d", "brown": "#784e2e",
    "orange": "#e27a37", "yellow": "#eac63a", "purple": "#8448a0", "pink": "#dd7ba2",
}


def _accent_from_colors(colors: list) -> str:
    """Pick a page accent from the sign's icon fill colours.

    Prefer a saturated fill (skip plaque white, ink black, and the neutral
    silver/grey which make a washed-out page accent); fall back to a neutral
    only if that's all there is, then to a warm brown default."""
    neutral = ("white", "black", "silver", "grey")
    for name in colors or []:
        if name not in neutral and name in _FILAMENT_HEX:
            return _FILAMENT_HEX[name]
    for name in colors or []:
        if name in ("silver", "grey") and name in _FILAMENT_HEX:
            return _FILAMENT_HEX[name]
    return "#b5651d"  # warm brown default (fits the trail-sign palette)


def _split_words(text: str) -> list[str]:
    return [w for w in re.split(r"\s+", (text or "").strip()) if w]


def _is_meaningful(text: str) -> bool:
    """A reasoning/innuendo note worth showing (skip empty + bare 'None')."""
    t = (text or "").strip().rstrip(".")
    return bool(t) and t.lower() != "none"


def _word_morphemes(sro: str, syll: str, meaning: str, slug: str) -> list[dict]:
    """Split the chosen rendering into word-level parts for the formula display.

    We carve at word boundaries (not sub-morpheme) because the workbench data
    gives us the full transliteration + syllabics but not a vetted per-affix
    gloss; the reasoning text is surfaced separately in the story box. A single
    word collapses to one part glossed with the overall meaning."""
    sros = _split_words(sro)
    sylls = _split_words(syll)
    base = (slug or "word").replace("-", "_")
    if len(sros) <= 1:
        return [{"key": base, "sro": sro, "syllabics": syll, "gloss": meaning}]
    out = []
    for i, word in enumerate(sros):
        out.append({
            "key": f"{base}_{i}",
            "sro": word,
            "syllabics": sylls[i] if i < len(sylls) else "",
            "gloss": "",
        })
    return out


def _trail_facts_sentence(trail: dict) -> str:
    """Compose a short 'Trail: location; distance; descent/ascent' line."""
    if not isinstance(trail, dict):
        return ""
    bits: list[str] = []
    loc = str(trail.get("loc") or "").strip()
    if loc:
        bits.append(f"Located in {loc}")
    dist = str(trail.get("dist") or "").strip()
    if dist:
        bits.append(f"about {dist} long")
    desc = str(trail.get("desc") or "").strip()
    asc = str(trail.get("asc") or "").strip()
    if desc and asc:
        bits.append(f"{desc} descent / {asc} ascent")
    elif desc:
        bits.append(f"{desc} descent")
    elif asc:
        bits.append(f"{asc} ascent")
    if not bits:
        return ""
    return "Trail stats: " + "; ".join(bits) + "."


def _resolve_repo_or_docs(rel: str) -> Path | None:
    """Resolve a sign asset path that may be docs-relative (e.g.
    'sign-drafts/x.png') or repo-relative (e.g. 'signs/x/x_assembly.png')."""
    rel = (rel or "").strip().lstrip("/")
    if not rel:
        return None
    for base in (DOCS_ROOT, REPO_ROOT):
        candidate = (base / rel).resolve()
        try:
            ensure_inside(candidate, base)
        except Exception:
            continue
        if candidate.exists():
            return candidate
    return None


def _image_orientation(path: Path) -> str:
    """'landscape' | 'portrait' | 'square' | '' for an image file (best-effort)."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        if w > h:
            return "landscape"
        if h > w:
            return "portrait"
        return "square"
    except Exception:
        return ""


def _copy_preview_photo(slug: str, preview_png: str, assembly_png: str = "",
                        orient: str = "portrait") -> dict:
    """Copy a sign preview into docs/assets/<slug>/ for the page's 'Trail Sign
    Design' image, choosing an image whose aspect matches the sign orientation.

    The composed flat poster (``sign-drafts/<slug>.png``) is preferred when its
    aspect matches the sign's orientation; otherwise the OpenSCAD assembly
    render (``signs/<slug>/<slug>_assembly.png``) is used, since it is always
    rendered in the correct orientation. This prevents a stale portrait preview
    from landing on a landscape sign page (and vice-versa). Best-effort."""
    composed = _resolve_repo_or_docs(preview_png)
    assembly = _resolve_repo_or_docs(assembly_png)
    want = orient if orient in ("landscape", "portrait") else ""

    # Prefer a candidate whose orientation matches the sign; the composed poster
    # wins ties (nicer flat artwork), else the always-correct assembly render.
    source = None
    for cand in (composed, assembly):
        if cand and (not want or _image_orientation(cand) in (want, "square", "")):
            source = cand
            break
    if source is None:
        source = composed or assembly
    if source is None:
        return {}

    is_assembly = source == assembly
    assets_dir = DOCS_ROOT / "assets" / slug
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / f"{slug}_sign.png"
    try:
        shutil.copy2(source, dest)
    except Exception:
        return {}
    caption = ("3D render of the multi-colour printed sign — icon, Cree "
               "syllabics, transliteration, and English name."
               if is_assembly else
               "Draft 3D-printed sign preview — transliteration, icon, "
               "syllabics overlay, and English name.")
    return {
        "src": f"../assets/{slug}/{dest.name}",
        "alt": f"{slug} trail sign design with Cree name and icon",
        "caption": caption,
    }


def build_auto_page_content(en: str, slug: str, rec: dict, payload: dict) -> dict:
    """Assemble a full kiwapamitin-style pageContent object from the workbench
    data chosen for a sign (translation + reasoning + alternates + trail facts +
    icon/design concept), so 'Move to production' yields a rich page, not a stub.

    Everything is best-effort and degrades gracefully when a field is absent.
    pageStatus is 'agent-drafted' so the renderer emits the page while the card's
    review chip stays pending until a human confirms it."""
    comps = rec.get("components") or {}
    cree_name = (payload.get("creeName") or rec.get("translit") or "").strip()
    syllabics = (payload.get("creeSyllabics") or "").strip()
    meaning = (payload.get("meaning") or "").strip()
    reasoning = (payload.get("reasoning") or "").strip()
    innuendo = (payload.get("innuendo") or "").strip()
    design = payload.get("design") or {}
    trail = payload.get("trail") or {}
    alternates = payload.get("alternates") or []
    try:
        chosen_index = int(payload.get("chosenIndex") or 0)
    except (TypeError, ValueError):
        chosen_index = 0

    header_bits = [en]
    if cree_name:
        header_bits.append(cree_name)
    if syllabics:
        header_bits.append(syllabics)

    content: dict[str, Any] = {
        "pageStatus": "agent-drafted",
        "accentColor": _accent_from_colors(comps.get("colors", [])),
        "headerTitle": " • ".join(header_bits),
        "linguistics": {
            "meaning": meaning,
            "type": "",
            "primarySection": {
                "heading": "The Name",
                "sro": cree_name,
                "syllabics": syllabics,
                "morphemes": _word_morphemes(cree_name, syllabics, meaning, slug),
            },
            "relatedForms": [],
            "quickReference": [],
            "baseWords": [],
        },
        "culturalStory": {"heading": "", "body": []},
        "trailStory": {"heading": "", "body": []},
        "sources": ["itwêwina", "Online Cree Dictionary", "Plains Cree Dictionary"],
        "notes": ["Draft Cree rendering chosen in the translation workbench; "
                  "awaiting review by a fluent speaker."],
    }

    # The Name & Its Meaning — meaning + the reasoning behind the rendering.
    name_body: list[str] = []
    if meaning:
        name_body.append(f'The chosen Plains Cree rendering for \u201c{en}\u201d means '
                          f'\u201c{meaning}.\u201d')
    if _is_meaningful(reasoning):
        name_body.append(reasoning)
    if name_body:
        content["culturalStory"] = {"heading": "The Name & Its Meaning", "body": name_body}

    # Design & Trail — icon concept, wordplay, and trail stats.
    trail_body: list[str] = []
    concept = str(design.get("concept") or "").strip()
    subject = str(design.get("subject") or "").strip()
    if concept:
        trail_body.append(f"Sign icon: {concept}")
    elif subject:
        trail_body.append(f"Sign icon: {subject}.")
    if _is_meaningful(innuendo):
        trail_body.append(f"Wordplay / second meaning: {innuendo}")
    facts = _trail_facts_sentence(trail)
    if facts:
        trail_body.append(facts)
    if trail_body:
        content["trailStory"] = {"heading": "Design & Trail", "body": trail_body}

    # Alternate renderings -> related forms + quick-reference table.
    related: list[dict] = []
    quick: list[dict] = []
    for i, opt in enumerate(alternates):
        if not isinstance(opt, dict):
            continue
        t = str(opt.get("t") or "").strip()
        s = str(opt.get("s") or "").strip()
        g = str(opt.get("g") or "").strip()
        why = str(opt.get("why") or "").strip()
        if not t and not s:
            continue
        quick.append({"english": g, "sro": t, "syllabics": s,
                      "note": why if _is_meaningful(why) else ""})
        if i != chosen_index:
            related.append({"english": g, "sro": t, "syllabics": s,
                            "morphemes": [], "note": why if _is_meaningful(why) else ""})
    content["linguistics"]["relatedForms"] = related
    content["linguistics"]["quickReference"] = quick

    # Trail Sign Design photo — pick an image matching the sign orientation.
    photo = _copy_preview_photo(
        slug,
        payload.get("previewPng") or rec.get("png") or "",
        payload.get("assemblyPng") or (comps.get("assembly_scad") and
            f"signs/{slug}/{slug}_assembly.png") or "",
        comps.get("orient") or "portrait",
    )
    if photo:
        content["photo"] = photo

    return content


def build_sign(payload: dict) -> dict:
    """Run the draft factory for ONE trail (optionally with overridden Cree
    text / orientation), then return its refreshed sign-drafts manifest entry."""
    en = (payload.get("en") or "").strip()
    if not en:
        raise ValueError("en (English trail name) is required")
    orient = payload.get("orient") or "auto"
    if orient not in ("auto", "portrait", "landscape"):
        orient = "auto"
    cmd = [sys.executable, str(BUILD_SIGNS), "--only", en, "--orient", orient]
    if payload.get("translit") is not None:
        cmd += ["--translit", str(payload["translit"])]
    if payload.get("syllabics") is not None:
        cmd += ["--syllabics", str(payload["syllabics"])]
    if payload.get("colorMode") in ("staggered", "flat"):
        cmd += ["--color-mode", payload["colorMode"]]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise ValueError("build failed: " + (proc.stderr or proc.stdout or "")[-400:])
    entry = _load_drafts().get(en)
    return {"ok": True, "en": en, "orient": orient, "entry": entry,
            "log": (proc.stdout or "").strip()[-400:]}


def _write_drafts(drafts: dict) -> None:
    write_json(DRAFTS_MANIFEST, drafts)


def build_assembled(payload: dict) -> dict:
    """Render a draft sign's ONE combined assembled STL (the production pipeline)
    and split it into a print-ready multi-object .3mf, both under signs/<slug>/.

    This is the same render the production page uses, made available in the
    workbench so a draft can be slice-tested before promotion. The assembled STL
    slices cleanly (single CGAL solid); the .3mf carries that same fidelity with
    one object per filament colour. Paths are recorded back on the draft manifest
    entry so the workbench can offer them as downloads."""
    en = (payload.get("en") or "").strip()
    if not en:
        raise ValueError("en (English trail name) is required")
    drafts = _load_drafts()
    rec = drafts.get(en)
    if not rec or not rec.get("components"):
        raise ValueError(f"No built draft components for '{en}' — build it first.")
    comps = rec["components"]
    slug = rec.get("slug") or _slugify(en)
    sdir = SIGNS_DIR / slug
    asm = sdir / f"{slug}_assembly.scad"
    if not asm.exists():
        raise ValueError(f"Missing assembly scad: {asm}")

    openscad = shutil.which("openscad") or "/opt/homebrew/bin/openscad"
    out_stl = sdir / f"{slug}.stl"
    force = bool(payload.get("force"))
    if force or not out_stl.exists():
        proc = subprocess.run([openscad, "-o", str(out_stl), str(asm)],
                              capture_output=True, text=True, timeout=900)
        if proc.returncode != 0 or not out_stl.exists():
            raise ValueError("OpenSCAD render failed: " + (proc.stderr or "")[-300:])

    objects = None
    out_3mf = sdir / f"{slug}.3mf"
    if _build_layered_3mf is not None:
        try:
            res = _build_layered_3mf(out_stl, comps.get("colorLayers", []), out_3mf)
            if res:
                objects = res.get("objects")
        except Exception as exc:  # pragma: no cover
            print(f"[build_assembled] layered 3mf build failed: {exc}")
    if objects and out_3mf.exists():
        try:
            inject_3mf_slots(out_3mf, objects)   # pre-assign objects to filament slots
        except Exception as exc:  # pragma: no cover
            print(f"[build_assembled] slot pre-assignment skipped: {exc}")

    rec["assembled_stl"] = f"signs/{slug}/{slug}.stl"
    if out_3mf.exists():
        rec["print_3mf"] = f"signs/{slug}/{slug}.3mf"
    drafts[en] = rec
    _write_drafts(drafts)
    return {"ok": True, "en": en, "slug": slug,
            "assembledStl": rec["assembled_stl"],
            "print3mf": rec.get("print_3mf"),
            "objects": objects, "entry": rec}


# --- adjusted (re-laid-out) sign builder ----------------------------------- #
# Filament RGBs for the non-icon parts, mirroring build_signs.py so the baked
# .3mf objects carry the right tint. Icon fills use _FILAMENT_HEX (defined above).
_PLAQUE_RGB = (232, 225, 207)   # cream/white plaque base
_TEXT_RGB = (38, 38, 38)        # english + transliteration + icon outline
_SYLL_RGB = (192, 57, 43)       # syllabics + group number accent


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = (hex_str or "").lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except (ValueError, IndexError):
        return (200, 200, 200)


def _filament_rgb(name: str) -> tuple[int, int, int]:
    """Resolve a filament NAME to RGB (white/black/red + the icon palette)."""
    n = (name or "").strip().lower()
    if n == "white":
        return _PLAQUE_RGB
    if n == "black":
        return _TEXT_RGB
    if n == "red":
        return _SYLL_RGB
    if n in _FILAMENT_HEX:
        return _hex_to_rgb(_FILAMENT_HEX[n])
    return (200, 200, 200)


def _adjusted_part_color(key: str, colors: dict | None = None) -> tuple[str, tuple[int, int, int]]:
    """Map a component key to its (filament-name, RGB) so adjusted parts can be
    grouped into one coloured object per filament in the baked .3mf. A per-key
    override in ``colors`` (from the viewer's recolour swatches) wins."""
    if colors:
        ov = colors.get(key)
        if isinstance(ov, str) and ov.strip():
            return ov.strip(), _filament_rgb(ov)
    if key == "plaque":
        return "white", _PLAQUE_RGB
    if key in ("english", "translit", "icon_outline"):
        return "black", _TEXT_RGB
    if key in ("syllabics", "number"):
        return "red", _SYLL_RGB
    if key.startswith("icon_"):
        fil = key[5:]
        return fil, _hex_to_rgb(_FILAMENT_HEX.get(fil, "#c8cacd"))
    return key or "other", (200, 200, 200)


# --- printer filament slots + .3mf extruder pre-assignment ----------------- #
FILAMENT_SLOTS_PATH = DOCS_ROOT / "filament-slots.json"
_DEFAULT_SLOTS = ["teal", "pink", "yellow", "purple", "grey", "white", "black", "red"]


def load_filament_slots() -> list[str]:
    """The filaments loaded per printer slot (slot 1 first), from
    docs/filament-slots.json. Falls back to a sensible default set."""
    try:
        if FILAMENT_SLOTS_PATH.exists():
            data = json.loads(FILAMENT_SLOTS_PATH.read_text(encoding="utf-8"))
            slots = data.get("slots")
            if isinstance(slots, list) and slots:
                cleaned = [str(s).strip().lower() for s in slots if str(s).strip()]
                if cleaned:
                    return cleaned
    except Exception:
        pass
    return list(_DEFAULT_SLOTS)


def slot_for_filament(name: str, slots: list[str]) -> int:
    """1-based slot index for a filament name. Exact match wins; otherwise the
    nearest loaded colour by RGB distance (so an un-loaded colour still maps to
    the closest available filament)."""
    if not slots:
        return 1
    n = (name or "").strip().lower()
    if n in slots:
        return slots.index(n) + 1
    target = _filament_rgb(n)
    best_i, best_d = 0, None
    for i, s in enumerate(slots):
        sr = _filament_rgb(s)
        d = (target[0] - sr[0]) ** 2 + (target[1] - sr[1]) ** 2 + (target[2] - sr[2]) ** 2
        if best_d is None or d < best_d:
            best_d, best_i = d, i
    return best_i + 1


def _xml_attr(text: str) -> str:
    return (str(text or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _ensure_config_content_type(content_types_xml: str) -> str:
    """Make sure the OPC [Content_Types].xml declares the .config extension so a
    strict reader accepts the added Metadata/*.config part."""
    if 'Extension="config"' in content_types_xml:
        return content_types_xml
    inject = '<Default Extension="config" ContentType="text/xml"/>'
    if "</Types>" in content_types_xml:
        return content_types_xml.replace("</Types>", inject + "</Types>")
    return content_types_xml


def inject_3mf_slots(out_3mf: Path, objects: list[dict] | None,
                     slots: list[str] | None = None) -> dict | None:
    """Add a Bambu/Orca-style ``Metadata/model_settings.config`` to a freshly
    written .3mf so Creality Print opens with each object already assigned to the
    filament SLOT whose loaded colour matches (nearest-colour fallback).

    ``objects`` is the builder's list of ``{key, color}`` where ``key`` is the
    object name written into the 3mf and ``color`` is the filament name. Returns
    a small summary (or None on failure / nothing to do)."""
    import zipfile

    out_3mf = Path(out_3mf)
    if not out_3mf.exists():
        return None
    if slots is None:
        slots = load_filament_slots()

    try:
        with zipfile.ZipFile(out_3mf, "r") as z:
            names = z.namelist()
            model_name = next((n for n in names if n.endswith("3dmodel.model")), None)
            if not model_name:
                return None
            model_xml = z.read(model_name).decode("utf-8", errors="replace")
            content_types = None
            for n in names:
                if n.endswith("[Content_Types].xml"):
                    content_types = z.read(n).decode("utf-8", errors="replace")
                    ct_name = n
                    break
    except Exception:
        return None

    # object id <-> name from the model (trimesh writes name="<scene key>")
    id_name = re.findall(r'<object\s+id="(\d+)"[^>]*?name="([^"]*)"', model_xml)
    if not id_name:
        return None

    color_by_name = {(o.get("key") or ""): (o.get("color") or "") for o in (objects or [])}

    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    assigns: list[dict] = []
    for oid, oname in id_name:
        fil = color_by_name.get(oname, "")
        slot = slot_for_filament(fil, slots) if fil else 1
        cfg.append(f'  <object id="{oid}">')
        cfg.append(f'    <metadata key="name" value="{_xml_attr(oname)}"/>')
        cfg.append(f'    <metadata key="extruder" value="{slot}"/>')
        cfg.append(f'    <part id="{oid}" subtype="normal_part">')
        cfg.append(f'      <metadata key="name" value="{_xml_attr(oname)}"/>')
        cfg.append(f'      <metadata key="extruder" value="{slot}"/>')
        cfg.append("    </part>")
        cfg.append("  </object>")
        assigns.append({"name": oname, "color": fil, "slot": slot})
    cfg.append("</config>")
    cfg_text = "\n".join(cfg) + "\n"

    cfg_path = "Metadata/model_settings.config"
    tmp = out_3mf.with_name(out_3mf.name + ".tmp")
    try:
        with zipfile.ZipFile(out_3mf, "r") as zin, \
                zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                fn = item.filename.replace("\\", "/")
                if fn == cfg_path:
                    continue  # we re-write it below
                data = zin.read(item.filename)
                if content_types is not None and item.filename == ct_name:
                    data = _ensure_config_content_type(content_types).encode("utf-8")
                zout.writestr(item, data)
            zout.writestr(cfg_path, cfg_text)
        tmp.replace(out_3mf)
    except Exception as exc:  # pragma: no cover
        print(f"[inject_3mf_slots] failed to rewrite {out_3mf.name}: {exc}")
        if tmp.exists():
            tmp.unlink()
        return None
    return {"slots": slots, "assignments": assigns}


def _clean_adjustments(raw: Any) -> tuple[float, dict[str, dict[str, float]], dict[str, str]]:
    """Validate/clamp the {global, parts:{key:{s,x,y,z}}, colors:{key:name}} set
    sent by the viewer.

    Mirrors the viewer's transform model exactly: a per-part uniform scale `s`
    about the part's own bbox centroid, an (x,y,z) mm offset, a per-part relief
    height multiplier `hz` that scales ONLY the Z thickness about the piece's
    base (so it sticks out more), and a whole-sign `global` scale about the
    origin. ``colors`` carries per-component filament recolour overrides."""
    if not isinstance(raw, dict):
        raw = {}

    def _num(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    gscale = _num(raw.get("global"), 1.0)
    if not (0.05 <= gscale <= 20.0):
        gscale = 1.0

    parts: dict[str, dict[str, float]] = {}
    praw = raw.get("parts")
    if isinstance(praw, dict):
        for key, val in praw.items():
            if not isinstance(val, dict):
                continue
            s = _num(val.get("s"), 1.0)
            if not (0.05 <= s <= 20.0):
                s = 1.0
            hz = _num(val.get("hz"), 1.0)
            if not (0.1 <= hz <= 8.0):
                hz = 1.0
            parts[str(key)] = {
                "s": s,
                "x": _num(val.get("x"), 0.0),
                "y": _num(val.get("y"), 0.0),
                "z": _num(val.get("z"), 0.0),
                "hz": hz,
            }

    colors: dict[str, str] = {}
    craw = raw.get("colors")
    if isinstance(craw, dict):
        for key, name in craw.items():
            if isinstance(name, str) and name.strip():
                colors[str(key)] = name.strip()

    return gscale, parts, colors


def _bundle_adjusted_3mf(meshes_by_key: dict, out_3mf: Path,
                         colors: dict | None = None) -> list[dict] | None:
    """Bundle adjusted component meshes into ONE multi-object .3mf, merging all
    parts that share a filament into a single coloured object (one object per
    print colour). Per-component recolour overrides in ``colors`` are honoured.
    Returns a small objects list or None."""
    import trimesh

    groups: dict[str, dict] = {}
    for key, mesh in meshes_by_key.items():
        fil, rgb = _adjusted_part_color(key, colors)
        grp = groups.setdefault(fil, {"rgb": rgb, "meshes": []})
        grp["meshes"].append(mesh.copy())

    geoms: dict[str, Any] = {}
    objects: list[dict] = []
    for i, (fil, grp) in enumerate(groups.items()):
        ms = grp["meshes"]
        merged = ms[0] if len(ms) == 1 else trimesh.util.concatenate(ms)
        merged.visual.face_colors = list(grp["rgb"]) + [255]
        key = f"{i:02d}_{fil}"
        geoms[key] = merged
        objects.append({"key": key, "color": fil, "faces": int(len(merged.faces))})

    if not geoms:
        return None
    out_3mf = Path(out_3mf)
    out_3mf.parent.mkdir(parents=True, exist_ok=True)
    trimesh.Scene(geoms).export(str(out_3mf))
    return objects


def _recompute_color_layers(meshes_by_key: dict, colors: dict | None = None) -> list[dict]:
    """Derive bottom->top ``colorLayers`` height bands from the adjusted meshes.

    Groups parts by filament, takes each colour's highest Z, and orders the
    colours ascending so ``build_layered_3mf`` can split the clean combined solid
    into the same stacked colour bands the signs use — but adapted to whatever
    sizes/offsets the user dialled in (so a raised/scaled syllabics still ends up
    in the top band, etc.). The tallest colour gets no ``maxZ`` (open top)."""
    by_color: dict[str, float] = {}
    for key, mesh in meshes_by_key.items():
        fil, _rgb = _adjusted_part_color(key, colors)
        ztop = float(mesh.bounds[1][2])
        by_color[fil] = max(by_color.get(fil, ztop), ztop)
    ordered = sorted(by_color.items(), key=lambda kv: kv[1])
    layers: list[dict] = []
    for i, (fil, ztop) in enumerate(ordered):
        layer = {"color": fil, "label": fil}
        if i < len(ordered) - 1:           # tallest colour stays open-topped
            layer["maxZ"] = round(ztop, 3)
        layers.append(layer)
    return layers


def _bake_adjusted_core(comps: dict, slug: str, sdir: Path,
                        gscale: float, parts_adj: dict, colors: dict,
                        out_stl: Path, out_3mf: Path) -> dict:
    """Apply the viewer's per-part transform to each component STL and produce a
    clean combined solid (``out_stl``) + colour-correct multi-object ``out_3mf``.

    Shared by ``build_adjusted`` (writes the draft's ``_adj`` files) and
    ``promote_sign`` (writes the published ``docs/<slug>/`` files) so a promoted
    sign carries the exact same size/spacing/recolour tweaks as the viewer.
    Returns ``{adjusted, adj_paths, objects, color_layers}``."""
    import numpy as np
    import trimesh

    stl_keys = [k for k, v in comps.items() if isinstance(v, str) and v.endswith(".stl")]
    if not stl_keys:
        raise ValueError("draft has no per-component STLs to adjust")

    adjusted: dict[str, Any] = {}
    adj_paths: dict[str, str] = {}
    for key in stl_keys:
        src = (REPO_ROOT / comps[key]).resolve()
        if not src.exists():
            continue
        try:
            mesh = trimesh.load(str(src), process=False, force="mesh")
        except Exception:
            continue
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.dump()))
        if mesh is None or len(getattr(mesh, "faces", [])) == 0:
            continue
        a = parts_adj.get(key, {"s": 1.0, "x": 0.0, "y": 0.0, "z": 0.0, "hz": 1.0})
        s = a["s"] or 1.0
        hz = a.get("hz", 1.0) or 1.0
        centre = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
        offset = np.array([a["x"], a["y"], a["z"]], dtype=float)
        verts = s * (mesh.vertices - centre) + centre + offset
        if hz != 1.0:
            # scale ONLY the Z thickness about the (transformed) base so the
            # piece grows upward — matches the viewer's relief-height control.
            zmin = float(verts[:, 2].min())
            verts[:, 2] = hz * (verts[:, 2] - zmin) + zmin
        mesh.vertices = gscale * verts
        adjusted[key] = mesh
        out_part = sdir / f"{src.stem}_adj.stl"
        try:
            mesh.export(str(out_part))
            adj_paths[key] = str(out_part.relative_to(REPO_ROOT))
        except Exception:
            pass

    if not adjusted:
        raise ValueError("no component STLs could be loaded for adjustment")

    # Combined assembled solid. The per-component relief/text STLs are not all
    # closed volumes on their own, so a trimesh boolean union refuses them. We
    # instead CGAL-union the adjusted parts via OpenSCAD (the same clean engine
    # the rest of the pipeline uses), falling back to a concatenation if OpenSCAD
    # is missing so the action still produces a (sliceable) file.
    openscad = shutil.which("openscad") or "/opt/homebrew/bin/openscad"
    union_scad = sdir / f"{slug}_adj_union.scad"
    imports = "\n".join(
        f'  import("{(REPO_ROOT / p).resolve().as_posix()}", convexity=10);'
        for p in adj_paths.values()
    )
    union_scad.write_text(f"$fn = 48;\nunion() {{\n{imports}\n}}\n", encoding="utf-8")
    out_stl.parent.mkdir(parents=True, exist_ok=True)
    combined_ok = False
    if os.path.exists(openscad):
        proc = subprocess.run([openscad, "-o", str(out_stl), str(union_scad)],
                              capture_output=True, text=True, timeout=900)
        combined_ok = proc.returncode == 0 and out_stl.exists()
        if not combined_ok:
            print(f"[bake_adjusted] OpenSCAD union failed: {(proc.stderr or '')[-300:]}")
    if not combined_ok:
        print("[bake_adjusted] falling back to trimesh concatenation for combined STL")
        combined = trimesh.util.concatenate(list(adjusted.values()))
        combined.export(str(out_stl))

    # Print-ready multi-object .3mf — one coloured object per filament, keeping
    # each component WHOLE (avoids the Z-band split that can clip thin glyph tops)
    # and honouring recolour overrides. Then pre-assign filament slots.
    objects = None
    color_layers = _recompute_color_layers(adjusted, colors)
    try:
        objects = _bundle_adjusted_3mf(adjusted, out_3mf, colors)
    except Exception as exc:  # pragma: no cover
        print(f"[bake_adjusted] 3mf bundle failed: {exc}")
    if objects and out_3mf.exists():
        try:
            inject_3mf_slots(out_3mf, objects)
        except Exception as exc:  # pragma: no cover
            print(f"[bake_adjusted] slot pre-assignment skipped: {exc}")

    return {"adjusted": adjusted, "adj_paths": adj_paths,
            "objects": objects, "color_layers": color_layers}


def _render_flat_projection(out_png: Path, *, adj_paths: dict | None = None,
                            colors: dict | None = None, scad_path: Path | None = None,
                            orient: str = "portrait") -> bool:
    """Render a flat, front-on, COLOURED 2D projection of the 3D sign to a PNG —
    the sign-face "photo" that replaces the hand-composed poster so the page art
    always matches the actual (possibly adjusted/recoloured) geometry.

    Either renders a given ``scad_path`` (the assembly, which already carries
    colours) or, for adjusted signs, a generated scad that imports each adjusted
    part STL wrapped in its filament colour. Orthographic top-down camera."""
    openscad = shutil.which("openscad") or "/opt/homebrew/bin/openscad"
    if not os.path.exists(openscad):
        return False
    render_scad = scad_path
    tmp_scad = None
    if render_scad is None:
        if not adj_paths:
            return False
        lines = ["$fn = 48;"]
        for key, rel in adj_paths.items():
            _fil, rgb = _adjusted_part_color(key, colors)
            r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
            p = (REPO_ROOT / rel).resolve().as_posix()
            lines.append(f'color([{r:.3f}, {g:.3f}, {b:.3f}]) import("{p}", convexity=10);')
        tmp_scad = out_png.with_suffix(".proj.scad")
        tmp_scad.write_text("\n".join(lines) + "\n", encoding="utf-8")
        render_scad = tmp_scad
    imgsize = "1100,560" if orient == "landscape" else "620,1140"
    cmd = [openscad, "-o", str(out_png), f"--imgsize={imgsize}",
           "--projection=ortho", "--viewall", "--autocenter",
           "--camera=0,0,0,0,0,0,500", "--colorscheme=Tomorrow", str(render_scad)]
    ok = subprocess.run(cmd, capture_output=True, text=True).returncode == 0 and out_png.exists()
    if tmp_scad is not None:
        try:
            tmp_scad.unlink()
        except Exception:
            pass
    return ok


def build_adjusted(payload: dict) -> dict:
    """Bake the workbench viewer's per-component size/spacing/recolour tweaks into
    the draft's ``signs/<slug>/<slug>_adj.stl`` + ``_adj.3mf`` and record the
    adjustment set so promotion can carry the tweaks straight into production."""
    en = (payload.get("en") or "").strip()
    if not en:
        raise ValueError("en (English trail name) is required")
    drafts = _load_drafts()
    rec = drafts.get(en)
    if not rec or not rec.get("components"):
        raise ValueError(f"No built draft components for '{en}' — build it first.")
    comps = rec["components"]
    slug = rec.get("slug") or _slugify(en)
    sdir = SIGNS_DIR / slug

    try:
        import numpy  # noqa: F401
        import trimesh  # noqa: F401
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ValueError(
            "trimesh + numpy are required for adjusted builds; install them in "
            f"the venv (see requirements.txt). Import error: {exc}"
        )

    gscale, parts_adj, colors = _clean_adjustments(payload.get("adjustments"))
    out_stl = sdir / f"{slug}_adj.stl"
    out_3mf = sdir / f"{slug}_adj.3mf"
    res = _bake_adjusted_core(comps, slug, sdir, gscale, parts_adj, colors, out_stl, out_3mf)

    rec["adjusted"] = {"global": gscale, "parts": parts_adj, "colors": colors}
    rec["adjustedComponents"] = res["adj_paths"]
    rec["adjustedColorLayers"] = res["color_layers"]
    rec["assembled_stl"] = str(out_stl.relative_to(REPO_ROOT))
    if out_3mf.exists():
        rec["print_3mf"] = str(out_3mf.relative_to(REPO_ROOT))
    drafts[en] = rec
    _write_drafts(drafts)
    return {
        "ok": True,
        "en": en,
        "slug": slug,
        "assembledStl": rec["assembled_stl"],
        "print3mf": rec.get("print_3mf"),
        "objects": res["objects"],
        "adjustedComponents": res["adj_paths"],
        "entry": rec,
    }


def save_adjustments(payload: dict) -> dict:
    """Persist the viewer's current adjustment set onto the draft WITHOUT a heavy
    rebuild. The viewer calls this (debounced) as the user nudges/recolours, so
    "Move to production" can bake the latest tweaks even if the per-sign print
    bake was never run explicitly."""
    en = (payload.get("en") or "").strip()
    if not en:
        raise ValueError("en (English trail name) is required")
    drafts = _load_drafts()
    rec = drafts.get(en)
    if not rec:
        raise ValueError(f"Unknown draft '{en}'")
    gscale, parts_adj, colors = _clean_adjustments(payload.get("adjustments"))
    has_tweaks = (abs(gscale - 1.0) > 1e-6
                  or any(abs(p.get("s", 1) - 1) > 1e-6 or p.get("x") or p.get("y") or p.get("z")
                         or abs(p.get("hz", 1) - 1) > 1e-6
                         for p in parts_adj.values())
                  or bool(colors))
    if has_tweaks:
        rec["adjusted"] = {"global": gscale, "parts": parts_adj, "colors": colors}
    else:
        rec.pop("adjusted", None)   # cleared back to default -> drop so promote uses original
    drafts[en] = rec
    _write_drafts(drafts)
    return {"ok": True, "en": en, "hasAdjustments": has_tweaks}


def promote_sign(payload: dict) -> dict:
    """Promote a draft sign into the published catalogue: F6-render its assembly
    to one combined STL under docs/<slug>/, then append/update a catalogue.json
    model (with auto colorLayers) and render its page."""
    en = (payload.get("en") or "").strip()
    if not en:
        raise ValueError("en (English trail name) is required")
    drafts = _load_drafts()
    rec = drafts.get(en)
    if not rec or not rec.get("components"):
        raise ValueError(f"No built draft components for '{en}' — build it first.")
    comps = rec["components"]
    slug = rec.get("slug") or _slugify(en)
    asm = SIGNS_DIR / slug / f"{slug}_assembly.scad"
    if not asm.exists():
        raise ValueError(f"Missing assembly scad: {asm}")

    openscad = shutil.which("openscad") or "/opt/homebrew/bin/openscad"
    docs_folder = DOCS_ROOT / slug
    docs_folder.mkdir(parents=True, exist_ok=True)
    out_stl = docs_folder / f"{slug}.stl"
    out_3mf = docs_folder / f"{slug}.3mf"
    threemf_objects = None
    model_colors = comps.get("colors", [])
    model_layers = comps.get("colorLayers", [])

    # If the draft carries the viewer's size/spacing/recolour tweaks, BAKE the
    # published STL + .3mf directly from the adjusted components (so production
    # matches the 3D editor exactly). Otherwise F6-render the assembly scad.
    adjustments = rec.get("adjusted") if isinstance(rec.get("adjusted"), dict) else None
    bake = None
    if adjustments:
        try:
            gscale = float(adjustments.get("global") or 1.0)
            parts_adj = adjustments.get("parts") or {}
            colors = adjustments.get("colors") or {}
            bake = _bake_adjusted_core(comps, slug, SIGNS_DIR / slug, gscale,
                                       parts_adj, colors, out_stl, out_3mf)
            threemf_objects = bake.get("objects")
            if bake.get("color_layers"):
                model_layers = bake["color_layers"]
                model_colors = []
                for ly in model_layers:
                    c = ly.get("color")
                    if c and c not in model_colors:
                        model_colors.append(c)
        except Exception as exc:  # pragma: no cover
            print(f"[promote_sign] adjusted bake failed ({exc}); using assembly render")
            bake = None

    if bake is None:
        if not asm.exists():
            raise ValueError(f"Missing assembly scad: {asm}")
        proc = subprocess.run([openscad, "-o", str(out_stl), str(asm)],
                              capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not out_stl.exists():
            raise ValueError("OpenSCAD render failed: " + (proc.stderr or "")[-300:])
        if _build_layered_3mf is not None:
            try:
                res = _build_layered_3mf(out_stl, comps.get("colorLayers", []), out_3mf)
                if res:
                    threemf_objects = res.get("objects")
                    if out_3mf.exists():
                        inject_3mf_slots(out_3mf, threemf_objects)
            except Exception as exc:  # pragma: no cover
                print(f"[promote_sign] layered 3mf build skipped: {exc}")

    # Flat, front-on coloured 2D projection of the ACTUAL 3D sign -> the page
    # "Trail Sign Design" photo (replaces the hand-composed poster so the art
    # always matches the current geometry + colours).
    orient = comps.get("orient") or "portrait"
    assets_dir = DOCS_ROOT / "assets" / slug
    assets_dir.mkdir(parents=True, exist_ok=True)
    proj_png = assets_dir / f"{slug}_sign.png"
    proj_ok = False
    try:
        if bake is not None and bake.get("adj_paths"):
            proj_ok = _render_flat_projection(proj_png, adj_paths=bake["adj_paths"],
                                              colors=(adjustments or {}).get("colors"),
                                              orient=orient)
        elif asm.exists():
            proj_ok = _render_flat_projection(proj_png, scad_path=asm, orient=orient)
    except Exception as exc:  # pragma: no cover
        print(f"[promote_sign] flat projection render skipped: {exc}")

    catalogue = load_catalogue()
    models = catalogue.setdefault("models", [])
    model = next((m for m in models if m.get("id") == slug), None)
    if model is None:
        model = {"id": slug}
        next_num = max([int(m.get("signNumber") or 0) for m in models], default=0) + 1
        model["signNumber"] = next_num
        models.append(model)
    meaning = payload.get("meaning") or ""
    model.update({
        "numberedFolder": f"{int(model.get('signNumber') or 0):02d}-{slug}",
        "title": payload.get("englishName") or en,
        "englishName": payload.get("englishName") or en,
        "creeName": payload.get("creeName") or (rec.get("translit") or ""),
        "creeSyllabics": payload.get("creeSyllabics") or "",
        "folder": slug,
        "pagePath": f"{slug}/",
        "stlPath": f"{slug}/{slug}.stl",
        "docsStlPath": f"{slug}/{slug}.stl",
        "colors": model_colors,
        "colorLayers": model_layers,
        "status": payload.get("status") or "draft",
    })
    if out_3mf.exists():
        model["docs3mfPath"] = f"{slug}/{slug}.3mf"
    # Build a full kiwapamitin-style page from the chosen translation, its
    # reasoning, the alternate renderings, the icon/design concept, and the
    # trail facts — so promotion produces a rich page, not a bare stub. An
    # already-reviewed/published page is left alone so we never clobber human
    # edits; only draft/agent-drafted (or missing) pages are regenerated.
    existing_pc = model.get("pageContent") if isinstance(model.get("pageContent"), dict) else {}
    existing_status = (existing_pc or {}).get("pageStatus", "")
    if existing_status in ("user-reviewed", "published"):
        pc = existing_pc
    else:
        pc = build_auto_page_content(en, slug, rec, payload)
        model["pageContent"] = pc
        # Use the flat 3D projection as the sign-design photo (the 2D poster is
        # retired) so the page art tracks the real, possibly-adjusted geometry.
        if proj_ok:
            pc["photo"] = {
                "src": f"../assets/{slug}/{proj_png.name}",
                "alt": f"{model.get('englishName') or en} trail sign — 3D render",
                "caption": "Front view of the 3D-printed multi-colour sign, "
                           "rendered from the print geometry.",
            }
    model.setdefault("checks", {})

    write_json(CATALOGUE_PATH, catalogue)
    manifest = regenerate_manifest()
    rendered = []
    try:
        rendered = render_pages_for_ids([slug], force=True)
    except Exception as exc:  # pragma: no cover
        print(f"[promote_sign] page render skipped: {exc}")
    return {"ok": True, "model": model, "manifest": manifest,
            "docsStlPath": model["docsStlPath"],
            "docs3mfPath": model.get("docs3mfPath"),
            "threemfObjects": threemf_objects, "rendered": rendered}


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1

    while True:
        candidate = parent / f"{stem}_moved{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def unique_variant_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1

    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def repo_relative(path: Path) -> Path:
    return path.resolve().relative_to(REPO_ROOT.resolve())


def copy_preserving_existing(source: Path, destination: Path) -> tuple[Path, bool]:
    if destination.exists():
        if filecmp.cmp(source, destination, shallow=False):
            return destination, False
        destination = unique_destination(destination)

    shutil.copy2(source, destination)
    return destination, True


def public_candidate_path(location: str, model: dict, path: Path) -> str:
    folder = model.get("folder")
    if not folder:
        raise ValueError("Model has no folder")
    prefix = "" if location == "docs" else "../"
    return f"{prefix}{folder}/{path.name}"


def candidate_records(model: dict) -> list[dict]:
    folder = model.get("folder")
    if not folder:
        return []

    docs_folder = safe_join(DOCS_ROOT, folder)
    root_folder = safe_join(REPO_ROOT, folder)
    candidates = []
    seen: set[str] = set()

    for location, base, prefix in [
        ("docs", docs_folder, ""),
        ("root", root_folder, "../"),
    ]:
        for path in stl_files(base):
            key = f"{location}:{path.name}"
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "location": location,
                    "filename": path.name,
                    "path": f"{prefix}{folder}/{path.name}",
                    "publicPath": f"{folder}/{path.name}" if location == "docs" else None,
                }
            )

    return candidates


def resolve_candidate(model: dict, requested_path: str) -> tuple[str, Path]:
    normalized = posixpath.normpath(requested_path)
    folder = model.get("folder")
    if not folder:
        raise ValueError("Model has no folder")

    docs_prefix = f"{folder}/"
    root_prefix = f"../{folder}/"

    if normalized.startswith(docs_prefix):
        filename = normalized[len(docs_prefix) :]
        return "docs", safe_join(DOCS_ROOT, folder, filename)

    if normalized.startswith(root_prefix):
        filename = normalized[len(root_prefix) :]
        return "root", safe_join(REPO_ROOT, folder, filename)

    raise ValueError("STL path must point to the selected sign folder")


def save_print_setup(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))
    folder = model["folder"]

    operations: list[str] = []
    final_public_path = payload.get("finalStlPath")

    if final_public_path:
        location, source_path = resolve_candidate(model, str(final_public_path))
        if not source_path.exists():
            raise ValueError(f"Selected STL does not exist: {final_public_path}")

        docs_folder = safe_join(DOCS_ROOT, folder)
        root_folder = safe_join(REPO_ROOT, folder)
        docs_folder.mkdir(parents=True, exist_ok=True)
        root_folder.mkdir(parents=True, exist_ok=True)

        final_docs_path = docs_folder / source_path.name
        if location == "root":
            copied_path, did_copy = copy_preserving_existing(source_path, final_docs_path)
            final_docs_path = copied_path
            if did_copy:
                operations.append(f"Copied final STL {repo_relative(source_path)} to {repo_relative(final_docs_path)}")
        else:
            final_docs_path = source_path

        final_root_path, did_copy_root = copy_preserving_existing(
            final_docs_path,
            root_folder / final_docs_path.name,
        )
        if did_copy_root:
            operations.append(f"Copied final STL {repo_relative(final_docs_path)} to {repo_relative(final_root_path)}")

        for variant in stl_files(docs_folder):
            if variant.resolve() == final_docs_path.resolve():
                continue
            destination = unique_destination(root_folder / variant.name)
            shutil.move(str(variant), str(destination))
            operations.append(f"Moved {repo_relative(variant)} to {repo_relative(destination)}")

        model["docsStlPath"] = f"{folder}/{final_docs_path.name}"
        operations.append(f"Kept public final STL at {repo_relative(final_docs_path)}")
        operations.append(f"Set docsStlPath to {model['docsStlPath']}")

    if "colors" in payload:
        colors = payload["colors"]
        if not isinstance(colors, list) or not all(isinstance(color, str) and color for color in colors):
            raise ValueError("colors must be a non-empty string array")
        model["colors"] = colors
        operations.append("Updated colors")

    if "colorLayers" in payload:
        layers = payload["colorLayers"]
        if not isinstance(layers, list):
            raise ValueError("colorLayers must be an array")
        cleaned_layers = []
        for layer in layers:
            if not isinstance(layer, dict) or not isinstance(layer.get("color"), str):
                raise ValueError("Each color layer needs a color")
            cleaned = {"color": layer["color"]}
            if layer.get("maxZ") not in (None, ""):
                cleaned["maxZ"] = float(layer["maxZ"])
            if isinstance(layer.get("label"), str) and layer["label"]:
                cleaned["label"] = layer["label"]
            cleaned_layers.append(cleaned)
        model["colorLayers"] = cleaned_layers
        operations.append("Updated colorLayers")

    if "printEffect" in payload:
        effect = payload["printEffect"]
        if effect in (None, ""):
            if "printEffect" in model:
                del model["printEffect"]
                operations.append("Removed gradient print effect")
        else:
            if not isinstance(effect, dict):
                raise ValueError("printEffect must be an object or null")
            mode = effect.get("mode")
            if mode not in ("threshold", "transmission"):
                raise ValueError("printEffect.mode must be threshold or transmission")
            palette = effect.get("palette")
            if not isinstance(palette, list) or len(palette) == 0:
                raise ValueError("printEffect.palette must be a non-empty array")

            cleaned_palette = []
            for layer in palette:
                if not isinstance(layer, dict) or not isinstance(layer.get("color"), str) or not layer["color"]:
                    raise ValueError("Each printEffect palette layer needs a color")
                cleaned_layer = {
                    "color": layer["color"],
                    "startLayer": int(layer.get("startLayer") or 1),
                }
                if isinstance(layer.get("label"), str) and layer["label"]:
                    cleaned_layer["label"] = layer["label"]
                if mode == "threshold":
                    cleaned_layer["mixFactor"] = float(layer.get("mixFactor") or 0.3)
                else:
                    cleaned_layer["td"] = float(layer.get("td") or 4)
                cleaned_palette.append(cleaned_layer)

            cleaned_effect = {
                "mode": mode,
                "source": effect.get("source") if isinstance(effect.get("source"), str) else "IllumiStack",
                "totalLayers": int(effect.get("totalLayers") or 15),
                "layerHeightMm": float(effect.get("layerHeightMm") or 0.08),
                "baseLayers": int(effect.get("baseLayers") or 0),
                "backgroundColor": effect.get("backgroundColor") if isinstance(effect.get("backgroundColor"), str) else "#000000",
                "palette": cleaned_palette,
            }
            if isinstance(effect.get("previewImage"), str) and effect["previewImage"]:
                cleaned_effect["previewImage"] = effect["previewImage"]
            model["printEffect"] = cleaned_effect
            operations.append("Updated gradient print effect")

    write_json(CATALOGUE_PATH, catalogue)
    manifest = regenerate_manifest()

    return {
        "ok": True,
        "model": model,
        "manifest": manifest,
        "candidates": candidate_records(model),
        "operations": operations,
    }


_ADMESH_FACET_LINE_RE = re.compile(
    r"^\s*(Facets with [123] disconnected edges?|Total disconnected facets)\s*:\s*"
    r"(\d+)\s+(\d+)\s*$",
    re.MULTILINE,
)


def parse_admesh_stats(output: str) -> dict:
    """Parse admesh's ``=== Facet Status ===`` table for original/final counts.

    admesh prints lines like::

        Total disconnected facets        :     0                   0

    where the first integer is the original (input) count and the second is
    the final (post-repair) count. We surface both so the caller can decide
    if the mesh ended up watertight.
    """
    stats: dict[str, dict[str, int]] = {}
    for match in _ADMESH_FACET_LINE_RE.finditer(output or ""):
        label, original, final = match.group(1).strip(), int(match.group(2)), int(match.group(3))
        stats[label] = {"original": original, "final": final}
    total = stats.get("Total disconnected facets")
    is_watertight = total is not None and total["final"] == 0
    return {
        "byLabel": stats,
        "isWatertight": is_watertight,
        "totalDisconnectedFinal": total["final"] if total else None,
        "totalDisconnectedOriginal": total["original"] if total else None,
    }


def _empty_admesh_stats() -> dict:
    return {
        "byLabel": {},
        "isWatertight": False,
        "totalDisconnectedFinal": None,
        "totalDisconnectedOriginal": None,
    }


def _run_admesh_repair(source_path: Path, repaired_path: Path) -> tuple[dict, str, str]:
    admesh_path = shutil.which("admesh")
    if not admesh_path:
        raise ValueError("admesh is not installed. Run: brew install admesh")

    command = [
        admesh_path,
        "--nearby",
        "--fill-holes",
        "--normal-directions",
        "--normal-values",
        f"--write-binary-stl={repaired_path}",
        str(source_path),
    ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )

    stdout_text = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr_text = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    if result.returncode != 0:
        if repaired_path.exists():
            repaired_path.unlink()
        raise ValueError((stderr_text or stdout_text or "admesh repair failed").strip())

    return parse_admesh_stats(stdout_text + "\n" + stderr_text), stdout_text, stderr_text


def repair_stl(payload: dict) -> dict:
    admesh_path = shutil.which("admesh")
    if not admesh_path:
        raise ValueError("admesh is not installed. Run: brew install admesh")

    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))
    requested_path = str(payload.get("stlPath", ""))
    location, source_path = resolve_candidate(model, requested_path)

    if not source_path.exists():
        raise ValueError(f"Selected STL does not exist: {requested_path}")

    backup_path = unique_variant_path(source_path.with_name(f"{source_path.stem}_bk{source_path.suffix}"))
    repaired_path = unique_variant_path(source_path.with_name(f"{source_path.stem}_admesh_fixed{source_path.suffix}"))

    shutil.copy2(source_path, backup_path)
    stdout_text = ""
    stderr_text = ""
    admesh_stats = _empty_admesh_stats()

    operations = [
        f"Backed up {repo_relative(source_path)} to {repo_relative(backup_path)}",
    ]

    # Boolean-union pass. Even a watertight STL can still
    # contains many disjoint shells (plaque body + embedded silhouettes) that
    # share coincident faces; slicers like Creality Print cancel those facets
    # and end up slicing the embedded shapes as open-bottomed vases. Running a
    # manifold boolean union here turns the selected STL into multiple
    # independent closed solids while preserving relief detail. Important:
    # run this on the selected source STL, not on an admesh --fill-holes
    # intermediate, because admesh can fill intentional fine negative detail
    # (eyes, fur cuts, tiny text counters) before the boolean sees it.
    union_stats: dict | None = None
    union_skipped_reason: str | None = None
    # `union_skipped_intentionally` distinguishes "user turned union off" from
    # "we tried to union and couldn't". The mesh-ready calculation below only
    # treats the former as still-acceptable.
    union_skipped_intentionally = False
    final_repair_path = repaired_path
    union_requested = bool(payload.get("unionShells", True))

    if not union_requested:
        union_skipped_reason = "unionShells flag was false in the request"
        union_skipped_intentionally = True
    elif _union_stl is None:
        union_skipped_reason = (
            f"Boolean-union deps unavailable ({_UNION_IMPORT_ERROR or 'unknown error'}); "
            "install trimesh + manifold3d in the venv to enable solidify step"
        )
    else:
        solid_path = unique_variant_path(
            source_path.with_name(f"{source_path.stem}_solid{source_path.suffix}")
        )
        # Strategy passthrough: front-end can override with "clean" (drop
        # cancelling triangle pairs only), "preserve" (solidify shells
        # independently), "manifold" (boolean union), or "silhouette" (force
        # flatten to single slab). The default "auto" runs the minimal-touch
        # clean strategy that preserves the original artwork surface.
        union_strategy = str(payload.get("unionStrategy", "auto"))
        if union_strategy not in {"auto", "clean", "preserve", "manifold", "silhouette"}:
            union_strategy = "auto"
        try:
            union_stats = _union_stl(
                source_path,
                solid_path,
                strategy=union_strategy,
                verbose=False,
            )
        except Exception as exc:
            union_skipped_reason = f"Boolean-union step failed: {exc}"
        else:
            if union_stats.get("skipped"):
                operations.append(
                    f"Boolean-union skipped: input was already a single shell "
                    f"({union_stats['inputShells']} shell{'s' if union_stats['inputShells'] != 1 else ''})"
                )
                if solid_path.exists():
                    solid_path.unlink()
            else:
                final_repair_path = solid_path
                used = union_stats.get("strategyUsed") or "?"
                fallback_note = ""
                if union_stats.get("manifoldAttempted") and used == "silhouette":
                    fallback_note = " (manifold attempt was not watertight; fell back to silhouette)"
                verb = {
                    "clean": "Cleaned",
                    "preserve": "Solidified",
                    "manifold": "Boolean-union",
                    "silhouette": "Flattened",
                }.get(used, "Processed")
                operations.append(
                    f"{verb} [{used}] processed {union_stats['inputShells']} shells "
                    f"into {union_stats['outputShells']} shell"
                    f"{'s' if union_stats['outputShells'] != 1 else ''}"
                    f"; output watertight={union_stats['outputWatertight']}"
                    f"; wrote {repo_relative(solid_path)}{fallback_note}"
                )
                cleanup = union_stats.get("cleanupAdmesh")
                if isinstance(cleanup, dict) and cleanup.get("ran"):
                    nf = cleanup.get("normalsFixed", 0)
                    dr = cleanup.get("degeneratesRemoved", 0)
                    if nf or dr:
                        operations.append(
                            f"Post-union admesh cleanup: normals_fixed={nf}, "
                            f"degenerates_removed={dr}"
                        )

    if union_skipped_reason:
        operations.append(union_skipped_reason)

    # Fallback / legacy path: if solidification didn't produce an output, run
    # the old admesh repair so the button still does something useful when
    # union deps are missing, union is intentionally disabled, or the boolean
    # step fails. This path is deliberately after the union attempt to avoid
    # losing fine relief details on signs like sôniyâwâhkêsîs.
    if final_repair_path == repaired_path and not repaired_path.exists():
        admesh_stats, stdout_text, stderr_text = _run_admesh_repair(source_path, repaired_path)
        operations.append(f"Repaired {repo_relative(source_path)} to {repo_relative(repaired_path)}")
    elif union_stats and union_stats.get("outputWatertight"):
        admesh_stats = {
            "byLabel": {},
            "isWatertight": True,
            "totalDisconnectedFinal": 0,
            "totalDisconnectedOriginal": None,
        }

    manifest = regenerate_manifest()
    candidates = candidate_records(model)
    repaired_public_path = public_candidate_path(location, model, final_repair_path)
    repaired_candidate = next(
        (candidate for candidate in candidates if candidate["path"] == repaired_public_path),
        {
            "location": location,
            "filename": final_repair_path.name,
            "path": repaired_public_path,
            "publicPath": repaired_public_path if location == "docs" else None,
        },
    )

    # Mesh is "ready" when admesh found it watertight AND the solidify step
    # either succeeded (output watertight), was a no-op (input was already a
    # single shell), or was intentionally disabled by the caller. A failed or
    # dep-missing union does NOT count as ready, because the slicer-side
    # hollow-shell bug is precisely what the union step exists to fix.
    admesh_ok = admesh_stats["totalDisconnectedFinal"] is not None and admesh_stats["isWatertight"]
    if union_stats is None:
        union_ok = union_skipped_intentionally
    elif union_stats.get("skipped"):
        union_ok = True
    else:
        union_ok = bool(union_stats.get("outputWatertight", False))
    mesh_ready = bool(admesh_ok and union_ok)

    if admesh_stats["totalDisconnectedFinal"] is not None:
        existing_checks = model.get("checks") if isinstance(model.get("checks"), dict) else {}
        merged_checks = dict(existing_checks)
        merged_checks["meshRepaired"] = mesh_ready
        model["checks"] = merged_checks
        write_json(CATALOGUE_PATH, catalogue)
        if mesh_ready:
            ran_union = union_stats is not None and not union_stats.get("skipped")
            if ran_union:
                operations.append(
                    "Mesh is watertight and solidified — flagged checks.meshRepaired=true"
                )
            elif union_stats and union_stats.get("skipped"):
                operations.append(
                    "Mesh is watertight (single-shell input, no solidify needed) "
                    "— flagged checks.meshRepaired=true"
                )
            else:
                operations.append(
                    "Mesh is watertight (solidify intentionally disabled) "
                    "— flagged checks.meshRepaired=true"
                )
        else:
            reasons: list[str] = []
            if not admesh_ok and admesh_stats["totalDisconnectedFinal"] is not None:
                reasons.append(f"{admesh_stats['totalDisconnectedFinal']} admesh-disconnected facets")
            if union_stats is None and not union_skipped_intentionally:
                reasons.append("boolean-union step did not run (see solidify reason)")
            elif union_stats and not union_stats.get("skipped") and not union_stats.get("outputWatertight"):
                reasons.append("union output is not watertight")
            joined = "; ".join(reasons) or "see above"
            operations.append(
                f"Mesh not yet ready ({joined}) — checks.meshRepaired set to false"
            )

    return {
        "ok": True,
        "manifest": manifest,
        "candidates": candidates,
        "repairedCandidate": repaired_candidate,
        "model": model,
        "admeshStats": admesh_stats,
        "unionStats": union_stats,
        "unionSkippedReason": union_skipped_reason,
        "meshReady": mesh_ready,
        "operations": operations,
        "admeshOutput": "\n".join(part for part in [stdout_text.strip(), stderr_text.strip()] if part),
    }


ALLOWED_PAGE_STATUSES = {"draft", "agent-drafted", "user-reviewed", "published"}


def _clean_string(value: Any, *, allow_empty: bool = True) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not allow_empty and not text:
        raise ValueError("Empty string not allowed")
    return text


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clean_coord(raw: Any, field_name: str) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"trailforks.{field_name} must be an object")
    lat = raw.get("lat")
    lng = raw.get("lng")
    if not _is_number(lat) or not _is_number(lng):
        raise ValueError(f"trailforks.{field_name} must include numeric lat and lng")
    coord = {"lat": lat, "lng": lng}
    source = _clean_string(raw.get("source"))
    if source:
        coord["source"] = source
    return coord


def _clean_track(raw: Any) -> list[list[float]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("trailforks.track must be a list")
    cleaned: list[list[float]] = []
    for index, point in enumerate(raw):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"trailforks.track point {index} must be [lat, lng]")
        lat, lng = point
        if not _is_number(lat) or not _is_number(lng):
            raise ValueError(f"trailforks.track point {index} must contain numeric lat/lng")
        cleaned.append([lat, lng])
    return cleaned if len(cleaned) > 1 else []


def _clean_morphemes(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("morphemes must be a list")
    cleaned: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"morpheme {index} must be an object")
        entry = {
            "key": _clean_string(item.get("key")),
            "sro": _clean_string(item.get("sro")),
            "syllabics": _clean_string(item.get("syllabics")),
            "gloss": _clean_string(item.get("gloss")),
        }
        if not entry["sro"] and not entry["syllabics"]:
            continue
        cleaned.append(entry)
    return cleaned


def _clean_related_forms(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("relatedForms must be a list")
    cleaned: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"relatedForm {index} must be an object")
        entry = {
            "english": _clean_string(item.get("english")),
            "sro": _clean_string(item.get("sro")),
            "syllabics": _clean_string(item.get("syllabics")),
            "morphemes": _clean_morphemes(item.get("morphemes")),
            "note": _clean_string(item.get("note")),
        }
        if not entry["english"] and not entry["sro"]:
            continue
        cleaned.append(entry)
    return cleaned


def _clean_quick_reference(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("quickReference must be a list")
    cleaned: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"quickReference {index} must be an object")
        entry = {
            "english": _clean_string(item.get("english")),
            "sro": _clean_string(item.get("sro")),
            "syllabics": _clean_string(item.get("syllabics")),
            "note": _clean_string(item.get("note")),
        }
        if not any(entry.values()):
            continue
        cleaned.append(entry)
    return cleaned


def _clean_base_words(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("baseWords must be a list")
    cleaned: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"baseWord {index} must be an object")
        entry = {
            "sro": _clean_string(item.get("sro")),
            "english": _clean_string(item.get("english")),
            "syllabics": _clean_string(item.get("syllabics")),
        }
        if not entry["sro"] and not entry["syllabics"]:
            continue
        cleaned.append(entry)
    return cleaned


def _clean_story(raw: Any) -> dict:
    if raw is None:
        return {"heading": "", "body": []}
    if not isinstance(raw, dict):
        raise ValueError("story must be an object")
    body_raw = raw.get("body") or []
    if isinstance(body_raw, str):
        body_raw = [body_raw]
    if not isinstance(body_raw, list):
        raise ValueError("story.body must be a list of strings")
    body = [_clean_string(p) for p in body_raw]
    body = [p for p in body if p]
    return {
        "heading": _clean_string(raw.get("heading")),
        "body": body,
    }


def _clean_photo(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("photo must be an object")
    src = _clean_string(raw.get("src"))
    if not src:
        return {}
    return {
        "src": src,
        "alt": _clean_string(raw.get("alt")),
        "caption": _clean_string(raw.get("caption")),
    }


def _has_trailforks_link(raw: dict) -> bool:
    return bool(
        _clean_string(raw.get("trailUrl"))
        or _clean_string(raw.get("trailId"))
        or _clean_string(raw.get("widgetUrl"))
    )


def _legacy_strava_segment_id(raw: dict) -> str:
    segment_id = _clean_string(raw.get("stravaSegmentId"))
    if segment_id:
        return segment_id
    display_name = _clean_string(raw.get("displayName"))
    if display_name.isdigit() and len(display_name) >= 5 and not _has_trailforks_link(raw):
        return display_name
    return ""


def _infer_trail_source(raw: dict) -> str:
    trail_source = _clean_string(raw.get("trailSource"))
    if trail_source in {"trailforks", "strava"}:
        return trail_source
    if _clean_string(raw.get("stravaSegmentUrl")) or _legacy_strava_segment_id(raw):
        return "strava"
    return "trailforks"


def _clean_map_embed_mode(raw: Any) -> str:
    mode = _clean_string(raw)
    if mode in {"local", "widget"}:
        return mode
    return ""


def _clean_trailforks(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("trailforks must be an object")

    trail_source = _infer_trail_source(raw)
    display_name = _clean_string(raw.get("displayName"))
    map_embed_mode = _clean_map_embed_mode(raw.get("mapEmbedMode"))
    track_source_path = _clean_string(raw.get("trackSourcePath"))
    map_status = _clean_string(raw.get("mapStatus"))
    icon_status = _clean_string(raw.get("iconStatus"))
    icon_src = _clean_string(raw.get("iconSrc"))
    map_coords = _clean_coord(raw.get("mapCoords"), "mapCoords") if raw.get("mapCoords") is not None else {}
    map_end_coords = _clean_coord(raw.get("mapEndCoords"), "mapEndCoords") if raw.get("mapEndCoords") is not None else {}
    track = _clean_track(raw.get("track")) if raw.get("track") is not None else []

    trail_id = ""
    trail_url = ""
    widget_url = ""
    strava_segment_id = ""
    strava_segment_url = ""

    if trail_source == "strava":
        strava_segment_id = _legacy_strava_segment_id(raw)
        strava_segment_url = _clean_string(raw.get("stravaSegmentUrl"))
        if strava_segment_id and not strava_segment_url:
            strava_segment_url = f"https://www.strava.com/segments/{strava_segment_id}"
        if not display_name and strava_segment_url:
            display_name = strava_segment_url.rstrip("/").split("/")[-1]
    else:
        trail_id = _clean_string(raw.get("trailId"))
        trail_url = _clean_string(raw.get("trailUrl"))
        widget_url = _clean_string(raw.get("widgetUrl"))
        if trail_id and not widget_url and map_embed_mode != "local":
            widget_url = (
                f"https://www.trailforks.com/widgets/trail/?trailid={trail_id}"
                "&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets"
                "&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1"
            )
        if not display_name and trail_url:
            display_name = trail_url.rstrip("/").split("/")[-1]

    cleaned: dict[str, Any] = {
        "trailSource": trail_source,
        "trailId": trail_id,
        "trailUrl": trail_url,
        "widgetUrl": widget_url,
        "stravaSegmentId": strava_segment_id,
        "stravaSegmentUrl": strava_segment_url,
        "mapEmbedMode": map_embed_mode,
        "displayName": display_name,
        "trackSourcePath": track_source_path,
        "mapStatus": map_status,
        "iconStatus": icon_status,
        "iconSrc": icon_src,
    }
    if map_coords:
        cleaned["mapCoords"] = map_coords
    if map_end_coords:
        cleaned["mapEndCoords"] = map_end_coords
    if track:
        cleaned["track"] = track
    return {
        key: value for key, value in cleaned.items()
        if value not in ("", [], {})
    }


def _clean_linguistics(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("linguistics must be an object")
    primary_raw = raw.get("primarySection") or {}
    if not isinstance(primary_raw, dict):
        raise ValueError("linguistics.primarySection must be an object")
    primary = {
        "heading": _clean_string(primary_raw.get("heading")),
        "sro": _clean_string(primary_raw.get("sro")),
        "syllabics": _clean_string(primary_raw.get("syllabics")),
        "morphemes": _clean_morphemes(primary_raw.get("morphemes")),
    }
    return {
        "meaning": _clean_string(raw.get("meaning")),
        "type": _clean_string(raw.get("type")),
        "primarySection": primary,
        "relatedForms": _clean_related_forms(raw.get("relatedForms")),
        "quickReference": _clean_quick_reference(raw.get("quickReference")),
        "baseWords": _clean_base_words(raw.get("baseWords")),
    }


def _clean_page_content(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("pageContent must be an object")

    page_status = _clean_string(raw.get("pageStatus")) or "draft"
    if page_status not in ALLOWED_PAGE_STATUSES:
        raise ValueError(f"pageStatus must be one of {sorted(ALLOWED_PAGE_STATUSES)}")

    sources_raw = raw.get("sources") or []
    if not isinstance(sources_raw, list):
        raise ValueError("sources must be a list of strings")
    sources = [_clean_string(s) for s in sources_raw]
    sources = [s for s in sources if s]

    notes_raw = raw.get("notes") or []
    if not isinstance(notes_raw, list):
        raise ValueError("notes must be a list of strings")
    notes = [_clean_string(n) for n in notes_raw]
    notes = [n for n in notes if n]

    return {
        "pageStatus": page_status,
        "accentColor": _clean_string(raw.get("accentColor")) or "#dc3545",
        "themeName": _clean_string(raw.get("themeName")),
        "headerTitle": _clean_string(raw.get("headerTitle")),
        "photo": _clean_photo(raw.get("photo")),
        "trailforks": _clean_trailforks(raw.get("trailforks")),
        "linguistics": _clean_linguistics(raw.get("linguistics")),
        "culturalStory": _clean_story(raw.get("culturalStory")),
        "trailStory": _clean_story(raw.get("trailStory")),
        "sources": sources,
        "notes": notes,
    }


def _clean_checks(raw: Any, existing: Any) -> dict:
    """Merge per-card readiness checklist booleans onto the existing model checks.

    Today only ``meshRepaired`` is a manual toggle; the other checklist items
    shown on each catalogue card (final STL selected, colours and layers,
    trailforks, photo, page draft confirmed) are derived from existing model /
    pageContent fields and do not need to be persisted as booleans.
    """
    merged: dict = {}
    if isinstance(existing, dict):
        merged.update({k: v for k, v in existing.items() if isinstance(k, str)})
    if raw is None:
        return merged
    if not isinstance(raw, dict):
        raise ValueError("checks must be an object")
    if "meshRepaired" in raw:
        merged["meshRepaired"] = bool(raw.get("meshRepaired"))
    return merged


def _clean_name_fields(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("nameFields must be an object")
    english_name = _clean_string(raw.get("englishName"))
    if not english_name:
        raise ValueError("English primary name is required")
    return {
        "englishName": english_name,
        "creeName": _clean_string(raw.get("creeName")),
        "creeSyllabics": _clean_string(raw.get("creeSyllabics")),
    }


def save_sign_content(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))

    name_fields = _clean_name_fields(payload.get("nameFields"))
    if name_fields:
        model.update(name_fields)

    page_content = _clean_page_content(payload.get("pageContent"))
    model["pageContent"] = page_content

    if "checks" in payload:
        model["checks"] = _clean_checks(payload.get("checks"), model.get("checks"))

    write_json(CATALOGUE_PATH, catalogue)

    rendered = None
    render_summary: list[dict] = []
    page_status = page_content.get("pageStatus")
    auto_render = bool(payload.get("autoRender", True))
    if auto_render and page_status in {"agent-drafted", "user-reviewed", "published"}:
        render_summary = render_pages_for_ids([model["id"]], force=False)
        rendered = next((entry for entry in render_summary if entry.get("id") == model["id"]), None)

    return {
        "ok": True,
        "model": model,
        "rendered": rendered,
        "renderSummary": render_summary,
    }


ALLOWED_PHOTO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
PHOTO_MAX_BYTES = 20 * 1024 * 1024  # 20 MB safety cap
ALLOWED_TRAIL_SOURCE_EXTENSIONS = {".xml", ".gpx", ".kml", ".tcx"}
TRAIL_SOURCE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB safety cap
TRAIL_TRACK_MAX_POINTS = 4000


def _strip_xml_namespaces(elem: ET.Element) -> None:
    """Drop ``{ns}tag`` prefixes so tag lookups work regardless of schema."""
    for node in elem.iter():
        tag = node.tag
        if isinstance(tag, str) and tag.startswith("{"):
            node.tag = tag.split("}", 1)[1]


def _round_coord(value: float) -> float:
    return round(float(value), 6)


def parse_trail_track(raw: bytes, suffix: str) -> list[list[float]]:
    """Parse GPX/KML/TCX/XML track files into ``[[lat, lng], ...]`` pairs.

    Trailforks "Download GPX" exports, Garmin TCX, and KML LineStrings all
    funnel through one entry point so the editor can hydrate
    ``pageContent.trailforks.track`` automatically right after the file is
    uploaded. Unknown / unrecognised formats raise ``ValueError`` so the
    caller can surface a clear error instead of saving a half-broken trail.
    """
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"Could not parse XML trail file: {exc}") from exc

    _strip_xml_namespaces(root)
    points: list[list[float]] = []

    for trkpt in root.iter("trkpt"):
        lat = trkpt.get("lat")
        lon = trkpt.get("lon")
        if lat is None or lon is None:
            continue
        try:
            points.append([_round_coord(lat), _round_coord(lon)])
        except (TypeError, ValueError):
            continue

    if not points:
        for rtept in root.iter("rtept"):
            lat = rtept.get("lat")
            lon = rtept.get("lon")
            if lat is None or lon is None:
                continue
            try:
                points.append([_round_coord(lat), _round_coord(lon)])
            except (TypeError, ValueError):
                continue

    if not points:
        for tp in root.iter("Trackpoint"):
            pos = tp.find("Position")
            if pos is None:
                continue
            lat_el = pos.find("LatitudeDegrees")
            lon_el = pos.find("LongitudeDegrees")
            if lat_el is None or lon_el is None:
                continue
            try:
                points.append(
                    [_round_coord(lat_el.text or ""), _round_coord(lon_el.text or "")]
                )
            except (TypeError, ValueError):
                continue

    if not points:
        for coords_el in root.iter("coordinates"):
            text = (coords_el.text or "").strip()
            if not text:
                continue
            for chunk in re.split(r"\s+", text):
                parts = chunk.split(",")
                if len(parts) < 2:
                    continue
                try:
                    lng = _round_coord(parts[0])
                    lat = _round_coord(parts[1])
                except ValueError:
                    continue
                points.append([lat, lng])

    if not points:
        raise ValueError(
            f"No track points found in {suffix or 'file'}. "
            "Expected GPX <trkpt>, KML <coordinates>, or TCX <Trackpoint>."
        )

    deduped: list[list[float]] = []
    for pt in points:
        if not deduped or deduped[-1] != pt:
            deduped.append(pt)

    if len(deduped) > TRAIL_TRACK_MAX_POINTS:
        step = len(deduped) / TRAIL_TRACK_MAX_POINTS
        sampled = [deduped[int(i * step)] for i in range(TRAIL_TRACK_MAX_POINTS)]
        if sampled[-1] != deduped[-1]:
            sampled.append(deduped[-1])
        deduped = sampled

    return deduped


def _sanitize_asset_filename(name: str) -> str:
    name = name.strip().replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    name = name.strip("._-") or "photo"
    if "." not in name:
        name = name + ".png"
    return name


def list_sign_assets(model_id: str) -> list[dict]:
    catalogue = load_catalogue()
    model = find_model(catalogue, model_id)
    folder = model.get("folder")
    if not folder:
        return []
    assets_root = DOCS_ROOT / "assets" / folder
    if not assets_root.exists() or not assets_root.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(assets_root.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file() and path.suffix.lower() in ALLOWED_PHOTO_EXTENSIONS:
            out.append({
                "filename": path.name,
                "src": f"../assets/{folder}/{path.name}",
                "bytes": path.stat().st_size,
            })
    return out


def upload_sign_photo(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))
    folder = model.get("folder")
    if not folder:
        raise ValueError("Model has no folder")

    filename = _sanitize_asset_filename(str(payload.get("filename", "photo.png")))
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise ValueError(
            f"Unsupported image extension {ext!r}; allowed: {sorted(ALLOWED_PHOTO_EXTENSIONS)}"
        )

    data_b64 = payload.get("contentBase64") or ""
    if not isinstance(data_b64, str) or not data_b64.strip():
        raise ValueError("contentBase64 is required")
    if data_b64.startswith("data:"):
        comma = data_b64.find(",")
        if comma >= 0:
            data_b64 = data_b64[comma + 1 :]
    try:
        raw = base64.b64decode(data_b64, validate=False)
    except Exception as exc:
        raise ValueError(f"Could not decode base64 image: {exc}")

    if len(raw) == 0:
        raise ValueError("Decoded image is empty")
    if len(raw) > PHOTO_MAX_BYTES:
        raise ValueError(
            f"Image is too large ({len(raw)} bytes); max {PHOTO_MAX_BYTES} bytes (20 MB)"
        )

    assets_root = DOCS_ROOT / "assets" / folder
    assets_root.mkdir(parents=True, exist_ok=True)

    destination = assets_root / filename
    if destination.exists():
        destination = unique_variant_path(destination)

    destination.write_bytes(raw)

    public_src = f"../assets/{folder}/{destination.name}"
    return {
        "ok": True,
        "filename": destination.name,
        "src": public_src,
        "bytes": len(raw),
        "assets": list_sign_assets(model["id"]),
    }


def upload_trail_source(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))
    folder = model.get("folder")
    if not folder:
        raise ValueError("Model has no folder")

    filename = _sanitize_asset_filename(str(payload.get("filename", "trail.gpx")))
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_TRAIL_SOURCE_EXTENSIONS:
        raise ValueError(
            f"Unsupported trail file extension {ext!r}; "
            f"allowed: {sorted(ALLOWED_TRAIL_SOURCE_EXTENSIONS)}"
        )

    data_b64 = payload.get("contentBase64") or ""
    if not isinstance(data_b64, str) or not data_b64.strip():
        raise ValueError("contentBase64 is required")
    if data_b64.startswith("data:"):
        comma = data_b64.find(",")
        if comma >= 0:
            data_b64 = data_b64[comma + 1 :]
    try:
        raw = base64.b64decode(data_b64, validate=False)
    except Exception as exc:
        raise ValueError(f"Could not decode base64 trail file: {exc}")

    if len(raw) == 0:
        raise ValueError("Decoded trail file is empty")
    if len(raw) > TRAIL_SOURCE_MAX_BYTES:
        raise ValueError(
            f"Trail file is too large ({len(raw)} bytes); "
            f"max {TRAIL_SOURCE_MAX_BYTES} bytes (10 MB)"
        )

    tracks_root = DOCS_ROOT / "assets" / folder / "tracks"
    tracks_root.mkdir(parents=True, exist_ok=True)

    destination = tracks_root / filename
    if destination.exists():
        destination = unique_variant_path(destination)

    destination.write_bytes(raw)
    repo_path = repo_relative(destination)

    track: list[list[float]] = []
    parse_error: str | None = None
    try:
        track = parse_trail_track(raw, ext)
    except ValueError as exc:
        parse_error = str(exc)

    map_coords: dict[str, float] | None = None
    map_end_coords: dict[str, float] | None = None
    if track:
        map_coords = {"lat": track[0][0], "lng": track[0][1]}
        if len(track) > 1:
            map_end_coords = {"lat": track[-1][0], "lng": track[-1][1]}

    return {
        "ok": True,
        "filename": destination.name,
        "path": repo_path.as_posix(),
        "src": f"../assets/{folder}/tracks/{destination.name}",
        "bytes": len(raw),
        "track": track,
        "trackPoints": len(track),
        "mapCoords": map_coords,
        "mapEndCoords": map_end_coords,
        "parseError": parse_error,
    }


def upload_map_icon(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))
    folder = model.get("folder")
    if not folder:
        raise ValueError("Model has no folder")

    filename = _sanitize_asset_filename(str(payload.get("filename", "map-icon.png")))
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise ValueError(
            f"Unsupported image extension {ext!r}; allowed: {sorted(ALLOWED_PHOTO_EXTENSIONS)}"
        )

    data_b64 = payload.get("contentBase64") or ""
    if not isinstance(data_b64, str) or not data_b64.strip():
        raise ValueError("contentBase64 is required")
    if data_b64.startswith("data:"):
        comma = data_b64.find(",")
        if comma >= 0:
            data_b64 = data_b64[comma + 1 :]
    try:
        raw = base64.b64decode(data_b64, validate=False)
    except Exception as exc:
        raise ValueError(f"Could not decode base64 map icon: {exc}")

    if len(raw) == 0:
        raise ValueError("Decoded map icon is empty")
    if len(raw) > PHOTO_MAX_BYTES:
        raise ValueError(
            f"Map icon is too large ({len(raw)} bytes); max {PHOTO_MAX_BYTES} bytes (20 MB)"
        )

    icon_root = DOCS_ROOT / "assets" / folder / "map-icons"
    icon_root.mkdir(parents=True, exist_ok=True)

    destination = icon_root / filename
    if destination.exists():
        destination = unique_variant_path(destination)

    destination.write_bytes(raw)
    public_src = f"../assets/{folder}/map-icons/{destination.name}"

    return {
        "ok": True,
        "filename": destination.name,
        "src": public_src,
        "bytes": len(raw),
    }


def regenerate_sign_page(payload: dict) -> dict:
    ids_raw = payload.get("modelIds")
    if ids_raw is None and payload.get("modelId"):
        ids_raw = [payload["modelId"]]
    if ids_raw is None:
        ids = None
    elif isinstance(ids_raw, list):
        ids = [str(item) for item in ids_raw if item]
    else:
        raise ValueError("modelIds must be a list")

    force = bool(payload.get("force"))
    summaries = render_pages_for_ids(ids, force=force)
    return {"ok": True, "summaries": summaries}


def flesh_out_sign(payload: dict) -> dict:
    """Ask a Cursor agent to author rich pageContent for a sign, then apply it.

    Gathers the sign's Cree options / graphic / trail facts, runs the
    ``cursor-agent`` CLI headless (uses the local Cursor login, no API key),
    validates the returned JSON through the schema cleaner, and re-renders the
    page at pageStatus=agent-drafted for human review. Implemented in
    tools/flesh_out_sign.py; imported lazily to avoid an import cycle."""
    model_id = str(payload.get("modelId", "")).strip()
    if not model_id:
        raise ValueError("modelId is required")

    import flesh_out_sign as fos  # lazy: fos imports this module at top level

    catalogue = load_catalogue()
    model = find_model(catalogue, model_id)
    ctx = fos.gather_context(model)
    prompt = fos.build_prompt(ctx)

    agent_bin = fos.find_cursor_agent(payload.get("cursorAgentPath") or None)
    if not agent_bin:
        raise ValueError(
            "cursor-agent CLI not found. Install it once and log in: "
            "`curl https://cursor.com/install -fsS | bash` then `cursor-agent login`. "
            "(Or author the JSON in chat and apply with "
            "`tools/flesh_out_sign.py --model <id> --from-json <file>`.)")

    model_name = str(payload.get("modelName") or "")  # empty -> account default
    text = fos.run_cursor_agent(prompt, agent_bin, model_name)
    authored = fos.extract_json_object(text)
    summaries = fos.apply_authored(model_id, authored)
    summary = next((s for s in summaries if s.get("id") == model_id), None)
    return {"ok": True, "model": model_name, "summaries": summaries, "rendered": summary}


class CatalogueEditorHandler(SimpleHTTPRequestHandler):
    server_version = "CatalogueEditor/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def send_json(self, status: int, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json(status, {"ok": False, "error": message})

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)

        try:
            if parsed.path == "/api/health":
                self.send_json(200, {
                    "ok": True,
                    "repoRoot": str(REPO_ROOT),
                    "apiVersion": EDITOR_API_VERSION,
                    "features": EDITOR_API_FEATURES,
                })
                return

            if parsed.path == "/api/stl-candidates":
                query = parse_qs(parsed.query)
                model_id = query.get("modelId", [""])[0]
                catalogue = load_catalogue()
                model = find_model(catalogue, model_id)
                self.send_json(200, {"ok": True, "candidates": candidate_records(model)})
                return

            if parsed.path == "/api/stl-manifest":
                self.send_json(200, {"ok": True, "manifest": build_manifest()})
                return

            if parsed.path == "/api/list-sign-assets":
                query = parse_qs(parsed.query)
                model_id = query.get("modelId", [""])[0]
                self.send_json(200, {"ok": True, "assets": list_sign_assets(model_id)})
                return
        except Exception as exc:  # pragma: no cover - local tool ergonomics
            self.send_error_json(400, str(exc))
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)

        known_endpoints = {
            "/api/save-print-setup",
            "/api/repair-stl",
            "/api/save-sign-content",
            "/api/regenerate-sign-page",
            "/api/upload-sign-photo",
            "/api/upload-trail-source",
            "/api/upload-map-icon",
            "/api/build-sign",
            "/api/build-assembled",
            "/api/build-adjusted",
            "/api/save-adjustments",
            "/api/promote-sign",
            "/api/flesh-out-sign",
        }
        if parsed.path not in known_endpoints:
            self.send_error_json(404, "Unknown API endpoint")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if parsed.path == "/api/save-print-setup":
                self.send_json(200, save_print_setup(payload))
                return
            if parsed.path == "/api/repair-stl":
                self.send_json(200, repair_stl(payload))
                return
            if parsed.path == "/api/save-sign-content":
                self.send_json(200, save_sign_content(payload))
                return
            if parsed.path == "/api/regenerate-sign-page":
                self.send_json(200, regenerate_sign_page(payload))
                return
            if parsed.path == "/api/upload-sign-photo":
                self.send_json(200, upload_sign_photo(payload))
                return
            if parsed.path == "/api/upload-trail-source":
                self.send_json(200, upload_trail_source(payload))
                return
            if parsed.path == "/api/upload-map-icon":
                self.send_json(200, upload_map_icon(payload))
                return
            if parsed.path == "/api/build-sign":
                self.send_json(200, build_sign(payload))
                return
            if parsed.path == "/api/build-assembled":
                self.send_json(200, build_assembled(payload))
                return
            if parsed.path == "/api/build-adjusted":
                self.send_json(200, build_adjusted(payload))
                return
            if parsed.path == "/api/save-adjustments":
                self.send_json(200, save_adjustments(payload))
                return
            if parsed.path == "/api/promote-sign":
                self.send_json(200, promote_sign(payload))
                return
            if parsed.path == "/api/flesh-out-sign":
                self.send_json(200, flesh_out_sign(payload))
                return
        except Exception as exc:  # pragma: no cover - local tool ergonomics
            self.send_error_json(400, str(exc))


def _check_solidify_deps() -> None:
    """Print a loud warning when the solidify pass won't be available.

    The /api/repair-stl endpoint runs an stl_union solidify pass after admesh
    that needs trimesh + manifold3d + shapely installed in the active Python.
    When the server is started outside the project venv those imports fail
    silently per request and only show up as "Boolean-union deps unavailable"
    in the operations log. Shout about it at startup so it's obvious which
    Python the server is running on.
    """
    venv_python = REPO_ROOT / ".venv" / "bin" / "python3"
    in_venv = (
        sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        or os.environ.get("VIRTUAL_ENV")
    )

    if _union_stl is not None:
        print(
            f"[catalogue_editor] solidify deps OK "
            f"(python: {sys.executable}, venv active: {bool(in_venv)})"
        )
        return

    print("=" * 78, file=sys.stderr)
    print(
        "[catalogue_editor] WARNING: solidify (boolean-union / preserve) deps "
        "are not importable.",
        file=sys.stderr,
    )
    print(f"  reason : {_UNION_IMPORT_ERROR}", file=sys.stderr)
    print(f"  python : {sys.executable}", file=sys.stderr)
    print(f"  prefix : {sys.prefix}", file=sys.stderr)
    print(f"  venv   : {'active' if in_venv else 'NOT active'}", file=sys.stderr)
    print(
        "  -> /api/repair-stl will fall back to admesh-only repair and the M chip "
        "will stay pending.",
        file=sys.stderr,
    )
    print("  Fix:", file=sys.stderr)
    print("    bash tools/run_catalogue_editor_server.sh", file=sys.stderr)
    if venv_python.exists():
        print(
            f"    # or: source .venv/bin/activate && python3 tools/catalogue_editor_server.py",
            file=sys.stderr,
        )
    else:
        print(
            "    # first create the venv: python3 -m venv .venv && "
            "source .venv/bin/activate && pip install -r requirements.txt",
            file=sys.stderr,
        )
    print("=" * 78, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local nehiyoMTB catalogue editor server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    mimetypes.add_type("model/stl", ".stl")
    regenerate_manifest()

    _check_solidify_deps()

    server = ThreadingHTTPServer((args.host, args.port), CatalogueEditorHandler)
    print(f"Serving local catalogue editor at http://{args.host}:{args.port}/docs/index.html")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
