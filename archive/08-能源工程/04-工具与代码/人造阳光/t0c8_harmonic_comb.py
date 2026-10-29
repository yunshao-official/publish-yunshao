#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t0c8_harmonic_comb.py
人造阳光 · T0-C8 光谱分布律首次构造尝试 —— 可复跑计算脚本

用途：
  检验“f0 谐波梳（f_n = r_n * f0，r_n = 1.15 * 2^(k/m)）+ 洛伦兹线型 + 普朗克包络”
  能否在 400-700 nm 内复现 5772 K 黑体的可见光谱形状，并做三类判别：
    1) 谐波中心 vs 等波长中心（可判别性）；
    2) 普朗克包络 vs 自由振幅 vs alpha^k 衰减（振幅律）；
    3) 线宽 Q 与所需线数 N 的权衡（工程/材料要求）。

重要边界（与正文一致）：
  - 目标谱是 5772 K 黑体，不是 ASTM G173 AM1.5G；大气吸收、Fraunhofer 线未计。
  - 线型为理想洛伦兹/高斯，不是实测缺陷发光谱；本脚本只做“形状可行性”，不做机制证明。
  - 所有输出标签：模型推演（非实测）。

运行：
  python t0c8_harmonic_comb.py            # 跑全部表，写 results/t0c8_results-<date>.json
  python t0c8_harmonic_comb.py --quick    # 只跑核心判别表

