# -*- coding: utf-8 -*-
"""
天工开物·逐条模拟 · 第三批（T3精算 / T4扩展 / T5屏蔽实测数字设计）
诚实口径：全部为真实物理（声辐射力/弹性力学/核物理屏蔽公式）；体系机制部分不模拟。
"""
import numpy as np
import os, json

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
SEP = "=" * 76

# ============ T3 精算：三种颗粒尺寸的辐射力与图案窗口 ============
print(SEP)
print("T3 精算 · 驻波辐射力/声流比 vs 颗粒尺寸（40kHz 水介质，Gor'kov 口径）")
print(SEP)
rho_w, c_w, f = 1000.0, 1480.0, 40e3
k = 2 * np.pi * f / c_w
eta = 1e-3
Phi = 0.5
print(f"{'振幅μm':>8}{'E_ac J/m³':>14}{'F_1μm(N)':>13}{'F_10μm(N)':>13}{'F_100μm(N)':>13}{'流扰u(m/s)':>13}")
rows = []
for A in [0.5e-6, 2e-6, 5e-6, 10.7e-6, 15e-6]:
    E_ac = 0.5 * rho_w * (2 * np.pi * f * A) ** 2
    Fs = [4 * np.pi * (a**3) * k * Phi * E_ac for a in [1e-6, 10e-6, 100e-6]]
    u = E_ac / (rho_w * c_w) * 0.1
    print(f"{A*1e6:>8.1f}{E_ac:>14.3f}{Fs[0]:>13.2e}{Fs[1]:>13.2e}{Fs[2]:>13.2e}{u:>13.2e}")
    rows.append({"A_um": A * 1e6, "E_ac": E_ac, "F1": Fs[0], "F10": Fs[1], "F100": Fs[2], "u": u})
# 100μm 颗粒在 10.7μm 振幅下的辐射力（声子车床加工档）
A = 10.7e-6
E_ac = 0.5 * rho_w * (2 * np.pi * f * A) ** 2
F_100 = 4 * np.pi * (100e-6)**3 * k * Phi * E_ac
print(f"  加工档参考：100μm 颗粒 @10.7μm 振幅 → F={F_100:.2e} N（可对比重力 {4/3*np.pi*(100e-6)**3*2700*9.8:.2e} N）")

# ============ T4 扩展：全维度压缩能量账 + 能源对照 ============
print()
print(SEP)
print("T4 扩展 · 压缩能量账全表（K·ln(R)，钢 160GPa / 金刚石 443GPa）+ 能源对照")
print(SEP)
Ks = {"钢160GPa": 160e9, "金刚石443GPa": 443e9}
sources = {"TNT": 6.8e9, "锂电池组": 6.5e9, "氢气(700bar)": 4.5e9, "铀235裂变": 1.56e18}
print(f"{'D':>5}{'压缩比R':>12}{'钢:GJ/m³':>12}{'金刚石:GJ/m³':>14}{'=TNT体积倍数':>14}")
for D in [3, 5, 8, 13, 21, 24, 33, 48]:
    R = 2 ** (16 * (D - 3) / 7)
    e_steel = Ks["钢160GPa"] * np.log(R) if R > 1 else 0
    e_dia = Ks["金刚石443GPa"] * np.log(R) if R > 1 else 0
    tnt = e_steel / sources["TNT"] if R > 1 else 0
    print(f"{D:>5}{R:>12.3g}{e_steel/1e9:>12.1f}{e_dia/1e9:>14.1f}{tnt:>14.1f}")
print(f"  对照基准：TNT {sources['TNT']/1e9:.1f} GJ/m³ | 锂电池组 {sources['锂电池组']/1e9:.1f} GJ/m³ | 铀235裂变 {sources['铀235裂变']/1e12:.1f} TJ/m³")
print("  【口径】K·ln(R) 为弹性力学均匀压缩功；不是体系宣称的实现方式——是把'这个压缩比需要多少能量'算给主流物理看。")

# ============ T5 屏蔽实测：D-D 束靶增强因子表（V1 实验的判据数字） ============
print()
print(SEP)
print("T5-V1 屏蔽实测设计数字 · D+束打氘化金属靶，增强因子 f=exp(31.29√(μ/E)·εs/E)")
print(SEP)
S_DD = 55.0  # keV·barn
print(f"{'E束keV':>7}{'裸σ(barn)':>12}" + "".join([f"{f'εs={v}eV':>13}" for v in [0, 300, 750, 2000]]))
res_t5 = []
for E_keV in [2, 5, 10, 20]:
    two_pie_eta = 31.29 * np.sqrt(1.0 / E_keV)
    sigma_bare = (S_DD / E_keV) * np.exp(-two_pie_eta)
    line = f"{E_keV:>7}{sigma_bare:>12.2e}"
    row = {"E_keV": E_keV, "sigma_bare_b": sigma_bare}
    for es_eV in [0, 300, 750, 2000]:
        es_keV = es_eV / 1000
        f_enh = np.exp(two_pie_eta * es_keV / E_keV)
        sigma = sigma_bare * f_enh
        line += f"{f_enh:>13.1f}"
        row[f"es{es_eV}"] = round(f_enh, 2)
    print(line)
    res_t5.append(row)
# 产额示例：1μA 束流、TiD₂ 靶 1mm（D面密度≈4.8e21/cm²）
n_areal = 4.8e21
I_D = 1e-6 / 1.602e-19
print()
print("  产额示例（1 μA 束流、TiD₂ 靶）：")
for E_keV in [5, 10]:
    two_pie = 31.29 * np.sqrt(1.0 / E_keV)
    for es in [0, 750]:
        f_enh = np.exp(two_pie * (es / 1000) / E_keV)
        sigma_cm2 = (S_DD / E_keV) * np.exp(-two_pie) * f_enh * 1e-24
        rate = (I_D / 1.602e-19 if False else (1e-6 / 1.602e-19)) * sigma_cm2 * n_areal
        print(f"    E={E_keV}keV εs={es}eV: 产额 {rate:.1f} 聚变/秒（2.45MeV中子可探测）")
print("  判定规则（冻结）：实测 εs ≤1 keV → 室温聚变判负关门（文献区间 19–750eV）；")
print("  实测 εs ≥10 keV → 路线重开（新机制成立）。中间带 → 扩束复测。")
print("  成本：大学加速器平台机时 10–50 万级；无需自行建塔。")

json.dump({"T3_rows": rows, "T4": "ok", "T5": res_t5},
          open(os.path.join(OUT, "tiangong_batch3.json"), "w"), ensure_ascii=False, indent=1, default=float)
print(f"\n数据已存：{OUT}/tiangong_batch3.json")
