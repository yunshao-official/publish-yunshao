# -*- coding: utf-8 -*-
"""
T1-G2 · 超导磁选捕获-反冲洗(backflush)循环建模（天工开物 第四批 · 台账G-2遗留任务）
==================================================================================
真实物理口径（过阻尼斯托克斯 + 磁化钢丝梯度力 + 重力沉降 + 势流绕柱）：
  - 几何：**立式**（工业HGMS口径）——浆料沿 +y 上行，通道长 100mm、半宽 5mm，
    单根磁化钢丝（半径 a=0.5mm）轴向垂直纸面、位于中心。
  - 磁力：F = V·Δχ/(2μ0)·∇B²，顺磁 Δχ=+2e-3（T1口径），超导 Δχ≈-1（迈斯纳排磁）
  - 高μ钢丝外场（解析解）：H_r=(B0/μ0)(1+a²/r²)cosθ, H_θ=-(B0/μ0)(1-a²/r²)sinθ
  - 曳力 6πηrp(u-v)，水 η=1e-3；重力沉降 Stokes v_s=2rp²Δρg/(9η)（沿 -y）
  - 循环账本：捕获相（顺磁在钢丝富集；超导被排离随流导出）
              → 降场 + 反向冲洗（顺磁脱附回收）→ 下一循环
  - 颗粒结局：captured（钢丝）/ top_exit（随流导出）/ settled_back（沉降回落）
诚实口径：二维过阻尼玩具模型——无湍流/无多体聚集/单丝（工业HGMS用钢毛矩阵
放大梯度，单丝=保守下限）；近丝强磁力区数值速度上限 0.5 m/s（过阻尼失效区，
只影响瞬时不影响去向）；结论以数量级与趋势为准。
"""
import json
import numpy as np

ETA = 1e-3
MU0 = 4 * np.pi * 1e-7
B0 = 1.0
A_WIRE = 0.5e-3
L_CH = 0.10          # 沿 y 通道长
H_CH = 5e-3          # 半宽（x 向）
U_FLOW = 0.01        # 上行平均流速 m/s
CHI_PM = 2e-3
DELTA_RHO = 5000.0
G = 9.81
V_CAP = 0.5          # 数值稳定上限 m/s

def v_stokes(rp, delta_rho=DELTA_RHO):
    return 2 * rp**2 * delta_rho * G / (9 * ETA)

def wire_B2(x, y):
    """|B|²（T²）。Hr/Ht 已以磁通密度口径写（含 B0），不再乘 μ0。"""
    r = np.maximum(np.hypot(x, y), A_WIRE * 1.001)
    theta = np.arctan2(y, x)
    a2 = A_WIRE**2
    Hr = B0 * (1 + a2 / r**2) * np.cos(theta)
    Ht = -B0 * (1 - a2 / r**2) * np.sin(theta)
    return Hr**2 + Ht**2

def grad_B2(x, y):
    h = A_WIRE * 1e-3
    return np.array([(wire_B2(x + h, y) - wire_B2(x - h, y)) / (2 * h),
                     (wire_B2(x, y + h) - wire_B2(x, y - h)) / (2 * h)])

def flow(x, y):
    """势流绕柱，均匀来流沿 +y（复势 w=-iU(z+a²/z) 展开）。"""
    r2 = np.maximum(x**2 + y**2, A_WIRE**2)
    ux = -2 * U_FLOW * x * y / r2**2 * A_WIRE**2
    uy = U_FLOW * (1 + A_WIRE**2 * (x**2 - y**2) / r2**2)
    return ux, uy

def capture_run(rp, dchi, n_part=400, seed=42, t_max=40.0):
    """系综向量化轨迹（立式几何）。返回结局统计。"""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-H_CH * 0.98, H_CH * 0.98, n_part)
    y = np.full(n_part, -L_CH / 2)
    active = np.ones(n_part, dtype=bool)
    outcome = np.full(n_part, "timeout", dtype=object)
    vs = v_stokes(rp)
    dt0 = 0.2 * rp / max(vs, U_FLOW)
    dt0 = float(np.clip(dt0, 1e-5, 2e-3))
    t = 0.0
    while active.any() and t < t_max:
        xa, ya = x[active], y[active]
        ux, uy = flow(xa, ya)
        gx, gy = grad_B2(xa, ya)
        vmx = rp**2 * dchi * gx / (9 * ETA * MU0)
        vmy = rp**2 * dchi * gy / (9 * ETA * MU0)
        vx, vy = ux + vmx, uy + vmy - vs
        sp = np.hypot(vx, vy)
        cap = sp > V_CAP
        vx = np.where(cap, vx * V_CAP / np.maximum(sp, 1e-30), vx)
        vy = np.where(cap, vy * V_CAP / np.maximum(sp, 1e-30), vy)
        x[active] = xa + vx * dt0
        y[active] = ya + vy * dt0
        t += dt0
        idx = np.where(active)[0]
        x[idx] = np.clip(x[idx], -H_CH, H_CH)          # 侧壁夹持
        r = np.hypot(x[idx], y[idx])
        hit_wire = r < A_WIRE + rp
        hit_top = y[idx] >= L_CH / 2
        hit_bot = y[idx] <= -L_CH / 2
        outcome[idx[hit_wire]] = "captured"
        outcome[idx[hit_top & ~hit_wire]] = "top_exit"
        outcome[idx[hit_bot & ~hit_wire & ~hit_top]] = "settled_back"
        active[idx[hit_wire | hit_top | hit_bot]] = False
    return {lab: int(np.sum(outcome == lab)) for lab in
            ("captured", "top_exit", "settled_back", "timeout")}

