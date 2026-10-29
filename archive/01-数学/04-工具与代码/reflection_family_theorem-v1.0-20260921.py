# -*- coding: utf-8 -*-
# 反射族定理化（R24 主格二·判据书 B 系实算）
# B0 锚 / B1 反射恒等 S_c(2π-t)=conj S_c(t) / B2 半周期×轨道等高 / B3 argmax 全清 / B4 δ 记录
import json
import numpy as np
from mpmath import mp, mpf, cos, sin, pi as mpi_pi

mp.dps = 30
N = 2 ** 20
PAIRS12 = [(0,8),(2,10),(4,12),(6,14),(8,16),(10,18),(12,20),(14,22),(16,0%1),(0,0)]
# 商类 c∈0..7（mod 8）；"10|22" 等 12 组对 → 商类映射 c(r)=(r-(r mod 3))/3 mod 8
def c_of(r):
    return ((r - (r % 3)) // 3) % 8
PAIRS_R = [(2,8),(2,14),(2,20),(8,14),(8,20),(14,20),(4,10),(4,16),(4,22),(10,16),(10,22),(16,22)]  # R19 正本 12 对

def zeta_pow(j):
    # ζ=e^{iπ/4}, 返回 numpy 复数
    return np.exp(1j * np.pi / 4 * (j % 8))

def build_S(k, tgrid):
    """S_c(t) 谱闭式：S_c=(1/8)Σ_m ζ^{mc} A_m^p A_{3m}^q, A_m=1+iζ^{-m}x-ζ^{-2m}x²"""
    p = (k + 1) // 2
    q = k // 2
    x = np.exp(1j * tgrid)
    S = {}
    Am = {}
    for m in range(8):
        zm = np.exp(-1j * np.pi / 4 * (m % 8))
        Am[m] = 1 + zm * x + (zm ** 2) * x * x
    for c in range(8):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j * np.pi / 4 * ((m * c) % 8)) * (Am[m] ** p) * (Am[(3 * m) % 8] ** q)
        S[c] = acc / 8
    return S


NORM = None
def class_N(k):
    M = (3 ** k - 3) // 8
    return [M + 1 if c in (0, 1) else M for c in range(8)]

def delta_phi(k, r, rp, tgrid, S=None):
    """正本口径：Δφ=e^{itd}(S_c/N_c − S_cp/N_cp)，d=r mod 3（R22 P 系判据书术语速览）"""
    c, cp = c_of(r), c_of(rp)
    d = r % 3
    if S is None: S = build_S(k, tgrid)
    Nc = class_N(k)
    return np.abs(np.exp(1j * d * tgrid) * (S[c] / Nc[c] - S[cp] / Nc[cp]))

def mp_dphi(k, r, rp, t):
    """mpmath A 口径单点"""
    mp.dps = 50
    p = (k + 1) // 2; q = k // 2
    tt = mp.exp(1j * t)
    z = lambda n: mp.exp(1j * mp.pi / 4 * (n % 8))
    M = (3 ** k - 3) // 8
    def Scc(c):
        tot = mp.mpc(0)
        for m in range(8):
            zm = mp.exp(-1j * mp.pi / 4 * (m % 8))
            z3m = mp.exp(-1j * mp.pi / 4 * ((3 * m) % 8))
            tot += z(m * c) * (1 + zm * tt + zm ** 2 * tt ** 2) ** p * (1 + z3m * tt + z3m ** 2 * tt ** 2) ** q
        return tot / 8
    c, cp = c_of(r), c_of(rp)
    Nc = M + 1 if c in (0, 1) else M
    Ncp = M + 1 if cp in (0, 1) else M
    return abs(mp.exp(1j * (r % 3) * t) * (Scc(c) / Nc - Scc(cp) / Ncp))

def mp_S(k, c, t):
    """mpmath 50 位单点 S_c(t)"""
    mp.dps = 50
    p = (k + 1) // 2; q = k // 2
    j = mp.exp(1j * t)
    zc = lambda n: mp.exp(1j * mp.pi / 4 * (n % 8))
    tot = mp.mpc(0)
    for m in range(8):
        zm = mp.exp(-1j * mp.pi / 4 * (m % 8))
        A = 1 + 1j * zm * j - (zm ** 2) * j * j
        tot += zc(m * c) * (A ** p) * (A_3(m) ** q)
    return tot / 8
