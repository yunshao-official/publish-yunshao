# -*- coding: utf-8 -*-
"""
人体作用机制研究 · 模拟一：经颅穿透与组织内 SAR（真实物理，公开组织参数）
诚实口径：①组织介电参数取 IT'IS/Gabriel 数据库量级近似（精确设计须查库）；②平面波分层衰减近似
（忽略界面反射，反射损耗另计会再降 10–20%）；③只算电磁穿透与吸收热——"写入知识"等机制声称
无已知物理对应，无法模拟；④SAR 对照 ICNIRP/IEEE 安全限值（公开标准）。
不构成任何医疗结论。数学实验口径。
"""
import numpy as np
import os, json

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
SEP = "=" * 78
mu0 = 4 * np.pi * 1e-7
eps0 = 8.854e-12

# 组织介电参数近似（IT'IS/Gabriel 数量级）：σ S/m, εr
TISSUE = {
    "皮肤(湿)": {"10k": (0.011, 1423), "100k": (0.11, 1423), "1M": (0.104, 164), "10M": (0.24, 62),
                 "100M": (0.43, 38), "433M": (0.65, 35), "1G": (0.87, 34), "2.4G": (1.39, 31)},
    "颅骨":   {"10k": (0.02, 220), "100k": (0.02, 220), "1M": (0.06, 87), "10M": (0.10, 29),
               "100M": (0.16, 21), "433M": (0.21, 17), "1G": (0.27, 16), "2.4G": (0.48, 13)},
    "脑(灰质)": {"10k": (0.075, 3100), "100k": (0.075, 3100), "1M": (0.11, 334), "10M": (0.19, 106),
                 "100M": (0.45, 62), "433M": (0.59, 52), "1G": (0.94, 52), "2.4G": (1.65, 47)},
}
rho_brain = 1050.0  # kg/m³

def attenuation(alpha, d):
    """场衰减因子 e^{-αd} 与 dB"""
    fac = np.exp(-alpha * d)
    return fac, round(-20 * np.log10(max(fac, 1e-300)), 1)

print(SEP)
print("① 各频率在三种组织中的衰减系数 α（dB/cm）与 10dB 穿透深度")
print(SEP)
print(f"{'频率':>8}{'皮肤α':>10}{'颅骨α':>10}{'脑α':>10}{'脑10dB深度':>12}")
depths = {}
for fkey, f in [("10k", 1e4), ("100k", 1e5), ("1M", 1e6), ("10M", 1e7), ("100M", 1e8),
                ("433M", 4.33e8), ("1G", 1e9), ("2.4G", 2.4e9)]:
    row = {}
    for tissue, dpar in TISSUE.items():
        s, er = dpar[fkey]
        w = 2 * np.pi * f
        alpha_np = w * np.sqrt(mu0 * eps0 * er / 2 * (np.sqrt(1 + (s / (w * eps0 * er)) ** 2) - 1))
        alpha_dbcm = alpha_np * 8.686 / 100  # Np/m → dB/cm
        row[tissue] = (alpha_np, alpha_dbcm)
    d10_brain = 2.303 / row["脑(灰质)"][0] * 100  # cm
    depths[fkey] = d10_brain
    print(f"{fkey:>8}{row['皮肤(湿)'][1]:>10.2f}{row['颅骨'][1]:>10.2f}{row['脑(灰质)'][1]:>10.2f}{d10_brain:>10.1f} cm")

print()
print(SEP)
print("② 到达海马深度（约 7 cm，经 皮肤2mm+颅骨7mm+脑5.6cm）的场保持率（配方场强 10⁴ V/m）")
print(SEP)
E0 = 1e4
layers = [("皮肤(湿)", 2e-3), ("颅骨", 7e-3), ("脑(灰质)", 5.6e-2)]
print(f"{'频率':>8}{'海马处场强V/m':>14}{'保持率%':>10}{'脑SAR W/kg':>14}{'超安全限倍数(10W/kg)':>16}")
res = []
for fkey, f in [("10k", 1e4), ("100k", 1e5), ("1M", 1e6), ("10M", 1e7), ("100M", 1e8), ("1G", 1e9)]:
    keep = 1.0
    for tissue, d in layers:
        a = TISSUE[tissue][fkey]
        w = 2 * np.pi * f
        alpha_np = w * np.sqrt(mu0 * eps0 * a[1] / 2 * (np.sqrt(1 + (a[0] / (w * eps0 * a[1])) ** 2) - 1))
        keep *= np.exp(-alpha_np * d)
    E_loc = E0 * keep
    s, er = TISSUE["脑(灰质)"][fkey]
    sar = s * E_loc ** 2 / rho_brain
    over = sar / 10.0
    res.append({"f": fkey, "E_loc": E_loc, "keep_pct": keep * 100, "SAR": sar, "over_10Wkg": over})
    print(f"{fkey:>8}{E_loc:>14.1f}{keep*100:>9.1f}%{sar:>14.3e}{over:>14.0f} x")

print()
print("③ 合规场强：海马处 SAR=10 W/kg（局部安全上限）允许的表面场强")
print(f"{'频率':>8}{'允许表面场强V/m':>16}")
for fkey, f in [("1M", 1e6), ("10M", 1e7)]:
    keep = [r for r in res if r["f"] == fkey][0]["keep_pct"] / 100
    s, er = TISSUE["脑(灰质)"][fkey]
    E_loc_max = np.sqrt(10.0 * rho_brain / s)
    print(f"{fkey:>8}{E_loc_max / keep:>14.0f}   （配方 10⁴ V/m 超出 {1e4/(E_loc_max/keep):.0f} 倍）")

print()
print("【结论】")
print("  1. 穿透：1MHz 及以下，电磁场穿透颅脑到海马深度衰减很小（组织在 MHz 段近似透明）——")
print("     '电路板供电的场够得着海马'在电磁学上成立，经颅穿透不是这条路线的瓶颈。")
print("  2. 真实伤害通道（数量化）：配方场强 10⁴ V/m 在脑内 SAR 超局部安全限（10 W/kg）数百到数千倍——")
print("     这是普通电磁吸收热，不是体系机制；同深度合规场强上限约 200–400 V/m（随频率）。")
print("  3. 机制（'写入知识''信道恢复'）仍无已知物理对应，无法模拟——只能实验裁决。")
print("  4. 工程含义：若继续，安全合规路径=把场强降到合规线内再谈效果——那又回到'有效剂量'问题。")

json.dump({"depth10dB": depths, "res": res}, open(os.path.join(OUT, "human_penetration.json"), "w"), ensure_ascii=False, indent=1, default=float)
print(f"\n数据已存：{OUT}/human_penetration.json")
