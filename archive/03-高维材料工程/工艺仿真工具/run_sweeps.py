# -*- coding: utf-8 -*-
"""
一键扫描（工艺仿真工具 · 主入口）
产出三样裁决/设计数据：
  ①模式 A/B 裁决数据包（同预算对比：图案对比度、周期、井数、连通性）
  ②超声条带周期表（5 材料 × 10 频率 × 衰减可行性）+ 共振模态对齐示例
  ③理论周期对照（FFT 实测主峰 vs 解析值）
运行：python run_sweeps.py  （轻算力，约 1-2 分钟）
"""
import numpy as np
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interference_sim import three_beam_120, modeB_layered, extract_wells, wells_graph, graph_metrics, dominant_period_fft
from ultrasound_sim import band_table, resonance_modes, nearest_mode
from materials_db import MATERIALS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
SEP = "=" * 76

print(SEP)
print("① 模式 A / 模式 B 裁决数据包（同能量预算 30×30 μm 视场）")
print(SEP)

grid, IA, beamsA, wlA = three_beam_120(I_total=3.0, wl=1.064, size=30.0, n=600)
theory_A = round(wlA / np.sqrt(3), 3)  # 三束120°六方晶格主周期理论值 λ/√3
pA = dominant_period_fft(IA, scale=30.0 / 600)
wA = extract_wells(IA, pct=15)
adjA, eA = wells_graph(wA, scale=30.0 / 600)
mA = graph_metrics(adjA)
contrastA = (IA.max() - IA.min()) / IA.mean()
print(f"模式 A（等频三束 120°，λ=1.064μm）:")
print(f"   FFT 实测主周期 {pA} μm vs 理论 {theory_A} μm")
print(f"   图案对比度(峰谷/均值) {contrastA:.2f} | 势阱 {len(wA)} | 边 {eA} | 分量 {mA['components']} | 最大片 {mA['largest_pct']}% | λ₂ {mA['lam2']}")

grid, IB, beamsB = modeB_layered(wls=(10.6, 1.286, 1.064), I_each=1.0, r=0.9, size=30.0, n=600)
pB = dominant_period_fft(IB, scale=30.0 / 600)
wB = extract_wells(IB, pct=15)
adjB, eB = wells_graph(wB, scale=30.0 / 600)
mB = graph_metrics(adjB)
contrastB = (IB.max() - IB.min()) / IB.mean()
print(f"模式 B（多频 10.6/1.286/1.064μm 自驻波层，r=0.9）:")
print(f"   FFT 实测主周期 {pB} μm（理论=各频 λ/2：5.30/0.643/0.532 μm 叠加）")
print(f"   图案对比度 {contrastB:.2f} | 势阱 {len(wB)} | 边 {eB} | 分量 {mB['components']} | 最大片 {mB['largest_pct']}% | λ₂ {mB['lam2']}")

print()
print("   裁决含义：模式 A 给出单一静态周期晶格（等频相干）；模式 B 给出多周期分层叠加（非晶格）。")
print("   连通性/势阱数接近时，选型依据=你要'单一周期晶格'（模式A）还是'多层复合图案'（模式B）。")

print(); print(SEP)
print("② 超声条带周期表（0.5-20 MHz 窗口，10 mm 厚，-6dB 判据）")
print(SEP)
all_rows = []
for name in MATERIALS:
    vL = MATERIALS[name]["vL"]
    rows = band_table(name, vL, L_thick=0.01)
    all_rows += rows
print(f"{'材料':<14}{'f(MHz)':>8}{'周期(mm)':>10}{'10mm可行':>10}")
for r in all_rows:
    print(f"{r['材料']:<14}{r['f_MHz']:>8}{r['条带周期_mm']:>10}{r['10mm厚可行']:>10}")

print(); print(SEP)
print("③ 共振模态对齐示例（固体驻波只能取离散振型；10 mm 厚钢）")
print(SEP)
vL = MATERIALS["Fe70Ni20Cr10"]["vL"]
for tgt in [1.0, 2.5, 5.0, 10.0]:
    r = nearest_mode(vL, 0.01, tgt * 1e6)
    print(f"   目标 {tgt:>5} MHz → 最近模态 n={r['n']:<3} 实际 {r['f_actual_MHz']:>7} MHz（偏差 {r['偏差%']}%）→ 条带周期 {r['条带周期_mm']} mm")

json.dump({"modeA": {"period_um": pA, "theory_um": theory_A, **mA, "wells": len(wA), "contrast": round(contrastA, 2)},
           "modeB": {"period_um": pB, **mB, "wells": len(wB), "contrast": round(contrastB, 2)},
           "ultrasound": all_rows},
          open(os.path.join(OUT, "sweep_results.json"), "w"), ensure_ascii=False, indent=1)
print(f"\n全部结果：{OUT}/sweep_results.json")
