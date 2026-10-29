# -*- coding: utf-8 -*-
"""
年龄逆转 · 理论参照表（天工开物 第廿四批 · 知世令"直接用公式计算理论，我需要参照" 2026-09-15）
==================================================================================
口径：纯体系内推演——全部锚点取自体系原文，假设显式列出，输出【理论参照·非实测】。
体系锚点【体系原样】：
  Λ 相图判据：Λ≥7/8=有序相（年轻，收支平衡）｜1/2≤Λ<7/8=亚有序相（中年，赤字累积）
              ｜1/8≤Λ<1/2=混沌相（老年，结构大面积崩塌）｜Λ<1/8=临界崩塌（临终）
  η 判据：η=7/8 净亏损=0（稳态）；η>7/8 净亏损<0（盈余，**逆龄方向**）
  LEV 效应主张：延寿 20 年（保守）= 半年~数年照射
  Λ 测量：五路传感器融合 Λ=ΣwᵢΛᵢ，w={0.25,0.20,0.15,0.25,0.15}，秒级
参照假设（本批引入，非体系原文，显式声明）：
  H1 年龄线性锚定：Λ=7/8 ↔ 25 岁（"年轻"基准）；Λ=1/2 ↔ 65 岁（亚有序相上界=中老分界）；
    Λ=1/8 ↔ 90 岁（临终锚）。线性插值 → K = 65/0.75 ≈ 86.7 年/unitΛ
  H2 逆转目标：恢复至 Λ≥7/8（体系"年轻，收支平衡"相界）
  H3 剂量线性参照：逆转所需 ΔΛ 与 LEV 延寿 ΔΛ 同单位可比（线性剂量假设）
"""
import json
import numpy as np

OUT = {}
K = (90 - 25) / (7/8 - 1/8)          # 86.67 年/unitΛ（H1）
YOUNG_AGE, YOUNG_L = 25.0, 7/8

def age_from_L(L):
    return YOUNG_AGE + (YOUNG_L - L) * K

def years_reverse(L_now, L_target=YOUNG_L):
    return (L_target - L_now) * K if L_now < L_target else 0.0

def ref_table():
    rows = []
    for L in [0.90, 0.875, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.25, 0.15]:
        phase = ("有序相·年轻" if L >= 7/8 else
                 "亚有序相·中年" if L >= 1/2 else
                 "混沌相·老年" if L >= 1/8 else "临界崩塌·临终")
        rows.append({"Lambda": L, "phase": phase,
                     "ref_age_years": age_from_L(L),
                     "years_to_reverse_to_25": years_reverse(L)})
    return rows

def dose_reference():
    """剂量参照：LEV 延寿 20 年 ⟺ ΔΛ=20/K；各逆转目标所需 ΔΛ 与相对剂量。"""
    dlev = 20 / K
    rows = []
    for age_now in (40, 50, 60, 70):
        L_now = YOUNG_L - (age_now - YOUNG_AGE) / K
        dL = YOUNG_L - L_now
        rows.append({"current_age": age_now, "Lambda_now": L_now,
                     "target": "Λ=7/8（25 岁基准）", "required_dLambda": dL,
                     "relative_to_LEV_20y_dose": dL / dlev})
    return {"LEV_20y_dLambda": dlev, "rows": rows,
            "note": "相对剂量>1 的区间需要第三层（反云韶场回写）；≤1 区间理论上第一/二层（云韶场维持+LEV 照射）即可覆盖【理论参照】"}

if __name__ == "__main__":
    OUT["体系锚点"] = {"Λ相图": "≥7/8 年轻｜1/2~7/8 中年｜1/8~1/2 老年｜<1/8 临终",
                       "η逆龄方向": "η>7/8 → 净亏损<0 → 盈余逆龄",
                       "Λ融合": "Λ=ΣwᵢΛᵢ, w={0.25,0.20,0.15,0.25,0.15}",
                       "LEV主张": "延寿20年保守=半年~数年照射"}
    OUT["参照假设"] = {"H1": "线性年龄锚定 25/65/90 岁 ↔ Λ=7/8、1/2、1/8", "K_年每单位Λ": K,
                       "H2": "逆转目标=Λ≥7/8", "H3": "剂量线性参照"}
    OUT["逆转参照表"] = ref_table()
    OUT["剂量参照"] = dose_reference()
    OUT["label"] = "【理论参照·非实测】——全部锚点取自体系原文，假设 H1-H3 显式声明；实测以 Λ-年龄校准实验（100人/12万/6-12月）为准"
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/age_reverse_ref.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    print("== 逆转参照表（Λ → 参照年龄 → 恢复到 25 岁基准所需逆转年数） ==")
    for r in OUT["逆转参照表"]:
        print(f"  Λ={r['Lambda']:.3f}  {r['phase']:10s}  参照年龄={r['ref_age_years']:5.1f}岁  "
              f"逆转年数={r['years_to_reverse_to_25']:5.1f}")
    print("== 剂量参照（相对 LEV 延寿 20 年剂量） ==")
    for r in OUT["剂量参照"]["rows"]:
        print(f"  {r['current_age']}岁(Λ={r['Lambda_now']:.3f}) → 需ΔΛ={r['required_dLambda']:.3f} "
              f"= LEV 20年剂量的 {r['relative_to_LEV_20y_dose']:.2f}×")
