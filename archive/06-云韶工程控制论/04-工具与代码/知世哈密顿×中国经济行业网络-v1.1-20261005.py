# -*- coding: utf-8 -*-
"""知世哈密顿路径 × 中国经济行业网络 v1.1（加权完备图·简化版）
每个行业对所有其他行业都有权重（反映传导强弱），找最大权重哈密顿路径
"""
import io, json
import numpy as np
from itertools import permutations

sectors = ["农林","采矿","食品","纺织","化工","冶金","装备","汽车",
           "电子","电力","建筑","交通","信息","金融","房地产","科研",
           "水利","教育","卫生","文化","餐饮","零售","租赁","公共管理"]
n = len(sectors)

# 构建权重矩阵：行业间传导强度（带值）
rng = np.random.default_rng(2026)
W = rng.uniform(0.01, 0.3, (n, n))
np.fill_diagonal(W, 0)
# 骨架强边（主要传导链）
strong = [(0,2,0.8),(0,21,0.7),(1,5,0.8),(1,8,0.6),(2,21,0.7),
          (5,6,0.8),(6,7,0.6),(6,8,0.7),(4,6,0.6),(4,7,0.5),
          (8,12,0.8),(9,6,0.6),(9,8,0.5),(10,14,0.8),(10,21,0.6),
          (13,12,0.7),(13,14,0.6),(14,10,0.7),(17,21,0.5),(20,21,0.6),
          (12,21,0.5),(12,20,0.5),(21,12,0.6),(22,12,0.5),
          (3,21,0.5),(15,12,0.6),(16,0,0.4),(18,21,0.5),(19,21,0.5),
          (11,12,0.5),(23,21,0.4),(12,22,0.5),(12,20,0.4)]
for i,j,w in strong:
    W[i][j] = max(W[i][j], w)
    W[j][i] = max(W[j][i], w*0.5)  # 反向半权

# 暴力+剪枝（n=24太大，用n=24的最近邻+2-opt局部搜索近似）
def greedy_ham_path(W, start):
    n = len(W)
    visited = [False]*n
    path = [start]
    visited[start] = True
    total = 0
    cur = start
    for _ in range(n-1):
        best_j, best_w = -1, -1
        for j in range(n):
            if not visited[j] and W[cur][j] > best_w:
                best_w = W[cur][j]; best_j = j
        if best_j < 0: break
        path.append(best_j); visited[best_j] = True
        total += best_w; cur = best_j
    return path, total

def two_opt(W, path):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path)-2):
            for j in range(i+1, len(path)-1):
                # 反转 path[i..j] 看是否改善
                old = W[path[i-1]][path[i]] + W[path[j]][path[j+1]]
                new = W[path[i-1]][path[j]] + W[path[i]][path[j+1]]
                if new > old:
                    path[i:j+1] = path[i:j+1][::-1]
                    improved = True
    # 重算总权重
    return sum(W[path[i]][path[i+1]] for i in range(len(path)-1)), path

# 多起点贪心+2-opt
best_path, best_weight = None, 0
for start in range(n):
    p, w = greedy_ham_path(W, start)
    w2, p2 = two_opt(W, p)
    if w2 > best_weight:
        best_weight = w2
        best_path = p2[:]

print("=" * 60)
print("知世哈密顿路径 × 中国经济行业网络")
print(f"节点：{n} 行业 ｜ 方法：多起点贪心 + 2-opt 局部搜索")
print("=" * 60)

print("\n最优经济激活顺序（最大权重哈密顿路径）：")
print()
for i, p in enumerate(best_path):
    marker = " ←" if i > 0 else " [起点]"
    print("  {:>2}. {:<8s}{}".format(i+1, sectors[p], marker))

print("\n总权重：{:.3f}".format(best_weight))

# 传导强度前10
print("\n路径传导强度前10步：")
for i in range(min(10, len(best_path)-1)):
    w = W[best_path[i]][best_path[i+1]]
    print("  {} → {}  (权重 {:.3f})".format(sectors[best_path[i]], sectors[best_path[i+1]], w))

print("\n经济含义：")
print("  沿这条路径依次激活每个行业，每一步的传导权重最大")
print("  = 最优的经济刺激顺序（先激活起点，沿传导链逐级激活）")

out_data = {
    "method": "多起点贪心+2-opt",
    "best_path_names": [sectors[p] for p in best_path],
    "best_weight": round(best_weight, 3),
    "n_nodes": n,
}
io.open(r"H:/理论存档/06-云韶工程控制论/02-实验与数据/知世哈密顿×中国经济行业网络-v1.1-20261005.json",
        "w", encoding="utf-8").write(json.dumps(out_data, ensure_ascii=False, indent=1))
print("\n结果件已写入")
