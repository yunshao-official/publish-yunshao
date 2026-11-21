# hp_ref_m4_scan v1.0 (2026-09-27)
# 预注册判据书：m4悬崖边界·参考实现扫描预注册判据书-v1.0-20260927.md（先于本脚本落盘）
# 口径：生成器=networkx.barabasi_albert_graph；求解器=参考实现（非体系正本工具）；结果语义=下界
# 臂A=单端动态度数Warnsdorff+有限回溯+重启（终点自由）
# 臂B=端点锚定（两端强制=图内度最小顶点，低度先占端点名额）+同款DFS
# 验证独立三关（甲）：长度=N ∧ 无重复 ∧ 每步真边
import networkx as nx, json, time, sys
from pathlib import Path

sys.setrecursionlimit(20000)
SIZES = [100, 200, 500, 1000]
SEEDS = [42, 43, 44, 45, 46]
BUDGET_S = {100: 5, 200: 5, 500: 5, 1000: 20}
RESTARTS = 200
DFS_BUDGET = 100000

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
        nbrs.sort(key=rem_deg)  # 动态Warnsdorff：剩余出路最少优先
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

def solve(g, arm, deadline):
    n = g.number_of_nodes()
    by_deg = sorted(g.nodes(), key=lambda v: (g.degree(v), v))
    neighbors_pre = {v: sorted(g.neighbors(v), key=lambda u: (g.degree(u), u)) for v in g.nodes()}
    if arm == "A":  # 起点=度升序轮换，终点自由
        starts = [by_deg[r % len(by_deg)] for r in range(RESTARTS)]
        ends = [None] * RESTARTS
    else:  # 臂B：两端锚定=两个最低度顶点，方向轮换
        e1, e2 = by_deg[0], by_deg[1] if n > 1 else by_deg[0]
        starts = [e1, e2] * (RESTARTS // 2)
        ends = [e2, e1] * (RESTARTS // 2)
    for s, e in zip(starts, ends):
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
        g = nx.barabasi_albert_graph(N, 4, seed=seed)
        deg_min = min(dict(g.degree()).values())
        for arm in ["A", "B"]:
            deadline = time.time() + BUDGET_S[N]
            t1 = time.time()
            p = solve(g, arm, deadline)
            dt = round(time.time() - t1, 3)
            solved = p is not None
            rec = {"N": N, "seed": seed, "arm": arm, "solved": solved,
                   "time_s": dt, "min_deg": deg_min,
                   "verified": bool(p) and verify(g, p)}
            results.append(rec)
            print(f"N={N} seed={seed} arm={arm} solved={solved} t={dt}s min_deg={deg_min}", flush=True)

out = Path(__file__).parent.parent / "02-实验与数据" / "m4_scan_results-v1.0-20260927.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"frozen_criteria": "m4悬崖边界·参考实现扫描预注册判据书-v1.0-20260927.md",
                           "generator": "networkx.barabasi_albert_graph(N,4,seed)",
                           "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")

# 汇总（判据J-A1/J-A2/J-B/J-C开票）
print("\n=== 汇总 ===")
for N in SIZES:
    row = {}
    for arm in ["A", "B"]:
        rs = [r for r in results if r["N"] == N and r["arm"] == arm]
        row[arm] = sum(r["solved"] for r in rs)
    print(f"N={N}: 臂A {row['A']}/5, 臂B {row['B']}/5")
print(f"总耗时 {round(time.time()-t0,1)}s")
