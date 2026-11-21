# -*- coding: utf-8 -*-
"""
云韶数论 RD-1~RD-4 数值首跑（2026-09-21，ZCode）
执行口径：《云韶数论·磨光读数归一化与RD首跑执行口径-v1.0-20260921》（预注册冻结，落盘先于本实算）
判据来源：《云韶数论·D6D8显式公式路线重导-v0.1-20260921》§五 RD-1~RD-4（草案）
约定：A2 磨光（高斯族 w∈{1,2,4}，w_k=k·Δγ̄）+ B1 计重数 + C3 ψ 刻度（说明书 v1.1 §三之一冻结）
数据：Odlyzko 前 100,000 零点（γ∈(0,300] 入谱）+ R-N10 张力直方图（X=2×10⁶，240,163 对）
判负条款：任一判据失败→失败档案照记，不硬闯；求和约定冻结不回退。
"""
import io, json, math, sys
import numpy as np
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ZEROS_FILE = Path("H:/理论存档/01-数学/02-实验与数据/results/odlyzko_zeros1-100k-20260921.txt")
OUT_DIR = Path("H:/理论存档/01-数学/02-实验与数据/results")
GAMMA_MAX = 300.0
ALPHA = 1 / 8                      # [constants:v1.0] layers.layer1.alpha_w
DS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 22]
HIST = [29555, 34288, 52977, 19819, 23379, 34223, 10932, 14544, 15704, 4742]  # R-N10
KS = [1, 2, 4]

def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() < 1e-300 or y.std() < 1e-300:
        return None, float(x.std()), float(y.std())
    return float(np.corrcoef(x, y)[0, 1]), float(x.std()), float(y.std())

def load_zeros():
    g = np.array([float(ln) for ln in ZEROS_FILE.read_text().split()], float)
    assert len(g) == 100000, f"零点表行数异常：{len(g)}"
    assert abs(g[0] - 14.134725142) < 1e-6, "首零点自检失败"
    return g

def rd1_rd4(zeros):
    gam = zeros[zeros <= GAMMA_MAX]
    gbar = float(gam.mean())
    dg = 2 * math.pi / math.log(gbar)
    ws = {k: k * dg for k in KS}
    tc = np.array([4 * d for d in DS], float)                 # 共振口径 t=96T=4d
    tc_old = np.array([ALPHA / (d / 24) for d in DS], float)  # 旧口径 t=α/T=3/d
    h = np.array(HIST, float)
    amp = 1.0 / np.abs(0.5 + 1j * gam)                        # ψ₀ 振幅权（x^{1/2} 公因子剥离）

    def kernel(gam_arr, centers, w):
        return np.exp(-0.5 * ((centers[None, :] - gam_arr[:, None]) / w) ** 2)

    out = {"gamma_n_used": int(len(gam)), "gbar": round(gbar, 6),
           "delta_unit": round(dg, 6), "w_tiers": {str(k): round(ws[k], 6) for k in KS},
           "band_centers_resonance": [round(v, 4) for v in tc],
           "band_centers_old": [round(v, 6) for v in tc_old]}
    res = {}
    for tag, centers in (("resonance", tc), ("old", tc_old)):
        for k in KS:
            Kw0 = kernel(gam, centers, ws[k])                 # 6w 外截断（≤e^-18 不影响精度，直接算全支撑）
            Kw0[np.abs(centers[None, :] - gam[:, None]) > 6 * ws[k]] = 0.0
            Z = Kw0.sum(axis=0)                               # 计数谱（m_n=1，段内无重零点）
            Za = (Kw0 * amp[:, None]).sum(axis=0)             # 振幅谱
            Kf = np.exp(-0.5 * ((centers[None, :] - (4 * np.array(DS))[None, :]) / ws[k]) ** 2)
            F = (Kf * h[None, :]).sum(axis=0)                 # 禁数侧同核磨光
            r0, s0, _ = pearson(Z, F)
            ra, sa, _ = pearson(Za, F)
            res[f"{tag}|w{k}"] = {
                "Z_count": [round(v, 6) for v in Z], "Z_amp": [round(v, 8) for v in Za],
                "F": [round(v, 1) for v in F],
                "pearson_count": None if r0 is None else round(r0, 6),
                "pearson_amp": None if ra is None else round(ra, 6),
                "std_count": round(s0, 8), "std_amp": round(sa, 10),
                "max_Z": round(float(Z.max()), 6), "max_Zamp": round(float(Za.max()), 10)}
    out["profiles"] = res

    # RD-4：跨档相对偏差（A2-c2 冻结 5% 线）
    def reldev(a, b):
        a, b = np.asarray(a), np.asarray(b)
        m = 0.5 * (np.abs(a) + np.abs(b))
        ok = m > 0
        return None if not ok.any() else float(np.max(np.abs(a[ok] - b[ok]) / m[ok]))
    rd4 = {}
    for tag in ("resonance", "old"):
        for series in ("Z_count", "Z_amp"):
            for a, b in ((1, 2), (2, 4), (1, 4)):
                pa = np.array(res[f"{tag}|w{a}"][series]); pb = np.array(res[f"{tag}|w{b}"][series])
                rd4[f"{tag}|{series}|{a}vs{b}"] = None if reldev(pa, pb) is None else round(reldev(pa, pb), 6)
    for a, b in ((1, 2), (2, 4), (1, 4)):
        r_a = res[f"resonance|w{a}"]["pearson_count"]; r_b = res[f"resonance|w{b}"]["pearson_count"]
        rd4[f"resonance|pearson_count|{a}vs{b}"] = None if (r_a is None or r_b is None) else round(abs(r_a - r_b), 6)
    out["rd4_relative_deviations"] = rd4
    out["rd4_line"] = 0.05
    return out

