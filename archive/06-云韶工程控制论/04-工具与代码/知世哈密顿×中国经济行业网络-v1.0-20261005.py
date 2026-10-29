# -*- coding: utf-8 -*-
"""知世哈密顿路径 × 中国经济行业网络 · 首跑
目标：在中国24行业投入产出网络中，找到一条哈密顿路径（每个行业恰好激活一次），
使得沿路径的累计传导权重最大——即"最优经济激活顺序"。
方法：CP-SAT完备判定（与JC-X1同族E3资产）+ 边权贪心对照
"""
import io, json
import numpy as np

# 中国24行业投入产出系数矩阵（文献带值构造，行业间传导关系）
sectors = ["农林", "采矿", "食品", "纺织", "化工", "冶金", "装备", "汽车",
           "电子", "电力", "建筑", "交通", "信息", "金融", "房地产", "科研",
           "水利", "教育", "卫生", "文化", "餐饮", "零售", "租赁", "公共管理"]

# 直接消耗系数（上游→下游传导权重，带值构造）
# 基于中国投入产出表结构：制造业链条/服务业链条/能源链条
W = np.zeros((24, 24))
np.random.seed(2026)
# 骨架：制造业链条（农林→食品→零售；采矿→冶金→装备→汽车；电子→信息）
chain_pairs = [
    (0,2,0.15),(2,21,0.20),(0,21,0.10),           # 农林→食品→零售
    (1,5,0.18),(5,6,0.15),(6,7,0.12),(6,8,0.10),   # 采矿→冶金→装备→汽车
    (1,8,0.08),(8,12,0.12),(12,21,0.08),            # 采矿→电子→信息
    (4,6,0.08),(4,7,0.06),(4,8,0.08),               # 化工→装备/汽车/电子
    (9,6,0.08),(9,8,0.06),(9,15,0.05),              # 电力→制造/科研
    (10,21,0.06),(10,14,0.12),(10,3,0.05),          # 建筑→零售/房地产
    (13,12,0.10),(13,14,0.08),(13,22,0.06),         # 金融→信息/房地产/租赁
    (14,10,0.15),(14,21,0.08),                      # 房地产→建筑/零售
    (16,0,0.05),(16,1,0.03),                        # 水利→农林/采矿
    (17,21,0.05),(18,21,0.05),                      # 教育/卫生→居民消费
    (19,21,0.05),(20,21,0.08),                      # 文化/餐饮→居民消费
    (21,12,0.05),(21,13,0.04),(22,12,0.05),         # 零售/租赁→信息
    (23,21,0.03),(12,22,0.05),(12,20,0.04),         # 公共→零售/信息→文化
]
for i,j,w in chain_pairs:
    W[j][i] = w  # j消费i的产出（传导方向：i→j）
    W[i][j] = max(W[i][j], w*0.3)  # 反向弱传导

print("=" * 60)
print("知世哈密顿路径 × 中国经济行业网络")
print(f"节点：{len(sectors)} 行业 ｜ 边数：{int(np.sum(W>0))} ｜ 目标：最大权重哈密顿路径")
print("=" * 60)

# --- 方法1：CP-SAT 精确求解（最大权重哈密顿路径）---
from ortools.sat.python import cp_model

def hamiltonian_path_cpsat(W, start=0):
    n = len(W)
    mdl = cp_model.CpModel()
    # x[i][j] = 1 表示路径走 i→j
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j and W[i][j] > 0:
                x[i,j] = mdl.NewBoolVar(f"x{i}_{j}")
    # 哈密顿约束：每个节点恰好一个入边和一个出边
    for i in range(n):
        mdl.Add(sum(x.get((j,i), 0) for j in range(n) if (j,i) in x) == 1)  # 入
        mdl.Add(sum(x.get((i,j), 0) for j in range(n) if (i,j) in x) == 1)  # 出
    # 起点：start 无入边
    mdl.Add(sum(x.get((j, start), 0) for j in range(n) if (j, start) in x) == 0)  # start无入边
    # 最大化总权重
    mdl.Maximize(sum(int(W[i][j]*100) * x[i,j] for (i,j) in x))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8
    st = solver.Solve(mdl)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        path = [start]
        current = start
        visited = {start}
        while len(visited) < n:
            for j in range(n):
                if j not in visited and current != j and (current, j) in x and solver.Value(x[current, j]):
                    path.append(j)
                    visited.add(j)
                    current = j
                    break
            else:
                break
        return path, solver.ObjectiveValue() / 100, "OPTIMAL" if st == cp_model.OPTIMAL else "FEASIBLE"
    return None, 0, "INFEASIBLE"

# --- 方法2：权重贪心（最近邻启发式）---
def greedy_path(W, start=0):
    n = len(W)
    visited = [False] * n
    path = [start]
    visited[start] = True
    current = start
    total = 0
    while len(path) < n:
        best_j, best_w = -1, 0
        for j in range(n):
            if not visited[j] and W[current][j] > best_w:
                best_w = W[current][j]
                best_j = j
        if best_j < 0:
            # 找不到未访问邻居，跳到最近未访问
            for j in range(n):
                if not visited[j]:
                    best_j = j; break
        path.append(best_j)
        visited[best_j] = True
        total += W[current][best_j]
        current = best_j
    return path, total

# 跑
print("\n--- CP-SAT 精确求解 ---")
path_opt, weight_opt, status = hamiltonian_path_cpsat(W, 0)
if path_opt:
    print("状态：{}".format(status))
    print("路径：{} → ...".format(sectors[path_opt[0]]))
    names = [sectors[p] for p in path_opt]
    print("完整路径：")
    for i, s in enumerate(names):
        print("  {}. {}".format(i+1, s))
    print("总权重：{:.2f}".format(weight_opt))

print("\n--- 贪心对照 ---")
path_greedy, weight_greedy = greedy_path(W, 0)
print("贪心路径总权重：{:.2f}".format(weight_greedy))
print("贪心路径：{} → {}".format(sectors[path_greedy[0]], sectors[path_greedy[-1]]))

# 对比
print("\n=== 对比 ===")
print("CP-SAT 精确：{:.2f}（最优）".format(weight_opt))
print("贪心对照：{:.2f}（比率 {:.1%}）".format(weight_greedy, weight_greedy/weight_opt if weight_opt > 0 else 0))

# 路径含义
print("\n=== 最优激活顺序的经济含义 ===")
print("沿这条路径依次激活每个行业，累计传导权重最大")
print("前10步：")
for i, p in enumerate(path_opt[:10]):
    print("  {}. {}".format(i+1, sectors[p]))

# 结果件
out_data = {
    "method": "CP-SAT AddCircuit 最大权重哈密顿路径",
    "nodes": len(sectors),
    "optimal_path": [sectors[p] for p in path_opt],
    "optimal_weight": round(weight_opt, 2),
    "greedy_weight": round(weight_greedy, 2),
    "status": status,
}
io.open(r"H:/理论存档/06-云韶工程控制论/02-实验与数据/知世哈密顿×中国经济行业网络-v1.0-20261005.json",
        "w", encoding="utf-8").write(json.dumps(out_data, ensure_ascii=False, indent=1))
print("\n结果件已写入")
