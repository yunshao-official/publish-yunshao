# -*- coding: utf-8 -*-
"""云韶计算体系首跑·实验一：CP-SAT 完备判定 × M1 启发式对拍
判据：云韶计算体系·四项首跑预注册判据书-v1.0-20261003.md（先于本脚本落盘）
素材：m4_grid4_observe_results-v1.0-20260927.json 的 solved=false 实例（N=100，前5个）
方法：gen_ba_rebuild 同参重构 + hp_cpsat AddCircuit 完备判定（300s/实例）
"""
import json, time, random, io, sys
sys.path.insert(0, r"H:/理论存档/04-哈密顿路径/04-工具与代码")
import networkx as nx
from ortools.sat.python import cp_model

# --- 与 m4 管线完全一致的图生成器（对拍同图同参） ---
def gen_ba_rebuild(N, m, seed):
    rng = random.Random(seed)
    g = nx.complete_graph(m)
    for u in range(m, N):
        nodes = list(g.nodes())
        weights = [g.degree(v) + 0.5 for v in nodes]
        total = sum(weights)
        for _ in range(m):
            pick = rng.random() * total
            acc = 0.0
            for v, w in zip(nodes, weights):
                acc += w
                if acc >= pick:
                    if v != u and not g.has_edge(u, v):
                        g.add_edge(u, v)
                    break
        g.add_node(u)
    return g

def hp_cpsat(g, tl):
    n = g.number_of_nodes()
    D = n
    mdl = cp_model.CpModel()
    lits = {}
    for u, v in g.edges():
        lits[(u, v)] = mdl.NewBoolVar(f"x{u}_{v}")
        lits[(v, u)] = mdl.NewBoolVar(f"x{v}_{u}")
    for i in range(n):
        lits[(i, D)] = mdl.NewBoolVar(f"d{i}e")
        lits[(D, i)] = mdl.NewBoolVar(f"d{i}s")
    arc_list = [(u, v, lit) for (u, v), lit in lits.items()]
    mdl.AddCircuit(arc_list)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = 8
    st = solver.Solve(mdl)
    if st == cp_model.INFEASIBLE:
        return "INFEASIBLE"
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return "FEASIBLE"
    return "TIMEOUT_UNKNOWN"

# --- 取 m4 判 false 的实例 ---
src = r"H:/理论存档/04-哈密顿路径/02-实验与数据/m4_grid4_observe_results-v1.0-20260927.json"
obs = json.load(io.open(src, encoding="utf-8"))["observations"]
falses = [(o["N"], o["seed"]) for o in obs if o.get("N") == 100 and not o.get("solved")][:5]
print("对拍实例（N=100, M1=false）：", falses)

results = []
for N, seed in falses:
    g = gen_ba_rebuild(N, 5, seed)  # m=5 与 m4@1e5 档一致
    t0 = time.time()
    verdict = hp_cpsat(g, 300)
    dt = time.time() - t0
    rec = {"N": N, "seed": seed, "M1": "false", "CPSAT": verdict, "sec": round(dt, 1)}
    if verdict == "INFEASIBLE":
        rec["judge"] = "C1 形态死局·完备层确认"
    elif verdict == "FEASIBLE":
        rec["judge"] = "C2 M1漏解"
    else:
        rec["judge"] = "C3 超时不计"
    results.append(rec)
    print(rec)

# 判据回填
n_c1 = sum(1 for r in results if r["CPSAT"] == "INFEASIBLE")
n_c2 = sum(1 for r in results if r["CPSAT"] == "FEASIBLE")
n_c3 = sum(1 for r in results if r["CPSAT"] not in ("INFEASIBLE", "FEASIBLE"))
summary = {"c1_infeasible": n_c1, "c2_leak": n_c2, "c3_timeout": n_c3,
           "frozen_prediction": "多数C1", "prediction_result": "成立" if n_c1 >= n_c2 and n_c1 > 0 else "不成立",
           "results": results}
out = r"H:/理论存档/01-数学/02-实验与数据/YSCS-R1-sat-duipai-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False, indent=1))
print("\n=== 判据开票：C1={} C2={} C3={} → 冻结预测『多数C1』{} ===".format(n_c1, n_c2, n_c3, summary["prediction_result"]))
print("结果件：", out)