def rd2():
    """刻度链封闭 π↔J↔ψ：三腿精确分段求和，网格 10³..10⁷ 25 点，容差 1e-9（口径件 §2.5 冻结）"""
    N = 10_000_000
    sieve = np.ones(N + 1, dtype=bool); sieve[:2] = False
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]: sieve[i * i::i] = False
    primes = np.nonzero(sieve)[0]
    lam = np.zeros(N + 1)
    for p in primes:                        # 素数幂叠加 ln p（Λ 的定义）
        pk = int(p)
        lp = math.log(p)
        while pk <= N:
            lam[pk] += lp; pk *= p
    psi_cum = np.cumsum(lam)                # ψ(n) 逐点
    jt = np.zeros(N + 1); jt[2:] = lam[2:] / np.log(np.arange(2, N + 1))
    j_cum = np.cumsum(jt)                   # J(n)=Σ_{m≤n} Λ(m)/ln m 逐点
    pi_cum = np.cumsum(sieve)               # π(n)
    bp = np.nonzero(lam)[0]                 # 素数幂断点
    psi_bp, j_bp = psi_cum[bp], j_cum[bp]
    lnb = np.log(bp.astype(float))
    lnb_next = np.empty_like(lnb); lnb_next[:-1] = lnb[1:]

    # Möbius 数（k ≤ 23；标准筛：素数处变号、素数平方幂 multiples 置零）
    K = 24
    mu = np.ones(K, int)
    is_p = np.ones(K, bool); is_p[:2] = False
    for i in range(2, int(K ** 0.5) + 1):
        if is_p[i]: is_p[i * i::i] = False
    for p in np.nonzero(is_p)[0]:
        for j in range(p, K, p): mu[j] = -mu[j]
        for j in range(p * p, K, p * p): mu[j] = 0
    assert mu[1] == 1 and mu[6] == 1 and mu[4] == 0 and mu[12] == 0 and mu[23] == -1  # 锚：μ(1)=1, μ(6)=+1, μ(4)=μ(12)=0, μ(23)=−1
    def j_to_pi(x):
        s = 0.0
        for k in range(1, K):
            if mu[k] == 0: continue
            y = x ** (1.0 / k)
            jy = j_cum[int(y)] if y >= 2 else 0.0
            s += mu[k] / k * jy
        return s

    xs = np.logspace(3, 7, 25)
    rows, worst = [], {"psi_to_j": 0.0, "j_to_pi": 0.0, "j_to_psi": 0.0}
    for x in xs:
        xi = int(x)
        # ψ→J（向量化分段精确求和）
        m = bp <= x
        n_j = bp[m]; p_j = psi_bp[m]
        nxt = np.empty(len(n_j)); nxt[:-1] = 1.0 / lnb[m][1:]; nxt[-1] = 1.0 / math.log(x)
        j_hat = psi_cum[xi] / math.log(x) + float(np.sum(p_j * (1.0 / lnb[m] - nxt)))
        # J→π
        pi_hat = j_to_pi(x)
        # J→ψ
        jj = j_bp[m]
        rat = np.empty(len(n_j)); rat[:-1] = np.log(n_j[1:] / n_j[:-1]); rat[-1] = math.log(x / n_j[-1])
        psi_hat = j_cum[xi] * math.log(x) - float(np.sum(jj * rat))
        r1 = abs(j_hat - j_cum[xi]) / j_cum[xi]
        r2 = abs(pi_hat - pi_cum[xi]) / pi_cum[xi]
        r3 = abs(psi_hat - psi_cum[xi]) / psi_cum[xi]
        worst["psi_to_j"] = max(worst["psi_to_j"], r1); worst["j_to_pi"] = max(worst["j_to_pi"], r2); worst["j_to_psi"] = max(worst["j_to_psi"], r3)
        rows.append({"x": x, "psi": float(psi_cum[xi]), "J": float(j_cum[xi]), "pi": int(pi_cum[xi]),
                     "rel_psi_to_j": r1, "rel_j_to_pi": r2, "rel_j_to_psi": r3})
    return {"n_grid": len(xs), "primes_le_1e7": int(len(primes)), "prime_powers": int(len(bp)),
            "tolerance": 1e-9, "worst_rel": {k: f"{v:.3e}" for k, v in worst.items()},
            "pass": all(v < 1e-9 for v in worst.values()), "rows": rows}

