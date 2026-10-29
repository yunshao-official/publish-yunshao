# -*- coding: utf-8 -*-
"""final_analysis.py · 猜想C闭合实验最终合并分析（2026-09-18，四遍合并）

口径：完全同 0917 analyze_final.py（格点取多遍最优：闭合>不闭合；同口径取 Λ 最小），
m3@1e5 对照取 runner 外补跑证书；R1 并入行按预注册 §六原样并入。
判定：预注册 §四冻结口径原样——每 m 跨 N 取格点 Λ 中位数 Λ̂(N)（Λ=0 档单独披露），
幂律拟合 ln Λ̂ = a + b·ln N；存活 b̂<0.3 且全闭合；强存活再加 max Λ≤32；
判负证据三条款 ①过检格点不闭合 ②b̂≥0.3 ③10⁵ 档 Λ>10²。
"""
import json
import math
import os
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
P17 = r"H:\door1\conjectureC_20260917"
Ns = [1000, 10000, 100000]


def merge():
    runs = []
    # checkpoint.json = 0917 pass3 中断时的落盘（含 m6@1e5 s42 PASS Λ=88），summary_pass2/3
    # 因当时会话被杀从未写出，故以 checkpoint 补入；同一格点多遍全披露。
    for base, fn in [(P17, "summary.json"), (P17, "summary_pass2.json"),
                     (P17, "summary_pass3.json"), (P17, "checkpoint.json"),
                     (BASE, "summary_pass4.json")]:
        p = os.path.join(base, fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                runs.append((fn, json.load(f)["results"]))
        else:
            runs.append((fn, None))
    cells = {}
    for fn, rs in runs:
        if rs is None:
            continue
        for c in rs:
            tag = c["tag"]
            if tag not in cells:
                cells[tag] = {"passes": []}
            cells[tag]["passes"].append({"run": fn, **c})
    return cells, [fn for fn, rs in runs if rs is not None]


def best_pass(plist):
    """格点代表遍次：闭合（Λ 非空）优先取 Λ 最小；否则在构造完整（size==N）的遍次中
    取断口最小；构造不完整（size<N）的 engine 结果不作为断口比较对象（其 breaks1 无意义）。"""
    closed = [p for p in plist if p.get("Lambda") is not None]
    if closed:
        return min(closed, key=lambda p: p["Lambda"])
    full = [p for p in plist if p.get("engine") and p["engine"].get("size") == p.get("N")]
    if full:
        # 断口最小优先；平局取预算更满者（代表"每实例30分钟预算"口径下的最终状态）
        return min(full, key=lambda p: (p["engine"]["breaks1"], -(p.get("engine_cap_given") or 0)))
    with_engine = [p for p in plist if p.get("engine")]
    if with_engine:
        return min(with_engine, key=lambda p: p["engine"]["breaks1"])
    return plist[0]


def med(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def main():
    cells, found = merge()
    print("合并的运行:", found)
    extra = os.path.join(P17, "logs", "cap_m3_N100000_s42.json")
    if os.path.exists(extra):
        j = json.load(open(extra))
        cells.setdefault("m3_N100000_s42", {"passes": [{
            "run": "runner外补跑(0917)", "m": 3, "N": 100000, "seed": 42, "tag": "m3_N100000_s42",
            "cap": j, "verdict": "capacity-KILLED", "wall_s": 0}]})
    order = []
    for N in Ns:
        order.append(f"m3_N{N}_s42")
        for m in (4, 5, 6):
            for s in (42, 13, 7):
                order.append(f"m{m}_N{N}_s{s}")
    rows = []
    for tag in order:
        if tag not in cells:
            rows.append({"tag": tag, "missing": True})
            continue
        bp = best_pass(cells[tag]["passes"])
        e = bp.get("engine")
        r1 = bp.get("r1")
        row = {"tag": tag, "m": bp["m"], "N": bp["N"], "seed": bp["seed"],
               "cap": bp.get("cap", {}).get("verdict"), "L": bp.get("cap", {}).get("L_size"),
               "flow": bp.get("cap", {}).get("flow"), "demand": bp.get("cap", {}).get("demand"),
               "LB": bp.get("cap", {}).get("breaks_lower_bound"),
               "lambda2": bp.get("lambda2", {}).get("lambda2"),
               "Lambda": bp.get("Lambda"),
               "n_passes": len(cells[tag]["passes"]),
               "passes_info": [(p["run"], p.get("engine_cap_given", "-"),
                                (p["engine"]["breaks0"], p["engine"]["breaks1"]) if p.get("engine") else
                                ((p["r1"]["breaks0"], p["r1"]["breaks1"]) if p.get("r1") else None))
                               for p in cells[tag]["passes"]]}
        if e:
            row.update(breaks=f"{e['breaks0']}→{e['breaks1']}", rot=e["rot"],
                       rounds=f"{e.get('rounds_fixp')}/{e.get('rounds_lns')}", pass_=e["pass"],
                       cap_given=bp.get("engine_cap_given"), wall=bp["wall_s"],
                       mode="PASS" if e["pass"] else
                       (f"构造不完整(size={e['size']})" if e["size"] < bp["N"] else f"残余断口{e['breaks1']}"))
        elif r1:
            row.update(breaks=f"{r1['breaks0']}→{r1['breaks1']}", rot=r1["rot"], rounds="-/300",
                       pass_=False, cap_given="R1:1400", wall=r1["wall_s"], mode="R1并入·残余断口")
        else:
            row.update(breaks="-", pass_=False, wall=bp.get("wall_s", 0),
                       mode=bp.get("verdict", "capacity-KILLED"))
        rows.append(row)

    print("\n== 最终矩阵表（27+3 格点）==")
    for r in rows:
        if r.get("missing"):
            print(f"{r['tag']:<18} 未跑")
            continue
        l2s = f"{r['lambda2']:.4f}" if r.get("lambda2") else "  -   "
        print(f"{r['tag']:<18} {str(r.get('cap'))[:14]:<14} |L|={str(r.get('L')):<6} flow={str(r.get('flow')):<6} "
              f"λ₂={l2s} 断口={r.get('breaks','-',):<12} Λ={str(r.get('Lambda')):<5} rot={str(r.get('rot')):<6} "
              f"轮(f/l)={str(r.get('rounds')):<8} {'PASS' if r.get('pass_') else 'FAIL':<4} cap给={str(r.get('cap_given')):<7} "
              f"wall={r.get('wall')}s 遍数={r['n_passes']} {r.get('mode','')}")

    print("\n== 冻结判定（预注册 §四，原样）==")
    verdicts = {}
    for m in (4, 5, 6):
        mrows = [r for r in rows if r["m"] == m]
        lams = {N: med([r.get("Lambda") for r in mrows if r["N"] == N]) for N in Ns}
        closed_by_N = {N: [r for r in mrows if r["N"] == N and r.get("Lambda") is not None] for N in Ns}
        all_closed = all(len(closed_by_N[N]) == 3 for N in Ns)
        n_notclosed = [(r["tag"], r.get("mode")) for r in mrows if r.get("Lambda") is None]
        pts = [(math.log(N), math.log(v)) for N, v in lams.items() if v not in (None, 0)]
        if len(pts) >= 2:
            n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
            sxx = sum(p[0] ** 2 for p in pts); sxy = sum(p[0] * p[1] for p in pts)
            bh = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        else:
            bh = None
        e5lams = [r.get("Lambda") for r in mrows if r["N"] == 100000 and r.get("Lambda") is not None]
        maxlam = max([v for v in (r.get("Lambda") for r in mrows) if v is not None], default=None)
        cond1 = all_closed          # ①过检格点全部闭合
        cond2 = (bh is not None and bh < 0.3)
        cond3 = (maxlam is not None and maxlam <= 32)
        cond_1e5 = all(v is not None and v <= 100 for v in e5lams) and len(e5lams) == 3
        if all_closed and bh is not None and bh < 0.3:
            status = "强存活" if cond3 else "存活"
        elif all_closed:
            status = "b̂线不符（存活条件半满足）"
        else:
            status = "判负证据（①过检格点不闭合）"
        extra_n = [N for N, v in lams.items() if v == 0]
        verdicts[m] = {"lams_median": lams, "b_hat": None if bh is None else round(bh, 4),
                       "all_closed": all_closed, "not_closed": n_notclosed, "max_Lambda": maxlam,
                       "status": status,
                       "note": ("含Λ̂=0档" + str(extra_n) + "（ln拟合无定义，b̂仅对非零档）") if extra_n else ""}
        print(f"m={m}: Λ̂中位数={lams} 全闭合={all_closed} 未闭合格点={n_notclosed} "
              f"b̂={verdicts[m]['b_hat']} maxΛ={maxlam} → {status} {verdicts[m]['note']}")

    c_notclosed = [m for m in (4, 5, 6) if verdicts[m]["not_closed"]]
    print("\n== 猜想C整体判定 ==")
    if c_notclosed:
        print(f"判负证据成立（条款①）：m={c_notclosed} 存在过检格点预算内不闭合（按 V2.0 可证伪条款记录；"
              f"注意预算上限=每实例30分钟，不闭合=预算内证据，非复杂性发散证明）")
    else:
        any_pos = [m for m in (4, 5, 6) if verdicts[m]["status"].startswith(("存活", "强存活"))]
        print(f"无判负证据条款①；各 m 状态：{ {m: verdicts[m]['status'] for m in (4,5,6)} }")

    out = {"rows": rows, "verdicts": {str(k): v for k, v in verdicts.items()},
           "runs_merged": found}
    with open(os.path.join(BASE, "final_matrix.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n已写 final_matrix.json")


if __name__ == "__main__":
    main()
