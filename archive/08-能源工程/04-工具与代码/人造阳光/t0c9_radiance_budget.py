#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t0c9_radiance_budget.py —— 人造阳光 T0-C9 辐亮度/étendue 预算表（可复跑）

用途：
  给定目标（AM1.5G 1000 W/m2 且光束全角 0.533°，或 AM0 1361 W/m2），
  算出所需源辐亮度，并把各类光源的辐亮度换算成
  “在该 0.53° 光束内实际能达到的面辐照度 E = Ω·L”。

物理依据（主流，非体系）：
  - 太阳立体角 Ω = π(θ/2)²，θ=0.533°；
  - 无源光学不提高辐亮度（étendue / 亮度守恒）：E_max(给定Ω) = Ω·L_source；
  - 朗伯源辐亮度 L = M/π = (出射度)/π；黑体 M=σT⁴；
  - 最大浓度比 C_max = n²/sin²(θ_half)。

边界：
  光源档位里的“W/mm2 / 面积”是本文件的**模型假设档位**，不是器件实测值；
  真实器件须用数据表或辐亮度计实测替换（脚本可改 ROWS 复跑）。
  标签：模型推演（非实测）。

运行：python t0c9_radiance_budget.py
"""

import json
import os
from datetime import date

import numpy as np

SIGMA = 5.670374419e-8  # W/m2/K4
PI = np.pi

THETA_FULL_DEG = 0.533  # 太阳全角（外部事实）
OMEGA = PI * (np.deg2rad(THETA_FULL_DEG) / 2) ** 2  # sr
E_TARGETS = {"AM1.5G": 1000.0, "AM0": 1361.0}

# (名称, 假设出射度 W/m2 或 辐亮度 W/m2/sr, 类型)
# 类型 "M"：给定出射度（朗伯源 L=M/pi）；类型 "P_over_A"：给定功率与发光面积
ROWS = [
    ("LED 1 W/mm2",            1e6,   "M"),
    ("LED 3 W/mm2",            3e6,   "M"),
    ("LED 10 W/mm2",           1e7,   "M"),
    ("LED 30 W/mm2",           3e7,   "M"),
    ("micro-LED 100 W/mm2",    1e8,   "M"),
    ("黑体 3000K",              SIGMA * 3000 ** 4, "M"),
    ("黑体 5000K",              SIGMA * 5000 ** 4, "M"),
    ("黑体 5772K",              SIGMA * 5772 ** 4, "M"),
]

LASER_PHOSPHOR = [  # 名称, 泵浦功率 W, 发光面积 m2
    ("激光泵荧光体 100W/0.1mm2", 100.0, 1e-7),
    ("激光泵荧光体 500W/0.25mm2", 500.0, 2.5e-7),
]


def radiance_from_M(M):
    return M / PI


def report(E_target, L_target):
    print(f"\n目标：E={E_target:.0f} W/m2 于全角 {THETA_FULL_DEG}° 内"
          f"（Ω={OMEGA:.3e} sr）→ 所需源辐亮度 L={L_target:.3e} W/(m2·sr)")
    print(f"{'源':30s} {'L W/(m2·sr)':>13s} {'L/L目标':>9s} {'E=Ω·L W/m2':>13s} {'缺口倍数':>10s}")
    out = []
    items = [(n, radiance_from_M(M)) for n, M, _ in ROWS]
    items += [(n, radiance_from_M(P / A)) for n, P, A in LASER_PHOSPHOR]
    for n, L in items:
        E = OMEGA * L
        out.append({"source": n, "radiance": L, "ratio_to_target": L / L_target,
                    "E_in_solar_beam": E, "deficit_factor": E_target / E})
        print(f"{n:30s} {L:13.3e} {L/L_target:9.4f} {E:13.1f} {E_target/E:10.1f}")
    return out


def etendue(A_target):
    G = A_target * OMEGA
    A_min = G / PI
    d = 2 * np.sqrt(A_min / PI)
    return G, A_min, d


def main():
    all_rows = {}
    for name, E in E_TARGETS.items():
        L_t = E / OMEGA
        all_rows[name] = {"L_required": L_t, "sources": report(E, L_t)}
    th = np.deg2rad(THETA_FULL_DEG / 2)
    print("\n最大浓度比 C_max = n^2/sin^2(theta_half): n=1 -> %.0f x, n=1.5 -> %.0f x"
          % (1 / np.sin(th) ** 2, 1.5 ** 2 / np.sin(th) ** 2))
    for name, E in E_TARGETS.items():
        Lt = E / OMEGA
        Tth = (Lt * PI / SIGMA) ** 0.25
        print("黑体阈值：要达到 %s 的 %.0f W/m2 于 0.53 度内，需黑体温度 >= %.0f K"
              % (name, E, Tth))
    print("\n光源最小面积（n=1，朗伯入射到 pi 立体角）：")
    for A_t in [0.01, 0.1, 1.0, 10.0, 100.0]:
        G, A_min, d = etendue(A_t)
        print("  目标 %.2f m2 -> G=%.3e m2 sr -> 光源面积 >= %.3e m2 (等效圆直径 %.2f mm)"
              % (A_t, G, A_min, d * 1e3))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "results", f"t0c9_results-{date.today():%Y%m%d}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"omega_sr": OMEGA, "theta_full_deg": THETA_FULL_DEG,
                   "targets": all_rows,
                   "label": "模型推演（非实测）；光源档位为假设档，需数据表/实测替换"},
                  f, ensure_ascii=False, indent=2)
    print("\nwritten:", out)


if __name__ == "__main__":
    main()
