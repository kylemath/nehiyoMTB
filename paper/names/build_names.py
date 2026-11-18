"""Build the Names submission from the repository, end to end.

  python3 paper/names/build_names.py

reads   docs/catalogue.json, the Translation Workbench in
        docs/cree-trail-names.html, allSigns.jpg, the provisional coding in
        paper/names/data/name_coding.csv and the template paper/names/manuscript.md
writes  paper/build/names/
          manuscript_anonymized.docx / .pdf   for blind review
          manuscript_final.docx / .pdf        with author details, for after acceptance
          figures/Figure1_map.jpg             1200 dpi line art, grayscale
          figures/Figure2_signs.jpg           600 dpi grayscale photograph
          tables/*.md, stats.json, wordcount.txt

The template uses three kinds of placeholder:
  {{key}}                 a number or table computed here (see stats)
  {{alt|anon text|final}} text that differs between the anonymized and final versions
  Cree syllabics          wrapped automatically in the "Syllabics" character style

The PDFs are previews made with LibreOffice from the .docx files, which are what
Names asks for.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from common import BUILD, INK, MUTED, REPO, is_built, models, setup_matplotlib, workbench  # noqa: E402
import fig_map  # noqa: E402
import orthography  # noqa: E402
from make_tables import gloss  # noqa: E402

OUT = BUILD / "names"
FIGS = OUT / "figures"
TABS = OUT / "tables"
SYL = re.compile(r"[᐀-ᙿ](?:[᐀-ᙿ\s]*[᐀-ᙿ])?")

STRATEGIES = ["translation proper", "modification", "substitution", "transference", "mixed"]
DOMAINS = ["Fauna", "Object", "Popular culture and brands", "Romance and innuendo",
           "Ride evaluation", "People and roles", "Phrase or pun"]


def pct(k, n):
    return f"{100 * k / n:.2f}%" if n else "0.00%"


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("*", "\\*")


def pipe_table(header, rows, widths):
    """A pandoc pipe table; the dashes set relative column widths."""
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("-" * w for w in widths) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


# ----------------------------------------------------------------- data

def first_in_repo(m: dict) -> str:
    """Date of the first commit that contains the sign's folder. This is when the
    sign's files reached the repository, which can be later than when the sign
    was made (the first commit, in October 2021, uploaded signs made before it)."""
    folder = m.get("folder")
    if not folder:
        return ""
    r = subprocess.run(["git", "-C", str(REPO), "log", "--all", "--format=%ad", "--date=short", "--", f"{folder}"],
                       capture_output=True, text=True)
    dates = r.stdout.split()
    return dates[-1] if dates else ""


def coded_names():
    coding = {int(r["sign_no"]): r for r in csv.DictReader(open(HERE / "data" / "name_coding.csv", encoding="utf-8"))}
    rows = []
    for m in sorted([m for m in models() if is_built(m)], key=lambda m: m["signNumber"]):
        c = coding.get(m["signNumber"])
        if c is None:
            raise SystemExit(f"sign {m['signNumber']} {m['englishName']} has no row in name_coding.csv")
        g = gloss(m) or c["gloss_if_missing"].strip("'")
        rows.append({"n": m["signNumber"], "en": m["englishName"], "sro": m["creeName"],
                     "syl": m.get("creeSyllabics") or "", "gloss": g,
                     "domain": c["source_domain"], "strategy": c["strategy"],
                     "first": first_in_repo(m)})
    # order the signs by when they reached the repository, then by sign number
    rows.sort(key=lambda r: (r["first"] or "9999", r["n"]))
    extra = set(coding) - {r["n"] for r in rows}
    if extra:
        raise SystemExit(f"name_coding.csv has rows for signs that are not finished: {sorted(extra)}")
    return rows


def workbench_stats():
    wb = workbench()
    cands = [c for d in wb for c in d["cree"]]
    phon = re.compile(r"phonetic|transliterat|loanword|borrow", re.I)
    none = re.compile(r"\s*(none|n/a)\b", re.I)
    t_phon = sum(1 for d in wb if any(phon.search(c.get("g", "") + " " + c.get("why", "")) for c in d["cree"]))
    c_phon = sum(1 for c in cands if phon.search(c.get("g", "") + " " + c.get("why", "")))
    c_conn = sum(1 for c in cands if c.get("inn") and not none.match(c["inn"]))
    t_conn = sum(1 for d in wb if any(c.get("inn") and not none.match(c["inn"]) for c in d["cree"]))
    return {
        "wbTrails": len(wb), "wbCands": len(cands),
        "wbAreas": len({d.get("loc") for d in wb if d.get("loc")}),
        "wbTrailsPhon": t_phon, "wbTrailsPhonPct": pct(t_phon, len(wb)),
        "wbCandsPhon": c_phon, "wbCandsPhonPct": pct(c_phon, len(cands)),
        "wbCandsConn": c_conn, "wbCandsConnPct": pct(c_conn, len(cands)),
        "wbTrailsConn": t_conn, "wbTrailsConnPct": pct(t_conn, len(wb)),
    }


# --------------------------------------------------------------- tables

def table_names(rows):
    body = []
    for r in rows:
        body.append([r["first"][:7] or "?", md_escape(r["en"]), f"*{md_escape(r['sro'])}*",
                     r["syl"] or "(none on record)",
                     f"'{md_escape(r['gloss'])}'" if r["gloss"] else "", r["strategy"]])
    return pipe_table(["First commit", "English name", "Cree name (SRO)", "Cree name (syllabics)",
                       "Literal sense", "Strategy"], body, [12, 15, 18, 18, 22, 17])


def table_batches(rows):
    """Translation strategy by the batch in which the signs reached the repository."""
    batches = sorted({r["first"][:7] for r in rows})
    used = [s for s in STRATEGIES if any(r["strategy"] == s for r in rows)]
    body = []
    for b in batches:
        sub = [r for r in rows if r["first"][:7] == b]
        body.append([b or "?", str(len(sub))] + [str(sum(1 for r in sub if r["strategy"] == s)) for s in used])
    return pipe_table(["First commit", "Signs"] + [s.capitalize() for s in used],
                      body, [14, 8] + [16] * len(used))


def table_crosstab(rows):
    n = len(rows)
    cnt = Counter((r["domain"], r["strategy"]) for r in rows)
    used = [s for s in STRATEGIES if any(r["strategy"] == s for r in rows)]
    head = ["Source of the English name"] + [s.capitalize() for s in used] + ["Total", "Share"]
    body = []
    for d in DOMAINS:
        k = sum(cnt[(d, s)] for s in used)
        if not k:
            continue
        body.append([d] + [str(cnt[(d, s)]) if cnt[(d, s)] else "0" for s in used] + [str(k), pct(k, n)])
    tot = [sum(cnt[(d, s)] for d in DOMAINS) for s in used]
    body.append(["Total"] + [str(t) for t in tot] + [str(n), "100.00%"])
    body.append(["Share"] + [pct(t, n) for t in tot] + ["", ""])
    return pipe_table(head, body, [26] + [12] * len(used) + [8, 10])


def table_audit(audit_rows):
    groups = [("built", "Finished signs"), ("draft", "Draft sign pages"),
              ("workbench", "Workbench candidates (unreviewed)")]
    body = []
    for g, label in groups:
        sub = [r for r in audit_rows if r[0] == g]
        n = len(sub)
        k = Counter(r[4] for r in sub)
        npl = sum(1 for r in sub if r[5])
        body.append([label, str(n), f"{k['exact']} ({pct(k['exact'], n)})",
                     f"{k['length']} ({pct(k['length'], n)})",
                     f"{k['mismatch']} ({pct(k['mismatch'], n)})", f"{npl} ({pct(npl, n)})"])
    return pipe_table(["Set of names", "Pairs", "Spellings agree", "Differ only in vowel length",
                       "Differ in letters", "Use non-Plains characters"], body, [26, 8, 16, 16, 16, 16])


# -------------------------------------------------------------- figures

def figure_map(stats):
    plt = setup_matplotlib()
    T = fig_map.trails()
    lat0 = sum(p[0] for t in T for p in t["pts"]) / sum(len(t["pts"]) for t in T)
    P = fig_map.project(lat0)
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    for t in sorted(T, key=lambda t: t["built"]):
        xs, ys = zip(*[P(p) for p in t["pts"]])
        if t["built"]:
            ax.plot(xs, ys, color="black", lw=1.8, solid_capstyle="round", zorder=3)
        else:
            ax.plot(xs, ys, color="#7a7a7a", lw=0.9, ls=(0, (3, 1.6)), zorder=2)
        ax.plot(xs[0], ys[0], "o", ms=2.6, color="white", mec="black" if t["built"] else "#7a7a7a",
                mew=0.8, zorder=4)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    sx, sy = x0 + 0.03 * (x1 - x0), y0 + 0.04 * (y1 - y0)
    ax.plot([sx, sx + 2.0], [sy, sy], color="black", lw=2, solid_capstyle="butt")
    ax.text(sx + 1.0, sy + 0.25, "2 km", ha="center", fontsize=8, color="black")
    ax.annotate("N", xy=(x0 + 0.04 * (x1 - x0), y1 - 0.06 * (y1 - y0)),
                xytext=(x0 + 0.04 * (x1 - x0), y1 - 0.2 * (y1 - y0)), ha="center", fontsize=9,
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1))
    nb = sum(t["built"] for t in T)
    ax.plot([], [], color="black", lw=1.8, label=f"Trail with a finished sign ({nb})")
    ax.plot([], [], color="#7a7a7a", lw=0.9, ls=(0, (3, 1.6)), label=f"Trail with a draft name only ({len(T) - nb})")
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig1_map.png", dpi=300)
    fig.savefig(FIGS / "Figure1_map.jpg", dpi=1200, pil_kwargs={"quality": 92})
    plt.close(fig)
    xs = [P(p)[0] for t in T for p in t["pts"]]
    ys = [P(p)[1] for t in T for p in t["pts"]]
    stats.update({"mapTrails": len(T), "mapBuilt": nb, "mapDraft": len(T) - nb,
                  "mapExtentEW": f"{max(xs) - min(xs):.0f}", "mapExtentNS": f"{max(ys) - min(ys):.0f}"})


def figure_signs():
    from PIL import Image, ImageOps
    im = Image.open(REPO / "allSigns.jpg")
    im = ImageOps.exif_transpose(im).convert("L")
    im = ImageOps.autocontrast(im, cutoff=0.5)
    w = 6.5 * 600   # 6.5 in at 600 dpi
    big = im.resize((int(w), int(w * im.height / im.width)), Image.LANCZOS)
    big.save(FIGS / "Figure2_signs.jpg", dpi=(600, 600), quality=90)
    small = im.resize((1800, int(1800 * im.height / im.width)), Image.LANCZOS)
    small.save(OUT / "fig2_signs.jpg", dpi=(300, 300), quality=88)


# ------------------------------------------------------------- template

def fill(template: str, stats: dict, version: str) -> str:
    def alt(m):
        a, f = m.group(1), m.group(2)
        return a if version == "anonymized" else f
    template = re.sub(r"<!--.*?-->\n?", "", template, flags=re.S)   # author notes in the template
    s = re.sub(r"<<<anon>>>\n?(.*?)<<<final>>>\n?(.*?)<<<end>>>\n?", alt, template, flags=re.S)
    s = re.sub(r"\{\{alt\|([^{}|]*)\|([^{}]*)\}\}", alt, s)

    def key(m):
        k = m.group(1)
        if k not in stats:
            raise SystemExit(f"manuscript.md uses {{{{{k}}}}}, which build_names.py does not define")
        return str(stats[k])
    s = re.sub(r"\{\{(\w+)\}\}", key, s)
    if "{{" in s:
        raise SystemExit("unresolved placeholder: " + s[s.index("{{"):s.index("{{") + 60])
    # syllabics in their own character style (not inside image lines or HTML comments)
    lines = []
    for line in s.split("\n"):
        if line.startswith("![") or line.startswith("<!--"):
            lines.append(line)
            continue
        lines.append(SYL.sub(lambda m: f"[{m.group(0)}]{{custom-style=\"Syllabics\"}}", line))
    s = "\n".join(lines)
    return s


def word_count(md: str) -> dict:
    """Main-text words: from the first heading to the Notes heading, without
    tables, graphics, their titles and sources, or citation keys' brackets."""
    body = md.split("\n# Introduction", 1)[1].split("\n# Notes", 1)[0]
    keep = []
    in_div = False
    for line in body.split("\n"):
        if line.startswith("::: {"):
            in_div = True
            continue
        if line.strip() == ":::":
            in_div = False
            continue
        if in_div or line.startswith("|") or line.startswith("![") or line.startswith("Table:"):
            continue
        keep.append(line)
    text = "\n".join(keep)
    text = re.sub(r"\{custom-style=\"[^\"]+\"\}", "", text)
    text = re.sub(r"[#*\[\]^]", " ", text)
    main_words = len(re.findall(r"\S+", text))
    head = md.split("\n# Introduction", 1)[0]
    abstract = head.split("**Abstract**", 1)[1].split("**Keywords**", 1)[0] if "**Abstract**" in head else ""
    notes = md.split("\n# Notes", 1)[1].split("\n# ", 1)[0] if "\n# Notes" in md else ""
    title = re.search(r"^::: \{custom-style=\"Title\"\}\n(.*?)\n:::", md, re.M | re.S)
    return {"main_text": main_words,
            "abstract": len(re.findall(r"\S+", abstract)),
            "notes": len(re.findall(r"\S+", notes)),
            "title": len(re.findall(r"\S+", title.group(1))) if title else 0}


