# -*- coding: utf-8 -*-
# 峰位轨迹极限点 t̂*（R26 主格二·判据书 D-L 系实算）
# 判据书：代数册·非继承档态数分解律与峰位极限点预注册判据书-v1.0-20260921.md（冻结 NTFS 10:16:34 在先）
# 口径：10|22 对；mpmath 50 位；轨道折算 t̂∈(π/2,π)，δ=t̂−3π/5；t₀=3π/5。
# D-L1 块谱结构（|Π1|/|Π3|=ρ0 k 无关·ρ2² 正实·Π4 奇档纯虚交替·虚部核）；
# D-L2 模型 M-A′：δ_k=c0+c1/(k−1)+c2·ρ2^k+c3·ρ2^k(−1)^((k−1)/2)，k=5,7,9,11 定参，k=13,15 复核 ≤0.10；
# D-L3 延伸 k=17,19 + P-L1..P-L6 记账；D-L4 t̂* 三态判定。
import json
import numpy as np
from mpmath import mp, mpf, exp, pi, cos, sin, atan2

mp.dps = 50

Z8 = exp(2j * pi / 8)

def build_S_mp(k, t):
    """S[c](t) 单点高精度（R25 口径）"""
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
    Nc = M + 1 if c in (0,1) else M
    Ncp = M + 1 if cp in (0,1) else M
    return abs(exp(1j * (r % 3) * t) * (S[c]/Nc - S[cp]/Ncp))

def orbit_fold(tstar):
    p = float(pi)
    cands = [tstar % (2*p), (p - tstar) % (2*p), (tstar + p) % (2*p), (2*p - tstar) % (2*p)]
    for t in cands:
        if p/2 < t < p: return t
    return None

def refine_peak(k, rep, rounds=70):
    lo = mpf(rep) - mpf('1e-3'); hi = mpf(rep) + mpf('1e-3')
    f = lambda tt: mp_dphi(k, tt)
    for _ in range(rounds):
        m1 = lo + (hi-lo)/3; m2 = hi - (hi-lo)/3
        if f(m1) < f(m2): lo = m1
        else: hi = m2
    return (lo+hi)/2

def peak_hat(k):
    """峰位轨道折算 t̂（从 t₀=3π/5 附近粗定位→细化→折算）"""
    # 粗扫（numpy 2^18）
    N = 2**18
    ts = np.linspace(0, 2*np.pi, N, endpoint=False)
    x = np.exp(1j*ts)
    p = (k+1)//2; q = k//2
    Am = [1 + x*np.conj(np.exp(2j*np.pi/8))**m + x*x*np.conj(np.exp(2j*np.pi/8))**(2*m) for m in range(8)]
    M = (3**k - 3)//8
    def Sc(c):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j*np.pi/4*((m*c)%8)) * (Am[m]**p) * (Am[(3*m)%8]**q)
        return acc/8
    c, cp = c_of(10), c_of(22)
    Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
    d = np.abs(np.exp(1j*(10%3)*ts)*(Sc(c)/Nc - Sc(cp)/Ncp))
    i = int(np.argmax(d))
    tref = refine_peak(k, mpf(float(ts[i])))
    that = orbit_fold(float(tref % (2*float(pi))))
    tref2 = refine_peak(k, mpf(that))
    that2 = orbit_fold(float(tref2 % (2*float(pi))))
    return that2

T0 = 3 * pi / 5

def cm(m, t):
    """c_m(t)=1+2cos(t−mπ/4)（实数，mpmath）"""
    return 1 + 2*cos(t - m*pi/4)

