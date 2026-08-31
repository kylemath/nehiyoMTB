# S3 Report — Pipeline & Schema (difficulty support)

**Agent:** Sub-subagent S3 (Pipeline & Schema), Manager M1 (Data & Backend), Coordinator 2219-C
**Date:** 2026-06-10
**Files touched:** `tools/export_trails_for_app.py`, `supabase/migrations/0002_home_and_difficulty.sql` (new), `mobile/src/lib/trails.ts`

---

## Task 1 — Export script (`tools/export_trails_for_app.py`)

Two minimal changes inside `main()`. No other functions, constants, or behavior altered.

### Change 1: trail dict gains `"difficulty"` (trails.json)

One line added to the trail dict built in the catalogue loop, right after `"trailforksUrl"`:

```python
"hasIcon": bool(icon_src),
"trailforksUrl": tf.get("trailUrl"),
"difficulty": tf.get("difficulty"),          # <-- added
"start": {"lat": start.get("lat"), "lng": start.get("lng")} if start else None,
```

`tf` is already computed as `page.get("trailforks", {}) or {}` at the top of the loop, so a missing `trailforks` block yields `{}` and `tf.get("difficulty")` returns `None` → serialized as JSON `null`. No new null-handling needed.

### Change 2: seed.sql insert gains a `difficulty` column

The `insert into public.trails` statement now lists `difficulty` as the last column (after `status`) and appends `{sql_str(t['difficulty'])}` as the last value:

```python
"insert into public.trails (id, sign_number, title, english_name, cree_name,"
" cree_syllabics, start_lat, start_lng, end_lat, end_lng, length_m, track, status,"
" difficulty)"
f" values ({sql_str(t['id'])}, {t['signNumber'] or 'null'}, {sql_str(t['title'])},"
...
f" {t['lengthM'] or 'null'}, {sql_str(track_json)}::jsonb, {sql_str(t['status'])},"
f" {sql_str(t['difficulty'])});"
```

`sql_str` is the script's existing helper for text columns: it emits `null` for `None`/empty string and single-quote-escapes otherwise — exactly the formatting used for `title`, `english_name`, etc.

### Compile check

```
$ .venv/bin/python -m py_compile tools/export_trails_for_app.py
COMPILE_OK   (exit code 0)
```

Script was NOT executed (per spec — manager runs it after merging difficulty into the catalogue). `mobile/src/data/trails.json` and `supabase/seed.sql` were not touched.

---

## Task 2 — Migration (new file)

Full contents of `supabase/migrations/0002_home_and_difficulty.sql`:

```sql
-- EdmontonTrailMaps — home location + trail difficulty

-- ---------------------------------------------------------------------------
-- Profiles: optional home/staging location
-- ---------------------------------------------------------------------------

-- Where the rider usually starts from (e.g. their house or a trailhead
-- parking lot); used as the default origin for route planning.
alter table public.profiles add column home_lat double precision;
alter table public.profiles add column home_lng double precision;

-- ---------------------------------------------------------------------------
-- Trails: Trailforks difficulty rating
-- ---------------------------------------------------------------------------

-- Difficulty token sourced from Trailforks:
--   'green' | 'blue' | 'black' | 'dblblack', null when unrated.
alter table public.trails add column difficulty text;
```

Style notes: header line, `-- ---` section dividers, and intent comments mirror `0001_init.sql`. Plain `add column` (no `if not exists`) was chosen because 0001 uses unguarded DDL throughout (`create table`, `create policy`, etc.); migrations in this repo run once, in order.

---

## Task 3 — Trail type (`mobile/src/lib/trails.ts`)

Only the `Trail` type definition changed; no functions, imports, or other types touched.

**Before:**

```ts
  trailforksUrl: string | null;
  start: { lat: number | null; lng: number | null } | null;
```

**After:**

```ts
  trailforksUrl: string | null;
  /** Trailforks rating: 'green' | 'blue' | 'black' | 'dblblack', or null. */
  difficulty: string | null;
  start: { lat: number | null; lng: number | null } | null;
```

No linter errors in any of the three edited files.

---

## Acceptance checklist

- [x] `tools/export_trails_for_app.py` compiles (py_compile exit 0)
- [x] Export writes `difficulty` into each trails.json entry (null-safe)
- [x] seed.sql inserts include a `difficulty` column using existing `sql_str` escaping
- [x] `supabase/migrations/0002_home_and_difficulty.sql` exists with `profiles.home_lat`, `profiles.home_lng`, `trails.difficulty`
- [x] `Trail` type includes `difficulty: string | null;`; nothing else in the file changed
- [x] No forbidden files touched (catalogue.json, trails.json, seed.sql, UI files all untouched)

---

## Tripartite self-assessment

**Craftsperson says:** The changes are minimal and idiomatic. The dict line reuses the already-null-safe `tf` accessor; the SQL change reuses `sql_str`, so escaping and null handling are byte-for-byte consistent with every other text column the script emits. The migration reads like a natural continuation of 0001. The TS type orders `difficulty` to match the export dict's key order.

**Skeptic says:** Three residual risks, all outside my file ownership: (1) until the manager re-runs the export, `trails.json` lacks the `difficulty` key — the `rawData as { trails: Trail[] }` cast means TypeScript won't flag it, so consumers would see `undefined` (not `null`) at runtime in the interim. (2) The seed insert column order changed; anything diffing old seed.sql will see every line change — expected, but worth the manager knowing. (3) I typed `difficulty` as plain `text`/`string | null` rather than an enum/union per spec; if the team later wants DB-level validation, a check constraint would be a follow-up migration. Also note `sql_str` maps empty string to `null` — correct for this token, but a silent coercion.

**Mover says:** All three risks are documented, none block acceptance, and all are either by-design (manager regenerates the data) or future work (enum constraint). The compile check and lints are green. Shipping.
