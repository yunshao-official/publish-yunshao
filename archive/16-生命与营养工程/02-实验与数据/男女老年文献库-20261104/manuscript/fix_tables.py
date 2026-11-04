"""Post-process the pandoc-rendered manuscript.

Pandoc 2.9 emits tables with an empty <w:tblGrid> and tblW=0 for pipe tables
that do not carry explicit relative widths.  LibreOffice (and Word, in some
layouts) then collapses every column into the first one.  This script rebuilds
the grid, sets explicit column widths, applies three-rule academic borders,
repeats the header row, and normalises body/caption typography.

Usage:
    python3 fix_tables.py SCI_manuscript.docx
"""
import sys
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

WIDTHS = {
    4: [9.0, 2.2, 2.2, 2.4],
    5: [3.0, 3.2, 3.4, 3.4, 2.2],
}
# table-specific overrides, keyed by index
OVERRIDES = {
    0: [8.6, 2.4, 2.4, 2.4],
    1: [9.4, 2.0, 2.2, 2.2],
    2: [3.4, 4.5, 4.5, 3.4],
    3: [2.9, 3.2, 3.5, 3.6, 2.4],
}


def set_cell_margins(table, top=40, bottom=40, left=90, right=90):
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
    widths = OVERRIDES.get(idx) or WIDTHS.get(ncols)
    if not widths or len(widths) != ncols:
        total = 15.5
        widths = [total / ncols] * ncols
    twips = [int(w * 567) for w in widths]

    tbl = table._tbl
    tblPr = tbl.tblPr
    # table width: fixed, absolute twips
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

    # rebuild grid
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
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        if r_i == 0:
            hdr = OxmlElement("w:tblHeader")
            trPr.append(hdr)
        for c_i, cell in enumerate(row.cells):
            cell.width = Pt(widths[c_i] * 28.35)  # cm -> pt
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.append(tcW)
            tcW.set(qn("w:type"), "dxa")
            tcW.set(qn("w:w"), str(twips[c_i]))
            if r_i == 0:
                shade(cell, "EFEFEF")
                # header bottom rule
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
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.0
                for run in p.runs:
                    run.font.size = Pt(8.5)
                    run.font.name = "Times New Roman"
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
                    if r_i == 0:
                        run.font.bold = True


def main(path):
    d = Document(path)
    for i, t in enumerate(d.tables):
        fix_table(t, i)

    from docx.text.paragraph import Paragraph
    for tbl in d.element.body.iter(qn("w:tbl")):
        nxt = tbl.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            Paragraph(nxt, d).paragraph_format.space_before = Pt(6)

    for p in d.paragraphs:
        txt = p.text.strip()
        if txt.startswith(("Table 1.", "Table 2.", "Table 3.", "Table 4.")):
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.bold = True
        if p.style.name == "Captioned Figure":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
        if p.style.name == "Image Caption":
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(12)
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.italic = True
        if txt.startswith("Cumulative n is the sum"):
            for r in p.runs:
                r.font.size = Pt(9)
        if p.style.name == "Bibliography":
            p.paragraph_format.left_indent = Cm(0.55)
            p.paragraph_format.first_line_indent = Cm(-0.55)
            p.paragraph_format.space_after = Pt(3)

    d.save(path)
    print("tables fixed:", len(d.tables))


if __name__ == "__main__":
    main(sys.argv[1])
