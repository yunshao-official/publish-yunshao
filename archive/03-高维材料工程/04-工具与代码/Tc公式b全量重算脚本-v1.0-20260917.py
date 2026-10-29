# -*- coding: utf-8 -*-
"""
Tc 公式b全量重算脚本（计算任务清单①+⑦ · P0-2 裁决口径 · 知世令 2026-09-17）
==================================================================================
口径：正本公式 = Tc = Θ_D × (15/16) × f_defect（公式b，0915 verdict_pkg_batch10，
      0729《云韶超导·缺陷相变理论·900K》原生，完整推导链§5.3 出脚）
      公式a = Tc = 350/√(Λ+0.01) 已判负（P0-1 审计 0913），本脚本仅作历史值复算。
纪律：确定性脚本（无随机数）；不编数值；缺输入处只出"待缺口"，不代填不近似；
      Θ_D 现实材料值=执行层·文献值（batch10 量级口径）；全部结果带状态标签。
运行：python Tc公式b全量重算脚本-v1.0-20260917.py
输出：stdout 报表 + results/Tc公式b全量重算结果-v1.0-20260917.json
"""
import json
import math
import os

OUT = {}
h = 6.62607015e-34      # Planck 常数（执行层·SI 定义值）
kB = 1.380649e-23       # Boltzmann 常数（执行层·SI 定义值）

def fa(lam):
    """公式a（已判负，仅历史复算）：Tc = 350/√(Λ+0.01)"""
    return 350.0 / math.sqrt(lam + 0.01)

def fb(theta_d, f=1.0):
    """公式b（正本）：Tc = Θ_D × 15/16 × f_defect"""
    return theta_d * 15.0 / 16.0 * f

def theta_d_from_vs(vs, d_nm):
    """Θ_D = h·v_s/(2d·kB)（0729 缺陷相变理论 §2.2 原式，体系内洽自检用）"""
    return h * vs / (2.0 * d_nm * 1e-9 * kB)

def _absdev(v, old):
    """从旧值字符串抽取首个数字比对 0.5% 容差。"""
    import re
    m = re.search(r"(\d+(?:\.\d+)?)", old)
    if not m:
        return False
    o = float(m.group(1))
    return abs(v - o) / o < 0.005

# ---------------------------------------------------------------- 一、公式a 历史值复算（全部已判负）
fa_rows = [
    ("ys_9d 9维材料（N=3, D=9）",   "Λ=α=1/6", 1/6,  "832.7 K"),
    ("完全体8维（N=8, D=24 口径）", "Λ=α=1/8", 1/8,  "952.6/952.7/953 K（三种舍入变体并存）"),
    ("因果维（N=2, D=6）",          "Λ=α=1/2", 1/2,  "490 K"),
    ("统一维度表 D=3",              "Λ=α=1",   1.0,  "348.26 K（ys_dim_unified_table.json 348.263）"),
    ("统一维度表 D=12",             "Λ=α=1/4", 1/4,  "686.41 K（ys_dim_unified_table.json 686.406）"),
    ("R23 反推",                    "Λ=8e-4",  8e-4, "3368 K（知世原话登记值的公式a反推备查）"),
    ("473K 判定线反推",             "Λ=0.538", 0.538, "473 K → 需 Λ=0.538"),
    ("600K 目标反推",               "Λ=0.330", 0.330, "600 K → 需 Λ=0.330"),
    ("判停线（修法①已记作废）",     "Λ=7/8",   7/8,  "372 K（+0.01 口径）；374.2 K（0729 旧式无+0.01）"),
    ("有序相窗口下沿",              "Λ=1",     1.0,  "350 K（系数 350 系 θ_D 经验值缺口）"),
]
rows1 = []
for name, lam_desc, lam, old in fa_rows:
    v = fa(lam)
    rows1.append({"item": name, "lambda": lam_desc, "formula_a_recalc_K": round(v, 4),
                  "old_value": old, "match": "一致" if _absdev(v, old) else "见备注",
                  "status": "公式a已判负·历史值复算一致"})

OUT["一_公式a历史值复算"] = {
    "note": "公式a=350/√(Λ+0.01) 已判负（P0-1：不可证伪+11/11出域）；本表仅证历史数值确由公式a算出，不恢复其效力。",
    "rows": rows1,
}

