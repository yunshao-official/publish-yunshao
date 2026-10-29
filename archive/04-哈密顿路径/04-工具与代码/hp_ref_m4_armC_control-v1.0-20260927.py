# hp_ref_m4_armC_control v1.0 (2026-09-27)
# 判据依据：攻防修正·臂C对照判据补录-v1.0-20260927.md（先于本脚本落盘）
# 臂C = 起点固定两个最低度顶点轮换（与臂B同款）+ 终点自由（与臂A同款）——拆分"多样性坍缩"与"终点锚定"两变量
# 口径同原实验：networkx.barabasi_albert_graph / DFS确定 / 验证三关甲 / 下界语义
import networkx as nx, json, time, sys
from pathlib import Path

sys.setrecursionlimit(20000)
SIZES = [100, 200]
SEEDS = [42, 43, 44, 45, 46]
BUDGET_S = {100: 5, 200: 5}
RESTARTS = 200
DFS_BUDGET = 100000

def verify(g, path):
    n = g.number_of_nodes()
    if len(path) != n or len(set(path)) != n:
        return False
    return all(g.has_edge(a, b) for a, b in zip(path, path[1:]))

def dfs(g, start, deadline, neighbors_pre):
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
            return True  # 终点自由（臂C语义）
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

def solve_armC(g, deadline):
    by_deg = sorted(g.nodes(), key=lambda v: (g.degree(v), v))
    e1, e2 = by_deg[0], by_deg[1]
    neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (g.degree(u), u)) for v in g.nodes()}
    starts = [e1, e2] * (RESTARTS // 2)  # 与臂B同款起点轮换（独立性受限已如实冻结）
    for s in starts:
        if time.time() > deadline:
            return None
        p = dfs(g, s, deadline, neighbors_pre)
        if p and verify(g, p):
            return p
    return None

results = []
t0 = time.time()
for N in SIZES:
    for seed in SEEDS:
        g = nx.barabasi_albert_graph(N, 4, seed=seed)
        deadline = time.time() + BUDGET_S[N]
        t1 = time.time()
        p = solve_armC(g, deadline)
        dt = round(time.time() - t1, 3)
        solved = p is not None
        results.append({"N": N, "seed": seed, "arm": "C", "solved": solved, "time_s": dt,
                        "verified": bool(p) and verify(g, p)})
        print(f"N={N} seed={seed} arm=C solved={solved} t={dt}s", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_armC_control_results-v1.0-20260927.json"
out.write_text(json.dumps({"frozen_criteria": "攻防修正·臂C对照判据补录-v1.0-20260927.md",
                           "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n=== 臂C对照开票 ===")
for N in SIZES:
    rs = [r for r in results if r["N"] == N]
    print(f"N={N}: 臂C {sum(r['solved'] for r in rs)}/5")
print(f"总耗时 {round(time.time()-t0,1)}s")
