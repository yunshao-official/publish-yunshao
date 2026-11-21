# hp_ref_m4_grid5 v1.0 (2026-09-27)
# 判据依据：格五·韧度证词与预算分配判据书-v1.0-20260927.md（先于本脚本落盘）
# T组：韧度证词搜索（低度闭邻域贪心+度带割集；c(G-S)>|S|=判死证人）
# B组：预算分配四档（等时2.5s，N=200）  P组：晚枢纽显式序（高风险）
import networkx as nx, json, time, sys, random
from pathlib import Path

sys.setrecursionlimit(20000)
SEEDS = list(range(42, 72))
DFS_BUDGET = 100000

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

def verify(g, path):
    n = g.number_of_nodes()
    if len(path) != n or len(set(path)) != n:
        return False
    return all(g.has_edge(a, b) for a, b in zip(path, path[1:]))

def toughness_witness(g):
    n = g.number_of_nodes()
    deg = dict(g.degree())
    by_deg = sorted(g.nodes(), key=lambda v: (deg[v], v))
    best = None  # (c-|S|, |S|, c, kind)
    cands = []
    for k in range(1, 11):
        S = set(by_deg[:k])
        for v in by_deg[:k]:
            S |= set(g.neighbors(v))
        cands.append((S, f"lowdeg{k}-closedNbr"))
    for lo, hi in [(0, 5), (5, 12), (0, 12)]:  # 度带割集
        S = {v for v in g.nodes() if deg[v] <= hi}
        cands.append((S, f"degband<={hi}"))
    for S, kind in cands:
        if not S or len(S) >= n - 1:
            continue
        rest = set(g.nodes()) - S
        c = nx.number_connected_components(g.subgraph(rest)) if rest else 0
        if c > len(S):
            d = c - len(S)
            if best is None or d > best[0]:
                best = (d, len(S), c, kind)
    return best

def solve(g, deadline, restarts, dfs_budget, late_global=False):
    n = g.number_of_nodes()
    deg = dict(g.degree())
    neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (deg[u], u)) for v in g.nodes()}
    by_deg = sorted(g.nodes(), key=lambda v: (deg[v], v))
    starts = [by_deg[0], by_deg[1]] * (restarts // 2)
    for s in starts:
        if time.time() > deadline:
            return None
        path = [s]; visited = {s}; steps = 0
        def rem(v):
            return sum(1 for u in g.neighbors(v) if u not in visited)
        def rec(cur):
            nonlocal steps
            if steps > dfs_budget or time.time() > deadline:
                return False
            if len(path) == n:
                return True
            nbrs = [u for u in neighbors_pre[cur] if u not in visited]
            if late_global and len(path) >= int(n * 0.6):
                nbrs.sort(key=lambda u: (deg[u], rem(u)))  # 晚段全局度优先（P组）
            else:
                nbrs.sort(key=rem)
            for u in nbrs:
                steps += 1
                visited.add(u); path.append(u)
                if rec(u):
                    return True
                path.pop(); visited.remove(u)
                if steps > dfs_budget or time.time() > deadline:
                    return False
            return False
        if rec(s) and verify(g, path):
            return path
    return None

res = {"T": [], "B": [], "P": []}
t0 = time.time()
# T组：60实例韧度证词
for N in [100, 200]:
    for seed in SEEDS:
        g = gen_ba_rebuild(N, 4, seed)
        w = toughness_witness(g)
        res["T"].append({"N": N, "seed": seed, "witness": w is not None,
                         "detail": w and {"c_minus_S": w[0], "S": w[1], "c": w[2], "kind": w[3]}})
wt = sum(1 for r in res["T"] if r["witness"])
print(f"T组: 证人 {wt}/60", flush=True)

# B组：预算四档 N=200
for arm, (rs, db) in {"B1": (40, 100000), "B2": (80, 50000), "B3": (160, 25000), "B4": (20, 200000)}.items():
    solved = 0
    for seed in SEEDS:
        g = gen_ba_rebuild(200, 4, seed)
        p = solve(g, time.time() + 2.5, rs, db)
        solved += p is not None
    res["B"].append({"arm": arm, "restarts": rs, "dfs_budget": db, "solved": solved})
    print(f"B组 {arm} (rs={rs},db={db}): {solved}/30", flush=True)

# P组：晚枢纽显式序 N=100
for arm in ["base", "P"]:
    solved = 0
    for seed in SEEDS:
        g = gen_ba_rebuild(100, 4, seed)
        p = solve(g, time.time() + 1.5, 40, DFS_BUDGET, late_global=(arm == "P"))
        solved += p is not None
    res["P"].append({"arm": arm, "solved": solved})
    print(f"P组 {arm}: {solved}/30", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_grid5_results-v1.0-20260927.json"
out.write_text(json.dumps({"frozen_criteria": "格五·韧度证词与预算分配判据书-v1.0-20260927.md",
                           "results": res}, ensure_ascii=False, indent=1), encoding="utf-8")
print("RESULTS_WRITTEN 总耗时 %.1fs" % (time.time() - t0))
