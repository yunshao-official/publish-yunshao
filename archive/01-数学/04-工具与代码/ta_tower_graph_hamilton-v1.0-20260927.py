# -*- coding: utf-8 -*-
"""
塔交互三构想·构想二（H 系列）：塔网络哈密顿化
预注册：《塔交互三构想·预注册判据书-v1.0-20260927》判据冻结在先
塔图：顶点=前 N_t 座塔（q>=7 素数）；连边 iff gcd(|PSL(2,q1)|,|PSL(2,q2)|) >= 阈值
主档阈值=12（衔尾蛇组数）；敏感档 4 / 48
检验序列（V2.1 三明治顺序）：连通性 → 定理A容量判据 → 扩张证书(λ2) → 哈密顿回溯 → 计数+规模阶梯
"""
import numpy as np, sympy as sp, networkx as nx, json, platform, datetime
from networkx.algorithms.flow import maximum_flow

TH_MAIN, TH_LO, TH_HI = 12, 4, 48
LADDER = [10, 20, 30, 40]
SEARCH_CAP = 100000  # 回溯计数上限

def order(q): return q * (q * q - 1) // 2

def build_graph(n_towers, th):
    qs = list(sp.primerange(7, 10 ** 4))[:n_towers]
    G = nx.Graph()
    G.add_nodes_from(qs)
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            if sp.gcd(order(qs[i]), order(qs[j])) >= th:
                G.add_edge(qs[i], qs[j])
    return G, qs

def capacity_kill(G):
    """定理A容量流判据（V2.1原文）：L={deg=d_min 顶点}，非独立则取贪心极大独立子集（如实记录）。"""
    degs = dict(G.degree())
    d_min = min(degs.values())
    L = [v for v in G if degs[v] == d_min]
    independent = (len(L) < 2) or (G.subgraph(L).number_of_edges() == 0)
    if not independent:
        # 贪心极大独立子集（诚实降级记录）
        keep, cand = [], sorted(L, key=lambda v: degs[v])
        blocked = set()
        for v in cand:
            if v not in blocked:
                keep.append(v); blocked |= set(G.neighbors(v)) | {v}
        L = keep
    if len(L) < 2:
        return False, {"L_size": len(L), "note": "低度顶点<2，容量判据无靶"}, L, independent
    D = nx.DiGraph()
    nbrs = sorted({u for l in L for u in G.neighbors(l)})
    D.add_node("S"); D.add_node("T")
    for l in L: D.add_edge("S", l, capacity=2)
    for l in L:
        for u in G.neighbors(l): D.add_edge(l, u, capacity=1)
    for u in nbrs: D.add_edge(u, "T", capacity=2)
    need = 2 * len(L) - 2
    R = maximum_flow(D, "S", "T")
    fv = R[0] if isinstance(R, tuple) else R.flow_value
    return fv < need, {"L_size": len(L), "flow": int(fv), "need": need}, L, independent

def hamilton_path(G, cap=SEARCH_CAP):
    """回溯+度排序剪枝。返回 (存在?, 找到解数[到上限], 起点尝试说明)。"""
    nodes = sorted(G.nodes, key=lambda v: G.degree(v), reverse=True)  # 从高度点起
    idx = {v: i for i, v in enumerate(nodes)}
    adj = {v: sorted(G.neighbors(v), key=lambda u: G.degree(u)) for v in G.nodes}
    count = 0; found_any = False
    def bt(path, used):
        nonlocal count, found_any
        if count >= cap: return True  # 停
        if len(path) == len(G.nodes):
            count += 1; found_any = True
            return count >= cap
        v = path[-1]
        for u in adj[v]:
            if u not in used:
                used.add(u); path.append(u)
                stop = bt(path, used)
                path.pop(); used.remove(u)
                if stop: return True
        return False
    for s0 in nodes[: min(8, len(nodes))]:
        if bt([s0], {s0}):
            break
    return found_any, count

results = {}
print("===== H 系列实算（判据冻结版）=====")
for n_t in LADDER:
    for th, tag in [(TH_MAIN, "main12"), (TH_LO, "sens4"), (TH_HI, "sens48")]:
        G, qs = build_graph(n_t, th)
        degs = sorted(dict(G.degree()).values())
        entry = {"n_towers": n_t, "threshold": th, "n_nodes": G.number_of_nodes(),
                 "n_edges": G.number_of_edges(), "connected": nx.is_connected(G),
                 "deg_min_max": [degs[0], degs[-1]], "avg_deg": round(np.mean(degs), 2)}
        if G.number_of_nodes() and nx.is_connected(G):
            killed, info, L, indep = capacity_kill(G)
            entry["capacity"] = {**info, "L_independent": bool(indep), "KILL": bool(killed)}
            lam = np.linalg.eigvalsh(nx.laplacian_matrix(G).toarray().astype(float))
            entry["lambda2"] = round(float(np.sort(lam)[1]), 4)
            if not killed:
                ok, cnt = hamilton_path(G)
                entry["hamilton"] = {"exists": ok, "count_capped": cnt, "cap": SEARCH_CAP}
            else:
                entry["hamilton"] = {"exists": None, "note": "定理A判死（H-KILL照记），不进回溯"}
        else:
            entry["capacity"] = None; entry["hamilton"] = {"exists": None, "note": "图不连通"}
        results[f"{n_t}t_th{th}"] = entry
        print(f"[{n_t}塔 th={th}] 点{entry['n_nodes']} 边{entry['n_edges']} 连通{entry['connected']} "
              f"λ2={entry.get('lambda2')} 容量={entry.get('capacity')} 哈密顿={entry.get('hamilton')}")

print("\n===== 判据记录 =====")
m30 = results["30t_th12"]
print(f"H-1 主档（30塔 th=12）：{m30['hamilton']}")
print(f"H-2 规模阶梯主档存在性：{[(k, results[k]['hamilton'].get('exists')) for k in ['10t_th12','20t_th12','30t_th12','40t_th12']]}")

out = {"script": "ta_tower_graph_hamilton-v1.0-20260927.py",
       "prereg": "塔交互三构想·预注册判据书-v1.0-20260927.md",
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "platform": platform.platform(), "results": results}
with open("results/ta_H_series_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("\n结果已写 results/ta_H_series_result-v1.0-20260927.json")