def main():
    res = {"anchors": {}, "blocks": {}, "model": {}, "ext": {}, "verdict": {}}
    log = []
    def L(m2):
        log.append(m2); print(m2, flush=True)

    # ---- 六点复现（对照 R25 在档） ----
    arch = {5: 2.0387610546255597, 7: 1.9696071195852347, 9: 1.921041687438436,
            11: 1.8868540456679372, 13: 1.8610554032566275, 15: 1.8406941892437405}
    that = {}
    for k in (5, 7, 9, 11, 13, 15):
        t = peak_hat(k)
        that[k] = t
        res["anchors"]["k=%d" % k] = {"that": float(t), "arch": arch[k], "absdiff": float(abs(t - arch[k]))}
        L("k=%d t̂=%.12f absdiff=%.2e" % (k, float(t), abs(t - arch[k])))
    six_ok = all(abs(that[k] - arch[k]) < mpf('1e-9') for k in that)
    L("six_point_reproduction_ok=%s" % six_ok)
    res["verdict"]["six_point_ok"] = bool(six_ok)

    # ---- D-L1 块谱结构 ----
    # c_m 值与 ρ0、ρ2²（t0=3π/5 解析式）
    cvals = {}
    for m in range(8):
        cvals["c%d" % m] = cm(m, T0)
    rho0 = abs(cvals["c1"] / cvals["c3"])
    rho2sq = abs(cvals["c2"] * cvals["c6"] / (cvals["c3"] * cvals["c1"]))
    res["blocks"]["rho0"] = float(rho0)
    res["blocks"]["rho2_sq"] = float(rho2sq)
    res["blocks"]["rho2"] = float(mpf(rho2sq) ** mpf('0.5'))
    res["blocks"]["cm_t0"] = {k2: float(v) for k2, v in cvals.items()}
    L("rho0=%.9f rho2^2=%.6f rho2=%.6f" % (float(rho0), float(rho2sq), float(mpf(rho2sq)**mpf('0.5'))))
    dl1 = {}
    dl1["rho0_match_685827"] = bool(abs(rho0 - mpf('0.6858274804')) < mpf('5e-10'))
    dl1["rho2sq_match_04934"] = bool(abs(rho2sq - mpf('0.4934')) < mpf('5e-5'))
    # |Π1|/|Π3| 六档恒等（p−q=1）
    ratios = []
    for k in (5, 7, 9, 11, 13, 15):
        p = (k+1)//2; q = k//2
        A1 = abs(1 + exp(-1j*pi/4)*exp(1j*T0) + exp(-1j*pi/2)*exp(2j*T0))
        A3 = abs(1 + exp(-3j*pi/4)*exp(1j*T0) + exp(-3j*pi/2)*exp(2j*T0))
        ratios.append(float(A1**(p) * A3**(q) / (A3**(p) * A1**(q))))
    dl1["p_q_ratio_six"] = ratios
    dl1["p_q_const"] = bool(max(abs(r - float(rho0)) for r in ratios) < 1e-12)
    # A2A6/(A3A1) 正实（虚部核）
    def A(m2, t):
        return 1 + exp(-1j*m2*pi/4)*exp(1j*t) + exp(-1j*m2*pi/2)*exp(2j*t)
    W = A(2, T0)*A(6, T0)/(A(3, T0)*A(1, T0))
    dl1["W_im_abs"] = float(abs(W.imag))
    dl1["W_im_tiny"] = bool(abs(W.imag) < mpf('1e-30'))
    dl1["W_re_positive"] = bool(W.real > 0)
    # Π4/Π3 主振荡 e^{-ikπ/2} 系数纯虚交替（奇档）：核 Π4/Π3 的相位结构
    quad = []
    for k in (5, 7, 9, 11, 13, 15):
        p = (k+1)//2; q = k//2
        P4 = A(4, T0)**k
        P3 = A(3, T0)**p * A(1, T0)**q
        R43 = P4/P3
        # 相位主部=k(−π/2+arg c4)；c4(t0)>0 ⟹ arg c4=0 ⟹ 主部=−kπ/2
        quad.append(float(atan2(R43.imag, R43.real) - (-k*pi/2)))
    dl1["quad_phase_resid"] = quad
    dl1["quad_pure_imag_alt"] = bool(all(abs(r) < mpf('1e-12') or abs(abs(r) - pi) < mpf('1e-12') for r in quad))
    res["verdict"]["D_L1"] = dl1
    L("D_L1: %s" % json.dumps({k2: v for k2, v in dl1.items() if k2 != "p_q_ratio_six" and k2 != "quad_phase_resid"}))

    # ---- D-L2 模型 M-A′ ----
    rho2 = mpf(rho2sq) ** mpf('0.5')
    def basis(k):
        sgn = 1 if ((k-1)//2) % 2 == 0 else -1
        return [mpf(1), mpf(1)/(k-1), rho2**k, rho2**k * sgn]
    ks_fit = [5, 7, 9, 11]
    dvals = {k: that[k] - T0 for k in (5,7,9,11,13,15)}
    # 四点线性方程组（精确解 mpmath）
    Mrow = [[basis(k)[j] for j in range(4)] for k in ks_fit]
    bvec = [dvals[k] for k in ks_fit]
    # 高斯消元
    Aaug = [Mrow[i][:] + [bvec[i]] for i in range(4)]
    for col in range(4):
        piv = next(r for r in range(col, 4) if abs(Aaug[r][col]) > mpf('1e-40'))
        Aaug[col], Aaug[piv] = Aaug[piv], Aaug[col]
        pv = Aaug[col][col]
        Aaug[col] = [x/pv for x in Aaug[col]]
        for r in range(4):
            if r != col and Aaug[r][col] != 0:
                f2 = Aaug[r][col]
                Aaug[r] = [x - f2*y for x, y in zip(Aaug[r], Aaug[col])]
    coef = [Aaug[i][4] for i in range(4)]
    res["model"]["coef"] = [float(c2) for c2 in coef]
    L("M-A' coef c0..c3 = %s" % res["model"]["coef"])
    def dpred(k):
        bs = basis(k)
        return sum(coef[j]*bs[j] for j in range(4))
    checks = {}
    for k in (13, 15):
        pr = dpred(k); ac = dvals[k]
        rel = abs(pr - ac)/abs(ac)
        checks["k=%d" % k] = {"pred": float(pr), "actual": float(ac), "relerr": float(rel)}
    ok2 = bool(all(v["relerr"] <= 0.10 for v in checks.values()))
    res["model"]["checks"] = checks
    res["model"]["ok"] = ok2
    L("M-A' checks: %s ok=%s" % (json.dumps(checks), ok2))

    # ---- D-L3 延伸 k=17,19 ----
    ext = {}
    for k in (17, 19):
        t = peak_hat(k)
        ext["k=%d" % k] = {"that": float(t), "delta": float(t - T0)}
        that[k] = t
        dvals[k] = t - T0
    res["ext"] = ext
    L("ext: %s" % json.dumps(ext))
    tk = {k: float(that[k]) for k in that}
    a17 = tk[15] - tk[17]; a19 = tk[17] - tk[19]
    pl = {
        "P_L1_t17_lt_t15": bool(tk[17] < tk[15]),
        "P_L2_t19_lt_t17": bool(tk[19] < tk[17]),
        "P_L3_a17": {"a17": a17, "lo": 0.013, "hi": 0.020, "hit": bool(0.013 < a17 < 0.020)},
        "P_L4_a19": {"a19": a19, "lo": 0.010, "hi": 0.018, "hit": bool(0.010 < a19 < 0.018)},
        "P_L5_t17": {"t17": tk[17], "lo": 1.8207, "hi": 1.8277, "hit": bool(1.8207 < tk[17] < 1.8277)},
        "P_L6_t19": {"t19": tk[19], "lo": 1.8097, "hi": 1.8177, "hit": bool(1.8097 < tk[19] < 1.8177)},
    }
    # M-A′ 公式外推 δ17/19
    pl["M_Ap_pred17"] = float(dpred(17)); pl["M_Ap_pred19"] = float(dpred(19))
    pl["M_Ap_actual17"] = float(dvals[17]); pl["M_Ap_actual19"] = float(dvals[19])
    res["verdict"]["P_L"] = pl
    L("P_L: %s" % json.dumps(pl))

    # ---- D-L4 t̂* 三态判定 ----
    if pl["P_L1_t17_lt_t15"] and pl["P_L2_t19_lt_t17"]:
        verdict4 = {"state": "A_convergent", "that_star_interval": [tk[19], float(3*pi/5)],
                    "basis": "单调延续（P-L1∧P-L2 真）⟹ 区间套 t̂*∈[t̂19,3π/5)；M-A' 衰减项占优佐证=%s" % ok2}
    elif ok2:
        verdict4 = {"state": "B_oscillatory", "basis": "单调破缺且 M-A′ 成立 ⟹ 持续振荡读法"}
    else:
        verdict4 = {"state": "C_open", "basis": "数据不足（模型判负+单调破缺并存或数据不足）"}
    res["verdict"]["D_L4"] = verdict4
    L("D_L4: %s" % json.dumps(verdict4, ensure_ascii=False))

    outp = "H:/理论存档/01-数学/02-实验与数据/results/delta_limit_point_result-v1.0-20260921.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
