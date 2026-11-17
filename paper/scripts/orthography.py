"""Orthographic consistency audit: does each syllabic spelling read back as the
Standard Roman Orthography (SRO) spelling it is paired with?

The syllabics are read back to SRO using the Unicode character names of the
Canadian Aboriginal Syllabics block, so the check needs no hand-made table and
is easy to audit. Each SRO/syllabics pair is then classed as

  exact        the two spellings agree letter for letter
  length       they agree once vowel length (the circumflex) is ignored
  mismatch     they disagree on consonants or vowels

and separately flagged when the syllabics use glyphs that are not part of the
western (Plains Cree) syllabary, for example eastern finals or the "sh" series.

This is a consistency check between two spellings of the same word. It says
nothing about whether the word itself is good Cree; that judgement belongs to
fluent speakers and Elders.
"""
from __future__ import annotations

import unicodedata as ud

from common import (FIG, GEN, INK, INK2, MUTED, SEQ_BLUE, ORANGE, is_built,
                    models, setup_matplotlib, tex_escape, workbench, write_macros)

# glyphs that belong to eastern conventions or to other syllabaries
NON_PLAINS_NAMES = {
    "WE", "WI", "WII", "WO", "WOO", "WA", "WAA",           # dot-left (eastern) w-forms
    "PWE", "PWI", "PWII", "PWO", "PWOO", "PWA", "PWAA",
    "TWE", "TWI", "TWII", "TWO", "TWOO", "TWA", "TWAA",
    "KWE", "KWI", "KWII", "KWO", "KWOO", "KWA", "KWAA",
    "CWE", "CWI", "CWII", "CWO", "CWOO", "CWA", "CWAA",
    "MWE", "MWI", "MWII", "MWO", "MWOO", "MWA", "MWAA",
    "SWE", "SWI", "SWII", "SWO", "SWOO", "SWA", "SWAA",
    "YWE", "YWI", "YWII", "YWO", "YWOO", "YWA", "YWAA",
    "T", "K", "N", "S", "Y", "M", "P", "C",                  # eastern-style finals
    "ON", "FE", "LE",
}

FINALS = {
    "FINAL ACUTE": "t", "FINAL GRAVE": "k", "FINAL TOP HALF RING": "s",
    "FINAL RIGHT HALF RING": "n", "FINAL RING": "w", "FINAL SHORT HORIZONTAL STROKE": "c",
    "FINAL PLUS": "y", "FINAL DOUBLE SHORT VERTICAL STROKES": "h", "HK": "hk",
    "WEST-CREE P": "p", "WEST-CREE M": "m", "WEST-CREE Y": "y", "L": "l", "MEDIAL R": "r",
    "T": "t", "K": "k", "N": "n", "S": "s", "Y": "y", "M": "m", "P": "p", "C": "c", "SH": "sh",
}
VOWELS = {"AA": "â", "II": "î", "OO": "ô", "E": "ê", "A": "a", "I": "i", "O": "o"}


def syl_to_sro(s: str) -> tuple[str, bool]:
    """Read syllabics back to SRO. Returns (sro, uses_non_plains_glyph)."""
    out: list[str] = []
    non_plains = False
    for ch in s:
        if not ("᐀" <= ch <= "ᙿ"):
            if ch.isalpha():
                out.append(ch.lower())
            continue
        name = ud.name(ch, "")
        if not name.startswith("CANADIAN SYLLABICS "):
            continue
        name = name[len("CANADIAN SYLLABICS "):]
        if name == "FINAL MIDDLE DOT":           # w-dot written as a separate mark
            if out and out[-1].strip() and out[-1][-1] in "aâiîoôê":
                syl = out.pop()
                cons = syl.rstrip("aâiîoôê")
                out.append(cons + "w" + syl[len(cons):])
            continue
        west = name.startswith("WEST-CREE ")
        bare = name[len("WEST-CREE "):] if west else name
        if not west and bare in NON_PLAINS_NAMES:
            non_plains = True
        if name in FINALS or bare in FINALS:
            out.append(FINALS.get(name, FINALS.get(bare)))
            continue
        # syllable: consonant cluster + vowel
        for v in ("AA", "II", "OO", "E", "A", "I", "O"):
            if bare.endswith(v):
                cons = bare[: -len(v)].lower()
                if cons.startswith("sh"):
                    non_plains = True
                out.append(cons + VOWELS[v])
                break
        else:
            non_plains = True
    return "".join(out).strip(), non_plains


MACRON = str.maketrans({"ā": "â", "ē": "ê", "ī": "î", "ō": "ô", "á": "â", "é": "ê",
                        "í": "î", "ó": "ô", "Ā": "â", "Ē": "ê", "Ī": "î", "Ō": "ô"})


