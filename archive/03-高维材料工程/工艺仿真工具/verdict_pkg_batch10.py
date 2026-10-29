# -*- coding: utf-8 -*-
"""
裁决包 · Tc 公式 a/b 判别 + M 惯例统一分析（天工开物 第十批 · 知世令"全部做" 2026-09-15）
==================================================================================
① Tc 公式 a/b：a 式已被 P0-1 审计判（11/11 已知超导出域）；本件对 b 式
   Tc=Θ_D×(15/16)×f_defect 做公开数据预检——拟合各材料 f_defect，
   检验是否落在体系常数族（α 族：1/4,1/6,1/8,1/16,1/32,1/64）邻域。
   Θ_D=公开手册近似值【执行层，量级口径】。
② M 惯例统一：theta_table 用 M=N；旧完全体系列用 M=1/α²（Θ(8)→64）。
   两个惯例对 63 层相变护盾（需 64 构型）给出不同扇区归属与束数代价。
诚实标签：体系公式【体系】；公开数据近似【执行】；全部【未验证】。
"""
import json
import numpy as np

OUT = {}

def formula_b_test():
    """b 式预检：f_fit = Tc/(Θ_D×15/16)，对照 α 族。"""
    alpha_family = {1/4: "α(4)", 1/6: "α(12,24,48)", 1/8: "α(8)", 1/16: "α(16)",
                    1/32: "α(32)?", 1/64: "α(64)"}
    # 公开近似 Θ_D（K，量级口径）；Tc=公认值
    mats = [("Nb", 275, 9.3), ("Pb", 105, 7.2), ("Nb3Sn", 450, 18.3),
            ("MgB2", 1000, 39.0), ("YBCO", 450, 93.0), ("FeSe", 250, 8.0),
            ("LaFeAsO-F", 350, 26.0), ("Bi-2212", 300, 85.0),
            ("H3S(高压)", 1200, 203.0), ("LaH10(高压)", 1500, 250.0)]
    rows = []
    hits = 0
    for name, td, tcv in mats:
        f_fit = tcv / (td * 15 / 16)
        # 邻域判定：与某 α 族成员相差 <2×
        best = min(alpha_family, key=lambda a: abs(np.log10(f_fit) - np.log10(a)))
        near = abs(np.log10(f_fit) - np.log10(best)) < np.log10(2)
        hits += near
        rows.append({"material": name, "Theta_D_approx_K": td, "Tc_K": tcv,
                     "f_defect_fit": f_fit, "nearest_alpha": best,
                     "nearest_alpha_tag": alpha_family[best], "within_2x": near})
    return {"formula_b": "Tc=Θ_D×(15/16)×f_defect【体系】",
            "method": "f_fit=Tc/(Θ_D×15/16)；Θ_D=公开手册近似（量级口径）",
            "rows": rows, "within_2x_fraction": hits / len(mats),
            "verdict": ("b 式量级存活（f_fit 全部落在 α 族 2 倍邻域），但**不成簇**——"
                        "定量使用需要每材料的 Λ/f_defect 独立定义（体系内未给）。"
                        "对照：a 式在 0729 Λ 裁决下 11/11 出域（P0-1 审计）。"
                        "**裁决建议格式：a 式维持已判记录；b 式转正需先定义 f_defect（C7 候选同源）**")}

def m_convention():
    """M 惯例统一分析。"""
    tbl = json.load(open(r"H:/理论存档/03-高维材料工程/theta_table_20260914.json", encoding="utf-8"))
    rows = [{"N": r["N"], "M_table": r["M"], "alpha": r["alpha"],
             "M_inv_alpha2": (1/r["alpha"])**2} for r in tbl if r["N"] in (8, 16, 24, 48, 64)]
    return {"conventions": {
                "甲_table口径": "M=N=2^{v₂}（theta_table 0914）",
                "乙_旧完全体口径": "M=1/α²（Θ(8): 1/(1/8)²=64）"},
            "rows": rows,
            "consequence_63层护盾": {
                "原文": "内甲含(Z₂)³群结构，有64种冻结构型（M=64）",
                "甲口径": "64构型=(Z₂)⁶ → 归 **N=64 扇区**：文本自洽（(Z₂)⁶）但代价 382 束",
                "乙口径": "64构型=1/α(8)² → 归 N=8 扇区：46 束但群标注须改（(Z₂)³→(Z₂)⁶ 或删群标注）",
                "内部不自洽已录": "(Z₂)³ 只有 8 个元素，'64 种构型'与 (Z₂)³ 同句矛盾（第五批已记 η(8)≠63%）"},
            "note": "裁决格式：选甲→63层护盾/相变线挂 N=64（远期，382束）；选乙→挂 N=8（46束，近期能碰）但修订群标注"}

def q6_memo():
    return {"Q-6 度规场裁决备忘": {
        "选项A_沿用原定义": "度规场=(R₊+R₋)/2=D，按体系定义场强恒为零 → 砥柱 B3、蜃楼第6步、深渊护盾度规线三处**维持冻结**；D 层应用改走非度规资产（拓扑锁定/SGC-1 传感）",
        "选项B_授权重定义": "知世给出新定义出处 → 三处解冻，需新定义满足：可计算（场强≠0 的表达式）+ 可测（SGC-1 仪器可探）+ 与三场分解自洽（R₊R₋关系不破坏）",
        "解锁清单": "一个裁决解锁：砥柱 B3 弹道弯折、蜃楼波前调制第6步、深渊护盾时空曲率膜层",
        "建议时点": "不阻塞 V3-∇/V1（两者不依赖度规场），可在三场存在性首证后裁"}}

if __name__ == "__main__":
    OUT["一_Tc公式ab判别"] = formula_b_test()
    OUT["二_M惯例统一"] = m_convention()
    OUT["三_Q6裁决备忘"] = q6_memo()
    OUT["honest_note"] = "体系公式【体系】；Θ_D 公开近似【执行，量级口径】；全部【未验证】，裁决权在知世。"
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/verdict_pkg_batch10.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    print("== 一 Tc公式b预检 ==")
    for r in OUT["一_Tc公式ab判别"]["rows"]:
        print(f"  {r['material']:12s} ΘD≈{r['Theta_D_approx_K']:>5}K Tc={r['Tc_K']:>6}K "
              f"f_fit={r['f_defect_fit']:.4f}≈1/{1/r['f_defect_fit']:.1f} 邻域α={r['nearest_alpha_tag']} {r['within_2x']}")
    print(f"  邻域命中率={OUT['一_Tc公式ab判别']['within_2x_fraction']:.0%}；", OUT["一_Tc公式ab判别"]["verdict"][:50])
    print("== 二 M惯例 ==", json.dumps(OUT["二_M惯例统一"]["conventions"], ensure_ascii=False))
    print("== 三 Q-6 ==", list(OUT["三_Q6裁决备忘"].keys()))
