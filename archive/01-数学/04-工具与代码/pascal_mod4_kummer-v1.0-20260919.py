# -*- coding: utf-8 -*-
"""
代数册 R13：Pascal 三角 mod 4 结构（Granville/Kummer 语言）+ (Z₂)³ 骨架对照 [constants:v1.0]
=====================================================================
背景（第六轮立账·第七轮续 mod 8 细化）：杨辉三角（纯数空间生成基底）↔ Pascal 三角；
mod 2=Sierpinski（Lucas）；mod 4 周期结构对照 (Z₂)³ 三分量骨架。
方法：64×64 三角真算（N=64=2⁶ 与 M 对账）+ Kummer 进位定理交叉验证。
Kummer 定理：v₂(C(n,k)) = k 与 n−k 二进制相加的进位次数 c。
  → mod 2 零元 ⇔ c≥1；mod 4 零元 ⇔ c≥2（"二阶亏损"=双进位位形）。
"""
import json
from math import comb
from collections import Counter

N = 64
rows = [[comb(n, k) % 4 for k in range(n + 1)] for n in range(N)]
dist = Counter(x for r in rows for x in r)
total = sum(dist.values())

# mod 2 零元（奇偶）：Lucas —— C(n,k) 奇 ⇔ (k & ~n)==0
odd = sum(1 for n in range(N) for k in range(n + 1) if (k & ~n) == 0)
# Kummer 交叉验证：v₂(C(n,k)) = 进位数 c
def carries(n, k):
    a, b, c, carry = n, k, n - k, 0
    for _ in range(8):
        if (b & 1) + (c & 1) + carry > 1:
            carry = 1
        else:
            carry = 0
        a >>= 1; b >>= 1; c >>= 1
    return cnt  # placeholder

def kummer_carries(k, m):   # k + m 的二进制进位次数
    c = carry = 0
    while k or m:
        if (k & 1) + (m & 1) + carry > 1:
            c += 1; carry = 1
        else:
            carry = 0
        k >>= 1; m >>= 1
    return c

mismatch = 0
for n in range(N):
    for k in range(n + 1):
        v = kummer_carries(k, n - k)
        if (comb(n, k) % 4 == 0) != (v >= 2):
            mismatch += 1
        if (comb(n, k) % 2 == 0) != (v >= 1):
            mismatch += 1

# 每 n 行的 mod 4 零元比例 vs 进位≥2 比例（抽样行展示）
sample = {}
for n in [15, 31, 47, 63, 62, 55]:
    row = [comb(n, k) for k in range(n + 1)]
    sample[n] = {
        "mod4_zero_ratio": sum(1 for x in row if x % 4 == 0) / (n + 1),
        "mod2_zero_ratio": sum(1 for x in row if x % 2 == 0) / (n + 1),
        "kummer_ge2_ratio": sum(1 for k in range(n + 1)
                                if kummer_carries(k, n - k) >= 2) / (n + 1),
    }

out = {
    "N": N, "total_cells": total,
    "mod4_distribution": {str(k2): v for k2, v in sorted(dist.items())},
    "mod4_zero_share": dist[0] / total,
    "mod2_odd_count": odd, "mod2_odd_share": odd / total,
    "kummer_cross_check_mismatch": mismatch,
    "sample_rows": sample,
    "labels": "数值【复算一致】；对照【同构≠同一·立项不硬凑】；体系内部定义·未验证",
}
print(json.dumps(out, ensure_ascii=False, indent=2))
with open(r"H:/理论存档/01-数学/02-实验与数据/results/pascal_mod4_kummer_result-v1.0-20260919.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
