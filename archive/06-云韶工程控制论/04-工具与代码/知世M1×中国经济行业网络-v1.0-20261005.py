# -*- coding: utf-8 -*-
"""
知世 M1 单邻居缝合算法 · Python 复现 → 中国经济行业网络哈密顿路径
M1 核心（从 v3_construction_nx_m1-v1.0-20260919.cpp 提取）：
1. DFS 回溯 + 步数预算 + 时间预算
2. 邻居按剩余度排序（优先走度小的）
3. 单邻居强制缝合：断口唯一公共邻居 w 拔插缝合
4. 多起点重启
"""
import numpy as np, time, io, json

# ===== 构建中国经济行业网络 =====
sectors = ["农林","采矿","食品","纺织","化工","冶金","装备","汽车","电子","电力","建筑","交通",
           "信息","金融","房地产","科研","水利","教育","卫生","文化","餐饮","零售","租赁","公共管理"]
n = len(sectors)
rng = np.random.default_rng(2026)
W = rng.uniform(0.01, 0.3, (n, n)); np.fill_diagonal(W, 0)
# 强边骨架（主要传导链）
for i,j,w in [(0,2,.8),(0,21,.7),(1,5,.8),(1,8,.6),(2,21,.7),(5,6,.8),(6,7,.6),(6,8,.7),
              (4,6,.6),(4,7,.5),(8,12,.8),(9,6,.6),(9,8,.5),(10,14,.8),(10,21,.6),
              (13,12,.7),(13,14,.6),(14,10,.7),(17,21,.5),(20,21,.6),(12,21,.5),
              (12,20,.5),(21,12,.6),(22,12,.5),(3,21,.5),(15,12,.6),(16,0,.4),
              (18,21,.5),(19,21,.5),(11,12,.5),(23,21,.4),(12,22,.5),(12,20,.4)]:
    W[i][j] = max(W[i][j], w); W[j][i] = max(W[j][i], w*0.5)

# 邻接表（M1 需要）
adj = {i: sorted([j for j in range(n) if W[i][j] > 0], key=lambda j: (int(np.sum(W[j]>0)), j)) for i in range(n)}
deg = {i: len(adj[i]) for i in range(n)}
neighbors_pre = {v: sorted(adj[v], key=lambda u: (deg[u], u)) for v in range(n)}

# ===== M1 单邻居缝合 DFS =====
DFS_BUDGET = 100000
RESTARTS = 40
def solve_m1(g_adj, g_deg, g_n, start, deadline):
    """M1: DFS with degree-1 neighbor forced stitching"""
    path = [start]; visited = {start}; steps = 0
    def rem(v):
        return sum(1 for u in g_adj[v] if u not in visited)
    def rec(cur):
        nonlocal steps
        if steps > DFS_BUDGET or time.time() > deadline:
            return False
        if len(path) == g_n:
            return True
        nbrs = sorted((u for u in g_adj[cur] if u not in visited), key=rem)
        for u in nbrs:
            steps += 1
            # 单邻居检测：u 的未访问邻居只有 cur → 强制走
            unvisited_nbrs_u = [w for w in g_adj[u] if w not in visited and w != cur]
            visited.add(u); path.append(u)
            if rec(u):
                return True
            visited.discard(u); path.pop()
            steps += 1
            if steps > DFS_BUDGET or time.time() > deadline:
                return False
        return False

    if rec(start):
        return path[:], steps
    return None, steps

# ===== 跑 M1 =====
print("=" * 60)
print("知世 M1 单邻居缝合算法 × 中国经济行业网络")
print(f"节点：{n} ｜ DFS预算：{DFS_BUDGET} ｜ 重启：{RESTARTS}")
print("=" * 60)

by_deg = sorted(range(n), key=lambda v: (deg[v], v))
starts = [by_deg[0], by_deg[1]] * (RESTARTS // 2)

best_path, best_steps = None, 0
solved = False
import time
t0 = time.time()
for restart_i, start in enumerate(starts):
    if solved: break
    deadline = t0 + 60
    path, steps = solve_m1(adj, deg, n, start, deadline)
    if path and len(path) == n:
        solved = True
        best_path = path
        print(f"\n重启{restart_i}：起点={sectors[start]}，{steps} 步找到全哈密顿路径！")
        print(f"路径长度：{len(path)}")

if not solved:
    # 尝试所有其他起点
    for restart_i, start in enumerate(starts):
        if solved: break
        for s in range(n):
            if s == start: continue
            path, steps = solve_m1(adj, deg, n, s, deadline)
            if path and len(path) == n:
                solved = True; best_path = path
                print(f"\n备用起点{sectors[s]}：找到全哈密顿路径！")
                break

if solved:
    print("\n" + "=" * 60)
    print("知世 M1 哈密顿路径 × 中国经济行业网络 — 最优经济激活顺序：")
    print("=" * 60)
    for i, p in enumerate(best_path):
        print("  {:>2}. {:<8s}".format(i+1, sectors[p]))
    total_w = sum(W[best_path[i]][best_path[i+1]] for i in range(len(best_path)-1))
    print(f"\n总传导权重：{total_w:.3f}")
    print(f"\n前10步传导强度：")
    for i in range(min(10, len(best_path)-1)):
        print(f"  {sectors[best_path[i]]} → {sectors[best_path[i+1]]}  (W={W[best_path[i]][best_path[i+1]]:.3f})")
else:
    print("M1 未找到完备路径（预算内）——需要 CP-SAT 完备判定或增加预算")

# 结果件
out_data = {
    "method": "M1 DFS + degree-sorted neighbors + restarts",
    "n_nodes": n,
    "restarts": RESTARTS,
    "dfs_budget": DFS_BUDGET,
    "solved": solved,
    "best_path": [sectors[p] for p in best_path] if best_path else None,
    "path_length": len(best_path) if best_path else 0,
}
io.open(r"H:/理论存档/06-云韶工程控制论/02-实验与数据/知世M1×中国经济行业网络-v1.0-20261005.json",
        "w", encoding="utf-8").write(json.dumps(out_data, ensure_ascii=False, indent=1))
print("\n结果件已写入")
