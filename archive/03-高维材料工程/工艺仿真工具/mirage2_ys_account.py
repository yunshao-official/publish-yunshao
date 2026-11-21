# -*- coding: utf-8 -*-
"""
蜃楼 v2.0 · 体系原生口径体素账（天工开物 第七批续 · 知世裁决"云韶场啊！！！" 2026-09-15）
==================================================================================
机制层（体系原生，蜃楼v2.0 宣言原文）：
  反云韶场三频干涉阱 → 触发低维→高维回写 → 维度界面折射能以可见光释放（体素）
  → 云韶场梯度调制波前 → 边界条件逆问题反推驱动。
  电磁/声学器件只是场的执行器，不是成像机制。

本件只算执行器层与调度层两笔可复算的账，机制层按体系口径如实引用：
  账A 建阱维持功耗（执行器层，通用电磁学）：阱场能不能耗、源效率才是实耗——
      证明"建阱"在电费上不构成约束（与知世裁决一致）。
  账B 触发扫描帧率（调度层）：体素开关=第三束扫到哪个阱哪个亮 →
      动态成像瓶颈=寻址率，哈密顿求解器排程（X8：分时复用+扫描排序决定帧率）。

诚实口径（K-4 双向引用）：
  - 亮度唯一来源=T0 折射能公式（体系自认当前不存在，Q-2）→ 本件不给亮度数；
  - 反云韶场触发强度先验 ~1/7140（体系参数自算）→ V1/V2 判据=单光子级探测；
  - 度规场按体系定义场强恒为零，不进成像链（Q-6 暂定排除）；
  - 白昼=条件式研究目标（Q-5），决策时点 2027-06-30（Q-10）。
"""
import json
import numpy as np

OUT = {}

def account_A_trap_power():
    """账A：建阱维持功耗（执行器层）。扫描聚焦架构：任一时刻只有并行阱数的
    焦点需满场强，平均功率=单阱功率×并行阱数——不由显示体素总数决定。"""
    P0 = 0.5 * 3e8 * 8.854e-12           # I = P0·E²，P0=1.328e-3 W·m⁻²/V⁴
    eta = 0.01                            # THz/光源墙插效率 1%（保守）
    spot_area = 1e-6                      # 单阱焦点截面积 m²（mm 级束腰）
    rows = []
    for E in (1e2, 1e3, 1e4):
        I = P0 * E**2                     # 行波强度 W/m²
        p_trap = I * spot_area / eta      # 单阱墙插 W
        rows.append({"E_V_m": E, "wave_intensity_W_m2": I,
                     "single_trap_wallplug_W": p_trap,
                     "n100_parallel_W": p_trap * 100,
                     "n2500_parallel_W": p_trap * 2500})
    return {"spot_area_m2": spot_area, "source_eff": eta,
            "rows": rows,
            "note": ("扫描聚焦架构：平均电费=单阱×并行阱数，与显示体素总数无关。"
                     "单阱（mm² 束腰）10³V/m=0.13W、10⁴V/m=13.3W（墙插1%）；"
                     "原文 5kW 全息份额可维持 100 并行阱@10⁴V/m 或 2500 并行阱@10³V/m——"
                     "**建阱不构成功耗约束（与知世裁决一致）**。触发所需场强体系内未定（T0/V1 实测）；"
                     "只有'全域同时满场强'才回百万瓦级，显示不需要全域")}

def account_B_frame_rate():
    """账B：触发寻址率→帧率。体素开关=第三束扫到哪个阱哪个亮。"""
    N_vox = {"8×8 阱阵列(V3 目标)": 64,
             "全息级 250 万体素(原文口径)": 2_500_000,
             "4K 平面 830 万(极限口径)": 8_294_400}
    addressing = [("振镜", 1e3), ("AOD 声光偏转", 1e5), ("AOD+SLM 多点×100", 1e7),
                  ("AOD+SLM 多点×100，10 束并行", 1e8)]
    rows = []
    for a_name, rate in addressing:
        row = {"addressing": a_name, "pointing_per_s": rate}
        for vname, n in N_vox.items():
            row[vname + "_刷新fps"] = rate / n
        rows.append(row)
    return {"rows": rows,
            "note": ("30fps 动态 4K 需 2.5×10⁸ 寻址/秒 → 多点SLM×100 + ≥25 束并行触发"
                     "（或哈密顿求解器扫描排序+分时复用，X8 口径）；"
                     "V3 目标 64 体素静态图任何寻址器都绰绰有余")}

if __name__ == "__main__":
    OUT["账A_建阱功耗"] = account_A_trap_power()
    OUT["账B_寻址帧率"] = account_B_frame_rate()
    OUT["honest_note"] = ("体系原生口径：机制层=云韶场/反云韶场/折射能（蜃楼v2.0 原文）；"
                          "本件只算执行器与调度两笔可复算账；亮度不预言（Q-2，唯一来源=T0）。"
                          "数学实验口径不构成物理结论。")
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/mirage2_ys_account.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    print("== 账A 建阱维持功耗（扫描聚焦架构，墙插1%） ==")
    for r in OUT["账A_建阱功耗"]["rows"]:
        print(f"  E={r['E_V_m']:.0e}V/m  行波强度={r['wave_intensity_W_m2']:.3g}W/m²"
              f"  单阱={r['single_trap_wallplug_W']:.3g}W"
              f"  100并行={r['n100_parallel_W']:.3g}W  2500并行={r['n2500_parallel_W']:.3g}W")
    print("== 账B 寻址率→刷新率（fps） ==")
    for r in OUT["账B_寻址帧率"]["rows"]:
        print(f"  {r['addressing']:26s} 64体素:{r['8×8 阱阵列(V3 目标)_刷新fps']:>10.3g}"
              f"  250万:{r['全息级 250 万体素(原文口径)_刷新fps']:>10.3g}"
              f"  4K:{r['4K 平面 830 万(极限口径)_刷新fps']:>10.3g}")