def cycle_ledger(rp=20e-6):
    """捕获-反冲洗循环账本（粒径规格 rp=20μm 口径）。"""
    pm = capture_run(rp, CHI_PM, n_part=200, seed=7)
    cap_frac = pm["captured"] / max(1, pm["captured"] + pm["top_exit"])  # 可输运颗粒中的捕获率
    n_per_len = 0.7 * (2 * np.pi * A_WIRE) / (np.pi * rp**2)     # 单层覆盖 颗/米钢丝（面积/占地×堆积0.7）
    conc = 0.05
    area_flux = U_FLOW * 2 * H_CH                                # m²/s 每米宽
    part_rate = conc * area_flux / (4 / 3 * np.pi * rp**3)
    capture_rate = part_rate * cap_frac
    t_sat = n_per_len / capture_rate if capture_rate > 0 else np.inf
    t_down, t_flush = 10.0, 2 * L_CH / (2 * U_FLOW)
    t_cycle = t_sat + t_down + t_flush
    return {"conveyable_fraction": float((pm["captured"] + pm["top_exit"]) / 200.0),
            "capture_fraction_of_conveyable": float(cap_frac),
            "n_per_meter_wire_monolayer": float(n_per_len),
            "particle_capture_rate_per_s_per_m": float(capture_rate),
            "t_saturate_s": float(t_sat), "t_field_down_s": t_down,
            "t_flush_s": float(t_flush), "t_cycle_s": float(t_cycle),
            "steady_throughput_m2_s_per_m_width": float(area_flux * (t_sat / t_cycle))
            if np.isfinite(t_sat) else None}

def main():
    sizes = [500e-6, 100e-6, 20e-6, 10e-6]
    x0 = A_WIRE + 20e-6
    g0 = float(np.linalg.norm(grad_B2(np.array([x0]), np.array([0.0]))[:, 0]))
    out = {"settling_table": [], "magnetic_drift_velocity_at_wire": [],
           "capture_PM": [], "capture_SC": [],
           "cycle_ledger_rp20um": cycle_ledger(),
           "meta": {"grad_B2_scale_at_wire_T2_per_m": g0,
                    "geometry": "立式上行（工业HGMS口径）",
                    "honest_note": "单丝保守下限（无钢毛矩阵放大）；过阻尼二维；"
                                   "近丝速度截断0.5m/s；湍流未计"}}
    for rp in sizes:
        out["settling_table"].append({"rp_m": rp, "v_stokes_m_s": v_stokes(rp),
                                      "v_stokes_over_upflow": v_stokes(rp) / U_FLOW})
        out["magnetic_drift_velocity_at_wire"].append({
            "rp_m": rp,
            "v_mag_PM_m_s": rp**2 * CHI_PM * g0 / (9 * ETA * MU0),
            "v_mag_SC_m_s": rp**2 * 1.0 * g0 / (9 * ETA * MU0)})
        out["capture_PM"].append({"rp_m": rp, **capture_run(rp, CHI_PM, n_part=400, seed=42)})
        out["capture_SC"].append({"rp_m": rp, **capture_run(rp, -1.0, n_part=400, seed=43)})
    return out

if __name__ == "__main__":
    out = main()
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/t1g2_backflush.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print("== 沉降 vs 上行流速(10mm/s) ==")
    for r in out["settling_table"]:
        print(f"  rp={r['rp_m']*1e6:7.1f}um  v_s={r['v_stokes_m_s']:.3e} m/s  (x{r['v_stokes_over_upflow']:.2g} 流速)")
    print("== 结局统计（400颗粒/组） ==")
    for tag, key in [("PM", "capture_PM"), ("SC", "capture_SC")]:
        for r in out[key]:
            print(f"  {tag} rp={r['rp_m']*1e6:7.1f}um  captured={r['captured']:3d} "
                  f"top_exit={r['top_exit']:3d} settled_back={r['settled_back']:3d} timeout={r['timeout']}")
    print("== 循环账本(rp=20um) ==", json.dumps(out["cycle_ledger_rp20um"], ensure_ascii=False))
