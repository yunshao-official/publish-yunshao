# hp_ref_m4_grid4_observe v1.0 (2026-09-27)
# 判据依据：格四·成功路径轨迹形态学纯观测判据书-v1.0-20260927.md（先于本脚本落盘）
# 纯观测零干预：base口径（格一C'同款）解出后记录O-1~O-6；H-O1~H-O4预注册假设开票
import networkx as nx, json, time, sys, random
from pathlib import Path
from statistics import mean

sys.setrecursionlimit(20000)
SIZES = [100, 200]
SEEDS = list(range(42, 72))
BUDGET_S = {100: 1.5, 200: 2.5}
RESTARTS = 40
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

def solve_base(g, deadline):
    n = g.number_of_nodes()
    deg = dict(g.degree())
    neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (deg[u], u)) for v in g.nodes()}
    by_deg = sorted(g.nodes(), key=lambda v: (deg[v], v))
    starts = [by_deg[0], by_deg[1]] * (RESTARTS // 2)
    for s in starts:
        if time.time() > deadline:
            return None
        path = [s]; visited = {s}; steps = 0
        def rem(v):
            return sum(1 for u in g.neighbors(v) if u not in visited)
        def rec(cur):
            nonlocal steps
            if steps > DFS_BUDGET or time.time() > deadline:
                return False
            if len(path) == n:
                return True
            nbrs = sorted((u for u in neighbors_pre[cur] if u not in visited), key=rem)
            for u in nbrs:
                steps += 1
                visited.add(u); path.append(u)
                if rec(u):
                    return True
                path.pop(); visited.remove(u)
                if steps > DFS_BUDGET or time.time() > deadline:
                    return False
            return False
        if rec(s) and verify(g, path):
            return path
    return None

obs = []
t0 = time.time()
for N in SIZES:
    for seed in SEEDS:
        g = gen_ba_rebuild(N, 4, seed)
        deadline = time.time() + BUDGET_S[N]
        p = solve_base(g, deadline)
        if not p:
            obs.append({"N": N, "seed": seed, "solved": False})
            continue
        n = len(p); deg = dict(g.degree())
        pos = {v: i / (n - 1) for i, v in enumerate(p)}
        ql = [v for v in g.nodes() if deg[v] <= 3]
        ql_pos = [pos[v] for v in ql]
        # O-1/O-2 端偏：准叶在两端或端点相邻位（pos<=1/12 or >=11/12，n>=24时≈端点±1位）
        edge_zone = sum(1 for x in ql_pos if x <= 1 / 12 or x >= 1 - 1 / 12)
        endshare = edge_zone / len(ql_pos) if ql_pos else 0.0
        ends_ql = (deg[p[0]] <= 3) + (deg[p[-1]] <= 3)
        # O-3 聚束：路径序号间隔<=2 的准叶对占比
        idx = sorted(p.index(v) for v in ql)
        pairs = [(a, b) for a, b in zip(idx, idx[1:])]
        bunch = sum(1 for a, b in pairs if b - a <= 2) / len(pairs) if pairs else 0.0
        # O-4 消费时序：前50%段内准叶占比
        first_half = sum(1 for v in ql if p.index(v) < n // 2)
        cons_half = first_half / len(ql) if ql else 0.0
        # O-5 枢纽位置：top-5%高度顶点中段(0.25-0.75)占比
        hub = sorted(g.nodes(), key=lambda v: -deg[v])[:max(1, n // 20)]
        hub_mid = sum(1 for v in hub if 0.25 <= pos[v] <= 0.75) / len(hub)
        # O-6 Phi全轨迹（尾断口计入）
        phis = []
        gaps = 0
        for i in range(n):
            if i < n - 1 and not g.has_edge(p[i], p[i + 1]):
                gaps += 1
            phis.append(gaps * (1 if deg[p[i]] <= 3 else 0) + (1 if deg[p[i]] <= 3 else 0))
        obs.append({"N": N, "seed": seed, "solved": True, "ql_count": len(ql),
                    "ql_endshare": round(endshare, 3), "ends_quasileaf": ends_ql,
                    "ql_bunch": round(bunch, 3), "ql_conshalf": round(cons_half, 3),
                    "hub_mid": round(hub_mid, 3), "phi_last5": phis[-5:]})
        print(f"N={N} seed={seed} solved ql={len(ql)} endshare={endshare:.2f} conshalf={cons_half:.2f}", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_grid4_observe_results-v1.0-20260927.json"
out.write_text(json.dumps({"frozen_criteria": "格四·成功路径轨迹形态学纯观测判据书-v1.0-20260927.md",
                           "observations": obs}, ensure_ascii=False, indent=1), encoding="utf-8")
print("RESULTS_WRITTEN", len(obs), "总耗时 %.1fs" % (time.time() - t0))
