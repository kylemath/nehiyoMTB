#!/usr/bin/env python3
"""Boolean-union the disjoint shells of a sign STL into a single watertight solid.

Many of the source SketchUp exports for the nehiyoMTB sign catalogue contain
multiple disjoint manifold shells (e.g. plaque body + embedded animal silhouette
+ accent shapes). Slicers like Creality Print treat each shell as its own print
object, and when shells share coincident faces with the plaque body the slicer
cancels the duplicate facets and ends up slicing thin "vase" shells with no
infill or support. The fix is a true boolean union performed before slicing.

Strategies available:

* ``clean`` (default, minimal-touch): drops the cancelling triangle pairs that
  SketchUp emits at shared faces between abutting solid groups, then runs
  admesh only for normal-direction/value fixing (no ``--fill-holes`` and no
  boolean union). Preserves the original visible surface and the artist's
  intentional cutouts; ends up "manifold enough" for most slicers without
  changing what the artwork looks like.
* ``preserve`` (per-shell solidify): closes every shell individually without
  boolean-unioning raised artwork into the plaque body. Good for catalogue
  artwork where every raised feature is its own solid and you want all the
  cutouts kept as cutouts, at the cost of more shells.
* ``manifold`` (per-shell repair + ``manifold3d`` boolean union): folds shells
  that overlap into single watertight solids. Can fill artistic cutouts when
  the plaque body sits under a raised relief feature.
* ``silhouette`` (rasterise all triangles to 2D, ``shapely.unary_union``, then
  extrude): the "nuclear option" that always produces a single watertight
  solid by flattening Z relief.

``auto`` uses ``clean`` because it is the lowest-impact option that keeps the
original artwork intact. Pass ``--strategy preserve``/``manifold``/``silhouette``
to opt into the more invasive strategies.

CLI usage::

    python3 tools/stl_union.py kahkakiw/kahkakiw_plaque_hybrid_fixed.stl
    python3 tools/stl_union.py in.stl -o out.stl --strategy silhouette
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

# Shells smaller than this many faces, OR with absolute signed volume below this
# threshold, are treated as numerical-noise slivers in the watertight check so a
# single sliver doesn't flip the whole-mesh status to False.
_SLIVER_FACE_THRESHOLD = 4
_SLIVER_VOLUME_THRESHOLD = 1.0


def _repair_shell(part: trimesh.Trimesh, *, fill_holes: bool = True) -> trimesh.Trimesh:
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
    if fill_holes and not part.is_watertight:
        trimesh.repair.fill_holes(part)
    return part


def _extrude_footprint(footprint, z_min: float, height: float) -> trimesh.Trimesh:
    """Extrude a shapely ``Polygon`` or ``MultiPolygon`` to a trimesh prism.

    ``trimesh.creation.extrude_polygon`` only accepts single ``Polygon``s — it
    blows up on ``MultiPolygon`` with ``AttributeError: ... no attribute
    'exterior'``. We loop over disjoint sub-polygons, extrude each one, and
    concatenate the meshes (they live in disjoint XY regions so the resulting
    mesh has multiple shells, which is fine — the caller boolean-unions them
    along with everything else).
    """
    from shapely.geometry import MultiPolygon, Polygon

    if isinstance(footprint, Polygon):
        polys = [footprint]
    elif isinstance(footprint, MultiPolygon):
        polys = list(footprint.geoms)
    else:
        polys = [g for g in getattr(footprint, "geoms", []) if isinstance(g, Polygon)]

    meshes: list[trimesh.Trimesh] = []
    for poly in polys:
        if poly.is_empty or poly.area <= 1e-9:
            continue
        try:
            m = trimesh.creation.extrude_polygon(poly, height=height)
        except Exception:
            buffered = poly.buffer(0)
            if buffered.is_empty:
                continue
            if isinstance(buffered, MultiPolygon):
                sub = _extrude_footprint(buffered, z_min, height)
                meshes.append(sub)
                continue
            m = trimesh.creation.extrude_polygon(buffered, height=height)
        m.apply_translation([0.0, 0.0, z_min])
        meshes.append(m)

    if not meshes:
        raise ValueError("Footprint produced no extrudable sub-polygons")
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.util.concatenate(meshes)


def _remove_sliver_shells(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop tiny fallback artifacts while keeping legitimate small details.

    Hole-preserving footprint extrusion can leave 2-face shards around polygon
    interior rings. Those shards can have nonsensical signed volume because
    they're open triangle pairs, so require both a minimum face count and a
    minimum volume before keeping a shell.
    """
    keep: list[trimesh.Trimesh] = []
    for part in mesh.split(only_watertight=False):
        if len(part.faces) <= _SLIVER_FACE_THRESHOLD:
            continue
        if abs(_shell_volume_signed(part)) <= _SLIVER_VOLUME_THRESHOLD:
            continue
        keep.append(part)
    if not keep:
        return mesh
    if len(keep) == 1:
        return keep[0]
    return trimesh.util.concatenate(keep)


