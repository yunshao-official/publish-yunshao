# -*- coding: utf-8 -*-
"""
电路板供电模拟器（工艺仿真工具 · 组件4）
对应知世原话（2026-08-29 11:43）："一块电路板，高维材料当元件嵌在板上，板子通电→材料激发云韶场。电流大小=场强，通断=开关。"

【诚实口径——必读】
本模拟器只计算**真实电路物理**：供电回路（恒流/恒压源）、材料块的等效电阻与功率耗散、
电极间电场、电流回路磁场、占空比时均、温升估计。
"材料激发云韶场"这一步**没有已知物理对应，无法模拟**——它是否发生、效果如何，只能实验实测。
本工具的用途：把"板子通电"这件事的电路工程参数先在电脑上算清楚（电流要多大、电压多高、
发热多少、什么材料参数下板子工作在什么状态），不含任何对"云韶场"效果的可模拟内容。

材料块电学参数未知（材料本身未验证），故对电导率做全范围扫描：
绝缘体（1e-10 S/m）→ 半导（1e-2）→ 导体（1e6）。
"""
import numpy as np
import os, json

# ---- 几何（知世 08-29 11:46 定：17分量材料 10×10×1 mm 薄片，镀银电极）----
L, W, TH = 10e-3, 10e-3, 1e-3      # m
A_elec = L * W                      # 电极面积（两面镀银电极）
d_elec = TH                         # 电极间距（厚度方向）

def circuit(I=None, V=None, sigma=1e-2, note=""):
    """恒流源或恒压源供电下的工作点。
    sigma: 材料电导率 S/m（未知→扫描）。
    返回：材料电阻、电压/电流、功率、电极间电场。"""
    R_mat = d_elec / (sigma * A_elec)         # 材料体电阻
    if I is not None:
        V = I * R_mat
    else:
        I = V / R_mat
    P = I * V
    E = V / d_elec                             # 电极间平均电场 V/m
    return {"sigma": sigma, "R_材料Ω": round(R_mat, 4), "I_A": round(I, 6),
            "V_V": round(V, 4), "P_W": round(P, 6), "E_V/m": round(E, 2), "备注": note}

def duty_avg(P, duty):
    return P * duty

def temp_rise(P_avg, mass_g=0.78, c=0.46, t_s=60):
    """温升估计：P_avg(W) × t(s) / (质量g × 比热J/gK)。默认钢块10×10×1mm≈0.78g。
    仅估算材料自身温升（绝热近似），不含散热。"""
    return round(P_avg * t_s / (mass_g * c), 3)

def B_field(I, r=5e-3):
    """供电回路在距离 r 处的磁场（直导线近似）μ₀I/(2πr)，单位特斯拉与高斯。"""
    mu0 = 4 * np.pi * 1e-7
    Bt = mu0 * I / (2 * np.pi * r)
    return round(Bt, 8), round(Bt * 1e4, 4)  # T, 高斯

if __name__ == "__main__":
    import json
    SEP = "=" * 74
    print(SEP)
    print("电路板供电模拟 · ①恒流源工作点扫描（10×10×1mm 材料，两面电极）")
    print(SEP)
    print(f"{'电导率S/m':>12}{'材料类别':>10}{'电阻Ω':>12}{'1mA下电压V':>12}{'1mA下功率W':>12}{'电极间场V/m':>12}")
    rows = []
    for sigma, cat in [(1e-10, "绝缘体"), (1e-6, "高阻"), (1e-2, "半导体类"), (1e2, "弱导体"), (1e6, "导体")]:
        r = circuit(I=1e-3, sigma=sigma)
        r["类别"] = cat; rows.append(r)
        print(f"{sigma:>12.0e}{cat:>10}{r['R_材料Ω']:>12}{r['V_V']:>12}{r['P_W']:>12}{r['E_V/m']:>12}")

    print()
    print(SEP)
    print("②恒压源（5V 典型 PCB 供电）工作点")
    print(SEP)
    print(f"{'电导率S/m':>12}{'材料类别':>10}{'电流A':>12}{'功率W':>12}{'电极间场V/m':>12}")
    for sigma, cat in [(1e-10, "绝缘体"), (1e-2, "半导体类"), (1e2, "弱导体"), (1e6, "导体")]:
        r = circuit(V=5.0, sigma=sigma)
        print(f"{sigma:>12.0e}{cat:>10}{r['I_A']:>12}{r['P_W']:>12}{r['E_V/m']:>12}")

    print()
    print(SEP)
    print("③占空比与温升（知世口径：通断=开关，电流大小=场强）")
    print(SEP)
    for I in [1e-3, 1e-2, 1e-1]:
        r = circuit(I=I, sigma=1e-2)
        for duty in [0.3, 0.5, 1.0]:
            Pavg = duty_avg(r["P_W"], duty)
            dT = temp_rise(Pavg, t_s=60)
            Bt, G = B_field(I)
            print(f"  I={I:>7} A  σ=1e-2  duty={duty} → 时均功率 {Pavg:.4f} W | 60s温升≈{dT} K | 回路5mm处磁场 {G} 高斯")

    print()
    print("【诚实边界】以上全部为真实电路物理（欧姆定律/焦耳热/毕奥-萨伐尔）。")
    print("'材料激发云韶场'环节无已知物理对应、无法模拟——该步是否发生只能实验实测。")
    print("本工具回答的问题是：'板子通电'在电路工程上意味着什么参数组合。")
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "circuit_sweep.json"), "w"), ensure_ascii=False, indent=1)
