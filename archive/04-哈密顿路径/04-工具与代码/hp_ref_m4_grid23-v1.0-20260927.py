# hp_ref_m4_grid23 v1.0 (2026-09-27)
# 判据依据：m4攻坚·格二格三合并判据书-v1.0-20260927.md（先于本脚本落盘）
# 格二(S组)：死区预防评分=Warnsdorff排序键追加低度邻占度次级评分（只排序不焊死）
# 格三(F组)：Φ引导回溯=扩展前Φ预估剪枝（排序层干预，无替代时放行保完备性）
# Φ定义=判据书§三（准叶deg<=3；断口端点归因；尾断口计入）
# 参数=§六：RESTARTS=40, DFS_BUDGET=100000, 预算1.5s/2.5s, seeds42..71
import networkx as nx, json, time, sys, random
from pathlib import Path

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

def phi(path, g):  # 判据书§三冻结定义
    gaps = [(a, b) for a, b in zip(path, path[1:]) if not g.has_edge(a, b)]
    if path:
        gaps.append((path[-1], None))
    s = 0
    for a, b in gaps:
        if g.degree(a) <= 3:
            s += 1
        if b is not None and g.degree(b) <= 3:
            s += 1
    return s

def make_solver(mode):
    # mode: "base"=格一C'口径基线 / "S"=死区预防评分 / "F"=Φ引导回溯 / "SF"=两者叠加
    def solve(g, deadline):
        n = g.number_of_nodes()
        deg = dict(g.degree())
        neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (deg[u], u)) for v in g.nodes()}
        by_deg = sorted(g.nodes(), key=lambda v: (deg[v], v))
        e1, e2 = by_deg[0], by_deg[1]
        starts = [e1, e2] * (RESTARTS // 2)  # C'口径：2低度起点+终点自由
        phi_trace = []
        for s in starts:
            if time.time() > deadline:
                return None, phi_trace
            path = [s]; visited = {s}; steps = 0
            def rem(v):
                return sum(1 for u in g.neighbors(v) if u not in visited)
            def low_frac(u):  # 格二死区风险分：u的未访问邻居中低度顶点占比
                un = [w for w in g.neighbors(u) if w not in visited]
                if not un:
                    return 1.0
                return sum(1 for w in un if deg[w] <= 3) / len(un)
            def cand_sort(cur, nxt_list):
                if mode in ("S", "SF"):
                    return sorted(nxt_list, key=lambda u: (rem(u), low_frac(u), deg[u]))
                return sorted(nxt_list, key=rem)
            def phi_preview(u):  # 格三：扩展u后的Φ增量预估（u若是准叶且为当前端点，断口计1）
                inc = 1 if deg[u] <= 3 else 0
                return inc
            def rec(cur):
                nonlocal steps
                if steps > DFS_BUDGET or time.time() > deadline:
                    return False
                if len(path) == n:
                    return True
                nbrs = [u for u in neighbors_pre[cur] if u not in visited]
                nbrs = cand_sort(cur, nbrs)
                if mode in ("F", "SF") and len(nbrs) > 1:
                    # Φ引导：Φ不增的分支优先（排序层，不删分支）
                    nbrs = sorted(nbrs, key=lambda u: phi_preview(u))
                for u in nbrs:
                    steps += 1
                    visited.add(u); path.append(u)
                    if rec(u):
                        return True
                    path.pop(); visited.remove(u)
                    if steps > DFS_BUDGET or time.time() > deadline:
                        return False
                return False
            ok = rec(s)
            if ok and verify(g, path):
                phi_trace = [phi(path[:i+1], g) for i in (0, len(path)//2, len(path)-1)]
                return path, phi_trace
        return None, phi_trace
    return solve

ARMS = {"base": make_solver("base"), "S": make_solver("S"), "F": make_solver("F"), "SF": make_solver("SF")}
results = []
t0 = time.time()
for N in SIZES:
    for seed in SEEDS:
        g = gen_ba_rebuild(N, 4, seed)
        for arm, solver in ARMS.items():
            deadline = time.time() + BUDGET_S[N]
            t1 = time.time()
            p, tr = solver(g, deadline)
            dt = round(time.time() - t1, 3)
            results.append({"N": N, "seed": seed, "arm": arm, "solved": p is not None,
                            "time_s": dt, "verified": bool(p) and verify(g, p),
                            "phi_final": tr[-1] if tr else None})
        print(f"N={N} seed={seed} done", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_grid23_results-v1.0-20260927.json"
out.write_text(json.dumps({"frozen_criteria": "m4攻坚·格二格三合并判据书-v1.0-20260927.md",
                           "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
print("RESULTS_WRITTEN", len(results))
print("总耗时 %.1fs" % (time.time() - t0))
