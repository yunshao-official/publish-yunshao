# -*- coding: utf-8 -*-
"""生成量表 HTML → stdout → Bash 重定向落盘"""
import json, sys

TPL = open("_tpl.html", encoding="utf-8").read() if os.path.exists("_tpl.html") else ""

SCALES = json.loads(open("_scales.json", encoding="utf-8").read())

for sc in SCALES:
    html = TPL.replace("__TITLE__", sc["title"]).replace("__SUB__", sc["sub"])
    html = html.replace("__ITEMS__", json.dumps(sc["items"], ensure_ascii=False))
    html = html.replace("__OPT__", json.dumps(sc["opts"], ensure_ascii=False))
    html = html.replace("__REV__", json.dumps(sc.get("rev", [])))
    html = html.replace("__LV__", json.dumps(sc["lv"], ensure_ascii=False))
    html = html.replace("__SRC__", sc.get("src", ""))
    print(f"<<<FILE:{sc['fn']}.html>>>")
    print(html)
print("<<<ALL_DONE>>>")
