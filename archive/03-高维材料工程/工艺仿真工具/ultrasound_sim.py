# -*- coding: utf-8 -*-
"""
超声驻波工艺仿真器（工艺仿真工具 · 组件3）
- 条带周期表：λ/2 = v/(2f)，按材料声速
- 衰减可行窗口：晶粒散射衰减 ~ B·f²（多晶金属经验量级），给出振幅保持判据
- 共振模式梳：固体内驻波只能取共振模态 f_n = n·v/(2L)（全轮攻防 C1 修正口径）
诚实口径：1D 纵波近似 + 经验衰减量级；具体工件以实测（RUS/超声测厚）为准。
"""

import numpy as np

# 多晶金属晶粒散射衰减经验量级（纵波，粗晶）：B·f²，B≈(1e-12 ~ 1e-10) Np/(m·Hz²)
# 取中值 B=5e-11；判据：穿过厚度 L 后振幅保持 e^(-B f² L) ≥ 0.5（-6dB）
B_SCATTER = 5e-11

def band_period(vL, f):
    """条带周期 λ/2（米）"""
    return vL / (2.0 * f)

def feasible(vL, f, L_thick, keep=0.5, B=B_SCATTER):
    """衰减可行性：穿过厚度 L 后振幅保持比例 ≥ keep"""
    return np.exp(-B * (f ** 2) * L_thick) >= keep

def band_table(mat_name, vL, L_thick=0.01, f_list=None):
    """材料条带周期表：f(MHz) → 周期(mm)、可行性"""
    if f_list is None:
        f_list = [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]  # MHz
    rows = []
    for fMHz in f_list:
        f = fMHz * 1e6
        p = band_period(vL, f) * 1000  # mm
        ok = feasible(vL, f, L_thick)
        rows.append({"材料": mat_name, "f_MHz": fMHz, "条带周期_mm": round(p, 3),
                     "10mm厚可行": "✓" if ok else "✗(衰减)"})
    return rows

def resonance_modes(vL, L=0.01, n_max=40):
    """固体共振模式梳：f_n = n·v/(2L)（两端自由纵模）。返回 n→f(MHz) 列表。"""
    return [(n, round(n * vL / (2 * L) / 1e6, 4)) for n in range(1, n_max + 1)]

def nearest_mode(vL, L, f_target):
    """离目标频率最近的共振模态（含模态数n与实际频率）——固体驻波只能取这些离散值"""
    n = max(1, round(2 * L * f_target / vL))
    f_actual = n * vL / (2 * L)
    return {"n": int(n), "f_actual_MHz": round(f_actual / 1e6, 4),
            "target_MHz": round(f_target / 1e6, 4),
            "偏差%": round(abs(f_actual - f_target) / f_target * 100, 2),
            "条带周期_mm": round(band_period(vL, f_actual) * 1000, 3)}