def A_3(m):
    zm = mp.exp(-1j * mp.pi / 4 * ((3 * m) % 8))
    return 1 + 1j * zm * jj - (zm ** 2) * jj * jj
jj = None
def mp_S_wrap(k, c, t):
    global jj
    mp.dps = 50
    jj = mp.exp(1j * t)
    return mp_S(k, c, t)

def enum_S(k, c, t):
    """k=3 锚：直接枚举 Q<3^k（三进制数字和）"""
    mp.dps = 50
    j = mp.exp(1j * t)
    def s3(n):
        s = 0
        while n:
            s += n % 3; n //= 3
        return s
    tot = mp.mpc(0)
    for Q in range(3 ** k):
        if Q % 8 == c % 8:
            tot += (1j ** s3(Q)) * (j ** Q)
    return tot / (3 ** k)

def main():
    res = {}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)
    tg = np.linspace(0, 2 * np.pi, N, endpoint=False)

    # ---- B0 锚 ----
    L("== B0 锚 ==")
    val1 = mp_dphi(3, 10, 22, 7 * mp.pi / 4)
    val2 = mp_dphi(5, 2, 20, mp.pi / 2)
    val3 = mp_dphi(5, 10, 22, mpf("5.180353708216"))
    res["B0"] = {"pair_10_22_classes": [c_of(10), c_of(22)],
                 "k3_10_22_at_7pi4": float(val1), "err_vs_2_3": float(abs(val1 - mpf(2)/3)),
                 "k5_2_20_at_pi2": float(val2), "err_vs_archive": float(abs(val2 - mpf("0.279569892473"))),
                 "k5_10_22_at_archive_peak": float(val3), "err_vs_archive2": float(abs(val3 - mpf("0.234689679073")))}
    L(json.dumps(res["B0"]))
    B0 = bool(abs(val1 - mpf(2)/3) < mpf("1e-12") and abs(val2 - mpf("0.279569892473")) < mpf("5e-10")
              and abs(val3 - mpf("0.234689679073")) < mpf("5e-10"))

    # ---- B1 反射恒等 + B2 半周期 ----
    L("== B1/B2 ==")
    b1 = 0.0; b1c = 0.0; b2 = 0.0
    for k in range(3, 13):
        S = build_S(k, tg)
        for (r, rp) in PAIRS_R:
            d = delta_phi(k, r, rp, tg, S)
            dref = np.roll(d[::-1], 1)   # dref[j]=d[(N-j) mod N]=|Δφ|(2π−t_j)
            e1 = float(np.max(np.abs(d - dref)))
            c, cp = c_of(r), c_of(rp)
            Nc = class_N(k)
            raw = np.exp(1j * (r % 3) * tg) * (S[c] / Nc[c] - S[cp] / Nc[cp])
            e1c = float(np.max(np.abs(raw - np.roll(raw[::-1], 1).conjugate())))
            e2 = float(np.max(np.abs(d - np.roll(d, N // 2))))
            b1 = max(b1, e1); b1c = max(b1c, e1c); b2 = max(b2, e2)
    res["B1"] = {"max_refl_diff": b1, "max_conj_diff": b1c}
    res["B2"] = {"max_halfperiod_diff": b2}
    L(json.dumps(res["B1"])); L(json.dumps(res["B2"]))
    B1 = bool(b1 <= 1e-12 and b1c <= 1e-12)

    # 轨道等高（k 奇三对）
    b2o = 0.0
    for k in (3, 5, 7, 9, 11):
        S = build_S(k, tg)
        for (a, b) in [(10, 22), (2, 20), (8, 14)]:
            d = delta_phi(k, a, b, tg, S)
            i = int(np.argmax(d))
            tstar = tg[i]
            orb = [(2 * np.pi - tstar) % (2 * np.pi), (np.pi - tstar) % (2 * np.pi),
                   (np.pi + tstar) % (2 * np.pi), (2 * np.pi - tstar) % (2 * np.pi)]
            vals = [d[int(round(ot / (2 * np.pi) * N)) % N] for ot in orb]
            b2o = max(b2o, float(max(vals) - min(vals)))
    res["B2"]["max_orbit_height_spread"] = b2o
    B2 = bool(res["B2"]["max_halfperiod_diff"] <= 1e-12 and b2o <= 1e-12)

    # ---- B3 argmax 全清 ----
    L("== B3 ==")
    b3rows = []
    B3 = True
    for k in (3, 5, 7, 9, 11):
        S = build_S(k, tg)
        for (a, b) in [(10, 22), (2, 20), (8, 14)]:
            d = delta_phi(k, a, b, tg, S)
            M = float(d.max())
            idx = np.where(d >= M - 1e-12)[0]
            # 聚类（环形相邻合并）
            clusters = []
            cur = [idx[0]]
            for j in idx[1:]:
                if j - cur[-1] <= 3:
                    cur.append(j)
                else:
                    clusters.append(cur); cur = [j]
            clusters.append(cur)
            if len(clusters) > 1 and (clusters[0][0] <= 3 and clusters[-1][-1] >= N - 4):
                clusters[0] = clusters[-1] + clusters[0]; clusters.pop()
            peaks = []
            for cl in clusters:
                j = cl[int(np.argmax(d[cl]))]
                peaks.append(tg[j])
            ncl = len(clusters)
            # 轨道匹配
            t0 = peaks[0]
            orb = sorted(set(round(x % (2 * np.pi), 12) for x in
                         [t0, (np.pi - t0), (np.pi + t0) % (2 * np.pi), (2 * np.pi - t0) % (2 * np.pi)]))
            # 双向距离（环上）
            def ringdist(x, y):
                dd = abs(x - y) % (2 * np.pi)
                return min(dd, 2 * np.pi - dd)
            dmax = 0.0
            for pk in peaks:
                dmax = max(dmax, min(ringdist(pk, o) for o in orb))
            extra = max(0, ncl - len(orb))
            ok = bool(ncl == len(orb) and dmax <= 1e-6)
            row = {"k": k, "pair": "%d|%d" % (a, b), "n_clusters": ncl, "n_orbit": len(orb),
                   "max_cluster_orbit_dist": dmax, "pass": ok, "peaks": [float(x) for x in peaks]}
            b3rows.append(row)
            B3 = B3 and ok
            L(json.dumps(row))
    res["B3"] = {"rows": b3rows, "all_pass": B3}

    # ---- B4 δ 记录 ----
    L("== B4 ==")
    deltas = {}
    for k in (5, 7, 9, 11):
        S = build_S(k, tg)
        d = delta_phi(k, 10, 22, tg, S)
        i = int(np.argmax(d))
        tstar = tg[i]
        rep = (2 * np.pi - tstar) % (2 * np.pi)
        if rep < np.pi:
            rep = rep + np.pi
        lo, hi = mpf(rep - 4 * 2 * np.pi / N), mpf(rep + 4 * 2 * np.pi / N)
        f = lambda tt: mp_dphi(k, 10, 22, tt)
        for _ in range(60):
            m1 = lo + (hi - lo) / 3; m2 = hi - (hi - lo) / 3
            if f(m1) < f(m2): lo = m1
            else: hi = m2
        tstar_ref = (lo + hi) / 2
        delta = float(tstar_ref - 8 * mp.pi / 5)
        deltas["k=%d" % k] = {"peak_refined": float(tstar_ref), "delta_8pi5": delta}
    res["B4"] = {"deltas_10_22": deltas}
    L(json.dumps(res["B4"]))

    res["verdict"] = {"B0": B0, "B1": B1, "B2": B2, "B3": B3,
                      "reflection_family_established": bool(B0 and B1 and B2 and B3)}
    res["log"] = log
    L("VERDICT %s" % json.dumps(res["verdict"]))
    with open("H:/理论存档/01-数学/02-实验与数据/results/reflection_family_theorem_result-v1.0-20260921.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