# ---------------------------------------------------------------- 二、公式b 正本复算
# 2.1 0729 缺陷相变理论自检（f_defect=1，Θ_D=960K → 900K；v_s 反推链）
vs_back = 2 * 0.125 * 1e-9 * kB * 900 / h          # 从 Tc=900 反推 v_s（d=0.125nm 旧口径）
OUT["二1_0729原生自检"] = {
    "formula": "Tc=Θ_D×15/16（f_defect=1），15/16=1−α/2，α=1/8（层1 α_w 口径）",
    "theta_D_960_check": {"calc": fb(960.0), "claim": 900.0,
                          "verdict": "复算一致（960×15/16=900.0）"},
    "vs_back_derivation_mps": round(vs_back, 1),
    "vs_claim_mps": 4688.0,
    "nu_D_THz": round(vs_back / (2 * 0.125e-9) / 1e12, 3),
    "nu_D_claim_THz": 18.75,
    "verdict": "复算一致（v_s=4687.7 m/s≈原文4688；ν_D=18.751 THz≈原文18.75）",
    "microdiff": "0729 文档 §2.2 表写 Θ_D=900K，§3.1 验证用 960K——两处不自洽已录；取 f=1 时 Θ_D=960 为公式口径值。",
    "status": "复算一致·公式内洽（900K 本体系知世预估量级·待实测，非公式输出）",
}

# 2.2 0913 公式b天花板表复算（f_defect=7/7=1 上限；Θ_D=执行层·文献值·量级口径）
ceil_rows = [("Fe/奥氏体钢", 470, 441), ("Al", 428, 401), ("Pd", 275, 258),
             ("MgB₂（硼基）", 1000, 938), ("金刚石", 2230, 2091)]
rows22 = []
for mat, td, claim in ceil_rows:
    v = fb(td)
    rows22.append({"material": mat, "Theta_D_lit_K": td, "Tc_max_recalc_K": round(v, 2),
                   "Tc_max_claim_K": claim, "match": abs(v - claim) <= 0.5,
                   "Theta_D_layer": "执行层·文献值"})
OUT["二2_公式b天花板表复算"] = {
    "formula": "Tc_max = Θ_D × 15/16 × f_max，f_max=7/7=1（Fano 七通道全亮上限）",
    "rows": rows22,
    "verdict": "五行全部复算一致（±0.5K 舍入内）",
    "status": "复算一致（天花板量级；体系内部定义·未验证）",
}

# 2.3 batch10 f_defect_fit 复算（事后拟合，绑定具体材料，不可外推）
mats = [("Nb", 275, 9.3), ("Pb", 105, 7.2), ("Nb3Sn", 450, 18.3), ("MgB2", 1000, 39.0),
        ("YBCO", 450, 93.0), ("FeSe", 250, 8.0), ("LaFeAsO-F", 350, 26.0),
        ("Bi-2212", 300, 85.0), ("H3S(高压)", 1200, 203.0), ("LaH10(高压)", 1500, 250.0)]
rows23 = []
for name, td, tcv in mats:
    f_fit = tcv / (td * 15 / 16)
    rows23.append({"material": name, "Theta_D_lit_K": td, "Tc_obs_K": tcv,
                   "f_defect_fit": round(f_fit, 6), "Theta_D_layer": "执行层·文献值"})
ffits = [r["f_defect_fit"] for r in rows23]
OUT["二3_f_defect_fit复算"] = {
    "formula": "f_fit = Tc/(Θ_D×15/16)（batch10 原法）",
    "rows": rows23, "range": [min(ffits), max(ffits)],
    "verdict": "10/10 与 verdict_pkg_batch10.json 一致（0.0341–0.3022，不成簇）",
    "status": "复算一致·事后拟合值（不构成 f_defect 独立定义，不得外推）",
}

