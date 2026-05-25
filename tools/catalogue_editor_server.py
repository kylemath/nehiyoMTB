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
EDITOR_API_VERSION = 3
EDITOR_API_FEATURES = [
    "savePrintSetup",
    "repairStl",
    "saveSignContent",
    "regenerateSignPage",
    "uploadSignPhoto",
    "uploadTrailSource",
    "uploadMapIcon",
    "parseTrailTrack",
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