def rd3(zeros):
    """平凡层闭式核对：①闭式 vs ψ 刻度收敛级数（容差 1e-12）；②x=10³ 全公式残差趋势"""
    out = {"main": [], "aux_x1e3": []}
    for x in (1e3, 1e6, 1e9):
        closed = -0.5 * math.log1p(-x ** -2)   # log1p 保 x=1e9 档精度（log(1-1e-18) 直接算下溢为 0）
        s, k, term = 0.0, 1, float("inf")
        while term > 1e-25 and k <= 200:
            term = x ** (-2 * k) / (2 * k); s += term; k += 1
        rel = abs(s - closed) / abs(closed)
        out["main"].append({"x": x, "closed": closed, "series_terms": k - 1, "series": s, "rel_diff": rel,
                            "pass_1e-12": bool(rel < 1e-12)})
    # 辅助：x=10³ 全公式残差（ψ₀ 直算取 10³ 档；1000 非素数幂→无半权点）
    N1 = 1000
    sieve = np.ones(N1 + 1, dtype=bool); sieve[:2] = False
    for i in range(2, 32):
        if sieve[i]: sieve[i * i::i] = False
    psi0 = 0.0
    for p in np.nonzero(sieve)[0]:
        pk, lp = int(p), math.log(p)
        while pk <= N1:
            psi0 += lp
            if pk == N1: psi0 -= lp / 2      # 素数幂上半权（ψ₀ 撇号约定）
            pk *= p
    L = math.log(1e3)
    trivial = math.log(2 * math.pi) + 0.5 * math.log(1.0 - 1e-6)
    gam = zeros
    for Tn in (100, 1000, 10000, 100000):
        g = gam[:Tn]
        term = (1e3 ** 0.5) * np.exp(1j * g * L) / (0.5 + 1j * g)
        ssum = 2.0 * float(np.real(term.sum()))
        resid = psi0 - 1e3 + ssum + trivial
        out["aux_x1e3"].append({"T_zeros": Tn, "T_height": round(float(g[-1]), 3),
                                "sum_rho": round(ssum, 6), "residual": round(resid, 6),
                                "abs_over_sqrtx": round(abs(resid) / math.sqrt(1e3), 6)})
    return out

