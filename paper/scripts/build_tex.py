"""Assemble the LaTeX sources in build/tex/ ready for pdflatex.

MDPI recompiles submissions with pdfLaTeX, which has no font for Cree
syllabics. So rather than switching engines, this step finds every run of
syllabics in the sources (the hand-written paper and the generated tables),
renders each run once to a small vector PDF with Noto Sans Canadian
Aboriginal, and replaces it with \\syl{<hash>}. The prose can therefore be
written with real syllabics, and the PDF carries them as outlines.
"""
from __future__ import annotations

import hashlib
import re
import shutil

from common import BUILD, FIG, GEN, PAPER, SYL_FONT, setup_matplotlib

TEX_SRC = PAPER / "tex"
OUT = BUILD / "tex"
SYL_DIR = OUT / "syl"
# a run of syllabics, allowing single spaces/hyphens between words
SYL_RUN = re.compile(r"[᐀-ᙿ]+(?:[ \-‑][᐀-ᙿ]+)*")

# text height: 1em = 10pt in the class; we render at 10pt and place the
# baseline at 0.22 of the box height so it sits on the surrounding text line
FONT_PT = 10.0
BOX_H_PT = 13.0
BASELINE_PT = 2.9


def render(text: str, path):
    plt = setup_matplotlib()
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    fp = FontProperties(family=SYL_FONT, size=FONT_PT)
    tp = TextPath((0, 0), text, prop=fp)
    bb = tp.get_extents()
    width_pt = max(bb.x1, 1.0) + 0.6
    fig = plt.figure(figsize=(width_pt / 72, BOX_H_PT / 72))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width_pt)
    ax.set_ylim(-BASELINE_PT, BOX_H_PT - BASELINE_PT)
    ax.axis("off")
    from matplotlib.patches import PathPatch
    ax.add_patch(PathPatch(tp, fc="black", ec="none"))
    fig.savefig(path, bbox_inches=None, pad_inches=0, transparent=True)
    plt.close(fig)


def process(src: str, seen: dict) -> str:
    def sub(m):
        text = m.group(0)
        h = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        seen[h] = text
        return r"\syl{" + h + "}"
    return SYL_RUN.sub(sub, src)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(TEX_SRC, OUT)
    (OUT / "generated").mkdir(exist_ok=True)
    SYL_DIR.mkdir(exist_ok=True)
    seen: dict[str, str] = {}
    for f in list(OUT.glob("*.tex")):
        f.write_text(process(f.read_text(encoding="utf-8"), seen), encoding="utf-8")
    for f in GEN.glob("*.tex"):
        (OUT / "generated" / f.name).write_text(process(f.read_text(encoding="utf-8"), seen),
                                                encoding="utf-8")
    for h, text in seen.items():
        p = SYL_DIR / f"{h}.pdf"
        if not p.exists():
            render(text, p)
    # figures next to the tex so \includegraphics paths stay short
    shutil.copytree(FIG, OUT / "figures", dirs_exist_ok=True)
    (OUT / "syl" / "index.tsv").write_text(
        "".join(f"{h}\t{t}\n" for h, t in sorted(seen.items())), encoding="utf-8")
    print(f"build_tex: {len(seen)} syllabic runs rendered")


if __name__ == "__main__":
    main()
