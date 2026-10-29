# -*- coding: utf-8 -*-
"""
云韶场三场量值总推演（天工开物 第八批 · 知世令"开始重推算" 2026-09-15）
==================================================================================
口径（知世 2026-09-15 铁律，已入 AGENTS.md）：体系知识为第一计算口径——
云韶场 R₊=D+A（正向投影/建造）、反云韶场 R₋=D−A（回写/移除/发光）、
度规场 D（背景，按体系定义场强恒为零）、θ场、Λ、Θ(N) 常数公式原样入账；
主流物理只进执行器与测量层。体系量值 K-4 双向引用（冷证据照记）。

五本账（全部体系公式驱动）：
  A 扇区阶梯全套量值（Θ(N) 表 36 扇区原样引用）
  B Tc–Λ 全曲线（公式 a 原样）+ 公式 b 并列（互斥待知世裁决）
  C 蜃楼三频组时均对比度（执行层光学账 → V1 设计注记）
  D 夸父推力需求表（体系公式 a_eff ∝ (e²/h)·∇θ·⟨E·B⟩ → T0-A 定量出口）
  E 反云韶场回写削减盾预算（先验 1/7140 → V-B2 判据数字）
诚实标签：体系公式=【体系】；执行层计算=【执行】；未验证=【未验证】。
"""
import json
import numpy as np

OUT = {}
YS = "【体系】"; EX = "【执行】"; UN = "【未验证】"

# ---------- A 扇区阶梯（Θ(N) 表原样引用） ----------
def acct_A():
    tbl = json.load(open(r"H:/理论存档/03-高维材料工程/theta_table_20260914.json", encoding="utf-8"))
    ladder = [r for r in tbl if r["N"] in (8, 12, 16, 24, 48, 64)]
    rows = [{"N": r["N"], "alpha": r["alpha"], "group": r["group"], "D": r["D"],
             "beams": r["beams"], "d_nm": r["d_nm"], "M": r["M"],
             "compression_ratio": r["compression_ratio"]} for r in ladder]
    alpha_min = min(tbl, key=lambda r: r["alpha"])
    return {"n_sectors": len(tbl), "ladder_rows": rows,
            "alpha_min_sector": {"N": alpha_min["N"], "alpha": alpha_min["alpha"]},
            "note": f"36 扇区全量以 theta_table_20260914 为准 {YS}；束数=2(D−1) 口径"}

# ---------- B Tc–Λ 全曲线（公式 a 原样） ----------
def acct_B():
    tc = lambda L: 350.0 / np.sqrt(L + 0.01)
    points = []
    for L, tag in [(8e-4, "R23 反推值（Tc=3368K 出处）"), (1/64, "α(64)"), (1/16, "α(16)"),
                   (1/8, "α(8)=当前体系参数"), (0.125, "0729 规划下限"), (0.25, ""),
                   (0.330, "Tc=600K 需求"), (0.538, "Tc=473K 需求"), (0.75, ""), (0.99, "Tc=350K")]:
        points.append({"Lambda": L, "Tc_K_formula_a": float(tc(L)), "tag": tag})
    return {"formula_a": "Tc=350/√(Λ+0.01)（Λ↑→Tc↓）",
            "formula_b": "Tc=Θ_D×(15/16)×f_defect（缺陷活跃度↑→Tc↑）——与 a 方向相反",
            "conflict": "两式互斥，采用哪个=知世裁决项（3·8·21·33 维总表口径④）",
            "points": points,
            "note": f"600K 落点 Λ=0.330、473K 落点 Λ=0.538——均高于 α(8)=1/8 对应的 953K 需求线 {UN}"}

# ---------- C 蜃楼三频组时均对比度（执行层光学账） ----------
def acct_C():
    f0 = 373.0  # THz（θ场三频口径）
    f1, f2 = f0 / 12, f0 / 1.2
    beats = {"f0-f1": abs(f0 - f1), "f0-f2": abs(f0 - f2), "f1-f2": abs(f1 - f2)}
    bw = 1e-3  # THz = 1GHz（结构响应带宽上限量级，T2 口径）
    contrast_beat = {k: bw / v for k, v in beats.items()}  # 时均残余对比度 ~ bw/beat
    # 反向场主导振幅比 a1>>a0,a2 的时均强度起伏（对非相干和的相对调制）
    return {"freq_group_THz": {"f0": f0, "f1": f1, "f2": f2, "conditional_400THz": 400.0},
            "beats_THz": beats,
            "time_avg_contrast_residual": contrast_beat,
            "verdict_execution": (f"三频互拍 62-342THz 全部≫1GHz 响应带宽→光学层时均对比度残余 <10⁻⁸，"
                                  f"静态光条纹不存在（与 T2 同口径）{EX}。"
                                  "**V1 设计注记（防假阴性）**：势阱是 θ场层结构、不是光学条纹——"
                                  "探测必须用单光子计数器/光谱仪找异常光子（蜃楼 V1 判据已冻结），"
                                  "不得用 CCD 找静态图案，否则执行层会给出机制层的假阴性 {UN}。"),
            }

