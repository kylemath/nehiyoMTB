"""Build the Word style template (reference.docx) that pandoc uses for the
Names manuscript.

The settings follow the Names author guidelines and the ANS Style Sheet
(checked November 2026): Times New Roman 12 pt, single spacing, justified
text, hyphenation off, one-inch margins, indented paragraphs with no blank
line between them, at most three heading levels (bold; bold italic; italic),
and references with a hanging indent, single spaced within an entry and
double spaced between entries.

A character style called "Syllabics" sets Cree syllabics in a font that has
the Unified Canadian Aboriginal Syllabics block (Euphemia UCAS ships with
Windows and macOS; Noto Sans Canadian Aboriginal is the free fallback).

Usage: python3 make_reference_docx.py OUT.docx
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Times New Roman"
SYL_FONT = "Euphemia UCAS"


def set_font(style, name=FONT, size=12, bold=None, italic=None):
    f = style.font
    f.name = name
    f.size = Pt(size)
    f.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    # drop theme fonts so the named font wins in every script
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(a)) is not None:
            del rfonts.attrib[qn(a)]
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), name)


def para(style, indent=0.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=0, hanging=None,
         keep_next=False):
    pf = style.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.0
    if hanging is not None:
        pf.left_indent = Inches(hanging)
        pf.first_line_indent = Inches(-hanging)
    else:
        pf.left_indent = Inches(0)
        pf.first_line_indent = Inches(indent)
    pf.keep_with_next = keep_next


def get_style(doc, name, kind=WD_STYLE_TYPE.PARAGRAPH, base=None):
    try:
        return doc.styles[name]
    except KeyError:
        s = doc.styles.add_style(name, kind)
        if base is not None:
            s.base_style = doc.styles[base]
        return s


def main(out: str):
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "default.docx"
        with open(base, "wb") as fh:
            subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                           stdout=fh, check=True)
        doc = Document(str(base))

    for s in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
        st = get_style(doc, s)
        set_font(st)
        para(st)
    para(doc.styles["Normal"], indent=0, align=WD_ALIGN_PARAGRAPH.LEFT)
    para(doc.styles["Compact"], indent=0, align=WD_ALIGN_PARAGRAPH.LEFT)
    set_font(doc.styles["Compact"], size=10)
    para(doc.styles["Block Text"], indent=0)
    doc.styles["Block Text"].paragraph_format.left_indent = Inches(0.5)

    # headings: L1 bold, L2 bold italic, L3 italic; flush left, 12 pt
    for name, b, i in (("Heading 1", True, False), ("Heading 2", True, True), ("Heading 3", False, True)):
        st = get_style(doc, name)
        set_font(st, bold=b, italic=i)
        para(st, indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, before=12, after=0, keep_next=True)
    for name in ("Heading 4", "Heading 5", "Heading 6"):
        st = get_style(doc, name)
        set_font(st, italic=True)

    st = get_style(doc, "Title")
    set_font(st, bold=True)
    para(st, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    for name in ("Subtitle", "Author", "Date", "Abstract", "Abstract Title"):
        st = get_style(doc, name)
        set_font(st)
        para(st, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER if name != "Abstract" else WD_ALIGN_PARAGRAPH.JUSTIFY)

    # references: hanging indent, single spaced inside, a blank line between
    st = get_style(doc, "Bibliography")
    set_font(st)
    para(st, align=WD_ALIGN_PARAGRAPH.LEFT, after=12, hanging=0.5)

    # tables and figures: title above, source below
    for name, al, b in (("Table Caption", WD_ALIGN_PARAGRAPH.LEFT, False),
                        ("Image Caption", WD_ALIGN_PARAGRAPH.LEFT, False),
                        ("Captioned Figure", WD_ALIGN_PARAGRAPH.CENTER, False),
                        ("Figure", WD_ALIGN_PARAGRAPH.CENTER, False)):
        st = get_style(doc, name)
        set_font(st, bold=b, italic=False)
        para(st, indent=0, align=al, before=6, after=6, keep_next=(name == "Table Caption"))
    st = get_style(doc, "Graphic Title", base="Normal")
    set_font(st)
    para(st, indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, before=12, after=6, keep_next=True)
    st = get_style(doc, "Graphic Source", base="Normal")
    set_font(st, size=10)
    para(st, indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, before=6, after=12)
    st = get_style(doc, "Unindented", base="Body Text")
    set_font(st)
    para(st, indent=0)
    st = get_style(doc, "Endnote Text Plain", base="Normal")
    set_font(st)
    para(st, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6)

    # character styles
    st = get_style(doc, "Syllabics", WD_STYLE_TYPE.CHARACTER)
    st.font.name = SYL_FONT
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), SYL_FONT)
    st = get_style(doc, "Hyperlink", WD_STYLE_TYPE.CHARACTER)
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.font.underline = False

    # page: US Letter, one-inch margins
    for sec in doc.sections:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, side, Inches(1))

    # hyphenation off
    settings = doc.settings.element
    for el in settings.findall(qn("w:autoHyphenation")):
        settings.remove(el)
    ah = OxmlElement("w:autoHyphenation")
    ah.set(qn("w:val"), "false")
    settings.append(ah)

    cp = doc.core_properties
    cp.author = ""
    cp.last_modified_by = ""
    cp.title = ""
    cp.comments = ""
    doc.save(out)


if __name__ == "__main__":
    main(sys.argv[1])