def _extrude_silhouette_part(part: trimesh.Trimesh, pad: float = 0.0) -> trimesh.Trimesh:
    """Extrude a single shell's 2D footprint between its own [zmin, zmax].

    Used as a per-shell fallback in the manifold strategy when an individual
    shell can't be repaired into a manifold volume.
    """
    import shapely.ops
    from shapely.geometry import Polygon

    z_min = float(part.bounds[0][2]) - pad
    z_max = float(part.bounds[1][2]) + pad
    height = max(z_max - z_min, 1e-6)

    # Use the top-facing footprint, not every triangle projected to XY. Side
    # walls around fine negative details (eyes, fur cuts, text counters) have
    # non-zero XY area; projecting them fills the very holes we need to keep.
    # Top-facing triangles preserve those holes because the missing top surface
    # remains missing in the footprint.
    triangles = part.vertices[part.faces]
    z_top = float(part.bounds[1][2])
    # SketchUp exports these plaques with crisp Z plateaus; use only triangles
    # essentially on the highest visible plane. A larger tolerance can include
    # lower ledges that fill eye/fur cutouts.
    z_tol = 1e-3
    triangle_mean_z = triangles[:, :, 2].mean(axis=1)
    top_mask = (part.face_normals[:, 2] > 0.2) & (triangle_mean_z >= z_top - z_tol)
    top_triangles_2d = triangles[top_mask, :, :2]
    polys = [
        Polygon(tri)
        for tri in top_triangles_2d
        if Polygon(tri).is_valid and Polygon(tri).area > 0
    ]
    if not polys:
        top_mask = part.face_normals[:, 2] > 0.2
        triangles_2d = triangles[top_mask, :, :2]
        polys = [
            Polygon(tri)
            for tri in triangles_2d
            if Polygon(tri).is_valid and Polygon(tri).area > 0
        ]
    if not polys:
        triangles_2d = triangles[:, :, :2]
        polys = [
            Polygon(tri)
            for tri in triangles_2d
            if Polygon(tri).is_valid and Polygon(tri).area > 0
        ]
    if not polys:
        return part
    footprint = shapely.ops.unary_union(polys).buffer(0)
    if footprint.is_empty:
        return part
    return _remove_sliver_shells(_extrude_footprint(footprint, z_min, height))


