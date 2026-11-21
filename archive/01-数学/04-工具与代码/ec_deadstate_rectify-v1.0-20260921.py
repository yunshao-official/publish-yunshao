# -*- coding: utf-8 -*-
# 死态判据修正轨（R26·D-N3 判负照记后的修正轨：活性反向闭包）
# 一步判据 30/32 对（E-25/E-26 二阶死判负照记）；修正轨=死集==keep−Act（Act=接受态反向 BFS 可达集）
# 48 档恒等 + 死深结构落盘 + 修正轨分解律恒等。
import json
import numpy as np
import importlib.util as ilu

spec = ilu.spec_from_file_location("m", "H:/理论存档/01-数学/04-工具与代码/ec_noninherit_mechanism-v1.0-20260921.py")
m = ilu.module_from_spec(spec); spec.loader.exec_module(m)

G = m.G; SIGN = m.SIGN; step = m.step
build_dfa = m.build_dfa; moore_minimize = m.moore_minimize

def rectify(c, Darr):
    keep_states, tr, q0, accept = build_dfa(c)
    n_min, classes = moore_minimize(tr, set(accept), keep_states)
    accset = {s for s in keep_states if s[0]==c}
    # 出边图（keep 内）
    outs = {}
    for s in keep_states:
        outs[s] = [step(s, r) for r in range(4)]
    # Act=接受态反向 BFS 可达（活性=正向可达接受）
    Act = set(accset)
    stack = list(accset)
    while stack:
        t = stack.pop()
        for s in keep_states:
            if s not in Act and any(o == t for o in outs[s]):
                Act.add(s); stack.append(s)
    deadset = set(keep_states) - Act
    # 死深：depth(s)=1 若四出全出 keep；否则 1+min depth(落点∈deadset)
    depth = {}
    frontier1 = {s for s in deadset if all(o not in keep_states for o in outs[s])}
    for s in frontier1: depth[s] = 1
    rest = deadset - frontier1
    d = 1
    while rest:
        d += 1
        nxt = {s for s in rest if any(o in deadset and depth.get(o, 10**9) <= d-1 for o in outs[s])}
        for s in nxt: depth[s] = d
        rest -= nxt
        if not nxt: break
    # Moore dead 类
    dead_members = []
    for k, v in classes.items():
        if "DEAD" in v and not any(x != "DEAD" and x[0]==c for x in v):
            dead_members += [x for x in v if x != "DEAD"]
    eq_rect = bool(sorted(dead_members) == sorted(deadset))
    # 修正轨分解律
    acc_n = len(accset)
    n_acc_classes = sum(1 for k,v in classes.items() if any(x!="DEAD" and x[0]==c for x in v))
    acc_members = sum(1 for k,v in classes.items() for x in v if x!="DEAD" and x[0]==c)
    M_acc = acc_members - n_acc_classes
    M_dead = len(dead_members)
    M_int = sum(len(v) for k,v in classes.items()
                if "DEAD" not in v and not any(x!="DEAD" and x[0]==c for x in v) and len(v)>1) \
            - sum(1 for k,v in classes.items()
                  if "DEAD" not in v and not any(x!="DEAD" and x[0]==c for x in v) and len(v)>1)
    reach = sum(len([x for x in v if x!="DEAD"]) for v in classes.values())
    R_f = reach + 1 - M_acc - M_dead - M_int
    return {"min_dfa": int(n_min), "eq_rect": eq_rect, "rect_decomp_eq": bool(R_f == n_min),
            "deadset": sorted([str(s) for s in deadset]),
            "depth_hist": {str(k2): sum(1 for v in depth.values() if v==k2) for k2 in sorted(set(depth.values()))},
            "R_f": int(R_f)}

def main():
    Darr = m.build_D_table()
    res = {}
    allok = True
    for c in list(range(0, -32, -1)) + list(range(-32, -48, -1)):
        r = rectify(c, Darr)
        res["c(%d)" % c] = r
        if not (r["eq_rect"] and r["rect_decomp_eq"]): allok = False
        print("c=%d R=%d rect_eq=%s decomp_eq=%s depths=%s" % (
            c, r["min_dfa"], r["eq_rect"], r["rect_decomp_eq"], r["depth_hist"]), flush=True)
    print("ALL_RECT_OK=%s" % allok)
    outp = "H:/理论存档/01-数学/02-实验与数据/results/ec_deadstate_rectify-v1.0-20260921.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump({"all_ok": allok, "entries": res}, f, ensure_ascii=False, indent=1)
    print("saved %s" % outp)

if __name__ == "__main__":
    main()
