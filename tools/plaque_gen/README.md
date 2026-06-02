# plaque_gen

Auto-generate a trail-sign `.scad` (and a draft `.stl`) by combining the blank
plaque with extruded English + Cree transliteration + syllabics text, plus an
optional icon STL fused on top with the syllabics protruding in front.

Pure Python standard library — no `pip install` needed. If
[OpenSCAD](https://openscad.org/) is on your `PATH`, a draft STL is rendered too;
otherwise just open the generated `.scad` in OpenSCAD and export.

## Quick start

```bash
python3 tools/plaque_gen/plaque_gen.py \
  --en "I See You" \
  --translit "kiwâpamitin" \
  --syllabics "ᑭᐚᐸᒥᑎᐣ"
# → signs/i_see_you/i_see_you.scad  (+ .stl if openscad is installed)
```

With an icon fused on the plaque (e.g. from the Icon Extruder):

```bash
python3 tools/plaque_gen/plaque_gen.py \
  --en "Raven" --translit "kâhkâkiw" --syllabics "ᑳᐦᑳᑭᐤ" \
  --icon docs/tools/icon-extruder/raven.stl --icon-width 55
```

## How it works

- The blank `blanks/blank_plaque_thinner.stl` is authored in arbitrary SketchUp
  units, so the script reads its bounding box and **rescales it to real mm**
  (default `90 × 165 × 1.75`), recentred with its base on `z = 0`. Importing the
  mesh preserves its drilled mounting holes.
- **Text is auto-fit**: the largest font size that fits the available width is
  chosen, wrapping into multiple centred lines if necessary. English sits at the
  bottom, transliteration at the top, syllabics in the upper-middle band.
- The **syllabics** use `Euphemia UCAS` (a Cree-capable font, built into macOS)
  and are extruded tall enough to **protrude in front of the icon**. Latin text
  uses `Raleway:style=Bold`.
- An optional `--icon` STL is scaled to `--icon-width`, centred in the plaque's
  middle dead-space, and seated on the plaque top.

## Options

| flag | default | meaning |
|------|---------|---------|
| `--en` | (required) | English trail name |
| `--translit` | "" | Cree transliteration (SRO) |
| `--syllabics` | "" | Cree syllabics |
| `--icon` | "" | icon STL to fuse on top |
| `--icon-width` | fit | icon target width (mm) |
| `--width / --height / --thickness` | 90 / 165 / 1.75 | plaque size (mm) |
| `--text-depth` | 1.5 | raised height of Latin text (mm) |
| `--syllabics-depth` | 2.5 | minimum raised height of syllabics (mm) |
| `--syllabics-front` | 1.5 | extra mm syllabics protrude beyond the icon top |
| `--blank` | `blanks/blank_plaque_thinner.stl` | base plaque STL |
| `--out` | `signs/<name>` | output directory |
| `--name` | slug of `--en` | base filename |
| `--openscad` | auto | path to the OpenSCAD binary |
| `--no-render` | off | write the `.scad` only, skip STL render |

## Notes

- If syllabics render as empty boxes, the font name/style isn't installed; edit
  the `font="…"` in the generated `.scad` (e.g. `Noto Sans Canadian Aboriginal`).
- The generated `.scad` is fully editable — tweak band positions, depths, or the
  icon transform and re-export from OpenSCAD.