# ------------------------------------------------------------- docx

def postprocess_docx(path: Path, version: str, author: str):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document(str(path))
    for tbl in doc.tables:
        tblPr = tbl._tbl.tblPr
        for el in tblPr.findall(qn("w:tblBorders")):
            tblPr.remove(el)
        b = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{side}")
            if side in ("top", "bottom"):
                e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000")
            else:
                e.set(qn("w:val"), "nil")
            b.append(e)
        tblPr.append(b)
        # rule under the header row
        for cell in tbl.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tb = OxmlElement("w:tcBorders")
            e = OxmlElement("w:bottom")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "000000")
            tb.append(e)
            tcPr.append(tb)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.bold = True
    cp = doc.core_properties
    cp.author = "" if version == "anonymized" else author
    cp.last_modified_by = ""
    cp.comments = ""
    cp.keywords = ""
    cp.subject = ""
    cp.category = ""
    cp.title = ""
    doc.save(str(path))
    # drop pandoc's custom metadata part, which can carry YAML fields
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/custom.xml":
                data = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                        b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
                        b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"/>')
            zout.writestr(item, data)
    tmp.replace(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    TABS.mkdir(parents=True, exist_ok=True)

    rows = coded_names()
    audit = orthography.audit()
    stats: dict = OrderedDict()
    n = len(rows)
    stats["nNames"] = n
    stats["nModels"] = len(models())
    for s in STRATEGIES:
        k = sum(1 for r in rows if r["strategy"] == s)
        key = "".join(w.capitalize() for w in s.split())
        stats[f"strat{key}"] = k
        stats[f"strat{key}Pct"] = pct(k, n)
    for d in DOMAINS:
        k = sum(1 for r in rows if r["domain"] == d)
        key = "".join(w.capitalize() for w in re.sub(r"[^A-Za-z ]", "", d).split())
        stats[f"dom{key}"] = k
        stats[f"dom{key}Pct"] = pct(k, n)
    stats["nTopThree"] = stats["domFauna"] + stats["domObject"] + stats["domPopularCultureAndBrands"]
    stats["nRefKept"] = stats["stratTranslationProper"] + stats["stratModification"]
    stats["nOneWord"] = sum(1 for r in rows if len(r["sro"].split()) == 1)
    stats["nMultiWord"] = n - stats["nOneWord"]
    dim = [r["en"] for r in rows if any(re.search(r"(is|os|ôs|âs|sis)$", w) for w in r["sro"].split())]
    stats["nDiminutive"] = len(dim)
    stats["nDiminutivePct"] = pct(len(dim), n)
    stats["diminutiveNames"] = ", ".join(f"*{d}*" for d in dim)
    stats["nNoSyllabics"] = sum(1 for r in rows if not r["syl"])
    for g in ("built", "draft", "workbench"):
        sub = [r for r in audit if r[0] == g]
        k = Counter(r[4] for r in sub)
        G = g.capitalize()
        stats[f"orth{G}N"] = len(sub)
        for c in ("exact", "length", "mismatch"):
            stats[f"orth{G}{c.capitalize()}"] = k[c]
            stats[f"orth{G}{c.capitalize()}Pct"] = pct(k[c], len(sub))
        npl = sum(1 for r in sub if r[5])
        stats[f"orth{G}NonPlains"] = npl
        stats[f"orth{G}NonPlainsPct"] = pct(npl, len(sub))
    stats.update(workbench_stats())

    figure_map(stats)
    figure_signs()
    stats["tableNames"] = table_names(rows)
    stats["tableCrosstab"] = table_crosstab(rows)
    stats["tableAudit"] = table_audit(audit)
    stats["tableBatches"] = table_batches(rows)
    batches = Counter(r["first"][:7] for r in rows)
    stats["nBatches"] = len(batches)
    order = sorted(batches)
    import calendar
    def month(b):
        y, mo = b.split("-")
        return f"{calendar.month_name[int(mo)]} {y}"
    stats["firstBatch"], stats["firstBatchN"] = month(order[0]), batches[order[0]]
    stats["lastBatch"], stats["lastBatchN"] = month(order[-1]), batches[order[-1]]
    def names_in(b, pred=lambda r: True):
        return [r for r in rows if r["first"][:7] == b and pred(r)]
    stats["firstBatchFauna"] = len(names_in(order[0], lambda r: r["domain"] == "Fauna"))
    stats["faunaN"] = sum(1 for r in rows if r["domain"] == "Fauna")
    late = [r for r in rows if r["strategy"] in ("transference", "mixed")]
    stats["lateLoanBatches"] = " and ".join(month(b) for b in sorted({r["first"][:7] for r in late}))
    for k in ("tableNames", "tableCrosstab", "tableAudit", "tableBatches"):
        (TABS / f"{k}.md").write_text(stats[k] + "\n", encoding="utf-8")
    (OUT / "stats.json").write_text(json.dumps({k: v for k, v in stats.items() if not k.startswith("table")},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "name_coding_full.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order", "first_in_repository", "sign_no", "english", "sro", "syllabics", "literal_sense",
                    "source_domain", "strategy"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["first"], r["n"], r["en"], r["sro"], r["syl"], r["gloss"], r["domain"], r["strategy"]])

    sup = OUT / "supplementary"
    sup.mkdir(exist_ok=True)
    shutil.copy(OUT / "name_coding_full.csv", sup / "name_coding.csv")
    with open(sup / "orthography_audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "english", "sro", "syllabics", "syllabics_read_back", "class", "non_plains_glyph"])
        for r in audit:
            w.writerow([r[0], r[1], r[2], r[3], orthography.syl_to_sro(r[3])[0], r[4], int(r[5])])

    ref = OUT / "reference.docx"
    subprocess.run([sys.executable, str(HERE / "make_reference_docx.py"), str(ref)], check=True)

    template = (HERE / "manuscript.md").read_text(encoding="utf-8")
    author = "Kyle E. Mathewson"
    counts = None
    for version in ("anonymized", "final"):
        md = fill(template, stats, version)
        mdp = OUT / f"manuscript_{version}.md"
        mdp.write_text(md, encoding="utf-8")
        if counts is None:
            counts = word_count(md)
        docx = OUT / f"manuscript_{version}.docx"
        subprocess.run(["pandoc", str(mdp), "-f", "markdown+smart", "-o", str(docx),
                        "--citeproc", "--bibliography", str(HERE / "references.bib"),
                        "--csl", str(HERE / "ans-chicago-author-date.csl"),
                        "--reference-doc", str(ref), "--resource-path", str(OUT),
                        "-M", "link-citations=false", "-M", "lang=en-US"], check=True)
        postprocess_docx(docx, version, author)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(docx)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    lines = [f"title words      {counts['title']:>5}  (limit 50)",
             f"abstract words   {counts['abstract']:>5}  (limit 200)",
             f"main text words  {counts['main_text']:>5}  (limit 5000; excludes notes, references, tables, graphics)",
             f"endnote words    {counts['notes']:>5}  (guideline about 400)"]
    (OUT / "wordcount.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    over = [l for l, lim in ((counts["title"], 50), (counts["abstract"], 200), (counts["main_text"], 5000)) if l > lim]
    if over:
        print("WARNING: over a Names length limit")


if __name__ == "__main__":
    main()
