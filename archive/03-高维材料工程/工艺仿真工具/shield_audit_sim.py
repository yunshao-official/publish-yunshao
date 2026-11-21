# -*- coding: utf-8 -*-
"""
护盾三件审计仿真（天工开物 第五批 · 知世令"我要护盾" 2026-09-15）
==================================================================================
对象（计划原文口径，0729修正版）：
  S1 深渊护盾（§1.4）：膜层<1mm 防步枪弹；冲击波"完全隔绝"；持续>10min@100kW；
     储能环100MJ；全功能预算50kW（护盾份额10kW）
  S2 概率偏转·弹道护盾（第六章十一）：不硬挡、改概率权重；α=1/8，k=5累积48.7%；
     响应~6飞秒；对激光/EMP无效（原文自认）
  S3 相变护盾·63层构型切换（第六章十二）：(Z2)³ 64构型；单次吸能=晶格能/64；
     3mm内甲≈189mm传统装甲；k=8恢复63%（原文数字）
方法：真实物理账本——动量/压强/面密度/能量密度四账 + 真实机制映射表。
诚实口径：标准公开弹道数据与经验公式（Kinney-Graham 超压、NIJ 面密度口径）；
影子机制（时空度量曲率/概率流扭曲/构型群）不入账，只审其数字主张。
"""
import json
import numpy as np

OUT = {}

# ---------------- 公共弹道表（公开口径） ----------------
THREATS = [
    ("9x19手枪",      0.008,  360, "软防护级"),
    ("7.62x39步枪",   0.0079, 715, "原文引用（约2000J）"),
    ("7.62x51步枪",   0.0095, 833, "北约弹"),
    ("12.7mm重机",    0.046,  860, "重防护级"),
    ("RPG PG-7(助推后)", 2.3,  295, "化学能破甲为主"),
    ("82mm迫弹",      3.5,    210, "落速口径"),
]

def ke(m, v):
    return 0.5 * m * v * v

# ---------------- S1 深渊护盾 ----------------
def s1_abyss():
    out = {}
    # 动量/压强账：假设膜层拦下弹丸（理想化）
    rows = []
    for name, m, v, note in THREATS[:4]:
        p = m * v
        E = ke(m, v)
        nose_area = np.pi * (0.0038) ** 2 / 4      # 7.62mm 弹头口径截面积 m²（统一口径化）
        contact_t = 100e-6                          # 接触时间量级
        F_avg = p / contact_t
        P_local = F_avg / nose_area / 1e9           # GPa
        body_dv = p / 60.0                          # 假设冲量散布到60kg人体
        rows.append({"threat": name, "KE_J": E, "momentum_kgms": p,
                     "avg_force_100us_N": F_avg, "local_pressure_GPa": P_local,
                     "wearer_delta_v_m_s": body_dv, "note": note})
    out["momentum_account"] = rows
    # 面密度账：1mm 膜 vs 实际防弹面密度
    mats = {"钢": 7850, "UHMWPE": 970, "石墨烯膜": 2200, "芳纶": 1440}
    need = {"III级(7.62 FMJ硬板)": 25, "IV级(7.62 AP硬板)": 35, "IIIA级(手枪软甲)": 5.5,
            "189mm RHA等效(原文主张)": 7850 * 0.189}
    out["areal_density"] = {
        "membrane_1mm_kg_m2": {k: v * 0.001 for k, v in mats.items()},
        "required_kg_m2": need}
    # 冲击波账：Kinney-Graham 入射超压（1kg TNT 标定；公式原生单位 bar，换算 kPa）
    def pso_kpa(Z):
        bar = 808 * (1 + (Z / 4.5) ** 2) / np.sqrt((1 + (Z / 0.048) ** 2) *
                (1 + (Z / 0.32) ** 2) * (1 + (Z / 1.35) ** 2))
        return bar * 98.07
    blast = []
    for W, d in [(1.0, 3.0), (1.0, 5.0), (10.0, 10.0)]:
        Z = d / W ** (1 / 3)
        P = pso_kpa(Z)
        torso_A = 0.3                                # 躯干迎爆面积 m²
        t_pos = 3e-3
        F = P * 1e3 * torso_A
        blast.append({"TNT_kg": W, "distance_m": d, "Z": Z, "incident_P_kPa": P,
                      "torso_force_kN_at_0.3m2": F / 1e3,
                      "equiv_static_mass_kg": F / 9.81})
    out["blast_account"] = {
        "rows": blast,
        "note": "有限尺寸膜层无法'完全隔绝'：冲击波绕射+呼吸通路；真实路线=结构+密封+超压呼吸（防雷口径）"}
    # 能耗账：100MJ 与"多发耗尽"的自洽性
    E_round = ke(0.0079, 715)
    out["energy_account"] = {
        "storage_MJ": 100, "rifle_KE_J": E_round,
        "shots_if_1x_KE": 100e6 / E_round,
        "per_shot_cost_J_for_50_shot_exhaust": 100e6 / 50,
        "per_shot_over_KE_ratio_for_50shot": (100e6 / 50) / E_round,
        "note": "原文'连续多发→储能耗尽'要求每发成本≈动能的1000倍量级，原文无此依据；若1:1则10万发——内部不自洽",
        "smes_volume_check_m3_at_200L_200m3": {"practical_10T_magnetic_pressure_MJ_m3": 40.0,
                                               "needed_100MJ_min_volume_m3": 100e6 / 40e6}}
    return out

