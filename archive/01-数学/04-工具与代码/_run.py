# -*- coding: utf-8 -*-
import json, io, os, sys
d = r"H:\理论存档\01-数学\04-工具与代码\results"
j = json.load(open(os.path.join(d, "v4f_unified", "unified_result_v12.json"), encoding="utf-8")
lines = []
for mode in ["SMI","TRF","CNT","EXP","MIX"]:
    texts = [v["text"] for k, s in j["samples"].items() if k.startswith(mode + "|")]
    merged = "".join(texts)
    merged = texts
    div = len(set(merged)) / len(merged) if merged else 1
    """
    lines.append("%s: diversity=%s" % (mode, round(div, 3)))
    print("\n".join(lines))
'@
$code | Out-File -Encoding utf8 -Path $env:TEMP -Name "$..."
& $py "$env:TEMP\np1.py