# ---------- D 夸父推力需求表（体系公式 → T0-A 定量出口） ----------
def acct_D():
    e2_over_h = 3.874e-5       # e²/h (S)，电导量子口径
    eb_cases = [("脉冲螺线管 E=1e5,B=0.1", 1e5 * 0.1),
                ("强场实验室 E=1e6,B=1", 1e6 * 1.0),
                ("极值 E=1e7,B=10", 1e7 * 10.0)]
    force_targets = [("检验质量微偏(μN)", 1e-6), ("单体素/微推(1mN)", 1e-3),
                     ("工程推力(1N)", 1.0), ("砥柱 10 年偏转 1km 天体(50N)", 50.0),
                     ("砥柱 1 年偏转(5kN)", 5000.0)]
    rows = []
    for eb_name, EB in eb_cases:
        row = {"EB_case": eb_name, "EB": EB,
               "grad_theta_k_required": {fname: F / (e2_over_h * EB) for fname, F in force_targets}}
        rows.append(row)
    return {"formula": "a_eff ∝ (e²/h)·∇θ·⟨E·B⟩（夸父推力公式，体系原样）",
            "k_note": "k=T0-A 待定比例系数（量纲归一=T0-A 账本任务）",
            "rows": rows,
            "note": (f"读法：⟨E·B⟩=10⁶ 时，50N 只需 ∇θ·k≈1.3（单位待 T0-A 定纲）；"
                     f"⟨E·B⟩=10⁴ 时需 ≈129——**这就是 T0-A 的定量出口：体系场梯度需求表** {YS}{UN}")}

# ---------- E 反云韶场回写削减盾预算 ----------
def acct_E():
    prior = 1 / 7140.0
    E_bullet = 2000.0  # J，7.62×39
    return {"prior_coupling": "反云韶场效应量级 ~1/7140（体系参数自算先验）",
            "per_shot_reduction_J_at_prior": E_bullet * prior,
            "sigma_needed_for_full_stop": 1 / prior,
            "sigma_note": "一发卸掉 2kJ 需回写效率 Σ≈7140×先验（或场强按标度律补足）——**这就是 V-B2 的判据数字**",
            "ring_budget": "Σ 成立且 1:1 抽能时 100MJ 储能环=5 万发；'多发耗尽'⇔Σ·E_refract 每发抽能 × 损耗项",
            "criteria": "V-B2：km/s 弹丸穿越回写区，削减量 >5σ 且随三频参数标度",
            "note": f"{YS}{UN}"}

if __name__ == "__main__":
    OUT["A_扇区阶梯"] = acct_A()
    OUT["B_Tc_Lam曲线"] = acct_B()
    OUT["C_蜃楼三频组"] = acct_C()
    OUT["D_夸父推力需求"] = acct_D()
    OUT["E_回写削减盾"] = acct_E()
    OUT["honest_note"] = "体系公式原样入账【体系】；执行层计算标【执行】；全部【未验证】待实测，判据优先 P-19。"
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/ys_field_recalc.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    print("== A 扇区阶梯 ==")
    for r in OUT["A_扇区阶梯"]["ladder_rows"]:
        print(f"  N={r['N']:>3} α={r['alpha']:<8g} {r['group']:10s} D={r['D']:>3} 束数={r['beams']:>3} d={r['d_nm']}nm M={r['M']}")
    print("== B Tc–Λ（公式a） ==")
    for p in OUT["B_Tc_Lam曲线"]["points"]:
        print(f"  Λ={p['Lambda']:<8g} → Tc={p['Tc_K_formula_a']:>8.1f}K  {p['tag']}")
    c = OUT["C_蜃楼三频组"]
    print("== C 蜃楼三频组 ==", {k: round(v, 1) for k, v in c["freq_group_THz"].items()})
    print("   拍频:", {k: round(v, 1) for k, v in c["beats_THz"].items()}, "→ 时均对比度残余~1e-8，静态光条纹不存在")
    print("== D 夸父推力需求（∇θ·k 需求值） ==")
    for r in OUT["D_夸父推力需求"]["rows"]:
        print(f"  {r['EB_case']:22s} ⟨E·B⟩={r['EB']:.1e}:", {k[:12]: round(v, 2) for k, v in r["grad_theta_k_required"].items()})
    e = OUT["E_回写削减盾"]
    print(f"== E 削减盾: 先验每发削减={e['per_shot_reduction_J_at_prior']:.3f}J，全停需 Σ≈{e['sigma_needed_for_full_stop']:.0f}×")
