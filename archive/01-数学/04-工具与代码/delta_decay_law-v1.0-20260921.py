# -*- coding: utf-8 -*-
# 峰位衰减律解析闭式与收敛阶（R27 主格一·判据书 D-T 系实算）
# 判据书：代数册·峰位衰减律解析闭式与收敛阶预注册判据书-v1.0-20260921.md
#         （冻结 NTFS 11:05:23 在先；首跑前更正两处 11:07:48：D-T1① t 网格改区间内、D-T1② 幅度 ρ4 就地比率）
# 口径：10|22 对（c=3,c'=7）；mpmath 50 位；轨道折算 t̂∈(π/2,π)；peak_hat 复用 R26 delta_limit_point 在档实现。
# 片1（--part 1）：D-T0 复现+块常量 / D-T1 解析恒等式核 / D-T2 平衡方程残差 / D-T3 衰减阶四候选拟合
# 片2（--part 2）：D-T4 k=21,23 延伸+P-T 记账 / D-T5 判定输出
import json, sys
import numpy as np
from mpmath import mp, mpf, exp, pi, cos, sin, atan2, sqrt

mp.dps = 50

T0 = 3 * pi / 5
PI = pi

# ---------- R26 在档口径复用（delta_limit_point-v1.0-20260921.py） ----------
def build_S_mp(k, t):
    p = (k + 1) // 2; q = k // 2
    tt = exp(1j * t)
    def Scc(c):
        tot = mp.mpc(0)
        for m in range(8):
            zm = exp(-1j * pi / 4 * (m % 8))
            z3m = exp(-1j * pi / 4 * ((3 * m) % 8))
            tot += exp(1j * pi / 4 * ((m * c) % 8)) * (1 + zm * tt + zm**2 * tt**2)**p \
                   * (1 + z3m * tt + z3m**2 * tt**2)**q
        return tot / 8
    return [Scc(c) for c in range(8)]

def c_of(r): return (r - (r % 3)) // 3 % 8

def mp_dphi(k, t):
    r, rp = 10, 22
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3) // 8
    S = build_S_mp(k, t)
    Nc = M + 1 if c in (0, 1) else M
    Ncp = M + 1 if cp in (0, 1) else M
    return abs(exp(1j * (r % 3) * t) * (S[c] / Nc - S[cp] / Ncp))

def orbit_fold(tstar):
    p = float(pi)
    cands = [tstar % (2 * p), (p - tstar) % (2 * p), (tstar + p) % (2 * p), (2 * p - tstar) % (2 * p)]
    for t in cands:
        if p / 2 < t < p: return t
    return None

def refine_peak(k, rep, rounds=70):
    lo = mpf(rep) - mpf('1e-3'); hi = mpf(rep) + mpf('1e-3')
    f = lambda tt: mp_dphi(k, tt)
    for _ in range(rounds):
        m1 = lo + (hi - lo) / 3; m2 = hi - (hi - lo) / 3
        if f(m1) < f(m2): lo = m1
        else: hi = m2
    return (lo + hi) / 2

def peak_hat(k):
    N = 2**18
    ts = np.linspace(0, 2 * np.pi, N, endpoint=False)
    x = np.exp(1j * ts)
    p = (k + 1) // 2; q = k // 2
    w = np.conj(np.exp(2j * np.pi / 8))
    Am = [1 + x * (w**m) + x * x * (w**(2 * m)) for m in range(8)]
    M = (3**k - 3) // 8
    def Sc(c):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j * np.pi / 4 * ((m * c) % 8)) * (Am[m]**p) * (Am[(3 * m) % 8]**q)
        return acc / 8
    c, cp = c_of(10), c_of(22)
    Nc = M + 1 if c in (0, 1) else M; Ncp = M + 1 if cp in (0, 1) else M
    d = np.abs(np.exp(1j * (10 % 3) * ts) * (Sc(c) / Nc - Sc(cp) / Ncp))
    i = int(np.argmax(d))
    tref = refine_peak(k, mpf(float(ts[i])))
    that = orbit_fold(float(tref % (2 * float(pi))))
    tref2 = refine_peak(k, mpf(that))
    that2 = orbit_fold(float(tref2 % (2 * float(pi))))
    return that2

