#!/usr/bin/env python3
"""Build the submission-ready DOCX from manuscript_with_refs.md.

Steps
1. Compose a render copy: move the H1 title into YAML metadata, drop the
   duplicated "Manuscript draft" subtitle line, drop section-separator rules.
2. Render with pandoc using the styled reference document.
3. Repair table grids and typography (see fix_tables.py).

Usage:
    python3 build_docx.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "manuscript_with_refs.md")
RENDER = os.path.join(HERE, "render.md")
OUT = os.path.join(HERE, "SCI_manuscript.docx")
REF = os.path.join(HERE, "style-reference.docx")


def compose():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    title = lines[0][2:].strip()
    body = []
    for ln in lines[1:]:
        if ln.strip().startswith("**Manuscript draft"):
            continue
        if ln.strip() == "---":
            continue
        body.append(ln)
    yaml = (
        "---\n"
        f'title: "{title}"\n'
        'subtitle: "Manuscript draft — for internal review and journal submission preparation"\n'
        "---\n"
    )
    open(RENDER, "w", encoding="utf-8").write(yaml + "\n".join(body))


def main():
    compose()
    cmd = ["pandoc", RENDER, "-o", OUT]
    if os.path.exists(REF):
        cmd += ["--reference-doc", REF]
    subprocess.run(cmd, check=True)
    subprocess.run([sys.executable, os.path.join(HERE, "fix_tables.py"), OUT], check=True)
    print("built", OUT)


if __name__ == "__main__":
    main()