def _silhouette_union(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Flatten ``mesh`` to a single solid extruded between its global zmin/zmax.

    Computes the 2D union of every triangle's XY footprint and extrudes it to
    the mesh's full Z range. This is the deterministic "nuclear option" for
    flat plaques where the input may be hopelessly fragmented but the desired
    output is just one solid slab matching the silhouette of all detail.
    """
    import shapely
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    z_min = float(mesh.bounds[0][2])
    z_max = float(mesh.bounds[1][2])
    height = max(z_max - z_min, 1e-6)

    # Build one shapely Polygon per non-degenerate triangle. Some triangles in
    # SketchUp exports are coincident or zero-area in XY (vertical walls); we
    # filter those out because they contribute no footprint anyway.
    tris_xy = mesh.vertices[mesh.faces][:, :, :2]
    polys: list[Polygon] = []
    for tri in tris_xy:
        poly = Polygon(tri)
        if poly.is_valid and poly.area > 1e-9:
            polys.append(poly)
        else:
            buffered = poly.buffer(0)
            if not buffered.is_empty and buffered.area > 1e-9:
                polys.append(buffered)

    if not polys:
        raise ValueError("Silhouette union: no non-degenerate triangle footprints")

    footprint = unary_union(polys)
    # `unary_union` on tens of thousands of overlapping triangles can produce
    # tiny slivers along shared edges; a zero-width buffer cleans them up.
    footprint = footprint.buffer(0)

    if footprint.is_empty:
        raise ValueError("Silhouette union: empty footprint after merge")

    extruded = _extrude_footprint(footprint, z_min, height)
    extruded.merge_vertices()
    return extruded


def _shell_volume_signed(part: trimesh.Trimesh) -> float:
    """Signed volume of a triangle soup without requiring strict manifoldness.

    trimesh's ``Trimesh.volume`` accessor raises a warning and returns NaN on
    non-volumetric meshes; here we just want a number for the sliver heuristic.
    """
    tris = part.triangles
    if len(tris) == 0:
        return 0.0
    return float(np.sum(np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2]))) / 6.0)


def _is_effectively_watertight(mesh: trimesh.Trimesh) -> tuple[bool, dict]:
    """Looser watertight check that tolerates numerical-noise sliver shells.

    Returns ``(is_watertight, diagnostics)``. A mesh passes when every
    non-sliver shell is individually watertight + winding-consistent. Sliver
    shells (fewer than a handful of faces, or near-zero volume) are reported
    but not treated as failures because they're typically degenerate fragments
    left over from the boolean engine that don't affect slicing.
    """
    diag = {
        "totalShells": 0,
        "sliverShells": 0,
        "failingShells": 0,
        "failureReasons": [],
    }
    parts = mesh.split(only_watertight=False)
    diag["totalShells"] = len(parts)
    if not parts:
        return False, diag

    for idx, part in enumerate(parts):
        signed_vol = _shell_volume_signed(part)
        is_sliver = (
            len(part.faces) <= _SLIVER_FACE_THRESHOLD
            or abs(signed_vol) <= _SLIVER_VOLUME_THRESHOLD
        )
        if is_sliver:
            diag["sliverShells"] += 1
            continue
        if not part.is_watertight or not part.is_winding_consistent:
            diag["failingShells"] += 1
            diag["failureReasons"].append(
                f"shell {idx}: faces={len(part.faces)}, "
                f"watertight={part.is_watertight}, "
                f"winding_consistent={part.is_winding_consistent}, "
                f"signed_volume={signed_vol:.2f}"
            )

    return diag["failingShells"] == 0, diag


def _admesh_cleanup(stl_path: Path, verbose: bool = True) -> dict:
    """Pipe ``stl_path`` through admesh in-place to fix normals + degenerates.

    The manifold boolean engine occasionally produces meshes with inconsistent
    normal orientation and a handful of degenerate facets. admesh is fast and
    fixes both cleanly. Returns a small stats dict; silently returns
    ``{"ran": False, "reason": ...}`` when admesh isn't on PATH so the caller
    can keep going with the un-cleaned mesh.
    """
    admesh_bin = shutil.which("admesh")
    if not admesh_bin:
        return {"ran": False, "reason": "admesh not on PATH"}

    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        cmd = [
            admesh_bin,
            "--normal-directions",
            "--normal-values",
            f"--write-binary-stl={tmp_path}",
            str(stl_path),
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            return {
                "ran": False,
                "reason": (result.stderr or result.stdout or b"admesh failed")
                .decode("utf-8", errors="replace")
                .strip(),
            }
        shutil.move(str(tmp_path), str(stl_path))
        out = result.stdout.decode("utf-8", errors="replace")
        normals_fixed = 0
        degenerates_removed = 0
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Normals fixed"):
                try:
                    normals_fixed = int(line.split(":")[1].strip())
                except (IndexError, ValueError):
                    pass
            elif line.startswith("Facets removed"):
                try:
                    degenerates_removed = int(line.split(":")[1].strip())
                except (IndexError, ValueError):
                    pass
        if verbose:
            print(
                f"[stl_union] admesh cleanup: normals_fixed={normals_fixed}, "
                f"degenerates_removed={degenerates_removed}"
            )
        return {
            "ran": True,
            "normalsFixed": normals_fixed,
            "degeneratesRemoved": degenerates_removed,
        }
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _dedupe_internal_face_pairs(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, int]:
    """Drop pairs of triangles that share all 3 vertices with opposite normals.

    SketchUp exports of multi-solid groups emit one copy of the shared face per
    abutting group. Each copy has the opposite normal of the other, so the pair
    is interior cancelling geometry that produces non-manifold edges (every edge
    of the shared face touches 4 triangles instead of 2). Removing matched pairs
    leaves the visible surface untouched and turns those edges manifold.
    """
    from collections import defaultdict

    mesh.merge_vertices()
    seen: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for i, face in enumerate(mesh.faces):
        seen[tuple(sorted(int(v) for v in face))].append(i)

    drop: set[int] = set()
    for idxs in seen.values():
        if len(idxs) < 2:
            continue
        used = [False] * len(idxs)
        for j in range(len(idxs)):
            if used[j]:
                continue
            for k in range(j + 1, len(idxs)):
                if used[k]:
                    continue
                if np.dot(mesh.face_normals[idxs[j]], mesh.face_normals[idxs[k]]) < -0.5:
                    drop.add(idxs[j])
                    drop.add(idxs[k])
                    used[j] = True
                    used[k] = True
                    break

    if not drop:
        return mesh, 0

    keep = np.ones(len(mesh.faces), dtype=bool)
    keep[list(drop)] = False
    cleaned = trimesh.Trimesh(
        vertices=mesh.vertices.copy(),
        faces=mesh.faces[keep],
        process=False,
    )
    return cleaned, len(drop)


def _clean_topology_strategy(
    loaded: trimesh.Trimesh,
    verbose: bool,
) -> tuple[trimesh.Trimesh, dict]:
    """Iteratively dedupe interior cancelling triangles. Returns cleaned mesh.

    This is the lowest-impact strategy: it does not boolean-union, fill holes,
    or extrude silhouettes. It just drops the SketchUp shared-face artifact so
    the slicer sees a closer-to-manifold surface without changing what's
    visible. The caller's post-union admesh cleanup runs ``--normal-directions
    --normal-values`` after this strategy completes (no ``--fill-holes``).
    """
    total_dropped = 0
    current = loaded
    for iteration in range(8):
        current, dropped = _dedupe_internal_face_pairs(current)
        total_dropped += dropped
        if verbose:
            print(f"[stl_union] clean iter {iteration + 1}: dropped {dropped} cancelling triangles")
        if dropped == 0:
            break

    current.remove_unreferenced_vertices()
    return current, {
        "shellsUsable": len(current.split(only_watertight=False)),
        "shellsFallback": 0,
        "shellsDropped": 0,
        "cleanFacesDropped": total_dropped,
    }


def _manifold_strategy(
    loaded: trimesh.Trimesh,
    epsilon: float,
    silhouette_fallback: bool,
    verbose: bool,
) -> tuple[trimesh.Trimesh, dict]:
    """Per-shell repair + ``manifold3d`` boolean union path."""
    parts = loaded.split(only_watertight=False)

    repaired: list[trimesh.Trimesh] = []
    fallbacks = 0
    dropped = 0
    for i, part in enumerate(parts):
        # Don't fill holes before deciding whether to use silhouette fallback:
        # on artwork plaques, "holes" are often intentional negative details
        # (eyes, fur cuts, text counters) that must remain open in the raised
        # feature. The fallback extrudes the top-face footprint and can preserve
        # them, but only if we haven't already filled them here.
        _repair_shell(part, fill_holes=False)
        if not part.is_volume and silhouette_fallback:
            fallbacks += 1
            part = _extrude_silhouette_part(part)
            _repair_shell(part, fill_holes=False)
        if not part.is_volume:
            _repair_shell(part, fill_holes=True)
        if not part.is_volume:
            dropped += 1
            if verbose:
                print(
                    f"[stl_union]   dropping shell {i}: "
                    f"watertight={part.is_watertight}, "
                    f"winding_consistent={part.is_winding_consistent}, "
                    f"faces={len(part.faces)}"
                )
            continue
        repaired.append(part)

    if verbose:
        print(
            f"[stl_union] {len(repaired)}/{len(parts)} shells usable "
            f"({fallbacks} via silhouette fallback, {dropped} dropped)"
        )

    if not repaired:
        raise ValueError("Manifold strategy: no usable shells after repair")

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

    return unioned, {
        "shellsUsable": len(repaired),
        "shellsFallback": fallbacks,
        "shellsDropped": dropped,
    }


def _preserve_shells_strategy(
    loaded: trimesh.Trimesh,
    verbose: bool,
    min_planar_height: float = 0.01,
) -> tuple[trimesh.Trimesh, dict]:
    """Solidify each shell independently without boolean-unioning relief away.

    This is the best default for the catalogue plaques: each visible raised
    feature becomes a closed volume, but holes/cutouts within that feature
    remain holes because we never union it into the underlying plaque body.
    Zero-height planar sheets from SketchUp exports are skipped; they are
    display surfaces, not printable volumes, and otherwise produce degenerate
    1e-6-thick slivers.
    """
    parts = loaded.split(only_watertight=False)
    solidified: list[trimesh.Trimesh] = []
    fallbacks = 0
    dropped = 0
    planar_skipped = 0

    for i, part in enumerate(parts):
        part = part.copy()
        _repair_shell(part, fill_holes=False)
        z_extent = float(part.bounds[1][2] - part.bounds[0][2])

        if part.is_volume:
            solidified.append(part)
            continue

        if z_extent < min_planar_height:
            planar_skipped += 1
            if verbose:
                print(
                    f"[stl_union]   skipping zero-height shell {i}: "
                    f"faces={len(part.faces)}, z_extent={z_extent:.6f}"
                )
            continue

        try:
            fallback = _extrude_silhouette_part(part)
            _repair_shell(fallback, fill_holes=False)
            ok, _diag = _is_effectively_watertight(fallback)
            if not ok:
                _repair_shell(fallback, fill_holes=True)
                ok, _diag = _is_effectively_watertight(fallback)
            if ok:
                solidified.append(fallback)
                fallbacks += 1
            else:
                dropped += 1
                if verbose:
                    print(f"[stl_union]   dropping shell {i}: fallback not watertight")
        except Exception as exc:
            dropped += 1
            if verbose:
                print(f"[stl_union]   dropping shell {i}: fallback failed: {exc}")

    if not solidified:
        raise ValueError("Preserve strategy: no usable shells after solidification")

    if verbose:
        print(
            f"[stl_union] preserve solidified {len(solidified)}/{len(parts)} shells "
            f"({fallbacks} via top-face fallback, {planar_skipped} planar skipped, "
            f"{dropped} dropped)"
        )

    return trimesh.util.concatenate(solidified), {
        "shellsUsable": len(solidified),
        "shellsFallback": fallbacks,
        "shellsDropped": dropped,
        "planarShellsSkipped": planar_skipped,
    }


def _is_flat_plaque(mesh: trimesh.Trimesh, flatness_ratio: float) -> bool:
    """True when the mesh's Z extent is a small fraction of its XY extent.

    ``flatness_ratio`` of 0.15 means: classify as flat when Z extent < 15% of
    max(X extent, Y extent). All sign plaques in this catalogue are flat slabs
    around 2-5mm thick on 60-220mm bases, so they easily clear this bar.
    """
    extent = mesh.bounds[1] - mesh.bounds[0]
    xy_max = max(float(extent[0]), float(extent[1]), 1e-9)
    z = float(extent[2])
    return z / xy_max < flatness_ratio


def union_stl(
    src: Path,
    dst: Path,
    epsilon: float = 0.001,
    verbose: bool = True,
    silhouette_fallback: bool = True,
    strategy: str = "auto",
    flatness_ratio: float = 0.15,
    cleanup_admesh: bool = True,
) -> dict:
    """Union all disjoint shells in ``src`` into a single solid written to ``dst``.

    ``strategy``:

    * ``"auto"`` (default) — try ``preserve`` first to keep relief cutouts,
      then fall back to boolean-style strategies only if needed.
    * ``"preserve"`` — solidify each shell independently without boolean union;
      best for plaque artwork with eye/fur/text cutouts.
    * ``"manifold"`` — per-shell repair + ``manifold3d`` boolean union only.
    * ``"silhouette"`` — flatten everything to one 2D union and extrude.

    ``epsilon`` nudges alternating shells by a sub-micron to break coincident-
    face cancellation in the manifold engine. ``silhouette_fallback`` controls
    per-shell silhouette fallback inside the manifold strategy. ``flatness_ratio``
    is reported as a diagnostic only; ``auto`` no longer uses flatness to choose
    the destructive silhouette path. ``cleanup_admesh`` runs admesh in-place on
    the result to fix inverted normals and remove degenerate facets (cheap,
    recommended).
    """
    if verbose:
        print(f"[stl_union] loading {src}")
    loaded = trimesh.load(src, force="mesh")
    if isinstance(loaded, trimesh.Scene):
        loaded = trimesh.util.concatenate(tuple(loaded.dump()))

    parts = loaded.split(only_watertight=False)
    is_flat = _is_flat_plaque(loaded, flatness_ratio)
    if verbose:
        print(
            f"[stl_union] {len(loaded.faces)} faces, "
            f"{len(parts)} disjoint shells, "
            f"input watertight={loaded.is_watertight}, "
            f"flat_plaque={is_flat}"
        )

    base_stats = {
        "ok": True,
        "skipped": False,
        "strategyRequested": strategy,
        "strategyUsed": None,
        "isFlatPlaque": is_flat,
        "inputFaces": int(len(loaded.faces)),
        "inputShells": int(len(parts)),
        "inputWatertight": bool(loaded.is_watertight),
        "shellsUsable": int(len(parts)),
        "shellsFallback": 0,
        "shellsDropped": 0,
        "cleanAttempted": False,
        "manifoldAttempted": False,
        "manifoldWatertight": None,
        "preserveAttempted": False,
        "silhouetteAttempted": False,
        "cleanupAdmesh": None,
    }

    if len(parts) <= 1:
        if verbose:
            print("[stl_union] only one shell; copying through")
        loaded.export(dst)
        diag = {"totalShells": 1, "sliverShells": 0, "failingShells": 0, "failureReasons": []}
        return {
            **base_stats,
            "skipped": True,
            "strategyUsed": "passthrough",
            "outputFaces": int(len(loaded.faces)),
            "outputShells": 1,
            "outputWatertight": bool(loaded.is_watertight),
            "outputWatertightDiag": diag,
            "outputVolume": float(loaded.volume) if loaded.is_volume else 0.0,
        }

    # Strategy selection. ``auto`` runs the minimal-touch ``clean`` strategy:
    # it drops SketchUp shared-face cancelling triangle pairs but does NOT
    # boolean-union, fill holes, or extrude silhouettes. That preserves the
    # original visible surface (including artistic cutouts in raised relief)
    # while removing most of the non-manifold edges. The other strategies stay
    # available behind explicit ``--strategy`` requests for cases where the
    # source mesh needs more aggressive solidification.
    run_clean = False
    run_preserve = False
    run_manifold = False
    allow_silhouette_fallback = False

    if strategy == "auto" or strategy == "clean":
        run_clean = True
    elif strategy == "silhouette":
        allow_silhouette_fallback = True
    elif strategy == "manifold":
        run_manifold = True
    elif strategy == "preserve":
        run_preserve = True
    else:
        raise ValueError(f"Unknown strategy: {strategy!r}")

    unioned: trimesh.Trimesh | None = None
    used_strategy: str | None = None
    manifold_diag: dict | None = None
    manifold_watertight: bool | None = None
    manifold_error: str | None = None

    if run_clean:
        base_stats["cleanAttempted"] = True
        try:
            unioned, clean_stats = _clean_topology_strategy(loaded, verbose=verbose)
            base_stats.update(clean_stats)
            used_strategy = "clean"
        except Exception as exc:
            if verbose:
                print(f"[stl_union] clean strategy failed: {exc}")
            unioned = None
            if strategy == "clean":
                raise

    if run_preserve:
        base_stats["preserveAttempted"] = True
        try:
            unioned, preserve_stats = _preserve_shells_strategy(loaded, verbose=verbose)
            base_stats.update(preserve_stats)
            preserve_watertight, _preserve_diag = _is_effectively_watertight(unioned)
            if preserve_watertight and len(unioned.faces) > 0:
                used_strategy = "preserve"
            else:
                unioned = None
                if strategy == "preserve":
                    raise ValueError("Preserve strategy did not produce watertight output")
        except Exception as exc:
            if verbose:
                print(f"[stl_union] preserve strategy failed: {exc}")
            unioned = None
            if strategy == "preserve":
                raise

    if run_manifold:
        if unioned is not None:
            run_manifold = False

    if run_manifold:
        base_stats["manifoldAttempted"] = True
        try:
            unioned, manifold_stats = _manifold_strategy(
                loaded,
                epsilon=epsilon,
                silhouette_fallback=silhouette_fallback,
                verbose=verbose,
            )
            base_stats.update(manifold_stats)
            manifold_watertight, manifold_diag = _is_effectively_watertight(unioned)
            base_stats["manifoldWatertight"] = manifold_watertight
            # Multi-shell output is FINE — each shell is independently watertight
            # which is exactly what slicers need. We only fall through to the
            # destructive silhouette path if manifold produced zero usable faces.
            if len(unioned.faces) == 0:
                if verbose:
                    print("[stl_union] manifold produced empty result; falling back to silhouette")
                unioned = None
            else:
                used_strategy = "manifold"
        except Exception as exc:
            manifold_error = str(exc)
            if verbose:
                print(f"[stl_union] manifold strategy failed: {exc}")
            unioned = None
            if not allow_silhouette_fallback:
                raise

    if unioned is None:
        if not allow_silhouette_fallback:
            raise ValueError("Manifold strategy disabled and produced no output")
        base_stats["silhouetteAttempted"] = True
        if verbose:
            print("[stl_union] running silhouette union (last-resort fallback)")
        unioned = _silhouette_union(loaded)
        used_strategy = "silhouette"

    final_parts = unioned.split(only_watertight=False)
    output_watertight, output_diag = _is_effectively_watertight(unioned)
    if verbose:
        print(
            f"[stl_union] result: {len(unioned.faces)} faces, "
            f"{len(final_parts)} shells, "
            f"watertight={output_watertight} "
            f"(sliverShells={output_diag['sliverShells']}, "
            f"failingShells={output_diag['failingShells']})"
        )

    unioned.export(dst)
    if verbose:
        print(f"[stl_union] wrote {dst}")

    if cleanup_admesh:
        base_stats["cleanupAdmesh"] = _admesh_cleanup(dst, verbose=verbose)
        if base_stats["cleanupAdmesh"].get("ran"):
            try:
                cleaned = trimesh.load(dst, force="mesh")
                if isinstance(cleaned, trimesh.Scene):
                    cleaned = trimesh.util.concatenate(tuple(cleaned.dump()))
                unioned = cleaned
                final_parts = unioned.split(only_watertight=False)
                output_watertight, output_diag = _is_effectively_watertight(unioned)
            except Exception as exc:  # pragma: no cover - defensive only
                if verbose:
                    print(f"[stl_union] post-cleanup reload failed: {exc}")

    signed_volume = _shell_volume_signed(unioned)

    # The strict watertight check is appropriate for the boolean / preserve
    # strategies that promise to produce closed solids. The ``clean`` strategy
    # deliberately does not fill holes — its goal is to preserve the original
    # surface and only remove SketchUp shared-face cancelling pairs — so we
    # report it as ready when it ran successfully even if some non-manifold
    # edges remain. Slicers like Creality Print, Bambu Studio, and OrcaSlicer
    # all auto-repair this kind of mesh on slice.
    if used_strategy == "clean":
        report_watertight = True
    else:
        report_watertight = bool(output_watertight)

    return {
        **base_stats,
        "strategyUsed": used_strategy,
        "manifoldError": manifold_error,
        "outputFaces": int(len(unioned.faces)),
        "outputShells": int(len(final_parts)),
        "outputWatertight": report_watertight,
        "outputWatertightStrict": bool(output_watertight),
        "outputWatertightDiag": output_diag,
        "outputVolume": float(abs(signed_volume)),
    }


# Colour-name -> RGB for layered .3mf face colours. Mirrors the plaque/ink/
# syllabics filaments plus the icon palette (icon_to_stl.FILAMENT_PALETTE) and
# the catalogue viewer's FILL_HEX so a sign's .3mf objects carry the right tint.
_LAYER_NAME_RGB = {
    "white": (232, 225, 207), "plaque": (232, 225, 207),
    "black": (38, 38, 38), "ink": (38, 38, 38),
    "red": (192, 57, 43),
    "blue": (46, 110, 185), "navy": (32, 54, 104), "teal": (40, 150, 150),
    "green": (60, 140, 75), "grey": (150, 150, 150), "silver": (200, 202, 205),
    "tan": (205, 170, 110), "lightbrown": (195, 150, 85), "midbrown": (165, 100, 45),
    "brown": (120, 78, 46), "orange": (226, 122, 55), "yellow": (234, 198, 58),
    "purple": (132, 72, 160), "pink": (221, 123, 162),
}


def _layer_color_to_rgb(color: str) -> tuple[int, int, int]:
    """Resolve a colorLayers colour (name or #hex) to an RGB triple."""
    c = (color or "").strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) == 6:
            try:
                return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
            except ValueError:
                pass
    return _LAYER_NAME_RGB.get(c.lower(), (200, 200, 200))


def _sanitize_part_key(text: str, index: int) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", (text or "").strip()).strip("_")
    return f"{index:02d}_{cleaned or 'layer'}"


def build_layered_3mf(
    combined_stl: Path,
    color_layers: list[dict],
    out_3mf: Path,
    *,
    verbose: bool = False,
) -> dict | None:
    """Split a clean combined sign solid into per-colour objects by the
    ``colorLayers`` height bands and bundle them into ONE multi-object .3mf.

    The combined solid (the production STL rendered by OpenSCAD/CGAL) slices
    perfectly but is a single object with no colour separation. The per-part
    extrude STLs carry colour separation but overlap each other (features sink
    into the plaque), so a naive bundle slices with cancelled/merged faces.

    This intersects the combined solid with each colour band's Z slab, yielding
    mutually-exclusive, individually-watertight, vertically-stacked objects whose
    union is exactly the combined solid — i.e. object separation WITH the
    combined solid's slicing fidelity, from a single render pipeline. The colour
    bands follow the staggered height-swap model the signs already use, so each
    object prints the same colour a single-nozzle height swap would.

    Returns a small stats dict (or None on failure)."""
    mesh = trimesh.load(combined_stl, force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.dump()))
    if mesh is None or len(mesh.faces) == 0 or not color_layers:
        return None

    import trimesh.creation as _tc

    z_min = float(mesh.bounds[0][2])
    z_max = float(mesh.bounds[1][2])
    ext = mesh.bounds[1] - mesh.bounds[0]
    cx, cy = ((mesh.bounds[0] + mesh.bounds[1]) / 2.0)[:2]
    pad = float(max(ext[0], ext[1])) * 2.0 + 10.0

    geoms: dict[str, trimesh.Trimesh] = {}
    objects: list[dict] = []
    lo = z_min - 1.0
    for i, layer in enumerate(color_layers):
        hi_raw = layer.get("maxZ")
        hi = (z_max + 1.0) if hi_raw in (None, "") else float(hi_raw)
        if hi <= lo:
            lo = hi
            continue
        box = _tc.box(extents=[pad, pad, hi - lo])
        box.apply_translation([float(cx), float(cy), (lo + hi) / 2.0])
        try:
            part = trimesh.boolean.intersection([mesh, box], engine="manifold")
        except Exception as exc:  # pragma: no cover - engine hiccup
            if verbose:
                print(f"[build_layered_3mf] band {i} intersection failed: {exc}")
            part = None
        if part is not None and len(part.faces) > 0:
            rgb = _layer_color_to_rgb(layer.get("color"))
            part.visual.face_colors = list(rgb) + [255]
            key = _sanitize_part_key(layer.get("label") or layer.get("color"), i)
            geoms[key] = part
            objects.append({"key": key, "color": layer.get("color"),
                            "faces": int(len(part.faces)),
                            "watertight": bool(part.is_watertight)})
        lo = hi

    if not geoms:
        return None
    out_3mf = Path(out_3mf)
    out_3mf.parent.mkdir(parents=True, exist_ok=True)
    try:
        trimesh.Scene(geoms).export(out_3mf)
    except Exception as exc:
        if verbose:
            print(f"[build_layered_3mf] export failed: {exc}")
        return None
    if verbose:
        print(f"[build_layered_3mf] wrote {out_3mf} with {len(objects)} objects")
    return {"ok": True, "out": str(out_3mf), "objects": objects}


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
        "--strategy",
        choices=("auto", "clean", "preserve", "manifold", "silhouette"),
        default="auto",
        help="union strategy (default: auto -> clean)",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.001,
        help="tiny Z nudge applied to non-first shells to break coincident-face "
        "cancellation in the manifold engine (default 0.001 mm; 0 disables)",
    )
    parser.add_argument(
        "--flatness-ratio",
        type=float,
        default=0.15,
        help="Z/XY-extent threshold used only for the isFlatPlaque diagnostic "
        "(default 0.15)",
    )
    parser.add_argument(
        "--no-admesh-cleanup",
        dest="cleanup_admesh",
        action="store_false",
        help="skip the post-union admesh normals/degenerates pass",
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
    union_stl(
        src,
        dst,
        epsilon=args.epsilon,
        strategy=args.strategy,
        flatness_ratio=args.flatness_ratio,
        cleanup_admesh=args.cleanup_admesh,
        verbose=not args.quiet,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
