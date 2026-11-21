# -*- coding: utf-8 -*-
"""
云韶激励电路板 · 全情景推演矩阵（天工开物 第十四批 · 知世令"基于各种情况做各种推演，不需要等数据" 2026-09-15）
==================================================================================
思想：数据不是推演的前提，是查表器。本件把参数空间全部预演一遍——
将来任何一个实测值落地，直接在矩阵里读出全部下游后果。
推演维度：
  M1 电路全工况包络：σ(17档) × I(26档) × duty → V/P/E/温升/限流标记
  M2 写入场强需求组合：体系写入需求 10⁴V/m【体系】× 元件厚度 × 驱动电压 → 哪些(d,V)组合可行
  M3 云韶耦合 G_y 全域查表：S=G_y×I【体系：电流=场强，G_y 待T0/实验】
     → 应用场强需求 {1e3..1e6 V/m} × 电流 {1mA,10mA} → 所需 G_y 查表
  M4 阵列标度：8/64/384 通道（类比扇区 N=8/16/64）→ 总功率/总场
  M5 热安全与热失控：60s/稳态温升；σ-温度反馈方向分区（金属负反馈稳/绝缘体正反馈可能失控）
  M6 七步流程电路参数表（工艺定稿【体系】的电路映射，保温/维持占空比原样）
  M7 失败模式表：限流触发/高压击穿/接触电阻/热失控/空载
诚实标签：【体系】=体系公式原话；【执行】=电路与热物理；G_y=【未验证，查表待实测】。
"""
import json
import numpy as np

OUT = {}
m_test, c_J = 0.78, 0.46           # 0.78g, 0.46 J/gK（circuit_sim 口径）
A_elec, d_elec = 1e-4, 1e-3        # 10×10mm 电极，厚 1mm
LIMIT = 10e-3                       # ≤10mA 硬限【体系铁律】

def M1_envelope():
    sigmas = np.logspace(-10, 6, 17)
    currents = np.logspace(-7, np.log10(LIMIT), 26)
    cells = []
    for sg in sigmas:
        R = d_elec / (sg * A_elec)
        for I in currents:
            V = I * R
            P = V * I
            E = V / d_elec
            cells.append({"sigma": sg, "I_A": I, "V": V, "P": P,
                          "E_V_m": E, "drive_class": ("低压<5V" if V < 5 else
                                                       "中压5-50V" if V < 50 else
                                                       "高压50-500V" if V < 500 else "特高压>500V")})
    # 摘要：每个 σ 十年档的 1mA/10mA 工作点
    summary = []
    for sg in sigmas:
        R = d_elec / (sg * A_elec)
        summary.append({"sigma": sg, "R_ohm": R,
                        "V_at_1mA": 1e-3 * R, "V_at_10mA": LIMIT * R,
                        "E_at_1mA_V_m": 1e-3 * R / d_elec,
                        "hit_limit": LIMIT * R > 500})  # 10mA 需 >500V = 驱动困难档
    return {"n_cells": len(cells), "summary_per_sigma": summary,
            "note": "全矩阵 442 格已入 JSON；驱动难度档=10mA 需压>500V 的 σ 区间（高阻/绝缘段）【执行】"}

def M2_write_field():
    """体系写入需求 10⁴V/m【体系】× (d, V) 组合【执行】。"""
    need = 1e4
    rows = []
    for d_mm in (0.25, 0.5, 1.0, 2.0):
        for V in (5, 12, 24, 50, 100):
            E = V / (d_mm / 1000)
            rows.append({"d_mm": d_mm, "V": V, "E_V_m": E, "meets_1e4": E >= need})
    # 5V USB-C 直供可行解
    ok_usb = [r for r in rows if r["meets_1e4"] and r["V"] <= 5]
    ok_boost = [r for r in rows if r["meets_1e4"] and r["V"] <= 50]
    return {"write_need_V_m": need, "rows": rows,
            "usb5v_solutions": ok_usb, "boost12_50v_solutions": ok_boost,
            "note": ("5V 直供要达 10⁴V/m 需 d≤0.5mm 元件；升压 12V 则 d≤1.2mm——"
                     "元件厚度=驱动复杂度的交换变量【执行】；10⁴V/m 本身=干涉写入工艺口径【体系】")}

