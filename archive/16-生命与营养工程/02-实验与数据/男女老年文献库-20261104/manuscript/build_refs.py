#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assign Vancouver-style reference numbers in order of first citation and build the reference list."""
import json, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
MD_IN = os.path.join(BASE, "manuscript_draft.md")
MD_OUT = os.path.join(BASE, "manuscript_with_refs.md")

D = json.load(open(os.path.join(ROOT, "文献主档-v1.0.json"), encoding="utf-8"))
records = {}
for sex in ("male", "female"):
    for r in D["records"][sex]:
        records[str(r["pmid"])] = r

text = open(MD_IN, encoding="utf-8").read()
order = []
for m in re.finditer(r"\[\[PMID:(\d+)\]\]", text):
    p = m.group(1)
    if p not in order:
        order.append(p)

missing = [p for p in order if p not in records]
if missing:
    print("MISSING PMIDs:", missing)
    sys.exit(1)

num = {p: i + 1 for i, p in enumerate(order)}
def repl(m):
    p = m.group(1)
    return f"[{num[p]}]"
text = re.sub(r"\[\[PMID:(\d+)\]\]", repl, text)

def clean_authors(a):
    a = (a or "").strip().rstrip(".")
    parts = [x.strip() for x in a.split(",") if x.strip()]
    if len(parts) > 6:
        return ", ".join(parts[:6]) + ", et al."
    return ", ".join(parts) + "."

def clean_title(t):
    t = (t or "").strip()
    if not t.endswith("."):
        t += "."
    return t

lines = []
for p in order:
    r = records[p]
    authors = clean_authors(r.get("authors"))
    title = clean_title(r.get("title"))
    journal = (r.get("journal_abbrev") or r.get("journal") or "").strip().rstrip(".")
    year = r.get("year") or ""
    vol = (r.get("volume") or "").strip()
    issue = (r.get("issue") or "").strip()
    pages = (r.get("pages") or "").strip()
    doi = (r.get("doi") or "").strip()
    loc = year
    if vol:
        loc += f";{vol}"
        if issue:
            loc += f"({issue})"
        if pages:
            loc += f":{pages}"
    elif pages:
        loc += f":{pages}"
    s = f"{num[p]}. {authors} {title} {journal}. {loc}."
    if doi:
        s += f" doi:{doi}."
    s += f" PMID: {p}."
    lines.append(s)

refs = "\n".join(lines)
text = text.replace("<!-- REFERENCES -->", refs)
open(MD_OUT, "w", encoding="utf-8").write(text)

print(f"cited unique PMIDs: {len(order)}")
print(f"core cited: {sum(1 for p in order if records[p].get('analysis_set')=='core')}")
print(f"output: {MD_OUT}")
print(f"words (approx): {len(text.split()):,}")
