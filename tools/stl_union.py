#!/usr/bin/env python3
"""Boolean-union the disjoint shells of a sign STL into a single watertight solid.

Many of the source SketchUp exports for the nehiyoMTB sign catalogue contain
multiple disjoint manifold shells (e.g. plaque body + embedded animal silhouette
+ accent shapes). Slicers like Creality Print treat each shell as its own print
object, and when shells share coincident faces with the plaque body the slicer
cancels the duplicate facets and ends up slicing thin "vase" shells with no
infill or support. The fix is a true boolean union performed before slicing.

This tool loads the STL, splits it into watertight components, optionally nudges
coincident faces apart by a tiny epsilon to make the union deterministic, and
runs a manifold-engine union, writing a single-shell STL.

CLI usage::

    python3 tools/stl_union.py kahkakiw/kahkakiw_plaque_hybrid_fixed.stl
    # writes kahkakiw/kahkakiw_plaque_hybrid_fixed_solid.stl

    python3 tools/stl_union.py in.stl -o out.stl --epsilon 0.001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh


def _repair_shell(part: trimesh.Trimesh) -> trimesh.Trimesh:
    """Best-effort repair of a single shell so the manifold engine accepts it.

    Steps: merge near-duplicate vertices, drop degenerate/duplicate faces,
    fix winding + outward normals, fill holes. Returns the part in place.
    """
    part.merge_vertices()
    if hasattr(part, "remove_duplicate_faces"):
        part.remove_duplicate_faces()
    if hasattr(part, "remove_degenerate_faces"):
        part.remove_degenerate_faces()
    part.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(part)
    trimesh.repair.fix_inversion(part)
    trimesh.repair.fix_normals(part)
    if not part.is_watertight:
        trimesh.repair.fill_holes(part)
    return part


def _extrude_silhouette(part: trimesh.Trimesh, pad: float = 0.0) -> trimesh.Trimesh:
    """Fallback: project ``part`` onto Z=min and extrude to Z=max.

    Used when a shell can't be repaired into a manifold volume. This guarantees
    a solid prism that fully covers the part's footprint, which is exactly what
    we want for embedded plaque features (heron silhouette, antlers, etc.).
    """
    import shapely.ops
    from shapely.geometry import Polygon

    z_min = float(part.bounds[0][2]) - pad
    z_max = float(part.bounds[1][2]) + pad
    height = max(z_max - z_min, 1e-6)

    triangles_2d = part.vertices[part.faces][:, :, :2]
    polys = [Polygon(tri) for tri in triangles_2d if Polygon(tri).is_valid and Polygon(tri).area > 0]
    if not polys:
        return part
    footprint = shapely.ops.unary_union(polys).buffer(0)
    extruded = trimesh.creation.extrude_polygon(footprint, height=height)
    extruded.apply_translation([0.0, 0.0, z_min])
    return extruded


def union_stl(
    src: Path,
    dst: Path,
    epsilon: float = 0.001,
    verbose: bool = True,
    silhouette_fallback: bool = True,
) -> dict:
    """Union all disjoint shells in ``src`` into a single solid written to ``dst``.

    ``epsilon`` is a tiny Z translation applied to alternating shells to break
    coincident-face cancellation in the boolean engine. Set to 0 to disable.

    ``silhouette_fallback``: if a shell can't be repaired into a watertight
    volume, replace it with a solid prism extruded from its 2D silhouette. This
    is appropriate for sign-style plaques where every shell is a flat plateau.

    Returns a stats dict suitable for JSON serialisation::

        {
            "ok": True,
            "skipped": False,           # True when input is already single-shell
            "inputFaces": int,
            "inputShells": int,
            "inputWatertight": bool,
            "shellsUsable": int,
            "shellsFallback": int,
            "shellsDropped": int,
            "outputFaces": int,
            "outputShells": int,
            "outputWatertight": bool,
            "outputVolume": float,
        }
    """
    if verbose:
        print(f"[stl_union] loading {src}")
    loaded = trimesh.load(src, force="mesh")
    if isinstance(loaded, trimesh.Scene):
        loaded = trimesh.util.concatenate(tuple(loaded.dump()))

    parts = loaded.split(only_watertight=False)
    if verbose:
        print(
            f"[stl_union] {len(loaded.faces)} faces, "
            f"{len(parts)} disjoint shells, "
            f"input watertight={loaded.is_watertight}"
        )

    base_stats = {
        "ok": True,
        "skipped": False,
        "inputFaces": int(len(loaded.faces)),
        "inputShells": int(len(parts)),
        "inputWatertight": bool(loaded.is_watertight),
        "shellsUsable": int(len(parts)),
        "shellsFallback": 0,
        "shellsDropped": 0,
    }

    if len(parts) <= 1:
        if verbose:
            print("[stl_union] only one shell; copying through")
        loaded.export(dst)
        return {
            **base_stats,
            "skipped": True,
            "outputFaces": int(len(loaded.faces)),
            "outputShells": 1,
            "outputWatertight": bool(loaded.is_watertight),
            "outputVolume": float(loaded.volume) if loaded.is_volume else 0.0,
        }

    repaired: list[trimesh.Trimesh] = []
    fallbacks = 0
    dropped = 0
    for i, part in enumerate(parts):
        _repair_shell(part)
        if not part.is_volume and silhouette_fallback:
            fallbacks += 1
            part = _extrude_silhouette(part)
            _repair_shell(part)
        if not part.is_volume:
            dropped += 1
            if verbose:
                print(
                    f"[stl_union]   dropping shell {i}: "
                    f"watertight={part.is_watertight}, winding_consistent={part.is_winding_consistent}, "
                    f"faces={len(part.faces)}"
                )
            continue
        repaired.append(part)

    if verbose:
        print(
            f"[stl_union] {len(repaired)}/{len(parts)} shells usable "
            f"({fallbacks} via silhouette fallback, {dropped} dropped)"
        )

    if epsilon > 0:
        for i, part in enumerate(repaired[1:], start=1):
            part.apply_translation([0.0, 0.0, epsilon * ((i % 2) * 2 - 1) * 0.5])

    if verbose:
        print(f"[stl_union] running manifold union on {len(repaired)} shells")
    unioned = trimesh.boolean.union(repaired, engine="manifold")

    if epsilon > 0:
        unioned.apply_translation([0.0, 0.0, -epsilon * 0.5])

    unioned.merge_vertices()
    if hasattr(unioned, "remove_duplicate_faces"):
        unioned.remove_duplicate_faces()
    unioned.remove_unreferenced_vertices()

    final_parts = unioned.split(only_watertight=False)
    if verbose:
        print(
            f"[stl_union] result: {len(unioned.faces)} faces, "
            f"{len(final_parts)} shells, "
            f"watertight={unioned.is_watertight}, "
            f"volume={unioned.volume:.2f}"
        )

    unioned.export(dst)
    if verbose:
        print(f"[stl_union] wrote {dst}")

    return {
        **base_stats,
        "shellsUsable": int(len(repaired)),
        "shellsFallback": int(fallbacks),
        "shellsDropped": int(dropped),
        "outputFaces": int(len(unioned.faces)),
        "outputShells": int(len(final_parts)),
        "outputWatertight": bool(unioned.is_watertight),
        "outputVolume": float(unioned.volume) if unioned.is_volume else 0.0,
    }


def _default_dst(src: Path) -> Path:
    stem = src.stem
    for suffix in ("_admesh_fixed", "_hybrid_fixed", "_bk", "_moved1"):
        while stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return src.with_name(f"{stem}_solid.stl")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("src", type=Path, help="input STL path")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output STL path (default: <src>_solid.stl, with redundant suffixes stripped)",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.001,
        help="tiny Z nudge applied to non-first shells to break coincident-face "
        "cancellation in the union engine (default 0.001 mm; 0 disables)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="suppress progress output"
    )
    args = parser.parse_args(argv)

    src: Path = args.src
    if not src.exists():
        print(f"[stl_union] error: source not found: {src}", file=sys.stderr)
        return 2

    dst: Path = args.output or _default_dst(src)
    union_stl(src, dst, epsilon=args.epsilon, verbose=not args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
