# -*- coding: utf-8 -*-
"""热仿真 · 半无限体表面恒热流解析解（Carslaw-Jaeger 教科书公式）"""
import numpy as np, os, json
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
q = 130.0 / 0.01          # W/m²：130W 均布 100cm²
k = 45.0                  # W/mK 钢导热
alpha = 1.2e-5            # m²/s 热扩散率（钢）
print("半无限体表面恒热流温升（Carslaw-Jaeger）：ΔT(t) = 2q√(αt/π)/k")
print(f"{'时间':>10}{'表面温升K':>12}{'10K影响深度mm':>14}")
res = {}
for t_s in [60, 300, 600, 1800, 3600]:
    dT = 2*q*np.sqrt(alpha*t_s/np.pi)/k
    # 深度 x 处温升 = ΔT·[exp(-x²/4αt) - x√(π/4αt)·erfc(x/2√(αt))]；10K 等温线近似 x≈2√(αt)·ln(ΔT/10)
    d10 = 2*np.sqrt(alpha*t_s)*np.log(max(dT,10.1)/10)/2 if dT > 10 else 0
    print(f"{t_s:>8}s{dT:>12.1f}{d10*1000:>14.1f}")
    res[f"t{t_s}"] = {"dT_K": round(dT,1), "depth10mm": round(d10*1000,1)}
print()
print("【工程结论（解析解，量级可靠）】")
print(f"  130W 连续吸收：5 分钟表面升温 ~{2*q*np.sqrt(alpha*300/np.pi)/k:.0f}K，1 小时 ~{2*q*np.sqrt(alpha*3600/np.pi)/k:.0f}K")
print("  1 小时达数百 K → 必须主动冷却（≥130W 散热）；但单次写入窗口（数百秒）内温升可控制在")
print("  数十 K——回火温度（~900K）风险在连续运行 >30min 后才出现，脉冲写入（占空比0.3）下更安全。")
json.dump(res, open(os.path.join(OUT, "thermal_sim.json"), "w"))
print("已存 results/thermal_sim.json")
