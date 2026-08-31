#!/usr/bin/env python3
"""Manager M1 merge step: write researched difficulties into docs/catalogue.json
at models[i].pageContent.trailforks.difficulty. Single writer: M1 only."""

import json
import os

ROOT = "/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB"
M1 = os.path.join(ROOT, "backgroundMaterial/agent2219/coordinator/manager_M1")
CATALOGUE = os.path.join(ROOT, "docs/catalogue.json")
VALID = {"green", "blue", "black", "dblblack", None}

merged = {}
for sub in ("sub_S1", "sub_S2"):
    with open(os.path.join(M1, sub, "difficulties.json")) as f:
        data = json.load(f)
    for tid, entry in data.items():
        if tid in merged:
            raise SystemExit(f"duplicate trail id across batches: {tid}")
        if entry["difficulty"] not in VALID:
            raise SystemExit(f"invalid difficulty token for {tid}: {entry['difficulty']!r}")
        merged[tid] = entry

with open(CATALOGUE) as f:
    catalogue = json.load(f)

models = catalogue.get("models", [])
set_count = skipped_no_tf = nulls = 0
unmatched_models = []
for model in models:
    tid = model.get("id")
    if tid not in merged:
        unmatched_models.append(tid)
        continue
    tf = (model.get("pageContent") or {}).get("trailforks")
    if not isinstance(tf, dict):
        skipped_no_tf += 1
        print(f"SKIP (no trailforks block): {tid} (difficulty would be {merged[tid]['difficulty']!r})")
        continue
    tf["difficulty"] = merged[tid]["difficulty"]
    if merged[tid]["difficulty"] is None:
        nulls += 1
    else:
        set_count += 1

unused = sorted(set(merged) - {m.get("id") for m in models})

with open(CATALOGUE, "w") as f:
    json.dump(catalogue, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"models in catalogue: {len(models)}")
print(f"difficulty set non-null: {set_count}")
print(f"difficulty set null: {nulls}")
print(f"skipped (no trailforks block): {skipped_no_tf}")
print(f"catalogue models with no research entry: {unmatched_models}")
print(f"research ids not in catalogue: {unused}")
