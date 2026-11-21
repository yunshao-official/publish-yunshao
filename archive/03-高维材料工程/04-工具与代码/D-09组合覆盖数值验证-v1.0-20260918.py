# -*- coding: utf-8 -*-
"""
D-09 组合覆盖生成规则·数值验证 v1.0（2026-09-18）·纯计算版（零文件IO）
知世原话锚（2026-07-24·代数内部版）：
  "你没用过我的分量组合成总量呢！这个过程本身就是可逆的"
  "这1/8损耗，你可以通过不断的升维来减少损耗，直至无限逼近100%"
口径：W2声学PZT执行包v1.1 §2.2-2.5（k0=6.21、phi_j=j·pi/4、freq_ratio=1.5分半、
      势阱=15分位局部极小、建图阈值=中位近邻距×2×(1+κ)、κ=1/32）
确定性：无随机数、无网络、零API、零文件写入（结果经stdout由调用方落盘）。
"""
import json
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, laplacian
from scipy.sparse.linalg import eigsh
from itertools import combinations_with_replacement

N_COMP = 17          # 桥分量数
M_CHAN = 22          # 她的通道数
K0 = 6.21            # W2归一化波数
KAPPA = 1.0 / 32.0
EPS_ANG = 180.0 / N_COMP   # 场角分辨率 δθ=π/N（度）
GRID = 129           # 场验证网格（129×129，W2实测协议≥128口径）


def ang_diff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def diff_library(dirs):
    """强度谱差频库：I(r)=|Σ a_j e^{i k_j·r}|² 的空间谱={k_j−k_l}。"""
    lib = []
    for j, l in combinations_with_replacement(range(len(dirs)), 2):
        if j == l:
            continue
        dv = dirs[j] - dirs[l]
        ang = np.degrees(np.arctan2(dv[1], dv[0])) % 180.0
        lib.append({"j": j, "l": l, "ang": float(ang),
                    "mag": float(np.hypot(dv[0], dv[1]))})
    return lib


def cover_stats(lib, chan_angs):
    rows = []
    for m, ca in enumerate(chan_angs):
        best = min(lib, key=lambda e: ang_diff(e["ang"], ca))
        err = ang_diff(best["ang"], ca)
        rows.append({"chan": m + 1, "target_deg": float(ca),
                     "pair": [best["j"], best["l"]],
                     "pair_ang": best["ang"], "err_deg": float(err),
                     "covered": bool(err <= EPS_ANG)})
    cov = sum(r["covered"] for r in rows)
    errs = [r["err_deg"] for r in rows]
    return rows, {"covered": cov, "total": M_CHAN,
                  "max_err": float(max(errs)), "mean_err": float(np.mean(errs))}


def main():
    out = {"meta": {"N": N_COMP, "M": M_CHAN, "k0": K0, "kappa": KAPPA,
                    "eps_ang_deg": EPS_ANG, "grid": GRID,
                    "note": "零文件IO纯计算版；结果由调用方落盘"}}
    theta_j = 2 * np.pi * np.arange(N_COMP) / N_COMP
    theta_c = 2 * np.pi * np.arange(M_CHAN) / M_CHAN
    chan_angs = np.degrees(theta_c) % 180.0
    dirs_eq = np.stack([np.cos(theta_j), np.sin(theta_j)], 1)

    libA = diff_library(dirs_eq)
    rowsA, stA = cover_stats(libA, chan_angs)
    out["A_equal_freq"] = {"lib_size": len(libA), "coverage": stA,
                           "rows": rowsA}

    ks = np.where(np.arange(N_COMP) < N_COMP // 2 + 1, K0, 1.5 * K0)
    dirsB = dirs_eq * ks[:, None]
    libB = []
    for j, l in combinations_with_replacement(range(N_COMP), 2):
        if j == l or abs(ks[j] - ks[l]) > 1e-9:
            continue  # 跨频对时均交叉项为零（W2自攻防A10口径）
        dv = dirsB[j] - dirsB[l]
        libB.append({"j": j, "l": l,
                     "ang": float(np.degrees(np.arctan2(dv[1], dv[0])) % 180.0),
                     "mag": float(np.hypot(dv[0], dv[1]))})
    rowsB, stB = cover_stats(libB, chan_angs)
    out["B_w2_freq_split"] = {"lib_size": len(libB),
                              "pairs_same_freq": len(libB),
                              "coverage": stB, "rows": rowsB}

    xs = np.linspace(-6.0, 6.0, GRID)
    X, Y = np.meshgrid(xs, xs)
    re_part = np.zeros_like(X)
    im_part = np.zeros_like(X)
    for j in range(N_COMP):
        ph = theta_j[j] * 4.0  # φ_j=j·π/4（锁相律）
        arg = K0 * (dirs_eq[j, 0] * X + dirs_eq[j, 1] * Y) + ph
        re_part += np.cos(arg)
        im_part += np.sin(arg)
    I = re_part ** 2 + im_part ** 2  # 真复场强度 |Σ e^{i(k·r+φ)}|²
    p15 = np.percentile(I, 15)
    locmin = (I == ndimage.minimum_filter(I, size=5))
    wells = (I <= p15) & locmin
    yy, xx2 = np.mgrid[0:GRID, 0:GRID]
    r2 = (xx2 - GRID / 2.0) ** 2 + (yy - GRID / 2.0) ** 2
    wells &= r2 <= (0.92 * GRID / 2.0) ** 2  # 内切圆掩膜剔方域边界伪阱
    wy, wx = np.where(wells)
    pts = np.stack([wx, wy], 1).astype(float)
    n_w = len(pts)
    d2 = np.sum((pts[:, None, :] - pts[None, :, :]) ** 2, -1)
    np.fill_diagonal(d2, np.inf)
    med_nn = float(np.sqrt(d2.min(1)).mean())
    thr = med_nn * 2.0 * (1.0 + KAPPA)
    adjm = np.sqrt(np.maximum(d2, 0)) < thr
    adj = csr_matrix(adjm.astype(float))
    n_comp, _ = connected_components(adj, directed=False)
    L = laplacian(adj, normed=False)
    l2 = float("nan")
    if n_w > 3 and n_comp == 1:
        try:
            l2 = float(eigsh(L.astype(float), k=1, sigma=-1e-9,
                             which="LM", return_eigenvectors=False)[0])
        except Exception:
            l2 = float("nan")
    out["C_field_check"] = {"wells": n_w, "components": int(n_comp),
                            "connected_100": bool(n_comp == 1),
                            "lambda2": l2,
                            "median_nn_px": med_nn,
                            "threshold_px": float(thr)}

    out["analytic"] = {"pred_max_err_deg": 180.0 / (2 * N_COMP),
                       "pred_note": "17频与22频两栅格互素叠加，最坏最近距≤π/34"}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
