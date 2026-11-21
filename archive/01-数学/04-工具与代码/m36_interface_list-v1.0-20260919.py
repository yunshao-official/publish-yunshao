# -*- coding: utf-8 -*-
"""
G-E2 界面 36 行列表完备化 + 机器验证（第十二轮 R12 附件）[constants:v1.0]
=====================================================================
口径：0912 环面管重建稿（分裂型规范排布·H₁ 只依赖 (m=36, b=6)，排布为提案）。
任务：显式 36 行列表（管号/端点对/斜率/层归属）+五条机器验证+排布配比算术检验。
发现预告：重建稿提案"层间 L1-L2 8 / L2-L3 8 / L1-L3 2"与每 S³ 恰 6 管足的定义
可能算术不自洽（足数按层分配 10/16/10 → L1 每 S³ 2.5 足非整数）——真跑裁决。
"""
import json
import sympy
from itertools import combinations
from sympy import Matrix
from sympy.matrices.normalforms import smith_normal_form

# ---------- 构造修正案列表（层内 18 + 层间 6/6/6；中层 L2 六棱全 2-重） ----------
balls = {1: [1, 2, 3, 4], 2: [5, 6, 7, 8], 3: [9, 10, 11, 12]}   # 层 -> S³ 编号
layer_of = {b: L for L, bs in balls.items() for b in bs}
pipes = []
for L, bs in balls.items():
    kind = 2 if L == 2 else 0                                     # 中层 K₄ 六棱全 2-重
    for a, b in combinations(bs, 2):
        pipes.append({"id": f"P{len(pipes)+1:02d}", "ends": (a, b),
                      "p": kind, "scope": f"L{L}层内"})
# 层间：每 S³ 恰 3 层间足（配比 6/6/6，硬编码均衡匹配；手工验算每球 3 足）
# L1 需求 a=(1,1,2,2)@L1-L2 + y=(2,2,1,1)@L1-L3；L2 需求 b=(1,1,2,2)+c=(2,2,1,1)；L3 同构
INTER = [  # (L1-L2 6管)
    ((1, 5), "L1-L2层间"), ((2, 6), "L1-L2层间"), ((3, 7), "L1-L2层间"),
    ((3, 8), "L1-L2层间"), ((4, 7), "L1-L2层间"), ((4, 8), "L1-L2层间"),
    # (L2-L3 6管)
    ((5, 11), "L2-L3层间"), ((5, 12), "L2-L3层间"), ((6, 11), "L2-L3层间"),
    ((6, 12), "L2-L3层间"), ((7, 9), "L2-L3层间"), ((8, 10), "L2-L3层间"),
    # (L1-L3 6管)
    ((1, 9), "L1-L3层间"), ((1, 10), "L1-L3层间"), ((2, 9), "L1-L3层间"),
    ((2, 10), "L1-L3层间"), ((3, 11), "L1-L3层间"), ((4, 12), "L1-L3层间"),
]
for ends, scope in INTER:
    pipes.append({"id": f"P{len(pipes)+1:02d}", "ends": ends, "p": 0, "scope": scope})

# ---------- 五条验证 ----------
from collections import Counter
foot_cnt = Counter()
for pp in pipes:
    foot_cnt[pp["ends"][0]] += 1; foot_cnt[pp["ends"][1]] += 1
checks = {
    "V1_m36": len(pipes) == 36,
    "V2_every_S3_six_feet": all(foot_cnt[b] == 6 for b in layer_of),
    "V3_no_self_loop": all(a != b for pp in pipes for a, b in [pp["ends"]]),
    "V4_b6_two_fold": sum(1 for pp in pipes if pp["p"] == 2) == 6,
    "V5中层六棱全2重": all(pp["p"] == 2 for pp in pipes if "L2层内" in pp["scope"]),
}
# 管图连通性（并查集）
par = {b: b for b in layer_of}
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for pp in pipes:
    a, b = pp["ends"]; par[find(a)] = find(b)
checks["V6_graph_connected"] = len({find(b) for b in layer_of}) == 1

# ---------- 关系矩阵 Smith 复算（6×36：2-重管对角 2，斜率 0 管零列） ----------
rel = [[0]*36 for _ in range(6)]
two_idx = [i for i, pp in enumerate(pipes) if pp["p"] == 2]
for r, i in enumerate(two_idx):
    rel[r][i] = 2
S = smith_normal_form(Matrix(rel), domain=sympy.ZZ)
inv = [S[i, i] for i in range(min(S.rows, S.cols)) if S[i, i] != 0]
checks["V7_smith_inv"] = [int(x) for x in inv] == [2]*6
checks["V8_beta1_30"] = 36 - len(inv) == 30

# ---------- 排布配比算术检验（重建稿原提案 8/8/2） ----------
a, c, b_ = 8, 8, 2   # L1-L2 8 / L2-L3 8 / L1-L3 2
feet_L1 = a + b_; feet_L2 = a + c; feet_L3 = c + b_
per_ball = {"L1": feet_L1 / 4, "L2": feet_L2 / 4, "L3": feet_L3 / 4}
arith = {"feet_by_layer": {"L1": feet_L1, "L2": feet_L2, "L3": feet_L3},
         "per_S3_interlayer_feet": per_ball,
         "all_integer": all(v == int(v) for v in per_ball.values()),
         "verdict": "不自洽" if not all(v == int(v) for v in per_ball.values()) else "自洽"}

out = {"checks": checks, "arith_8_8_2": arith,
       "pipes_36": [{"id": pp["id"], "ends": list(pp["ends"]), "p": pp["p"],
                     "scope": pp["scope"]} for pp in pipes],
       "labels": "数值【复算一致】；排布=提案（分裂型下不影响 H₁ 定理内容）"}
print(json.dumps({"checks": checks, "arith_8_8_2": arith}, ensure_ascii=False, indent=2))
with open(r"H:/理论存档/01-数学/02-实验与数据/results/m36_interface_list_result-v1.0-20260919.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