# ---------------- S2 概率偏转护盾 ----------------
def s2_probability():
    out = {}
    # 算术复核
    out["arithmetic"] = {
        "formula": "1-(1-1/8)^k",
        "k5": 1 - (7 / 8) ** 5,
        "claimed_k5": 0.487, "match": abs(1 - (7 / 8) ** 5 - 0.487) < 1e-3}
    # 需求账：偏转需要横向冲量（真实物理第一账）
    rows = []
    cases = [("9x19手枪", 0.008, 360, 50, 0.5),
             ("7.62x51步枪", 0.0095, 833, 100, 0.5),
             ("RPG PG-7", 2.3, 295, 100, 1.0),
             ("82mm迫弹", 3.5, 210, 500, 2.0)]
    for name, m, v, R, miss in cases:
        t = R / v
        a = 2 * miss / t ** 2
        F = m * a
        rows.append({"threat": name, "range_m": R, "time_to_target_s": t,
                     "lateral_accel_m_s2": a, "force_N": F,
                     "impulse_Ns": F * t})
    out["deflection_requirement"] = {
        "rows": rows,
        "note": "偏转所需力极小(0.4~15N)——瓶颈不在力的大小，在①耦合(场如何抓住弹体)②探测-反应链"}
    # 耦合机制表（真实物理）
    bullet_V = 1.2e-6   # 7.62 弹体体积 m³（9.5g/8000kg·m⁻³量级）
    v_b = 833.0
    eddy_F = 5.8e7 * bullet_V * v_b * 1.0 ** 2          # σ·V·v·B²，1T
    ferro_F = 1.7e6 * bullet_V * 10.0                    # M_s·V·∇B，10T/m
    rad_pressure_I = 0.66 * 3e8 / (2 * 5e-5)             # 0.5cm² 上出 0.66N 所需光强
    pulse_E = (1.0 ** 2 / (2 * 4 * np.pi * 1e-7)) * 1.0  # 1T·1m³ 磁能
    out["coupling_mechanisms"] = {
        "eddy_conductive_B1T_N": eddy_F,
        "eddy_note": "涡流偏转（导电弹体）：1T 量级场即可出 >>需求力；真实文献锚=磁/感应拦截研究",
        "pulse_field_energy_1T_1m3_J": pulse_E,
        "ferro_gradient_10Tpm_N": ferro_F,
        "ferro_note": "铁磁梯度力（钢芯弹）：10T/m 梯度×超导磁体=重装备级，非穿戴级",
        "radiation_pressure_I_W_m2": rad_pressure_I,
        "radiation_note": "辐射压力对一切弹体有效但光强需求 ~2e11 W/m²，等效激光烧蚀=硬杀伤APS口径",
        "dose_note": "对速射步枪弹(30发/秒)烧蚀能耗 30-75MW 级=不可穿戴；对 RPG(单发)100kW 级=现实APS已实证"}
    # 反应链时间账
    out["reaction_chain"] = {
        "rifle_100m_flight_s": 100 / 833,
        "APS_real_reaction_s": "0.1~0.5s（Trophy/Iron Fist 公开口径）",
        "claimed_response_s": 6e-15,
        "note": "6飞秒无意义：真约束=传感器+决策+执行器链，非'概率场响应时间'"}
    return out

