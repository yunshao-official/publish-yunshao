#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the five-layer Chinese monograph DOCX (and a PDF-ready file).

Pipeline
1. Concatenate part1.md + part2.md into render.md (front matter kept once).
2. pandoc render.md -> DOCX using the styled reference document.
3. Post-process with python-docx: CJK typography, chapter page breaks,
   three-rule tables with fixed widths, captions, hanging-indent references,
   footer page numbers.

Usage: python3 build_cn.py
"""
import os
import re
import subprocess
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["part1.md", "part2.md"]
RENDER = os.path.join(HERE, "render.md")
OUT = os.path.join(HERE, "分层衍生-数学到医学-v1.0-20261104.docx")
REF = os.path.join(HERE, "style-reference.docx")

SONG = "宋体"
HEI = "黑体"
LATIN = "Times New Roman"

# table widths in cm, keyed by table index
WIDTHS = {
    0: [2.0, 3.4, 3.4, 6.0],                    # 表 1-1
    1: [3.4, 2.9, 5.4, 3.6],                    # 表 1-2
    2: [2.4, 1.7, 1.7, 2.2, 2.2, 1.5, 2.3],     # 表 3-1
    3: [4.6, 3.0, 2.6, 2.8, 2.6],               # 表 4-1
    4: [1.4, 6.2, 4.6, 3.0],                    # 表 5-1
    5: [2.0, 5.6, 3.4, 4.4],                    # 表 6-1
    6: [5.0, 4.2, 6.4],                         # 表 A-1
}


# ---------------------------------------------------------------- helpers
def set_run_font(run, ea=SONG, latin=LATIN, size=None, bold=None, italic=None):
    run.font.name = latin
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rFonts.get(qn(attr)) is not None:
            del rFonts.attrib[qn(attr)]
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:eastAsia"), ea)
    rFonts.set(qn("w:cs"), latin)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic


def style_fonts(style, ea, latin=LATIN, size=None, bold=None):
    style.font.name = latin
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rFonts.get(qn(attr)) is not None:
            del rFonts.attrib[qn(attr)]
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:eastAsia"), ea)
    rFonts.set(qn("w:cs"), latin)
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold


def compose():
    chunks = []
    for i, name in enumerate(PARTS):
        txt = open(os.path.join(HERE, name), encoding="utf-8").read()
        if i == 0:
            chunks.append(txt.strip("\n"))
        else:
            # drop a leading blank line
            chunks.append(txt.lstrip("\n").rstrip("\n"))
    open(RENDER, "w", encoding="utf-8").write("\n\n".join(chunks) + "\n")


def set_cell_margins(table, top=40, bottom=40, left=80, right=80):
    tblPr = table._tbl.tblPr
    mar = tblPr.find(qn("w:tblCellMar"))
    if mar is None:
        mar = OxmlElement("w:tblCellMar")
        tblPr.append(mar)
    for tag, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = mar.find(qn("w:" + tag))
        if el is None:
            el = OxmlElement("w:" + tag)
            mar.append(el)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")


def set_borders(table):
    tblPr = table._tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    spec = {
        "top": ("single", 8, "000000"),
        "bottom": ("single", 8, "000000"),
        "left": ("none", 0, "auto"),
        "right": ("none", 0, "auto"),
        "insideH": ("single", 2, "BFBFBF"),
        "insideV": ("none", 0, "auto"),
    }
    for edge, (val, sz, color) in spec.items():
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def fix_table(table, idx):
    ncols = len(table.rows[0].cells)
    widths = WIDTHS.get(idx)
    if not widths or len(widths) != ncols:
        widths = [15.2 / ncols] * ncols
    twips = [int(w * 567) for w in widths]

    tbl = table._tbl
    tblPr = tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(sum(twips)))
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")

    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        tbl.remove(grid)
    grid = OxmlElement("w:tblGrid")
    for w in twips:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(w))
        grid.append(col)
    tblPr.addnext(grid)

    set_borders(table)
    set_cell_margins(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for r_i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if r_i == 0:
            trPr.append(OxmlElement("w:tblHeader"))
        for c_i, cell in enumerate(row.cells):
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.append(tcW)
            tcW.set(qn("w:type"), "dxa")
            tcW.set(qn("w:w"), str(twips[c_i]))
            if r_i == 0:
                shade(cell, "EFEFEF")
                b = tcPr.find(qn("w:tcBorders"))
                if b is None:
                    b = OxmlElement("w:tcBorders")
                    tcPr.append(b)
                for edge in ("top", "left", "bottom", "right"):
                    e = b.find(qn("w:" + edge))
                    if e is not None:
                        b.remove(e)
                for edge, val, sz in (("top", "single", 8), ("bottom", "single", 8),
                                      ("left", "none", 0), ("right", "none", 0)):
                    e = OxmlElement("w:" + edge)
                    e.set(qn("w:val"), val)
                    e.set(qn("w:sz"), str(sz))
                    e.set(qn("w:space"), "0")
                    e.set(qn("w:color"), "000000")
                    b.append(e)
            for p in cell.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(1.5)
                pf.space_after = Pt(1.5)
                pf.line_spacing = 1.0
                pf.first_line_indent = Pt(0)
                if c_i > 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    set_run_font(run, ea=SONG, size=8.0,
                                 bold=True if r_i == 0 else None)


def add_page_number(section):
    """Insert exactly one PAGE field, purging any earlier footer content."""
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for child in list(p._p):
        if child.tag in (qn("w:r"), qn("w:fldSimple")):
            p._p.remove(child)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " PAGE ")
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), LATIN)
    rFonts.set(qn("w:hAnsi"), LATIN)
    rFonts.set(qn("w:eastAsia"), SONG)
    rPr.append(rFonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "18")
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    p._p.append(fld)


def is_formula(txt):
    core = txt.rstrip("。，；：")
    if not any(k in core for k in (" = ", "→", "≤", "≥", "≈", "∝")):
        return False
    if "，" in core or "：" in core:
        return False
    cjk = sum(1 for ch in core if "\u4e00" <= ch <= "\u9fff")
    if cjk and (cjk / max(len(core), 1) > 0.25 or len(core) > 60):
        return False
    if core.startswith(("在", "设", "取", "把", "若", "则", "其中", "这", "当",
                        "对", "用", "将", "即", "其", "如", "与", "和", "本", "从")):
        return False
    return True


def main():
    compose()
    if os.path.exists(OUT):
        os.remove(OUT)
    cmd = ["pandoc", RENDER, "-o", OUT]
    if os.path.exists(REF):
        cmd += ["--reference-doc", REF]
    subprocess.run(cmd, check=True)

    d = Document(OUT)

    # ---- page setup
    for sec in d.sections:
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        sec.top_margin = Cm(2.4)
        sec.bottom_margin = Cm(2.2)
        sec.left_margin = Cm(2.4)
        sec.right_margin = Cm(2.2)
        add_page_number(sec)

    styles = {s.name: s for s in d.styles}

    # ---- base styles
    for name, ea, size, bold in (
        ("Normal", SONG, 10.5, False),
        ("Body Text", SONG, 10.5, False),
        ("First Paragraph", SONG, 10.5, False),
        ("Compact", SONG, 10.5, False),
        ("Block Text", SONG, 10.0, False),
    ):
        st = styles.get(name)
        if st is not None:
            style_fonts(st, ea, size=size, bold=bold)

    for name, size in (("Heading 1", 17), ("Heading 2", 13)):
        st = styles.get(name)
        if st is not None:
            style_fonts(st, HEI, size=size, bold=True)
            st.font.color.rgb = None

    for name, size in (("Title", 22), ("Subtitle", 12.5), ("Date", 10.5), ("Author", 11.5)):
        st = styles.get(name)
        if st is not None:
            style_fonts(st, HEI if name == "Title" else SONG, size=size,
                        bold=True if name == "Title" else False)

    # ---- paragraph-level typography
    h1_seen = 0
    in_refs = False
    for p in d.paragraphs:
        txt = p.text.strip()
        stn = p.style.name

        if stn == "Heading 1":
            h1_seen += 1
            pf = p.paragraph_format
            pf.space_before = Pt(6)
            pf.space_after = Pt(14)
            pf.keep_with_next = True
            pf.page_break_before = not txt.startswith(("附录 B", "附录 C"))
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                set_run_font(r, ea=HEI, size=17, bold=True)
            in_refs = txt.startswith("附录 B")
            continue

        if stn == "Heading 2":
            pf = p.paragraph_format
            pf.space_before = Pt(14)
            pf.space_after = Pt(6)
            pf.keep_with_next = True
            for r in p.runs:
                set_run_font(r, ea=HEI, size=13, bold=True)
            continue

        if stn == "Author":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            pf.space_before = Pt(26)
            pf.space_after = Pt(8)
            for r in p.runs:
                set_run_font(r, ea=SONG, size=11.5, italic=False)
            continue

        if stn in ("Title", "Subtitle", "Date"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            pf.space_before = Pt(90 if stn == "Title" else 6)
            pf.space_after = Pt(10 if stn == "Title" else 6)
            for r in p.runs:
                set_run_font(r, ea=HEI if stn == "Title" else SONG,
                             size=22 if stn == "Title" else (12.5 if stn == "Subtitle" else 10.5),
                             bold=(stn == "Title"), italic=False)
            continue

        if stn in ("Captioned Figure", "Image Caption"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            if stn == "Captioned Figure":
                pf.space_before = Pt(10)
                pf.space_after = Pt(2)
                pf.keep_with_next = True
            else:
                pf.space_before = Pt(2)
                pf.space_after = Pt(12)
                for r in p.runs:
                    set_run_font(r, ea=SONG, size=9, italic=True)
            continue

        if stn == "Source Code":
            pf = p.paragraph_format
            pf.left_indent = Cm(0.6)
            pf.space_before = Pt(6)
            pf.space_after = Pt(8)
            pf.line_spacing = 1.05
            for r in p.runs:
                set_run_font(r, ea=SONG, latin="Consolas", size=8.5)
            continue

        # table captions: bold paragraph starting with 表
        if re.match(r"^表\s?[0-9A-C]", txt):
            pf = p.paragraph_format
            pf.keep_with_next = True
            pf.space_before = Pt(12)
            pf.space_after = Pt(5)
            pf.first_line_indent = Pt(0)
            for r in p.runs:
                set_run_font(r, ea=HEI, size=9.5, bold=True)
            continue

        # horizontal rule leftovers
        if txt == "":
            continue

        pf = p.paragraph_format
        has_num = p._p.pPr is not None and p._p.pPr.find(qn("w:numPr")) is not None
        if (not in_refs) and (not has_num) and is_formula(txt):
            pf.first_line_indent = Pt(0)
            pf.left_indent = Pt(0)
            pf.space_before = Pt(4)
            pf.space_after = Pt(6)
            pf.line_spacing = 1.3
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                set_run_font(r, ea=SONG, size=10.5)
            continue
        if in_refs:
            pf.left_indent = Cm(0.75)
            pf.first_line_indent = Cm(-0.75)
            pf.space_after = Pt(4)
            pf.line_spacing = 1.15
            for r in p.runs:
                set_run_font(r, ea=SONG, size=9.5)
        else:
            pf.first_line_indent = Pt(21)
            pf.space_after = Pt(4)
            pf.line_spacing = 1.45
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                set_run_font(r, ea=SONG, size=10.5)

    # bullets / numbered lists should not be first-line indented
    for p in d.paragraphs:
        if p.style.name in ("Compact", "Body Text") and p._p.pPr is not None:
            numPr = p._p.pPr.find(qn("w:numPr"))
            if numPr is not None:
                p.paragraph_format.first_line_indent = Pt(0)
                p.paragraph_format.left_indent = Cm(0.9)
                p.paragraph_format.space_after = Pt(2)

    # ---- tables
    for i, t in enumerate(d.tables):
        fix_table(t, i)

    from docx.text.paragraph import Paragraph
    for tbl in d.element.body.iter(qn("w:tbl")):
        nxt = tbl.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            Paragraph(nxt, d).paragraph_format.space_before = Pt(8)

    d.save(OUT)
    words = sum(len(p.text) for p in d.paragraphs)
    print("built", OUT)
    print("paragraphs", len(d.paragraphs), "tables", len(d.tables), "chars", words)


if __name__ == "__main__":
    main()
