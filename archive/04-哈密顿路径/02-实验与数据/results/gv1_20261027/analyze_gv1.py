#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G-V1 A/B 结算器：读 results/gv1_20261027/{base,geo}_N_m.jsonl，出对照表+JSON。"""
import json, glob, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
rows = {}
for path in glob.glob(os.path.join(HERE, "*.jsonl")):
    name = os.path.basename(path)[:-6]
    parts = name.split("_")
    if len(parts) != 3 or parts[0] not in ("base", "geo"):
        continue
    arm, n, m = parts
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rows[(int(d["N"]), int(d["m"]), int(d["seed"]), arm)] = d

cells = sorted({(n, m) for (n, m, s, a) in rows})
seeds = sorted({s for (n, m, s, a) in rows})
out = {"cells": [], "seeds": seeds, "cap_note": "cap=240s per case"}
print("| N | m | arm | PASS | 构造完整 | breaks0->1 | rot | con(s) | rep(s) |")
print("|---|---|---|---|---|---|---|---|---|")
for (n, m) in cells:
    for arm in ("base", "geo"):
        ds = [rows.get((n, m, s, arm)) for s in seeds]
        ds = [d for d in ds if d]
        if not ds:
            continue
        p = sum(1 for d in ds if d["pass"])
        full = sum(1 for d in ds if d["size"] == n)
        b0 = sum(d["breaks0"] for d in ds)
        b1 = sum(d["breaks1"] for d in ds)
        rot = int(st.mean(d["rot"] for d in ds))
        con = st.mean(d["t_con"] for d in ds)
        rep = st.mean(d["t_rep"] for d in ds)
        print(f"| {n} | {m} | {arm} | {p}/{len(ds)} | {full}/{len(ds)} | {b0}->{b1} | {rot} | {con:.2f} | {rep:.2f} |")
        out["cells"].append(dict(N=n, m=m, arm=arm, n=len(ds), pass_n=p, full_n=full,
                                 breaks0=b0, breaks1=b1, rot_mean=rot,
                                 con_mean=round(con, 3), rep_mean=round(rep, 3)))
print()
for (n, m) in cells:
    b = [rows.get((n, m, s, "base")) for s in seeds]
    g = [rows.get((n, m, s, "geo")) for s in seeds]
    if not all(b) or not all(g):
        continue
    fb = sum(1 for d in b if d["size"] == n)
    fg = sum(1 for d in g if d["size"] == n)
    pb = sum(1 for d in b if d["pass"])
    pg = sum(1 for d in g if d["pass"])
    print(f"{n}x{m}: 构造完整 base {fb}/{len(b)} vs geo {fg}/{len(g)}；PASS base {pb} vs geo {pg}")
    out.setdefault("pairs", []).append(dict(N=n, m=m, full_base=fb, full_geo=fg,
                                            pass_base=pb, pass_geo=pg, n=len(b)))
with open(os.path.join(HERE, "gv1_summary.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n-> gv1_summary.json")

csv_path = os.path.join(HERE, "gv1_pairs.csv")
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("N,m,seed,base_pass,geo_pass,base_size,geo_size,base_breaks0,geo_breaks0,"
            "base_rot,geo_rot,base_con,geo_con,base_rep,geo_rep,base_total,geo_total,total_ratio\n")
    for (n, m) in cells:
        for s in seeds:
            b = rows.get((n, m, s, "base"))
            g = rows.get((n, m, s, "geo"))
            if not b or not g:
                continue
            bt = b["t_con"] + b["t_rep"]
            gt = g["t_con"] + g["t_rep"]
            ratio = (gt / bt) if bt > 0 else float("inf")
            f.write(f"{n},{m},{s},{b['pass']},{g['pass']},{b['size']},{g['size']},"
                    f"{b['breaks0']},{g['breaks0']},{b['rot']},{g['rot']},"
                    f"{b['t_con']:.3f},{g['t_con']:.3f},{b['t_rep']:.3f},{g['t_rep']:.3f},"
                    f"{bt:.3f},{gt:.3f},{ratio:.2f}\n")
print("-> gv1_pairs.csv")
