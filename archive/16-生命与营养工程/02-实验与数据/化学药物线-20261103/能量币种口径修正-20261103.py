# -*- coding: utf-8 -*-
# 能量币种口径修正 · 化学线过程件 · 20261103
# 起因：对接二曾把"全心摄氧"写成 9 mL/min（我方假设值），
#       文献侧 ¹¹C-acetate PET 给出 MVO2 = 0.088 ml/g/min（局部质量归一）。
#       两者不是同一口径，必须换算后再看 7:1 达标率。
# 纪律：只改执行层输入口径，不改判据、不改 α/η、不撤销钟表读法判负。
kcal_O2 = 20.1          # J/mL O2（体系档沿用定标件同一换算）
P_mech  = 1.065         # W，定标件 §5（93bpm x 5L/min x 0.0229）→ 与 CPO 文献 1.15 W 同量级
mVO2    = 0.088         # ml/g/min，DOI=10.1016/j.ijcha.2019.100452（他方声明·未本机复算）
for M in (283.0, 300.0):
    VO2   = mVO2 * M                    # ml/min 全心
    P_met = VO2 * kcal_O2 / 60.0        # W
    P_rec = P_met - P_mech              # 非机械代谢功率＝可作修复配额的部分（上界读法）
    need  = 7.0 * P_mech
    eff   = P_mech / P_met
    print(f"心肌质量 {M:.0f} g -> 全心摄氧 {VO2:5.1f} ml/min -> 代谢功率 {P_met:5.2f} W "
          f"-> 机械效率 {eff*100:4.1f}% -> 可用修复 {P_rec:5.2f} W / 需 {need:4.2f} W "
          f"= 达标率 {P_rec/need*100:5.1f}%")
# 对照：原口径（9 mL/min 假设）
VO2_old = 9.0
P_old   = VO2_old * kcal_O2 / 60.0
print(f"原口径 9.0 ml/min -> 代谢功率 {P_old:.2f} W -> 可用修复 {P_old-P_mech:.2f} W "
      f"-> 达标率 {(P_old-P_mech)/(7*P_mech)*100:.1f}%")
# 频率侧的跨代核对（CC-1 附）
peaks = [619, 657, 675, 700, 740, 760, 800, 820, 840, 860]
cands = {"甲310K": 724.84, "现载波": 804.0, "丙310K": 966.45}
for name, lam in cands.items():
    best = min(peaks, key=lambda p: abs(lam - p) / p)
    dev  = (lam - best) / best * 100
    print(f"{name} {lam:7.2f} nm -> 最近实测峰 {best} nm 偏差 {dev:+.2f}%"
          f"（±3%带={'在带内' if abs(dev) <= 3 else '不在带内'}）")