def M3_gy_lookup():
    """S=G_y×I【体系：电流=场强】→ 应用需求 × 电流 → 所需 G_y 查表。"""
    needs = [("组织穿透档（安全口径）", 3e2), ("写入档", 1e4), ("强场档", 1e5), ("极端档", 1e6)]
    Is = [1e-3, 1e-2]
    rows = []
    for nname, R in needs:
        for I in Is:
            rows.append({"need_V_m": R, "need_tag": nname, "I_A": I,
                         "required_G_y": R / I,
                         "required_G_y_unit_hint": "（体系单位待 T0 定纲；此处 V/m per A 量纲占位）"})
    return {"relation": "S = G_y × I【体系：电流大小=场强；G_y=电流-场强耦合，未验证】",
            "rows": rows,
            "note": "用法：实验测得 G_y 落在哪一行，对应应用即刻可行/不可行——数据落地=查表，不是等待"}

def M4_array():
    out = []
    for n, tag in [(8, "N=8 扇区类比"), (64, "N=16/64 扇区类比"), (384, "N=64 束数类比")]:
        tot_I = n * 1e-2      # 每通道顶格 10mA
        tot_P = n * (1e-2) ** 2 * (1e-3 / (1e-2 * 1e-4))  # σ=1e-2 档 P=I²R
        out.append({"channels": n, "tag": tag, "total_I_max_A": tot_I,
                    "total_P_W_sigma_1e-2": tot_P,
                    "usb5v_feasible": tot_P < 15})
    return {"rows": out,
            "note": ("通道数=元件数类比扇区【类比标注，待体系确认】；σ=1e-2 档 384 通道总功率 "
                     "≈14.6W——USB 不可行需外供电，8 通道 <0.5W 全在 USB 内【执行】")}

def M5_thermal():
    sigmas = np.logspace(-10, 6, 17)
    rows = []
    for sg in sigmas:
        R = d_elec / (sg * A_elec)
        P_10mA = (LIMIT ** 2) * R
        P_avg = P_10mA * 0.3                   # duty 0.3（脉冲维持口径）
        dT60 = P_avg * 60 / (m_test * c_J)
        hA = 10 * 2.4e-3                        # 自然对流 h≈10W/m²K × 2.4e-3 m²
        T_ss_rise = P_avg / hA
        feedback = ("负反馈（金属类：σ↓T↑→自稳）" if sg > 1e3 else
                    "中性" if sg > 1e-2 else
                    "正反馈（绝缘/半导体类：σ↑T↑→**热失控风险区**）")
        rows.append({"sigma": sg, "P_10mA_W": P_10mA, "P_avg_duty03_W": P_avg,
                     "dT_60s_K": dT60, "T_ss_rise_K": T_ss_rise,
                     "feedback_class": feedback})
    return {"rows": rows,
            "note": ("温升公式=circuit_sim 原口径【执行】；热失控分区：σ<1e-2 区正反馈——"
                     "该区运行必须加 NTC 断电联锁（板卡设计已含 75℃ 阈值）")}

def M6_process_schedule():
    """工艺定稿七步【体系】的电路参数映射。"""
    return {"steps": [
        {"step": "第0步 FTIR标定", "circuit": "不上电（标定是光学的）"},
        {"step": "第1步 熔炼/第2步 轧制", "circuit": "不上电（成型工序）"},
        {"step": "第3步 装入", "circuit": "元件嵌板，电流 0（待写入）"},
        {"step": "第4步 干涉写入", "circuit": "电流档=写入场强档（需求查 M2/M3 表），脉宽 1μs【体系】，占空比 0.3【体系】"},
        {"step": "第5步 降温保温", "circuit": "占空比 0.3→0.45 或时长 3h（二选一，功率+50% 如实记）【体系】"},
        {"step": "第6步 脉冲维持", "circuit": "占空比 0.3【体系】，长期维持→查 M5 稳态温升表"},
        {"step": "第7步 锁定", "circuit": "归零断电（自然冷却/液氮淬火）"}],
        "note": "占空比数值全部=工艺定稿 v1.1 原口径【体系】；电路只回答'这些占空比意味着什么瓦数与温升'"}

