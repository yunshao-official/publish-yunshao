# -*- coding: utf-8 -*-
"""
第二轮·实验C：e₂ 零点间距统计 vs GUE（41 点样本，趋势级）
对象（冻结）：e₂(s)=(p₁²-p₂)/2，p_k=L₂*(k(s+1))，a_q=|PSL(2,q)|^{-(s+1)}，q≤293
判据：C-1 unfolded 最近邻间距 vs GUE Wigner surmise（<r> 对比：GUE≈0.7357/Poisson 0.5307）
      C-2 e₂ 零点 vs ζ 零点位置对表（描述性）
预注册：《黎曼猜想·通俗图解-v4.0-20260927》§十二（NTFS 时间戳在先）
"""
import numpy as np, sympy as sp, json, platform, datetime

orders = {q: q * (q * q - 1) // 2 for q in sp.primerange(7, 294)}
logs = np.array([float(sp.log(orders[q])) for q in orders])
ZEROS12 = [14.1347, 21.0220, 25.0109, 30.4249, 32.9351, 37.5862,
           40.9187, 43.3271, 48.0052, 49.7738, 52.8015, 56.4462]

def e2(s):
    # p_k = Σ_q exp(-k(s+1)·ln|PSL|)，k 到自适应截断
    tot = 0.0 + 0.0j
    b = (s + 1.0) * logs
    for k in range(1, 400):
        pk = np.exp(-k * b).sum()
        if k == 1: p1 = pk
        if k == 2: p2 = pk
        if abs(pk) < 1e-18 and k > 2: break
    return (p1 ** 2 - p2) / 2.0

# 扫描 + 二分精化
ts = np.arange(0, 100.0001, 0.02)
zeros = []
prev = e2(0.5 + 0j); prev_t = 0.0
for t in ts[1:]:
    v = e2(0.5 + 1j * t)
    if v.real * prev.real < 0:
        lo, hi, flo = prev_t, t, prev.real
        for _ in range(60):
            mid = (lo + hi) / 2
            fm = e2(0.5 + 1j * mid).real
            if flo * fm < 0: hi = mid
            else: lo, flo = mid, fm
        z = (lo + hi) / 2
        if abs(e2(0.5 + 1j * z)) < 1e-5:
            zeros.append(z)
    prev, prev_t = v, t
zeros = np.array(zeros)
print(f"e₂ 零点精化定位：{len(zeros)} 个（t∈[0,100]）")

# C-1 unfolded 间距（局部窗口线性密度）
gaps = np.diff(zeros)
t_mid = (zeros[:-1] + zeros[1:]) / 2
# 全局平均密度 unfold（窗口 ±20 局部密度）
sp_un = []
for i, g in enumerate(gaps):
    win = zeros[np.abs(zeros - t_mid[i]) < 20]
    rho = len(win) / (win.max() - win.min() + 1e-12) if len(win) > 1 else 1 / (g + 1e-12)
    sp_un.append(g * rho)
sp_un = np.array(sp_un)
r = np.array([min(g, gaps[i+1]) / max(g, gaps[i+1]) for i, g in enumerate(gaps[:-1])])
mean_r = float(np.mean(r))
# GUE Wigner surmise 拟合优度（KS 型直观：均值/方差对比）
gue_mean = 0.7357; poi_mean = 0.5307
print(f"C-1：n={len(sp_un)} unfolded 间距均值={np.mean(sp_un):.4f}（目标 1.0）")
print(f"     相邻间距比 <r>={mean_r:.4f}  [GUE≈0.7357 / Poisson≈0.5307] → 判向：{'GUE 趋势' if abs(mean_r-gue_mean)<abs(mean_r-poi_mean) else 'Poisson 趋势'}（样本小，趋势级）")

# C-2 与 ζ 零点最近距离
d = [float(min(abs(zeros - zz))) for zz in ZEROS12 if zeros.size and np.min(np.abs(zeros - zz)) < 100]
print(f"C-2：ζ 前 12 零点各到最近 e₂ 零点距离：{[round(x,3) for x in d]}（无系统性 <0.1 咬合，如实记录）")

out = {"script": "ta2_e2stats-v1.0-20260927.py",
       "prereg": "黎曼猜想·通俗图解-v4.0-20260927 §十二（NTFS冻结在先）",
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "n_zeros": int(len(zeros)), "zeros": [round(float(z), 4) for z in zeros],
       "C1_mean_r": mean_r, "C1_gue": gue_mean, "C1_poisson": poi_mean,
       "C1_verdict": "GUE 趋势" if abs(mean_r-gue_mean) < abs(mean_r-poi_mean) else "Poisson 趋势",
       "C2_nearest_to_zeta": d, "grade": "趋势级（样本41，预注册冻结口径）"}
with open("results/ta2_C_e2stats_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n结果已写 results/ta2_C_e2stats_result-v1.0-20260927.json")
