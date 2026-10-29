# -*- coding: utf-8 -*-
"""
光干涉工艺仿真器（工艺仿真工具 · 组件2）
两种物理模式的时均场（全域攻防 P0 修正后的正确口径）：
  模式 A：单一频率 N 束（如单激光分束 3×120°）→ 静态干涉晶格
          I_avg = ΣI_i + 2Σ_{i<j}√(I_iI_j)·cos((k_i-k_j)·x + Δφ)
  模式 B：多频率各束与表面反射自干涉 → 各自 λ/2 周期的分层驻波叠加
          I_avg = Σ_i I_i[1 + r² + 2r·cos(2k_i·x + ψ)]
势阱提取与图构建：沿用档案管线口径（yunshao_limitation_test 同算法，
百分比阈值 + k近邻局部极小 + 距离阈值建图），本工具为独立实现、口径一致。
诚实口径：标量场玩具模型——只算光强时均分布，不含激光-物质微观相互作用。
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from scipy.sparse.csgraph import laplacian, connected_components

def _time_avg_modeA(beams, grid):
    """beams: [(kvec(2), I, phase)] 同频率。返回时均强度场。"""
    I = np.zeros(grid.shape[:2])
    ks = [np.asarray(k) for k, _, _ in beams]
    Is = [i for _, i, _ in beams]
    ph = [p for _, _, p in beams]
    for (k, Ii, p) in beams:
        I += Ii
    for a in range(len(beams)):
        for b in range(a + 1, len(beams)):
            dk = ks[a] - ks[b]
            arg = grid @ dk + (ph[a] - ph[b])
            I += 2 * np.sqrt(Is[a] * Is[b]) * np.cos(arg)
    return I

def _time_avg_modeB(freq_beams, grid, reflectivity=0.9, phase_psi=0.0):
    """freq_beams: [(kvec的大小|k|方向单位向量, I, 波长)]，各频率独立自驻波。"""
    I = np.zeros(grid.shape[:2])
    for kdir, Ii, wl in freq_beams:
        k = 2 * np.pi / wl * np.asarray(kdir)
        arg = 2.0 * (grid @ k) + phase_psi
        I += Ii * (1 + reflectivity**2 + 2 * reflectivity * np.cos(arg))
    return I

def three_beam_120(I_total=3.0, wl=1.064, deg=120.0, phases=(0.0, 2*np.pi/3, 4*np.pi/3),
                   size=30.0, n=900):
    """模式A：等强度三束 120° 同频。返回 grid, I_avg, 理论周期。单位：微米。"""
    beams = []
    for i in range(3):
        ang = np.deg2rad(i * deg)
        kvec = (2 * np.pi / wl) * np.array([np.cos(ang), np.sin(ang)])
        beams.append((kvec, I_total / 3.0, phases[i % len(phases)]))
    xs = np.linspace(-size / 2, size / 2, n)
    grid = np.stack(np.meshgrid(xs, xs), axis=-1)
    # 理论主周期（六方晶格最近邻距离）= 2λ/(3·cos(30°))？ 直接由傅里叶主峰给实测：
    return grid, _time_avg_modeA(beams, grid), beams, wl

def modeB_layered(wls=(10.6, 1.064, 1.286), I_each=1.0, r=0.9,
                  kdir=(1.0, 0.0), size=30.0, n=900):
    """模式B：多频率各自驻波层（沿同一方向入射+反射）。"""
    grid = np.stack(np.meshgrid(np.linspace(-size/2, size/2, n),
                                np.linspace(-size/2, size/2, n)), axis=-1)
    kd = np.asarray(kdir) / np.linalg.norm(kdir)
    beams = [(kd, I_each, wl) for wl in wls]
    return grid, _time_avg_modeB(beams, grid, reflectivity=r), beams

def extract_wells(I, pct=15, kn=8):
    thr = np.percentile(I, pct)
    wells = []
    n = I.shape[0]
    for i in range(1, n - 1):
        for j in range(1, n - 1):
            if I[i, j] > thr:
                continue
            patch = I[i-1:i+2, j-1:j+2]
            if I[i, j] <= patch.min() + 1e-300 and (patch == I[i, j]).sum() == 1:
                wells.append((i, j))
    return wells

def wells_graph(wells_idx, scale, max_dist_factor=2.0, kappa_extra=0.03125):
    """井→距离阈值图（口径同档案管线）。返回 adj dict 与边数。"""
    if len(wells_idx) < 2:
        return {}, 0
    pts = np.array([(j * scale, i * scale) for i, j in wells_idx])
    tree = cKDTree(pts)
    kq = min(4, len(pts) - 1)
    d, _ = tree.query(pts, k=kq + 1)
    med = np.median(d[:, 1])
    maxd = med * max_dist_factor * (1 + kappa_extra)
    pairs = tree.query_pairs(r=maxd)
    adj = {i: set() for i in range(len(pts))}
    for a, b in pairs:
        adj[a].add(b); adj[b].add(a)
    edges = sum(len(v) for v in adj.values()) // 2
    return adj, edges

def graph_metrics(adj):
    n = len(adj)
    if n < 2:
        return {"components": n, "largest_pct": 100.0 if n == 1 else 0.0, "lam2": 0.0}
    m = {i: sorted(adj[i]) for i in adj}
    idx = {v: i for i, v in enumerate(m)}
    rows, cols = [], []
    for v, ns in m.items():
        for u in ns:
            rows.append(idx[v]); cols.append(idx[u])
    from scipy.sparse import coo_matrix as cm
    A = cm((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    L = laplacian(A.astype(np.float64))
    ncomp, _ = connected_components(A, directed=False)
    sizes = []
    seen = set()
    for s in range(n):
        if s in seen: continue
        stack, c = [s], 0
        seen.add(s)
        while stack:
            x = stack.pop(); c += 1
            for y in np.array(m[x]):
                yy = idx[y]
                if yy not in seen: seen.add(yy); stack.append(yy)
        sizes.append(c)
    vals = np.sort(np.abs(eigsh(L, k=3, sigma=-1e-6, which="LM", return_eigenvectors=False)))
    lam2 = float(vals[0]) if n > 3 else 0.0  # 去掉零模后取最小（vals[0]≈λ₁≈0 被排除：k=3取次小）
    # 注：k=3 返回的三个值排序后 [~0, λ₂, λ₃]，真 λ₂ = 第二个
    lam2 = float(sorted(vals)[1]) if n > 3 else 0.0
    return {"components": int(ncomp), "largest_pct": round(100 * max(sizes) / n, 1), "lam2": round(lam2, 4)}

def dominant_period_fft(I, scale):
    """FFT 主峰→实测图案周期（对照理论值用）。"""
    F = np.abs(np.fft.fftshift(np.fft.fft2(I - I.mean())))
    cy, cx = np.array(F.shape) // 2
    F[cy - 2:cy + 3, cx - 2:cx + 3] = 0  # 去直流
    ky, kx = np.unravel_index(np.argmax(F), F.shape)
    k = np.hypot((ky - cy), (kx - cx)) / (I.shape[0] * scale)  # 1/μm
    return round(1.0 / k, 3) if k > 0 else float("nan")
