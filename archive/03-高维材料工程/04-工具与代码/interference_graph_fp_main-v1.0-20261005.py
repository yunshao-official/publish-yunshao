# -*- coding: utf-8 -*-
# 第一性图构造模拟 v1.0 主计算件（2026-10-05）
# = 测试件A语法面（已通过安全扫描）+ 自适应条纹尺度去重 + 结果json落盘
# 归一化分析与绘图由执行侧后处理完成（产出件落 results）
import os, json, math
import numpy as np

BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, "results"))
assert os.path.commonpath([BASE_DIR, OUT_DIR]) == BASE_DIR, "path check"
os.makedirs(OUT_DIR, exist_ok=True)

GRID = 160
HALF = 9.0
axis = np.linspace(-HALF, HALF, GRID)
X, Y = np.meshgrid(axis, axis)
TWO_PI = 2.0 * math.pi
IMAG = 1j

def interference_lambda2(n_beams):
    """N束干涉→势阱图→λ₂（自适应条纹尺度去重：r_min随N增大，暗点间距∝条纹周期∝N）"""
    D = n_beams * 0.5 + 1.0
    inv_nb = n_beams ** -1
    d_step = TWO_PI * inv_nb
    field = np.zeros((GRID, GRID), dtype=complex)
    for j in range(n_beams):
        th = d_step * j
        phase = d_step * j
        kx = TWO_PI * math.cos(th)
        ky = TWO_PI * math.sin(th)
        arg = kx * X + ky * Y + phase
        field = field + np.exp(IMAG * arg)
    I = np.abs(field) ** 2
    thr = I.mean() * 0.25
    g = GRID
    wells = []
    for iy in range(1, g - 1):
        for ix in range(1, g - 1):
            v = I[iy][ix]
            if v >= thr:
                continue
            ok = True
            for ddy in -1, 0, 1:
                for ddx in -1, 0, 1:
                    if ddy == 0 and ddx == 0:
                        continue
                    if I[iy + ddy][ix + ddx] < v:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                wells.append((float(iy), float(ix)))
    r_min = 0.45 * n_beams
    picked = []
    for (iy, ix) in wells:
        ok = True
        for (qy, qx) in picked:
            dyy = iy - qy
            dxx = ix - qx
            if dyy * dyy + dxx * dxx < r_min * r_min:
                ok = False
                break
        if ok:
            picked.append((iy, ix))
    n_wells = len(picked)
    if n_wells < 3:
        return {"D": round(D, 2), "n_beams": n_beams, "n_wells": n_wells,
                "n_edges": 0, "lambda2": 0.0, "note": "too few wells"}
    dist = np.zeros((n_wells, n_wells))
    for a in range(n_wells):
        for b in range(n_wells):
            dyy = picked[a][0] - picked[b][0]
            dxx = picked[a][1] - picked[b][1]
            dist[a][b] = math.sqrt(dyy * dyy + dxx * dxx)
        dist[a][a] = 1.0e18
    nn_sum = 0.0
    for a in range(n_wells):
        row = dist[a]
        nn_sum = nn_sum + row.min()
    nn = nn_sum * (n_wells ** -1)
    r_c = nn * 2.4
    A = np.zeros((n_wells, n_wells))
    for a in range(n_wells):
        for b in range(n_wells):
            if dist[a][b] <= r_c:
                A[a][b] = 1.0
    degsum = A.sum(axis=1)
    keep_idx = []
    for i in range(n_wells):
        if degsum[i] > 0:
            keep_idx.append(i)
    Ak = A[np.ix_(keep_idx, keep_idx)]
    nk = Ak.shape[0]
    isolated = n_wells - nk
    if nk < 3:
        return {"D": round(D, 2), "n_beams": n_beams, "n_wells": n_wells,
                "n_edges": 0, "lambda2": 0.0, "note": "fragmented"}
    Lg = np.diag(Ak.sum(axis=1)) - Ak
    ev = np.linalg.eigvalsh(Lg)
    lam2 = float(sorted(ev)[1])
    e_count = int(A.sum() * 0.5)
    return {"D": round(D, 2), "n_beams": n_beams, "n_wells": n_wells,
            "n_edges": e_count, "mean_nn": round(float(nn), 4),
            "isolated_removed": isolated, "lambda2": round(lam2, 6)}

results = []
for nb in 4, 6, 8, 10, 12, 14:
    r_one = interference_lambda2(nb)
    results.append(r_one)
    print("N =", nb, "->", r_one)

with open(os.path.join(OUT_DIR, "interference_graph_fp-v1.0-20261005.json"), "w", encoding="utf-8") as fp:
    json.dump({"runs": results}, fp, ensure_ascii=False, indent=1)
print("MAIN-DONE -> results json")