# ---------- 解析量 ----------
def cm(m, t):
    return 1 + 2 * cos(t - m * pi / 4)

def Ablk(m, t):
    tt = exp(1j * t)
    zm = exp(-1j * pi / 4 * (m % 8))
    return 1 + zm * tt + zm * zm * tt**2

def Pi(m, k, t):
    p = (k + 1) // 2; q = k // 2
    return Ablk(m, t)**p * Ablk((3 * m) % 8, t)**q

def GJ(t):
    """G=(ln c3c1)'=c3'/c3+c1'/c1；J=(c3-c1)'/(c3-c1)（M-T3）"""
    c3 = cm(3, t); c1 = cm(1, t)
    c3p = -2 * sin(t - 3 * pi / 4)
    c1p = -2 * sin(t - pi / 4)
    G = c3p / c3 + c1p / c1
    J = (c3p - c1p) / (c3 - c1)
    return G, J

def dphi_blocks(k, t):
    """载体两项式 (1/(4M))[ζ³(Π1−Π5)+ζ(Π3−Π7)]（M-T1）"""
    M = (3**k - 3) // 8
    z = exp(2j * pi / 8)
    return (Pi(1, k, t) - Pi(5, k, t)) * z**3 / (4 * M) + (Pi(3, k, t) - Pi(7, k, t)) * z / (4 * M)

def dphi_machine(k, t):
    """机器口径 e^{it}(S3−S7)/M（N3=N7=M）"""
    S = build_S_mp(k, t)
    M = (3**k - 3) // 8
    return exp(1j * t) * (S[3] - S[7]) / M

def fit_ls(cols, ys):
    """普通最小二乘（cols=列向量列表 → 系数），mpmath 精度"""
    n = len(cols[0]); m2 = len(cols)
    A = [[sum(cols[r][j] * cols[s][j] for j in range(n)) for s in range(m2)] for r in range(m2)]
    b = [sum(cols[r][j] * ys[j] for j in range(n)) for r in range(m2)]
    aug = [A[i][:] + [b[i]] for i in range(m2)]
    for col in range(m2):
        piv = next(r for r in range(col, m2) if abs(aug[r][col]) > mpf('1e-60'))
        aug[col], aug[piv] = aug[piv], aug[col]
        pv = aug[col][col]
        aug[col] = [xv / pv for xv in aug[col]]
        for r in range(m2):
            if r != col and aug[r][col] != 0:
                f2 = aug[r][col]
                aug[r] = [xv - f2 * yv for xv, yv in zip(aug[r], aug[col])]
    return [aug[i][m2] for i in range(m2)]

ARCH = {5: 2.0387610546255597, 7: 1.9696071195852347, 9: 1.921041687438436,
        11: 1.8868540456679372, 13: 1.8610554032566275, 15: 1.8406941892437405,
        17: 1.8240941440196299, 19: 1.8102235269713327}

