# -*- coding: utf-8 -*-
"""√D定律复现：连续单次运动，逐自由度硬算(L1折线) vs 全身协同(L2测地直线)
论文表1数据（20万样本，D=2~256）：
  推导：Δ~U(0,1) iid → E[L1]=D/2, E[L2]=√(D/3) → R(D)=(√3/2)√D≈0.866√D
运行：python randwalk_vs_geodesic.py
"""
import numpy as np

rng = np.random.default_rng(42)
Ds = [2, 4, 8, 16, 32, 64, 128, 256]
N_SAMPLES = 200_000

print("自由度D | 逐自由度(玩具L1) | 全身协同(类人L2) | 浪费倍数R(D) | 理论(√3/2)√D | 偏差%")
rows = []
for D in Ds:
    delta = rng.uniform(0, 1, size=(N_SAMPLES, D))
    l1 = np.abs(delta).sum(axis=1)          # 玩具：坐标轴对齐折线（一次动一个关节）
    l2 = np.sqrt((delta ** 2).sum(axis=1))  # 类人：全身协同（测地直线）
    ratio = (l1 / l2).mean()
    th = (np.sqrt(3) / 2) * np.sqrt(D)
    dev = abs(ratio - th) / th * 100
    rows.append((D, ratio, th, dev))
    print(f"{D:>6} | {l1.mean():>14.3f} | {l2.mean():>14.3f} | {ratio:>10.3f} | {th:>14.3f} | {dev:.1f}%")

import json
with open(r"D:\data\scratch\sqrtd_result.json", "w", encoding="utf-8") as f:
    json.dump([{"D": d, "ratio": round(r, 3), "theory": round(t, 3), "dev_pct": round(v, 1)} for d, r, t, v in rows], f)
print("saved json")

# 图（可选）
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    Dth = np.linspace(1, 260, 200)
    plt.figure(figsize=(7, 5))
    plt.plot([r[0] for r in rows], [r[1] for r in rows], "o-", label="实测 R(D)（20万样本）")
    plt.plot(Dth, (np.sqrt(3)/2) * np.sqrt(Dth), "--", label="理论 (√3/2)·√D")
    plt.xlabel("自由度 D"); plt.ylabel("路径浪费倍数 R(D)")
    plt.title("维度错位：逐自由度硬算 vs 全身协同")
    plt.legend(); plt.grid(alpha=0.3)
    plt.savefig(r"D:\data\scratch\sqrtd_law.png", dpi=110, bbox_inches="tight")
    print("saved png")
except Exception as e:
    print("png skip:", e)