def norm_sro(s: str) -> str:
    s = ud.normalize("NFC", s).translate(MACRON).lower()
    s = "".join(c for c in s if c.isalpha())
    return s.replace("e", "ê").replace("êê", "ê")


def strip_length(s: str) -> str:
    return s.translate(str.maketrans("âîôê", "aioe"))


def classify(sro: str, syl: str) -> tuple[str, bool]:
    a = norm_sro(sro)
    b_raw, non_plains = syl_to_sro(syl)
    b = norm_sro(b_raw)
    if a == b:
        return "exact", non_plains
    if strip_length(a) == strip_length(b):
        return "length", non_plains
    return "mismatch", non_plains


def audit():
    rows = []
    for m in models():
        if m.get("creeName") and m.get("creeSyllabics"):
            c, np_ = classify(m["creeName"], m["creeSyllabics"])
            rows.append(("built" if is_built(m) else "draft", m["englishName"],
                         m["creeName"], m["creeSyllabics"], c, np_))
    for d in workbench():
        for cand in d.get("cree", []):
            if cand.get("t") and cand.get("s"):
                c, np_ = classify(cand["t"], cand["s"])
                rows.append(("workbench", d["en"], cand["t"], cand["s"], c, np_))
    return rows


def main():
    plt = setup_matplotlib()
    rows = audit()
    groups = [("built", "Finished signs"), ("draft", "Draft sign pages"),
              ("workbench", "Workbench candidates")]
    cats = [("exact", "Spellings agree"), ("length", "Differ only in vowel length"),
            ("mismatch", "Differ in letters")]
    colors = {"exact": SEQ_BLUE[3], "length": SEQ_BLUE[1], "mismatch": ORANGE}

    stats = {}
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.0, 1.9),
                                  gridspec_kw={"width_ratios": [3.2, 1.3], "wspace": 0.55})
    for gi, (g, label) in enumerate(groups):
        sub = [r for r in rows if r[0] == g]
        n = len(sub)
        left = 0.0
        for c, clabel in cats:
            k = sum(1 for r in sub if r[4] == c)
            frac = k / n if n else 0
            ax.barh(gi, frac, left=left, color=colors[c], height=0.62,
                    edgecolor="white", linewidth=1.2)
            if frac > 0.07:
                ax.text(left + frac / 2, gi, f"{k}", ha="center", va="center",
                        color="white" if c != "length" else INK, fontsize=7)
            left += frac
            stats[f"orth{g.capitalize()}{c.capitalize()}"] = k
        stats[f"orth{g.capitalize()}N"] = n
        np_k = sum(1 for r in sub if r[5])
        stats[f"orth{g.capitalize()}NonPlains"] = np_k
        ax2.barh(gi, np_k / n if n else 0, color=MUTED, height=0.62)
        ax2.text((np_k / n if n else 0) + 0.01, gi, f"{np_k}/{n}", va="center",
                 fontsize=7, color=INK2)
    ax.set_yticks(range(len(groups)), [f"{l}\n(n = {stats['orth' + g.capitalize() + 'N']})"
                                       for g, l in groups])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title("A. SRO and syllabic spellings read against each other")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[c]) for c, _ in cats]
    ax.legend(handles, [l for _, l in cats], ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.22), fontsize=7, handlelength=1.0)
    ax2.set_yticks(range(len(groups)), ["", "", ""])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.set_title("B. Uses non-Plains glyphs")
    fig.savefig(FIG / "orthography.pdf")
    plt.close(fig)

    wb = workbench()
    stats["wbTrails"] = len(wb)
    stats["wbAreas"] = len({d.get("loc") for d in wb if d.get("loc")})
    write_macros("orthography", stats)

    # a small table of illustrative disagreements from the finished/draft signs
    ex = [r for r in rows if r[0] in ("built", "draft") and r[4] != "exact"]
    lines = ["% generated by paper/scripts/orthography.py",
             r"\begin{tabular}{@{}llll@{}}", r"\toprule",
             r"\textbf{Sign} & \textbf{SRO on record} & \textbf{Syllabics on record} & \textbf{Syllabics read back} \\",
             r"\midrule"]
    for r in ex:
        back, _ = syl_to_sro(r[3])
        lines.append(f"{tex_escape(r[1])} & \\textit{{{tex_escape(r[2])}}} & {r[3]} & \\textit{{{tex_escape(back)}}} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (GEN / "orthography_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # full audit as CSV for the supplementary material
    import csv
    with open(GEN / "orthography_audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "english", "sro", "syllabics", "syllabics_read_back",
                    "class", "non_plains_glyph"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], syl_to_sro(r[3])[0], r[4], int(r[5])])
    print("orthography:", {k: v for k, v in stats.items()})


if __name__ == "__main__":
    main()