依赖：numpy, scipy
"""

import argparse
import json
import os
from datetime import date

import numpy as np
from scipy.constants import h, c, k
from scipy.optimize import nnls

TRAPZ = np.trapezoid  # numpy>=2.0

F0 = 373e12  # Hz, constants.yaml v1.0
T_SUN = 5772.0  # K, 名义太阳有效温度（外部事实）
LAM = np.linspace(400e-9, 700e-9, 1201)  # m
NU = c / LAM

BANDS = [(400, 450), (450, 500), (500, 550), (550, 600), (600, 650), (650, 700)]


def planck_lam(lam, T):
    nu = c / lam
    return 2 * h * nu**3 / c**2 / (np.exp(h * nu / (k * T)) - 1)


B_TARGET = planck_lam(LAM, T_SUN)
B_TARGET = B_TARGET / TRAPZ(B_TARGET, LAM)  # 归一化，仅比较形状


def centers_harmonic(m, lo=1.15, hi=2.0):
    """r_k = lo * 2^(k/m)，每倍频程 m 条，截到 hi。"""
    n = int(np.floor(np.log2(hi / lo) * m)) + 1
    rs = lo * 2 ** (np.arange(n) / m)
    return rs[rs <= hi + 1e-12]


def centers_equal_lambda(n=7, lo_nm=415, hi_nm=700):
    lams = np.linspace(lo_nm, hi_nm, n) * 1e-9
    return (c / lams) / F0


def basis(rs, Q, shape="lorentz"):
    cols = []
    for r in rs:
        fc = r * F0
        if shape == "lorentz":
            g = (0.5 * fc / Q) ** 2 / ((NU - fc) ** 2 + (0.5 * fc / Q) ** 2)
        else:
            sig = (fc / Q) / (2 * np.sqrt(2 * np.log(2)))
            g = np.exp(-0.5 * ((NU - fc) / sig) ** 2)
        cols.append(g / TRAPZ(g, LAM))
    return np.array(cols).T


def band_errors(fit):
    out = []
    for lo, hi in BANDS:
        m = (LAM >= lo * 1e-9) & (LAM < hi * 1e-9)
        out.append((TRAPZ(fit[m], LAM[m]) / TRAPZ(B_TARGET[m], LAM[m]) - 1) * 100)
    return np.array(out)


def metrics(fit):
    e = band_errors(fit)
    rmse = np.sqrt(np.mean((fit / B_TARGET - 1) ** 2)) * 100
    return {"max_abs_band_pct": float(np.max(np.abs(e))), "rmse_pct": float(rmse),
            "band_errors_pct": [float(x) for x in e]}


def scale_ls(base):
    s = np.dot(base, B_TARGET) / np.dot(base, base)
    return base * s


def fit_planck_envelope(rs, Q, shape="lorentz", T_grid=np.arange(3500, 8001, 25.0)):
    """振幅 ∝ B_lambda(lambda_n, T)；只优化 T 与总标度。返回最优 T 与指标。"""
    A = basis(rs, Q, shape)
    lams = c / (rs * F0)
    best = None
    for T in T_grid:
        amp = planck_lam(lams, T)
        fit = scale_ls(A @ amp)
        mt = metrics(fit)
        if best is None or mt["rmse_pct"] < best["rmse_pct"]:
            best = dict(mt, T_eff_K=float(T))
    best["n_lines"] = int(len(rs))
    best["Q"] = Q
    best["shape"] = shape
    return best


def fit_fixed_amplitudes(rs, Q, amp, shape="lorentz"):
    A = basis(rs, Q, shape)
    fit = scale_ls(A @ np.asarray(amp, float))
    return metrics(fit)


def fit_free(rs, Q, shape="lorentz"):
    A = basis(rs, Q, shape)
    w, _ = nnls(A, B_TARGET)
    fit = A @ w
    fit = fit * TRAPZ(B_TARGET, LAM) / TRAPZ(fit, LAM)
    mt = metrics(fit)
    mt["weights_norm"] = [float(x) for x in w / w.max()]
    return mt


def table_discrimination():
    """判别 1：谐波中心 vs 等波长中心；判别 2：振幅律。Q=8。"""
    out = {}
    sets = {
        "harmonic_2^(1/8)_7": centers_harmonic(8),
        "equal_lambda_7": centers_equal_lambda(7),
        "harmonic_2^(1/7)_7": centers_harmonic(7),
        "rational_9": np.array([1.2, 1.25, 1.33, 1.4, 1.5, 1.6, 1.67, 1.75, 2.0]),
        "harmonic_2^(1/8)_8": centers_harmonic(8, hi=2.15),
    }
    for name, rs in sets.items():
        out[name] = {
            "centers_nm": [round(float(x), 1) for x in c / (rs * F0) * 1e9],
            "planck_envelope_Q8": fit_planck_envelope(rs, 8),
            "free_weights_Q8": fit_free(rs, 8),
        }
    rs = centers_harmonic(8)
    out["amplitude_rules_Q8"] = {
        "equal": fit_fixed_amplitudes(rs, 8, np.ones(len(rs))),
        "alpha^k": fit_fixed_amplitudes(rs, 8, (1 / 8) ** np.arange(len(rs))),
        "1_over_n": fit_fixed_amplitudes(rs, 8, 1 / (np.arange(len(rs)) + 1)),
        "planck_5500K": fit_fixed_amplitudes(rs, 8, planck_lam(c / (rs * F0), 5500)),
        "free": fit_free(rs, 8),
    }
    return out


def table_q_vs_n():
    """判别 3：线宽 Q 与所需线数 N。每倍频程 m 条。"""
    rows = []
    for Q in [8, 12, 16, 24, 32, 48]:
        for m in [8, 12, 16, 24, 32, 48, 64]:
            rs = centers_harmonic(m)
            r = fit_planck_envelope(rs, Q)
            r["lines_per_octave"] = m
            rows.append(r)
    return rows


def minimal_n(rows, Q, threshold=10.0):
    cand = [r for r in rows if r["Q"] == Q and r["max_abs_band_pct"] <= threshold]
    if not cand:
        return None
    return min(cand, key=lambda r: r["n_lines"])["n_lines"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    result = {
        "meta": {
            "date": str(date.today()),
            "target": "5772 K Planck blackbody, normalized 400-700 nm",
            "f0_Hz": F0,
            "bands_nm": BANDS,
            "label": "模型推演（非实测）；非 AM1.5G",
            "script": os.path.basename(__file__),
        },
        "discrimination": table_discrimination(),
    }
    if not args.quick:
        rows = table_q_vs_n()
        result["q_vs_n"] = rows
        result["minimal_n_for_10pct"] = {str(Q): minimal_n(rows, Q, 10.0) for Q in [8, 12, 16, 24, 32, 48]}
        result["minimal_n_for_5pct"] = {str(Q): minimal_n(rows, Q, 5.0) for Q in [8, 12, 16, 24, 32, 48]}

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "results", f"t0c8_results-{date.today():%Y%m%d}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"written: {out}")
    print(json.dumps(result["discrimination"], ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()