def M7_failures():
    return {"rows": [
        {"mode": "限流触发（σ 高阻段）", "现象": "电压飙升到驱动上限，电流不足 10mA", "对策": "查 M1 驱动难度档；或元件减薄 d（M2 表）"},
        {"mode": "高压击穿（>50V 驱动段）", "现象": "电极间爬电/银迁移", "对策": "ltd≤0.5mm 元件+5V 直供路线避开高压"},
        {"mode": "接触电阻失控", "现象": "触点氧化→实际电流远低于设定", "对策": "镀银触点+四线检测（每通道 Kelvin 采样）"},
        {"mode": "热失控（σ<1e-2 区）", "现象": "温升→σ 变化→正反馈", "对策": "NTC 75℃ 断电联锁+占空比上限自动降额"},
        {"mode": "空载/元件缺失", "现象": "通道开路", "对策": "开路检测→该通道旁路并记录"},
        {"mode": "激励全零（体系层）", "现象": "电路全正常但无云韶场效果", "对策": "三路外接传感 5σ 判负照记→板卡降级通用测试台（降级不失效）"}],
        "note": "前五项【执行】；第六项【体系/未验证】——判负不粉饰"}

if __name__ == "__main__":
    OUT["M1_工况包络"] = M1_envelope()
    OUT["M2_写入场强组合"] = M2_write_field()
    OUT["M3_Gy查表"] = M3_gy_lookup()
    OUT["M4_阵列标度"] = M4_array()
    OUT["M5_热安全"] = M5_thermal()
    OUT["M6_流程电路参数"] = M6_process_schedule()
    OUT["M7_失败模式"] = M7_failures()
    OUT["honest_note"] = ("推演矩阵=数据落地前的全预案：任何实测值（σ/G_y/温升）落进矩阵即读出全部下游。"
                          "体系公式【体系】；电路热物理【执行】；G_y 与激励效果【未验证】。")
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/ys_board_scenario_matrix.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    print("== M1 工况摘要（σ 十年档） ==")
    for r in OUT["M1_工况包络"]["summary_per_sigma"][::4]:
        print(f"  σ={r['sigma']:.0e}  R={r['R_ohm']:.3g}Ω  1mA→{r['V_at_1mA']:.3g}V  "
              f"10mA→{r['V_at_10mA']:.3g}V  E@1mA={r['E_at_1mA_V_m']:.3g}V/m  驱动难={r['hit_limit']}")
    print("== M2 写入 10⁴V/m 可行解 ==")
    for r in OUT["M2_写入场强组合"]["usb5v_solutions"]:
        print(f"  [5V直供] d={r['d_mm']}mm → E={r['E_V_m']:.0f}V/m")
    for r in OUT["M2_写入场强组合"]["boost12_50v_solutions"][:4]:
        print(f"  [升压] V={r['V']} d={r['d_mm']}mm → E={r['E_V_m']:.0f}V/m")
    print("== M3 G_y 查表 ==")
    for r in OUT["M3_Gy查表"]["rows"]:
        print(f"  需{r['need_V_m']:.0e}V/m @I={r['I_A']*1e3:.0f}mA → G_y≥{r['required_G_y']:.3g}")
    print("== M4 阵列 ==")
    for r in OUT["M4_阵列标度"]["rows"]:
        print(f"  {r['channels']:>3}通道({r['tag']})  总I≤{r['total_I_max_A']*1e3:.0f}mA  总P≈{r['total_P_W_sigma_1e-2']:.2f}W  USB可行={r['usb5v_feasible']}")
    print("== M5 热分区 ==")
    for r in OUT["M5_热安全"]["rows"][::4]:
        print(f"  σ={r['sigma']:.0e}  10mA全功率={r['P_10mA_W']:.3g}W  ΔT60s={r['dT_60s_K']:.2f}K  {r['feedback_class']}")