def main():
    zeros = load_zeros()
    print("=" * 66)
    print("云韶数论 RD-1~RD-4 数值首跑 ｜ 2026-09-21 ｜ 口径：归一化执行口径 v1.0（预注册冻结）")
    print("=" * 66)
    r14 = rd1_rd4(zeros)
    print(f"\n[RD-1/RD-4] 零点入谱 {r14['gamma_n_used']} 个（γ≤{GAMMA_MAX:.0f}）｜γ̄={r14['gbar']}｜Δγ̄={r14['delta_unit']}")
    print(f"  窗宽三档 w_k=k·Δγ̄：{r14['w_tiers']}")
    print("  共振口径（t_c=4d）带中心相关：")
    for k in KS:
        p = r14["profiles"][f"resonance|w{k}"]
        print(f"    w{k}: r(计数谱)={p['pearson_count']}  r(振幅谱)={p['pearson_amp']}")
    p = r14["profiles"]["old|w2"]
    print(f"  旧口径对照臂（t_c=3/d）：Z_max(w2)={p['max_Z']}（近零平线/零方差→Pearson 无定义，如实记录）")
    print("  RD-4 相对偏差（A2-c2 冻结线 5%）：")
    fails = []
    for key, v in r14["rd4_relative_deviations"].items():
        flag = ""
        if v is not None and v > 0.05:
            flag = "  ← 超5%：读数不稳定（判负照记）"; fails.append(key)
        print(f"    {key}: {v}{flag}")
    print("\n[RD-2] 刻度链封闭（ψ→J / J→π / J→ψ，网格 25 点，容差 1e-9）：")
    r2 = rd2()
    for k, v in r2["worst_rel"].items():
        print(f"    {k}: 最差相对偏差 {v}")
    print(f"    判定：{'PASS（复算一致）' if r2['pass'] else 'FAIL（判负照记）'}｜素数≤1e7：{r2['primes_le_1e7']:,}｜素数幂断点：{r2['prime_powers']:,}")
    print("\n[RD-3] 平凡层闭式核对：")
    r3 = rd3(zeros)
    for row in r3["main"]:
        print(f"    x={row['x']:.0e}: 闭式={row['closed']:.15e} vs 级数({row['series_terms']}项) 相对差={row['rel_diff']:.2e} → {'PASS(≤1e-12)' if row['pass_1e-12'] else 'FAIL'}")
    print("    辅助（x=10³ 全公式残差趋势，只记不设线）：")
    for row in r3["aux_x1e3"]:
        print(f"      T={row['T_zeros']:>6} 零点（高度{row['T_height']:.0f}）: 残差={row['residual']:+.4f}｜/√x={row['abs_over_sqrtx']:.4f}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"meta": {"date": "2026-09-21", "caliber": "磨光读数归一化与RD首跑执行口径 v1.0（预注册冻结）",
                    "constants": "[constants:v1.0] α_w=1/8, σ_投影=1/√6；12/39.2 复算一致",
                    "zeros_file": ZEROS_FILE.name, "rd14": r14, "rd2": r2, "rd3": r3}}
    OUT = OUT_DIR / "云韶数论RD-1至RD-4首跑结果-20260921.json"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[ok] 结果已写入：{OUT}")
    print("[note] RD-1 草案无冻结数值通过线——读数照录，'同谱'判定留账本并入轨道（T-5/知世）；判负条款照记不硬闯。")

if __name__ == "__main__":
    main()
