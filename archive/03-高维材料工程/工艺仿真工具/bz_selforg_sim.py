# -*- coding: utf-8 -*-
"""
盘点#13 剥离版 · BZ 反应-扩散自组织真实成分演示（天工开物 第四批）
==================================================================================
真实物理口径：二维 Oregonator（Field-Noyes 无量纲模型，Belousov-Zhabotinsky
反应的标准动力学模型），活性介质从均匀+噪声初值自发形成时空图案——
化学自组织不需要任何 θ 场/体系机制，即盘点#13"剥离θ场叙事按真实文献推进"
的第一步演示（真实文献锚：Belousov 1959 / Zhabotinsky / Field-Noyes 1974）。
  ∂u/∂t = Du∇²u + (1/ε)(u(1-u) - f·v·(u-q)/(u+q))
  ∂v/∂t = Dv∇²v + u - v
参数（文献常用值）：ε=0.03, f=1.1, q=0.002, Du=1.0, Dv=0（v 不扩散）。
诚实口径：无量纲数值模型（周期边界），对应真实 BZ 介质的定性动力学，
不构成对体系 θ 场主线的任何背书；波长为格点单位。
"""
import json
import numpy as np

EPS, F, Q = 0.03, 1.1, 0.002
DU, DV = 1.0, 0.0
N = 256
DT = 0.1
STEPS = 6000
SEED = 42

def rest_state():
    """均匀静息态：由 (1-u)(u+q)=f(u-q), v=u 解得 u² - (1-q-f)u - q(1+f) = 0 的正根。"""
    b = 1 - Q - F
    disc = b * b + 4 * Q * (1 + F)
    u_s = (b + np.sqrt(disc)) / 2
    return u_s, u_s

def laplacian(Z):
    return (np.roll(Z, 1, 0) + np.roll(Z, -1, 0) +
            np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z)

def run():
    rng = np.random.default_rng(SEED)
    u_s, v_s = rest_state()
    u = np.full((N, N), u_s) + rng.uniform(0, 0.15, (N, N))
    v = np.full((N, N), v_s)
    snap_t = [0, 500, 2000, STEPS - 1]
    snaps = {}
    for k in range(STEPS):
        uv = u * v * (u - Q) / (u + Q)
        u += DT * (DU * laplacian(u) + (u * (1 - u) - F * uv) / EPS)
        v += DT * (DV * laplacian(v) + u - v)
        np.clip(u, 0, 1.2, out=u)
        if k in snap_t:
            snaps[k] = u.copy()
    return u, v, snaps

def metrics(u, u_rest):
    """图案度量：覆盖度/主波长（径向FFT）/空间自相关长度。"""
    act = u - u_rest
    coverage = float(np.mean(np.abs(act) > 0.05))
    U = np.fft.fftshift(np.abs(np.fft.fft2(u - u.mean()))**2)
    ky = np.fft.fftshift(np.fft.fftfreq(N))  # 格点单位周期
    kx = np.fft.fftshift(np.fft.fftfreq(N))
    KX, KY = np.meshgrid(kx, kx)
    KR = np.sqrt(KX**2 + KY**2)
    inside = (KR > 0) & (KR < 0.5)
    nbins = 40
    bins = np.linspace(0, 0.5, nbins + 1)
    prof = np.zeros(nbins)
    for i in range(nbins):
        m = inside & (KR >= bins[i]) & (KR < bins[i + 1])
        prof[i] = U[m].mean() if m.any() else 0.0
    k_peak = (bins[:-1] + np.diff(bins) / 2)[int(np.argmax(prof))]
    return {"coverage_fraction": coverage,
            "dominant_wavelength_grid_units": float(1.0 / k_peak) if k_peak > 0 else None,
            "amplitude_std": float(np.std(u))}

def main():
    u, v, snaps = run()
    u_s, _ = rest_state()
    out = {"params": {"eps": EPS, "f": F, "q": Q, "Du": DU, "N": N,
                      "dt": DT, "steps": STEPS, "seed": SEED},
           "rest_state": {"u0": float(u_s)},
           "snapshots": {str(k): metrics(s, u_s) for k, s in snaps.items()},
           "final": metrics(u, u_s),
           "honest_note": "无量纲 Oregonator，周期边界；定性对应真实BZ介质；格点单位"}
    return out

if __name__ == "__main__":
    out = main()
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/bz_selforg.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    u, v, snaps = run()
    fig, axes = plt.subplots(1, len(snaps), figsize=(4 * len(snaps), 4))
    for ax, (k, s) in zip(np.atleast_1d(axes), sorted(snaps.items())):
        ax.imshow(s, cmap="RdBu_r", origin="lower")
        ax.set_title(f"t={k}")
        ax.axis("off")
    fig.suptitle("Oregonator 2D self-organization (no theta field; grid units)")
    fig.tight_layout()
    fig.savefig(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/bz_selforg.png", dpi=110)
    for k, m in out["snapshots"].items():
        print(f"t={k:>6}  coverage={m['coverage_fraction']:.3f}  "
              f"λ={m['dominant_wavelength_grid_units'] if m['dominant_wavelength_grid_units'] else float('nan'):.1f}格点  "
              f"std={m['amplitude_std']:.4f}")
    print("rest u0 =", out["rest_state"]["u0"])
