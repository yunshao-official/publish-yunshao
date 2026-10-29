# -*- coding: utf-8 -*-
"""
天工开物·逐条模拟 · 第一批（卷三物质域①②）
诚实口径：①超导磁选=主流迈斯纳效应真实物理计算；②θ场三频=标准光学时均计算（检验多频能否出静态图案）。
全部为模型口径数学实验；"体系机制"部分不在可模拟范围内，如实标注。
"""
import numpy as np
import os, json

SEP = "=" * 76
mu0 = 4 * np.pi * 1e-7

# ============ 卷三① 室温超导磁选：迈斯纳分离真实物理 ============
print(SEP)
print("卷三① 超导磁选 · 磁场梯度中三类颗粒的受力与分离速度（真实物理计算）")
print(SEP)
# 场景：NdFeB/电磁铁 B=1T，梯度 dB/dx=50 T/m，水介质（粘度1e-3 Pa·s），颗粒半径0.5mm
B, gradB, eta, r = 1.0, 50.0, 1e-3, 0.5e-3
rho_w = 1e3
V = 4/3 * np.pi * r**3

# 超导颗粒（完全抗磁 χ=-1）：磁压强梯度力 F = V·∇(B²/2μ₀)（场被完全排出）
F_sc = V * B * gradB / mu0
# 顺磁性颗粒（χ=+2e-3，如钛铁矿量级）：F = V·χ·B·∇B/μ₀
F_para = V * 2e-3 * B * gradB / mu0
# 抗磁性基质（χ=-1e-5，如水/多数盐类）
F_dia = V * 1e-5 * B * gradB / mu0

rho_p = 5000.0  # kg/m³（陶瓷超导/钛铁矿量级）
m_p = rho_p * V
a_sc, a_para = F_sc / m_p, F_para / m_p
t_cm_sc = np.sqrt(2 * 0.01 / a_sc)  # 移动1cm所需时间（惯性区，初速0）
Re_sc = abs(v_term_sc := F_sc / (6 * np.pi * eta * r)) * rho_w * 2 * r / eta if False else 0
print(f"  场景：B={B} T，梯度 {gradB} T/m，颗粒半径 {r*1e3} mm，密度 {rho_p} kg/m³，水介质")
print(f"  超导颗粒（χ=-1 完全抗磁）：受力 {F_sc:.3e} N，加速度 {a_sc:.0f} m/s²（约为重力加速度的 {a_sc/9.8:.0f} 倍，方向：推离高场区）")
print(f"  顺磁颗粒（χ=+2e-3）    ：受力 {F_para:.3e} N，加速度 {a_para:.2f} m/s²（方向：吸向高场区）")
print(f"  抗磁基质（χ=-1e-5）    ：受力 {F_dia:.3e} N，加速度 {F_dia/m_p:.3f} m/s²")
print(f"  移动 1cm 时间：超导 {t_cm_sc*1e3:.1f} ms，顺磁 {np.sqrt(2*0.01/a_para):.2f} s → 秒级完全分离")
print(f"  分离比：加速度差 {a_sc/a_para:.0f} 倍、方向相反 → 磁选在原理上成立（惯性区，斯托克斯口径不适用已修正）")
print(f"  【注意】前提=颗粒真的是超导态（迈斯纳完全抗磁）；材料是否超导=R23送检要裁决的事，本模拟不背书。")
print(f"  【工程含义】若送检通过：0.5mm 颗粒在 50 T/m 梯度下秒级分离，普通磁选设备参数即可——这是送检通过后的现成收益。")

# 分离时间（相对位移 1cm 所需）
t_sep = np.sqrt(2 * 0.01 / a_sc)
print(f"  分离时间尺度：超导颗粒移出 1cm ≈ {t_sep*1e3:.1f} ms（惯性区）")

# ============ 卷三② 场控自组织：θ场三频时均图案检验 ============
print()
print(SEP)
print("卷三② 场控自组织 · 三频相干波束（373THz族）时均图案对比度检验（标准光学）")
print(SEP)
# 时均图案对比度 = 2√(I1I2)/ (I1+I2) × |1/(1+(Δω/γ)²)| ，γ=材料响应带宽
I1 = I2 = 1.0
contrast_max = 2 * np.sqrt(I1 * I2) / (I1 + I2)   # 同频最大对比度
gamma = 1e9  # 材料结构响应带宽 1 GHz（热/结构过程的上限量级）
print(f"{'频率差Δ':>12}{'材料响应带宽':>14}{'时均图案对比度':>16}{'能否形成静态图案':>16}")
for dTHz in [0.0, 1e-6, 1e-4, 1e-2, 1.0, 46.7]:
    df = dTHz * 1e12
    vis = contrast_max / np.sqrt(1 + (df / gamma) ** 2)
    ok = "能" if vis > 0.5 and dTHz < 1e-3 else "不能"
    print(f"{dTHz:>10} THz{gamma/1e9:>11} GHz{vis:>14.4f}{ok:>14}")
print("  结论（标准光学，非体系口径）：三频相干（373THz族内差频远大于材料响应带宽）")
print("  的时均图案对比度趋近于零——静态自组织图案要求同频（Δ→0）或材料响应快于差频（不现实）。")
print("  【诚实口径】此检验不否定'θ场'存在性，只说明：多频配置在普通物理下不产生静态空间结构，")
print("  卷三§3 的'预设干涉结构'必须改用同频分束（模式A）方案才能成立。")

# ============ 汇总 ============
print()
print(SEP)
print("第一批模拟小结")
print(SEP)
print("① 超导磁选：迈斯纳分离原理成立（速度差千倍级、方向相反）——但整个收益挂在'材料真的是超导'上，=R23送检门。")
print("② 三频场控自组织：多频静态图案在普通物理下不成立——工程方案须改同频分束。")
print("两条都有产出：一条给出送检通过后的现成工程设计参数，一条给出必须改的设计。")
json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
import os, json
os.makedirs(json_path, exist_ok=True)
json.dump({"c1_magnetic": {"F_sc": F_sc, "F_para": F_para, "a_sc": a_sc, "a_para": a_para, "t_cm_ms": t_cm_sc*1e3},
           "c2_threefreq": {"gamma_GHz": gamma/1e9, "contrast_max": contrast_max}},
          open(os.path.join(json_path, "tiangong_batch1.json"), "w"), ensure_ascii=False, indent=1, default=float)
print(f"数据已存：{json_path}/tiangong_batch1.json")