# ---------------- S3 相变护盾63层 ----------------
def s3_phasechange():
    out = {}
    # 算术复核
    eta = lambda k: 7 / 8 * (1 - (1 / 8) ** k)
    out["arithmetic"] = {
        "M64_layers": 63, "claimed_189mm_from_3mm": "3×63=189 算术一致",
        "recovery_formula_eta_k": "7/8×[1-(1/8)^k]",
        "eta_k8_value": eta(8),
        "claimed_k8_recovery": 0.63,
        "inconsistency": "η(8)=87.5%≠63%——原文内部不自洽（常数问命中）"}
    # 能量密度账：3mm ≡ 189mm RHA 需要多少吸能
    # 基准：7.62 AP 需 ~15mm RHA；189mm RHA 的防护对象=反装甲级
    rho_steel, rho_inner = 7850, 2000
    areal_189 = rho_steel * 0.189
    areal_3 = rho_inner * 0.003
    ratio = areal_189 / areal_3
    # 钢装甲对穿甲弹的有效吸能比能 ~0.5-1 kJ/g（口径值，公开装甲学量级）
    steel_spec = 0.75e6  # J/kg（0.75 kJ/g 量级）
    needed_spec = steel_spec * ratio
    out["energy_density_account"] = {
        "areal_189mm_RHA_kg_m2": areal_189, "areal_3mm_inner_kg_m2": areal_3,
        "needed_mass_efficiency_x": ratio,
        "steel_ballistic_specific_absorption_J_kg": steel_spec,
        "needed_specific_absorption_J_kg": needed_spec,
        "needed_specific_absorption_J_g": needed_spec / 1000,
        "needed_specific_absorption_kJ_g": needed_spec / 1e6,
        "known_phase_change_limits_J_g": {
            "石蜡熔化": 0.2, "水气化(总热)": 2.6, "铁气化(总热)": 6.3,
            "ZrO2相变增韧(有效)": 0.1},
        "verdict": (f"需 {needed_spec/1e6:.0f} kJ/g 级吸能，超已知一切相变上限"
                    f"（铁全气化 6.3 kJ/g）约 {needed_spec/1e6/6.3:.0f} 倍——'3mm≡189mm'能量密度账不成立")}
    # 真实机制映射
    out["real_mechanism_mapping"] = {
        "剪切增稠流体STF织物": "非牛顿'遇击变刚'=构型切换的真实近亲；面密度与芳纶同级，挡手枪弹，步枪需插板",
        "ZrO2相变增韧陶瓷": "四方→单斜吸能增韧（不可逆）；真实陶瓷装甲核心机制之一",
        "爆炸反应装甲ERA": "化学能做功推开穿甲体=真实'构型切换吸能'天花板，面密度重、不可逆、单次性",
        "self_note": "三者都无法同时满足：可逆+可恢复+3mm面密度挡步枪——原文组合主张无真实对应"}
    return out

if __name__ == "__main__":
    OUT["S1_深渊护盾"] = s1_abyss()
    OUT["S2_概率偏转护盾"] = s2_probability()
    OUT["S3_相变护盾63层"] = s3_phasechange()
    OUT["honest_note"] = ("真实物理账本口径：弹道数据=公开标准值；超压=Kinney-Graham；"
                          "面密度=NIJ口径；影子机制不入账只审数字主张。"
                          "数学实验口径，不构成物理结论，结论以实测为准。")
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/shield_audit.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    p = OUT["S1_深渊护盾"]["momentum_account"]
    for r in p:
        print(f"[S1] {r['threat']:12s} KE={r['KE_J']:8.0f}J p={r['momentum_kgms']:6.2f} "
              f"P_local={r['local_pressure_GPa']:6.2f}GPa 人体Δv={r['wearer_delta_v_m_s']:.3f}m/s")
    print("[S1] 面密度: 1mm膜", {k: round(v, 2) for k, v in OUT["S1_深渊护盾"]["areal_density"]["membrane_1mm_kg_m2"].items()})
    print("[S1] 需求:", {k: round(v, 1) for k, v in OUT["S1_深渊护盾"]["areal_density"]["required_kg_m2"].items()})
    b = OUT["S1_深渊护盾"]["blast_account"]["rows"]
    for r in b:
        print(f"[S1] 冲击波 {r['TNT_kg']}kg@{r['distance_m']}m: P={r['incident_P_kPa']:.0f}kPa "
              f"躯干受力={r['torso_force_kN_at_0.3m2']:.1f}kN(≈{r['equiv_static_mass_kg']:.0f}kg静载)")
    a2 = OUT["S2_概率偏转护盾"]["arithmetic"]
    print(f"[S2] 算术: k=5偏移={a2['k5']:.3f} vs 原文0.487 match={a2['match']}")
    for r in OUT["S2_概率偏转护盾"]["deflection_requirement"]["rows"]:
        print(f"[S2] {r['threat']:10s} R={r['range_m']}m t={r['time_to_target_s']:.3f}s "
              f"偏转需力={r['force_N']:.2f}N 冲量={r['impulse_Ns']:.3f}N·s")
    c = OUT["S2_概率偏转护盾"]["coupling_mechanisms"]
    print(f"[S2] 涡流(1T)={c['eddy_conductive_B1T_N']:.0f}N 脉冲场能={c['pulse_field_energy_1T_1m3_J']:.2e}J "
          f"铁磁梯度={c['ferro_gradient_10Tpm_N']:.1f}N 光强需={c['radiation_pressure_I_W_m2']:.2e}W/m²")
    a3 = OUT["S3_相变护盾63层"]["arithmetic"]
    e3 = OUT["S3_相变护盾63层"]["energy_density_account"]
    print(f"[S3] η(8)={a3['eta_k8_value']:.4f} vs 原文63% → {a3['inconsistency']}")
    print(f"[S3] 质量效率需×{e3['needed_mass_efficiency_x']:.0f} → 需吸能{e3['needed_specific_absorption_J_g']:.1f}kJ/g "
          f"vs 铁全气化6.3kJ/g → {e3['verdict'][:40]}…")
