# -*- coding: utf-8 -*-
"""黑暗森林打击形式·物理可行性算例（判据冻结）。seed=42。
D-1 RKV 齐射覆盖度：100弹丸 0.5c/0.9c → 地球截面积覆盖比
D-2 恒星耀斑武器化：类太阳恒星超级耀斑能量 vs 地球承受力
D-3 小行星 redirect：DART 反向（1Gt 级天体 redirect→地球命中精度）
D-4 光速约束打击半径：打击方在 d ly 外 → 打击到达时间 + 预警时间
D-5 自复制探针指数扩散：倍增时间×扩散半径→覆盖银河系时间
"""
import numpy as np, json, math
rng = np.random.default_rng(42)

# ---- D-1 RKV 齐射覆盖度 ----
R_EARTH = 6371e3  # m
CROSS = np.pi * R_EARTH**2  # 地球截面积
N_RKV = 100
SPREAD_ANG = 0.001  # 弹幕角散布（rad，远距离瞄准精度）
D_TARGET = 4 * 9.461e15  # 4 ly in m
spread_radius = D_TARGET * SPREAD_ANG
# 100 弹丸均匀散布在 spread_radius 圆内
covered = CROSS / (np.pi * spread_radius**2) * N_RKV * (R_EARTH/spread_radius)**2 if spread_radius > R_EARTH else 1.0
# 简化：命中概率 per 弹丸 = π*Re²/(π*spread_r²) 
p_hit_per = (R_EARTH/spread_radius)**2 if spread_radius > R_EARTH else 1.0
p_at_least_one = 1 - (1 - p_hit_per)**N_RKV
D1 = {"弹丸数": N_RKV, "散布半径m": round(spread_radius,0), "地球半径m": R_EARTH,
      "单弹命中概率": round(p_hit_per,6), "百弹至少一命中": round(1-(1-p_hit_per)**N_RKV, 6),
      "VERDICT": "远距瞄准精度0.001rad时命中概率极低" if p_hit_per < 0.01 else "命中概率高"}

# ---- D-2 恒星耀斑 ----
# 太阳正常耀斑 ~1e25 J；超级耀斑（开普勒观测）~1e33 J
# 地球接收截面 = πRe²/4πd² → d=1AU
d_AU = 1.496e11
E_super_flare = 1e33
E_at_earth = E_super_flare / (4*np.pi*d_AU**2) * np.pi*R_EARTH**2 * 0.7  # 0.7=吸收率
tnt_eq = E_at_earth / 4.184e9  # tons TNT
D2 = {"超级耀斑总能量J": E_super_flare, "地球接收J": round(E_at_earth,2),
      "TNT当量tons": round(tnt_eq,1),
      "破坏评估": "电离大气/破坏臭氧层/电网崩溃" if E_at_earth > 1e20 else "可承受"}

# ---- D-3 小行星 redirect ----
# 1km 小行星，质量~1.5e12 kg，速度 20km/s redirect→地球
m_ast = 1.5e12
v_impact = 20000
E_kin = 0.5 * m_ast * v_impact**2
D3 = {"直径": "1km", "质量kg": m_ast, "速度m/s": v_impact,
      "动能J": f"{E_kin:.2e}", "TNT当量": f"{E_kin/4.184e9:.1e} tons",
      "DART反向可行性": "DART证明0.5mm/s偏转可行→敌需精确redirect",
      "预警时间": "轨道力学可预测（月-年级）"}

# ---- D-4 光速约束打击半径 ----
D4 = []
for v_frac in [0.1, 0.5, 0.9, 0.99]:
    for d_ly in [10, 50, 100, 1000]:
        travel_yr = d_ly / v_frac
        warn_yr = d_ly * (1/v_frac - 1) if v_frac < 1 else float('inf')
        # 预警=光信号（发射事件）先到达的时间差
        D4.append({"v/c": v_frac, "d_ly": d_ly, "飞行年": round(travel_yr,1),
                   "预警年": round(warn_yr,1)})
# 关键：预警年>0 当且仅当 v<c。v→c 预警→0

# ---- D-5 自复制探针 ----
tau_d = 10  # 倍增时间（年，乐观估计）
years = np.arange(0, 2001, 100)
coverage = {str(y): round(2**(y/tau_d), 1) for y in years[::10]}
D5 = {"倍增时间年": tau_d, "指数增长表": coverage,
      "覆盖银河系年(立方根)": round((1e11)**(1/3) * tau_d, 0)}

out = {"D1_RKV覆盖": D1, "D2_耀斑": D2, "D3_小行星": D3, "D4_光速约束": D4, "D5_自复制": D5}
with open("dark_forest_strike_20260918.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("D-1 RKV覆盖:", D1["VERDICT"], "| 百弹至少一命中:", D1["百弹至少一命中"])
print("D-2 耀斑:", D2["破坏评估"], "| TNT:", D2["TNT当量tons"], "tons")
print("D-3 小行星:", D3["TNT当量"], "tons TNT | 预警:", D3["预警时间"])
print("D-5 自复制:", "覆盖银河系需", D5["覆盖银河系年(立方根)"], "年")