def main(part):
    res = {"part": part, "anchors": {}, "blocks": {}, "ident": {}, "balance": {}, "fit": {}, "ext": {}, "verdict": {}}
    def L(s):
        print(s, flush=True)

    # ---- D-T0 回归先行 ----
    that = {}
    for k in (5, 7, 9, 11, 13, 15, 17, 19):
        t = peak_hat(k)
        that[k] = t
        res["anchors"]["k=%d" % k] = {"that": float(t), "arch": ARCH[k], "absdiff": float(abs(t - ARCH[k]))}
        L("k=%d t̂=%.12f absdiff=%.2e" % (k, float(t), abs(t - ARCH[k])))
    repro_ok = all(abs(that[k] - ARCH[k]) < mpf('1e-9') for k in that)
    # 块常量
    cvals = {"c%d" % m: cm(m, T0) for m in range(8)}
    rho0 = abs(cvals["c1"] / cvals["c3"])
    rho2sq = abs(cvals["c2"] * cvals["c6"] / (cvals["c3"] * cvals["c1"]))
    rho3sq = abs(cvals["c5"] * cvals["c7"] / (cvals["c3"] * cvals["c1"]))
    rho4sq = cvals["c4"] ** 2 / (cvals["c3"] * cvals["c1"])
    res["blocks"] = {"rho0": float(rho0), "rho2_sq": float(rho2sq), "rho3_sq": float(rho3sq),
                     "rho4_sq": float(rho4sq), "cm_t0": {kk: float(vv) for kk, vv in cvals.items()}}
    L("rho0=%.10f rho2^2=%.10f rho3^2=%.6f rho4^2(t0)=%.10f" % (float(rho0), float(rho2sq), float(rho3sq), float(rho4sq)))
    dt0_ok = bool(abs(rho0 - mpf('0.6858274804')) < mpf('5e-10') and abs(rho2sq - mpf('0.4932215826')) < mpf('5e-10')
                  and abs(rho3sq - mpf('0.013556')) < mpf('1e-6'))
    res["verdict"]["D_T0"] = {"repro_ok": bool(repro_ok), "block_const_ok": dt0_ok}
    L("D_T0: repro_ok=%s block_const_ok=%s" % (repro_ok, dt0_ok))

    # ---- D-T1 解析恒等式机器核 ----
    ident = {}
    # ① Π1/Π3 = i·ρ0(t)（六档×六点）
    tgrid = [that[5], that[7], that[9], T0, mpf('2.2'), mpf('2.5')]
    max_re = mpf(0); max_amp = mpf(0)
    for k in (5, 7, 9, 11, 13, 15):
        for t in tgrid:
            R = Pi(1, k, t) / Pi(3, k, t)
            rho0t = cm(1, t) / cm(3, t)
            max_re = max(max_re, abs(R.real))
            max_amp = max(max_amp, abs(abs(R) - abs(rho0t)) / abs(rho0t))
    ident["i1_max_Re"] = float(max_re)
    ident["i1_max_amp_rel"] = float(max_amp)
    ident["i1_ok"] = bool(max_re < mpf('1e-30') and max_amp < mpf('1e-12'))
    # ② Π4/Π3 相位闭式 + 幅度层化（ρ4 就地）
    max_ph = mpf(0); max_am4 = mpf(0)
    for k in (5, 7, 9, 11, 13, 15):
        for t in tgrid:
            R43 = Pi(4, k, t) / Pi(3, k, t)
            Rp = R43 * exp(1j * k * pi / 2)
            ph = atan2(Rp.imag, Rp.real)
            max_ph = max(max_ph, abs(ph - pi / 4))
            rho4t = sqrt(abs(cm(4, t) ** 2 / (abs(cm(3, t) * cm(1, t)))))
            amp_model = abs(cm(4, t)) / abs(cm(3, t)) * rho4t ** (k - 1)
            max_am4 = max(max_am4, abs(abs(R43) / amp_model - 1))
    ident["i2_max_phase_dev"] = float(max_ph)
    ident["i2_max_amp_dev"] = float(max_am4)
    ident["i2_ok"] = bool(max_ph < mpf('1e-12') and max_am4 < mpf('1e-12'))
    # ③ 载体恒等式
    max_ld = mpf(0)
    for k in (5, 7):
        for t in [mpf('1.75'), mpf('1.9'), mpf('2.0'), mpf('2.2'), mpf('2.5'), mpf('2.8')]:
            a = abs(dphi_machine(k, t)); b = abs(dphi_blocks(k, t))
            max_ld = max(max_ld, abs(a - b) / a)
    ident["i3_max_reldev"] = float(max_ld)
    ident["i3_ok"] = bool(max_ld < mpf('1e-12'))
    res["ident"] = ident
    dt1_ok = ident["i1_ok"] and ident["i2_ok"] and ident["i3_ok"]
    res["verdict"]["D_T1"] = bool(dt1_ok)
    L("D_T1: %s" % json.dumps(ident))
    L("D_T1_ok=%s" % dt1_ok)

    # ---- D-T2 平衡方程残差 ----
    bal = {"resid": {}, "k5_resid": None}
    worst = mpf(0)
    for k in (7, 9, 11, 13, 15, 17, 19):
        G, J = GJ(that[k])
        r = abs(((k - 1) // 2) * G + J)
        bal["resid"]["k=%d" % k] = float(r)
        worst = max(worst, r)
    G5, J5 = GJ(that[5])
    r5 = abs(2 * G5 + J5)
    bal["k5_resid"] = float(r5)
    # Π5 层量级@t̂5（记录）
    p5 = (5 + 1) // 2; q5 = 5 // 2
    P5oP3 = abs(Pi(5, 5, that[5]) / Pi(3, 5, that[5]))
    bal["k5_Pi5_over_Pi3"] = float(P5oP3)
    # J/G 单调递增核（网格差分）
    mono_ok = True
    prev = None
    tt = mpf('1.58')
    while tt < mpf('2.87'):
        G, J = GJ(tt)
        v = J / G
        if prev is not None and v < prev - mpf('1e-12'):
            mono_ok = False
        prev = v
        tt += mpf('0.05')
    bal["JG_monotone_up"] = bool(mono_ok)
    bal["worst_resid_k7_19"] = float(worst)
    res["balance"] = bal
    dt2_ok = bool(worst <= mpf('0.02') and mono_ok)
    k5_in_band = bool(mpf('0.03') <= r5 <= mpf('0.12'))
    res["verdict"]["D_T2"] = {"ok": dt2_ok, "k5_band": k5_in_band}
    L("D_T2: worst=%.3e k5_resid=%.4f Pi5/Pi3@t5=%.4f mono=%s ok=%s" % (float(worst), float(r5), float(P5oP3), mono_ok, dt2_ok))

    # ---- D-T3 衰减阶四候选拟合（k=5..19 十点） ----
    qsl = list(range(2, 10))
    ysl = [that[k] - pi / 2 for k in (5, 7, 9, 11, 13, 15, 17, 19)]
    rho2 = sqrt(rho2sq)
    models = {
        "M1_inv_k": [[mpf(1) / (k2) for k2 in (5, 7, 9, 11, 13, 15, 17, 19)], [mpf(1) / (k2 ** 2) for k2 in (5, 7, 9, 11, 13, 15, 17, 19)]],
        "M2_sqrt": [[1 / sqrt(q2) for q2 in qsl], [mpf(1) / q2 for q2 in qsl]],
        "M3_geom": [[rho2 ** k2 for k2 in (5, 7, 9, 11, 13, 15, 17, 19)]],
        "M4_inv_k_only": [[mpf(1) / k2 for k2 in (5, 7, 9, 11, 13, 15, 17, 19)]],
    }
    fits = {}
    for name, cols in models.items():
        cf = fit_ls(cols, ysl)
        worst_rel = mpf(0)
        for r in range(len(ysl)):
            yh = sum(cf[j] * cols[j][r] for j in range(len(cf)))
            worst_rel = max(worst_rel, abs(yh - ysl[r]) / abs(ysl[r]))
        fits[name] = {"coef": [float(x2) for x2 in cf], "max_rel_resid": float(worst_rel)}
    # 解析 C
    Gp = mpf(-16) + 10 * sqrt(2)   # G'(π/2)=−16+10√2
    C_exact = 1 / sqrt(-Gp)
    fits["C_exact_1_over_sqrt16-10sqrt2"] = float(C_exact)
    fits["Gprime_pi2_exact"] = float(Gp)
    res["fit"] = fits
    m2r = mpf(str(fits["M2_sqrt"]["max_rel_resid"]))
    others = min(mpf(str(fits[n2]["max_rel_resid"])) for n2 in ("M1_inv_k", "M3_geom", "M4_inv_k_only"))
    dt3_ok = bool(m2r <= mpf('0.05') and m2r <= others / 3)
    res["verdict"]["D_T3"] = {"ok": dt3_ok, "M2_max_rel": float(m2r), "best_other": float(others),
                              "C_fit_band": bool(mpf('0.68') <= fits["M2_sqrt"]["coef"][0] <= 0.78 and True)}
    L("D_T3: %s ok=%s C_exact=%.6f" % (json.dumps({k2: v2 for k2, v2 in fits.items()}), dt3_ok, float(C_exact)))

    # ---- 片2：D-T4 延伸 + D-T5 判定 ----
    if part == 2:
        ext = {}
        for k in (21, 23):
            t = peak_hat(k)
            that[k] = t
            ext["k=%d" % k] = {"that": float(t), "delta": float(t - T0)}
            L("k=%d t̂=%.12f" % (k, float(t)))
        res["ext"] = ext
        P = {}
        P["P_T1_t21_lt_t19"] = bool(that[21] < that[19])
        P["P_T2_t23_lt_t21"] = bool(that[23] < that[21])
        P["P_T3_t21_band"] = bool(mpf('1.7945') < that[21] < mpf('1.8015'))
        P["P_T4_t23_band"] = bool(mpf('1.7850') < that[23] < mpf('1.7920'))
        P["P_T5_eq21"] = {"dev": float(abs(that[21] - mpf('1.7979'))), "hit": bool(abs(that[21] - mpf('1.7979')) <= mpf('0.005'))}
        P["P_T6_eq23"] = {"dev": float(abs(that[23] - mpf('1.7884'))), "hit": bool(abs(that[23] - mpf('1.7884')) <= mpf('0.005'))}
        A2 = fits["M2_sqrt"]["coef"][0]
        P["P_T7_C_band"] = bool(mpf('0.68') <= mpf(str(A2)) <= mpf('0.78'))
        P["P_T8_k5_resid_band"] = bool(mpf('0.03') <= mpf(str(r5)) <= mpf('0.12'))
        seq = [float(that[k]) for k in (5, 7, 9, 11, 13, 15, 17, 19, 21, 23)]
        P["P_T9_mono12"] = bool(all(seq[i] > seq[i + 1] for i in range(len(seq) - 1)))
        # 平衡方程数值解对照（记录级）
        eq = {}
        for k in (21, 23):
            q2 = (k - 1) // 2
            lo = mpf('1.55'); hi = mpf('2.10')
            for _ in range(200):
                mid = (lo + hi) / 2
                G, J = GJ(mid)
                if q2 * G + J > 0: lo = mid
                else: hi = mid
            eq["k=%d" % k] = float((lo + hi) / 2)
        res["verdict"]["P_T"] = P
        res["verdict"]["eq_solve"] = eq
        L("P_T: %s" % json.dumps(P))
        L("eq_solve: %s" % json.dumps(eq))
        # D-T5 判定
        state = None
        if dt2_ok and dt3_ok and P["P_T1_t21_lt_t19"] and P["P_T2_t23_lt_t21"]:
            state = "A_prime_closed"
        elif dt2_ok:
            state = "B_partial"
        else:
            state = "C_refuted"
        res["verdict"]["D_T5"] = {"state": state, "tstar_pi2": state == "A_prime_closed",
                                  "interval": [float(pi / 2), float(that[23])]}
        L("D_T5: state=%s t̂*∈(π/2, t̂₂₃]=(%.6f, %.6f]" % (state, float(pi / 2), float(that[23])))

    out = "H:/理论存档/01-数学/02-实验与数据/results/delta_decay_law_%s-v1.0-20260921.json" % ("part1" if part == 1 else "part2")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L("saved: %s" % out)

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