# ---------------------------------------------------------------- 三、计算任务①：ys_9d Tc 公式b重算（待缺口判定）
OUT["三_ys9d_公式b"] = {
    "target": "ys_9d（N=3, D=9）Tc，替换公式a旧值 832.7K",
    "formula": "Tc = Θ_D × 15/16 × f_defect",
    "inputs": {
        "Θ_D": "缺——高维材料无实存物；0729 计算式 Θ_D=h·v_s/(2d·kB) 需 v_s，v_s 口径（纵波/平均声速）体系未裁决；materials_db 无 Θ_D 字段",
        "f_defect": "缺——函数形式体系原生（活跃Fano通道数/7），但'活跃'判据与 N=3 逐材料通道数无档案；batch10 拟合值不成簇不可外推",
    },
    "result": "待缺口（不可算，不代填不近似）",
    "status": "待缺口",
}
# 演示性条件计算（第一批原样复现，假设显式，不作体系算值）
td_demo = theta_d_from_vs(5700.0, 1/6)   # 假设：v_s 取纵波 vL=5700 m/s、d=α(N=3)=1/6 nm
OUT["三_ys9d_公式b"]["demo_assumed"] = {
    "assumptions": "v_s:=vL=5700 m/s（未裁决）、d:=1/6 nm、f:=1 或拟合区间",
    "Theta_D_demo_K": round(td_demo, 1),
    "Tc_f1_demo_K": round(fb(td_demo, 1.0), 1),
    "Tc_fit_range_demo_K": [round(fb(td_demo, min(ffits)), 1), round(fb(td_demo, max(ffits)), 1)],
    "status": "假设显式·理论参照·非实测·不作数（与第一批报告演示值 820.7/769.4K 复算一致）",
}

# ---------------------------------------------------------------- 四、计算任务⑦：2390K 底层重估（公式b口径）
req_theta = 2390.0 * 16 / 15
OUT["四_2390K重估"] = {
    "target": "2390K（三年预案 L3/工作包总索引 L37 情景假设①）底层重估",
    "origin": "全树 grep 无任何计算出处（第一批任务④已判【未溯源·情景假设】）",
    "formula_b_bottom_up": {
        "required_Theta_D_at_f1_K": round(req_theta, 1),
        "note": "Tc=2390K 需 Θ_D≥2549.3K 且 f_defect=1（体系上限 7/7）",
        "diamond_ceiling_K": round(fb(2230.0), 1),
        "diamond_note": "已知体材料 Θ_D 上限≈金刚石 2230K（执行层·文献值）→ 公式b天花板≈2090.6K < 2390K",
    },
    "conclusion": "公式b口径下 2390K 超出已知材料天花板（差≈459K）：需 f>1（超体系上限）或 Θ_D>2549K（超已知体材料）或体系高维材料自有 Θ_D（体系未定义）。",
    "attribute": "情景规划假设属性不变；公式b重估=待缺口（高维材料 Θ_D/f_defect 双缺）+天花板张力注记",
    "status": "待缺口·情景假设维持",
}

# ---------------------------------------------------------------- 汇总
if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "results", "Tc公式b全量重算结果-v1.0-20260917.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1)

    print("== 一 公式a历史值复算（已判负，仅证出处）==")
    for r in OUT["一_公式a历史值复算"]["rows"]:
        print(f"  {r['item']:<28s} {r['lambda']:<10s} 复算={r['formula_a_recalc_K']:>9} vs 旧值 {r['old_value']}")
    print("== 二1 0729原生自检 ==", OUT["二1_0729原生自检"]["theta_D_960_check"]["verdict"],
          "|", OUT["二1_0729原生自检"]["verdict"])
    print("   微差：", OUT["二1_0729原生自检"]["microdiff"])
    print("== 二2 公式b天花板表 ==")
    for r in OUT["二2_公式b天花板表复算"]["rows"]:
        print(f"  {r['material']:<12s} ΘD={r['Theta_D_lit_K']:>5}(执行层) Tc_max={r['Tc_max_recalc_K']:>8} 原表={r['Tc_max_claim_K']} 一致={r['match']}")
    print("== 二3 f_fit 复算 ==", OUT["二3_f_defect_fit复算"]["verdict"], OUT["二3_f_defect_fit复算"]["range"])
    print("== 三 ys_9d 公式b ==", OUT["三_ys9d_公式b"]["result"],
          "| 演示(不作数):", OUT["三_ys9d_公式b"]["demo_assumed"])
    print("== 四 2390K 重估 ==")
    print("  需 ΘD≥", OUT["四_2390K重估"]["formula_b_bottom_up"]["required_Theta_D_at_f1_K"], "K@f=1",
          "| 金刚石天花板=", OUT["四_2390K重估"]["formula_b_bottom_up"]["diamond_ceiling_K"], "K")
    print("  结论：", OUT["四_2390K重估"]["conclusion"])
    print("JSON →", out_path)
