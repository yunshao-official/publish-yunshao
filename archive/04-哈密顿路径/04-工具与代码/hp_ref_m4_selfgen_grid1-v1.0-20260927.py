# hp_ref_m4_selfgen_grid1 v1.0 (2026-09-27)
# 判据依据：m4悬崖边界·参考实现扫描预注册判据书-v1.2-20260927.md §九（G组，先于本脚本落盘）
# 自研 gen_ba 口径重建：初始 K_m；新节点 m 次独立度加权抽样、重复跳过无重试 → 产生 deg<m 顶点（准叶）
# 四臂：A'(多起点终点自由,背景参考) / B'(2低度起点+终点锚定最低度) / C'(2低度起点+终点自由) / D(2低度起点+终点固定随机r)
# 参数全部=判据书§九.五：RESTARTS=40, DFS_BUDGET=100000, 预算 N=100:1.5s / N=200:2.5s, seeds 42..71
import networkx as nx, json, time, sys, random
from pathlib import Path

sys.setrecursionlimit(20000)
SIZES = [100, 200]
SEEDS = list(range(42, 72))          # 30 个
BUDGET_S = {100: 1.5, 200: 2.5}
RESTARTS = 40
DFS_BUDGET = 100000

def gen_ba_rebuild(N, m, seed):
    rng = random.Random(seed)
    g = nx.complete_graph(m)
    g = nx.Graph(g)  # 简单图
    for u in range(m, N):
        nodes = list(g.nodes())
        weights = [g.degree(v) + 0.5 for v in nodes]  # +0.5 防全零度起步（K_m 无零度，保守）
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

def verify(g, path):
    n = g.number_of_nodes()
    if len(path) != n or len(set(path)) != n:
        return False
    return all(g.has_edge(a, b) for a, b in zip(path, path[1:]))

def dfs(g, start, end, deadline, neighbors_pre):
    n = g.number_of_nodes()
    path = [start]; visited = {start}
    steps = 0
    def rem_deg(v):
        return sum(1 for u in g.neighbors(v) if u not in visited)
    def rec(cur):
        nonlocal steps
        if steps > DFS_BUDGET or time.time() > deadline:
            return False
        if len(path) == n:
            return end is None or cur == end
        nbrs = [u for u in neighbors_pre[cur] if u not in visited]
        nbrs.sort(key=rem_deg)
        for u in nbrs:
            steps += 1
            visited.add(u); path.append(u)
            if rec(u):
                return True
            path.pop(); visited.remove(u)
            if steps > DFS_BUDGET or time.time() > deadline:
                return False
        return False
    if rec(start):
        return path
    return None

def solve(g, arm, deadline, rand_end):
    n = g.number_of_nodes()
    by_deg = sorted(g.nodes(), key=lambda v: (g.degree(v), v))
    neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (g.degree(u), u)) for v in g.nodes()}
    e1, e2 = by_deg[0], (by_deg[1] if n > 1 else by_deg[0])
    if arm == "A'":
        starts = [by_deg[r % len(by_deg)] for r in range(RESTARTS)]
        ends = [None] * RESTARTS
    else:
        starts = [e1, e2] * (RESTARTS // 2)
        if arm == "B'":
            ends = [e2, e1] * (RESTARTS // 2)
        elif arm == "C'":
            ends = [None] * RESTARTS
        else:  # D：终点固定随机 r（≠两起点）
            r = rand_end
            ends = [r] * RESTARTS
    for s, e in zip(starts, ends):
        if e is not None and (e == s):
            continue
        if time.time() > deadline:
            return None
        p = dfs(g, s, e, deadline, neighbors_pre)
        if p and verify(g, p):
            return p
    return None

results = []
t0 = time.time()
for N in SIZES:
    for seed in SEEDS:
        g = gen_ba_rebuild(N, 4, seed)
        degs = dict(g.degree())
        quasi_leaf = sum(1 for v in g.nodes() if degs[v] < 4)
        min_deg = min(degs.values())
        rand_end = seed % N  # seed 决定的固定随机终点（≠由度排序选出的两起点大概率成立）
        for arm in ["B'", "C'", "D", "A'"]:
            deadline = time.time() + BUDGET_S[N]
            t1 = time.time()
            p = solve(g, arm, deadline, rand_end)
            dt = round(time.time() - t1, 3)
            results.append({"N": N, "seed": seed, "arm": arm, "solved": p is not None,
                            "time_s": dt, "min_deg": min_deg, "quasi_leaf": quasi_leaf,
                            "verified": bool(p) and verify(g, p)})
        print(f"N={N} seed={seed} min_deg={min_deg} quasi_leaf={quasi_leaf}", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_selfgen_grid1_results-v1.0-20260927.json"
out.write_text(json.dumps({"frozen_criteria": "m4悬崖边界·参考实现扫描预注册判据书-v1.2-20260927.md §九",
                           "generator": "gen_ba_rebuild(K_4 start, m-fold degree-weighted sampling, no-retry)",
                           "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n=== G组开票素材（解出数/30）===")
for N in SIZES:
    row = {}
    for arm in ["A'", "B'", "C'", "D"]:
        rs = [r for r in results if r["N"] == N and r["arm"] == arm]
        row[arm] = sum(r["solved"] for r in rs)
    ql = [r["quasi_leaf"] for r in results if r["N"] == N and r["arm"] == "A'"]
    md = min(dict(gen_ba_rebuild(N, 4, SEEDS[0])).degree().values())
    print("N=%d: B' %d/30, C' %d/30, D %d/30, A'(参考) %d/30 | 准叶均值 %.1f/%d, min_deg(seed42)=%d"
          % (N, row["B'"], row["C'"], row["D"], row["A'"], sum(ql)/len(ql), N, md))
print("总耗时 %.1fs" % (time.time() - t0))
