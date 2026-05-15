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
import posixpath
import re
import shutil
import subprocess
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
    _UNION_IMPORT_ERROR: str | None = None
except Exception as _exc:  # pragma: no cover - optional dependency
    _union_stl = None  # type: ignore[assignment]
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

    admesh_stats = parse_admesh_stats(stdout_text + "\n" + stderr_text)

    operations = [
        f"Backed up {repo_relative(source_path)} to {repo_relative(backup_path)}",
        f"Repaired {repo_relative(source_path)} to {repo_relative(repaired_path)}",
    ]

    # Boolean-union pass. Even an admesh-watertight mesh frequently still
    # contains many disjoint shells (plaque body + embedded silhouettes) that
    # share coincident faces; slicers like Creality Print cancel those facets
    # and end up slicing the embedded shapes as open-bottomed vases. Running a
    # manifold boolean union here merges everything that overlaps into a single
    # solid and nudges shells apart by a sub-micron to defeat the cancellation.
    union_stats: dict | None = None
    union_skipped_reason: str | None = None
    final_repair_path = repaired_path
    union_requested = bool(payload.get("unionShells", True))

    if not union_requested:
        union_skipped_reason = "unionShells flag was false in the request"
    elif _union_stl is None:
        union_skipped_reason = (
            f"Boolean-union deps unavailable ({_UNION_IMPORT_ERROR or 'unknown error'}); "
            "install trimesh + manifold3d in the venv to enable solidify step"
        )
    else:
        solid_path = unique_variant_path(
            source_path.with_name(f"{source_path.stem}_solid{source_path.suffix}")
        )
        try:
            union_stats = _union_stl(repaired_path, solid_path, verbose=False)
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
                operations.append(
                    f"Boolean-union merged {union_stats['inputShells']} shells "
                    f"({union_stats['shellsFallback']} via silhouette fallback, "
                    f"{union_stats['shellsDropped']} dropped) into "
                    f"{union_stats['outputShells']} shell"
                    f"{'s' if union_stats['outputShells'] != 1 else ''}; "
                    f"wrote {repo_relative(solid_path)}"
                )

    if union_skipped_reason:
        operations.append(union_skipped_reason)

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

    # Mesh is "ready" when admesh found it watertight AND, if the union step
    # ran, the solidified output is also watertight. The slicer-side hollow-
    # shell bug only goes away when both are true.
    admesh_ok = admesh_stats["totalDisconnectedFinal"] is not None and admesh_stats["isWatertight"]
    union_ok = (
        union_stats is None
        or union_stats.get("skipped")
        or union_stats.get("outputWatertight", False)
    )
    mesh_ready = bool(admesh_ok and union_ok)

    if admesh_stats["totalDisconnectedFinal"] is not None:
        existing_checks = model.get("checks") if isinstance(model.get("checks"), dict) else {}
        merged_checks = dict(existing_checks)
        merged_checks["meshRepaired"] = mesh_ready
        model["checks"] = merged_checks
        write_json(CATALOGUE_PATH, catalogue)
        if mesh_ready:
            operations.append(
                "Mesh is watertight and solidified — flagged checks.meshRepaired=true"
            )
        else:
            reasons: list[str] = []
            if not admesh_ok and admesh_stats["totalDisconnectedFinal"] is not None:
                reasons.append(f"{admesh_stats['totalDisconnectedFinal']} admesh-disconnected facets")
            if union_stats and not union_stats.get("skipped") and not union_stats.get("outputWatertight"):
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


def _clean_trailforks(raw: Any) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("trailforks must be an object")
    trail_id = _clean_string(raw.get("trailId"))
    trail_url = _clean_string(raw.get("trailUrl"))
    widget_url = _clean_string(raw.get("widgetUrl"))
    display_name = _clean_string(raw.get("displayName"))
    if not trail_url and not widget_url and not trail_id:
        return {}
    if trail_id and not widget_url:
        widget_url = (
            f"https://www.trailforks.com/widgets/trail/?trailid={trail_id}"
            "&w=50%&h=350px&activitytype=6&map=1&basemap=trailforks-streets"
            "&elevation=1&photos=1&title=1&info=1&trail_opacity=50&v=2&basicmap=1"
        )
    return {
        "trailId": trail_id,
        "trailUrl": trail_url,
        "widgetUrl": widget_url,
        "displayName": display_name,
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


def save_sign_content(payload: dict) -> dict:
    catalogue = load_catalogue()
    model = find_model(catalogue, str(payload.get("modelId", "")))

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
                self.send_json(200, {"ok": True, "repoRoot": str(REPO_ROOT)})
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
        except Exception as exc:  # pragma: no cover - local tool ergonomics
            self.send_error_json(400, str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local nehiyoMTB catalogue editor server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    mimetypes.add_type("model/stl", ".stl")
    regenerate_manifest()

    server = ThreadingHTTPServer((args.host, args.port), CatalogueEditorHandler)
    print(f"Serving local catalogue editor at http://{args.host}:{args.port}/docs/index.html")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
