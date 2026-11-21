# -*- coding: utf-8 -*-
# d±2 轨迹余项解析（R30 主格一·判据书 D-Y 系实算）
# 判据书：代数册·d±2余项解析与奇偶不变量定理化预注册判据书-v1.0-20260924.md（冻结 2026-09-24 03:29:44）
# 口径：D-Y0 Q 谱回归（Z4 通道重算 vs R29 dpm2_track_mech-q2 JSON 直读·整数零容差+b=0）
#       D-Y1 闭式三件（端点值抵消四条 Z4 精确恒等+块值闭式六条+对数导数闭式四条 mpmath 1e-12）
#       D-Y2 贡献矩阵分解协议（8x8 对 C_{m,m'} Z4 精确·Σ 恒等=Q 总值·主导对识别）
#       D-Y3 k=19,21 延伸器产出+P-Y1..Y4 记账；D-Y4 maxdiff 比率 P-Y5+候选闭式判别
# 器口径复用 R29 dpm2_track_mech（Z4 四元组/2^18 网格/mpmath 50 位/轨道折算）。
import json, argparse
import numpy as np
from mpmath import mp, mpf, exp, pi, sqrt as msqrt

mp.dps = 50

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_REG = [3, 5, 7, 9, 11, 13, 15, 17]
KS_EXT = [19, 21]
R29_Q2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-q2-v1.0-20260924.json"
R30_P2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part2-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-%s-v1.0-20260924.json"

def c_of(r): return (r - (r % 3)) // 3 % 8

# ---------- Z4 四元组通道（R29 口径复用） ----------
def zmul(A, B):
    a, b, c, d = A; e, f, g, h = B
    return (a*e - (b*h + c*g + d*f),
            a*f + b*e - (c*h + d*g),
            a*g + b*f + c*e - d*h,
            a*h + b*g + c*f + d*e)

def zconj(A):
    a, b, c, d = A
    return (a, -d, -c, -b)

def zscale(A, n):
    return (A[0]*n, A[1]*n, A[2]*n, A[3]*n)

def zadd(A, B):
    return (A[0]+B[0], A[1]+B[1], A[2]+B[2], A[3]+B[3])

Z = {0: (1,0,0,0), 1: (0,1,0,0), 2: (0,0,1,0), 3: (0,0,0,1),
     4: (-1,0,0,0), 5: (0,-1,0,0), 6: (0,0,-1,0), 7: (0,0,0,-1)}

def zpow(n):
    return Z[n % 8]

def poly_mul(A, B):
    out = [(0,0,0,0)] * (len(A) + len(B) - 1)
    out = list(out)
    for i, a in enumerate(A):
        if a == (0,0,0,0): continue
        for j, b in enumerate(B):
            if b == (0,0,0,0): continue
            out[i+j] = zadd(out[i+j], zmul(a, b))
    return out

def poly_pow(A, n):
    R = [(1,0,0,0)]
    B = list(A)
    while n:
        if n & 1: R = poly_mul(R, B)
        B = poly_mul(B, B); n >>= 1
    return R

def zpowN(A, n):
    R = (1,0,0,0); B = A
    while n:
        if n & 1: R = zmul(R, B)
        B = zmul(B, B); n >>= 1
    return R

def znorm(A):
    return sum(int(x)*int(x) for x in A)

def sign_qsqrt2(A, B):
    if B == 0: return 0 if A == 0 else (1 if A > 0 else -1)
    if A == 0: return 1 if B > 0 else -1
    if (A > 0) == (B > 0): return 1 if A > 0 else -1
    if A*A > 2*B*B: return 1 if A > 0 else -1
    if A*A < 2*B*B: return 1 if B > 0 else -1
    return 0

LAM = (1, 1, 0, -1)       # 1+√2 = 1+ζ+ζ^7（ζ^7=-ζ^3 约化）
LAMm = (-1, 1, 0, -1)     # √2-1
SQ2 = (0, 1, 0, -1)       # √2 = ζ+ζ^7
I4 = (0, 0, 1, 0)         # i = ζ^2

def Q2_second(k, r, rp):
    """Q(k)=d^2|P(e^{it})|^2/dt^2 at pi/2；P=Ncp*Sum z^{mc}Pi_m - Nc*Sum z^{mc'}Pi_m
    g''(pi/2) = -Sum n^2 c_n z^{2n}，c_n=Sum_i P_i conj(P_{i-n})（R29 口径）"""
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    p = (k+1)//2; q = k//2
    polys = pi_polys(k)
    deg = max(len(v) for v in polys.values())
    P = [(0,0,0,0)] * deg
    for m in range(8):
        zc = zpow(m*c); zcp = zpow(m*cp)
        for i, pm in enumerate(polys[m]):
            P[i] = zadd(P[i], zadd(zscale(zmul(zc, pm), Ncp), zscale(zmul(zcp, pm), -Nc)))
    L = len(P)
    res = (0,0,0,0)
    for i in range(L):
        if P[i] == (0,0,0,0): continue
        for j in range(L):
            if P[j] == (0,0,0,0): continue
            n = i - j
            if n == 0: continue
            term = zmul(P[i], zconj(P[j]))
            term = zscale(term, -(n*n))
            tw = zmul(term, zpow(2*n))
            res = zadd(res, tw)
    A, B, C, D = res
    real_ok = (C == 0 and D == -B)
    if not real_ok:
        return {"real_ok": False, "raw": [A, B, C, D]}
    sgn = sign_qsqrt2(A, B)
    return {"real_ok": True, "a": A, "b": B, "sign": sgn}

def pi_polys(k):
    p = (k+1)//2; q = k//2
    polys = {}
    for m in range(8):
        zm = zpow(-m); z3m = zpow(-3*m)
        Am = [(1,0,0,0), zm, zmul(zm, zm)]
        A3 = [(1,0,0,0), z3m, zmul(z3m, z3m)]
        polys[m] = poly_mul(poly_pow(Am, p), poly_pow(A3, q))
    return polys

def pi_values(k):
    """val[m]=Pi_m(i), der[m]=Pi_m'(i), der2[m]=Pi_m''(i)（Z4 精确；i^i=z^{2i}）"""
    polys = pi_polys(k)
    val = {}; der = {}; der2 = {}
    for m in range(8):
        v = (0,0,0,0); d1 = (0,0,0,0); d2 = (0,0,0,0)
        for i, ci in enumerate(polys[m]):
            if ci == (0,0,0,0): continue
            v = zadd(v, zmul(ci, zpow(2*i)))
            if i >= 1:
                d1 = zadd(d1, zscale(zmul(ci, zpow(2*i - 2)), i))
            if i >= 2:
                d2 = zadd(d2, zscale(zmul(ci, zpow(2*i)), -(i*(i-1))))
        val[m] = v; der[m] = d1; der2[m] = d2
    return val, der, der2

def gamma_m(k, r, rp):
    """γ_m = Ncp z^{mc} - Nc z^{mc'}（Z4）"""
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    return {m: zadd(zscale(zpow(m*c), Ncp), zscale(zpow(m*cp), -Nc)) for m in range(8)}

# ---------- 峰位通道（R29 口径复用） ----------
def build_S(k, t):
    p = (k + 1) // 2; q = k // 2
    tt = exp(1j * t)
    out = []
    for c in range(8):
        tot = mp.mpc(0)
        for m in range(8):
            zm = exp(-1j * pi / 4 * (m % 8))
            z3m = exp(-1j * pi / 4 * ((3 * m) % 8))
            tot += exp(1j * pi / 4 * ((m * c) % 8)) * (1 + zm*tt + zm**2*tt**2)**p \
                   * (1 + z3m*tt + z3m**2*tt**2)**q
        out.append(tot / 8)
    return out

def dphi_val(k, r, rp, t, Sc=None):
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3) // 8
    if Sc is None:
        Sc = build_S(k, t)
    Nc = M + 1 if c in (0, 1) else M
    Ncp = M + 1 if cp in (0, 1) else M
    return abs(exp(1j * (r % 3) * t) * (Sc[c]/Nc - Sc[cp]/Ncp))

def grid_peak(k, r, rp, N=2**18):
    ts = np.linspace(0, 2*np.pi, N, endpoint=False)
    x = np.exp(1j*ts)
    p = (k+1)//2; q = k//2
    w = np.conj(np.exp(2j*np.pi/8))
    Am = [1 + x*(w**m) + x*x*(w**(2*m)) for m in range(8)]
    M = (3**k - 3)//8
    Sc = {}
    for c in range(8):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j*np.pi/4*((m*c) % 8)) * (Am[m]**p) * (Am[(3*m) % 8]**q)
        Sc[c] = acc/8
    c, cp = c_of(r), c_of(rp)
    Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
    d = np.abs(np.exp(1j*(r % 3)*ts) * (Sc[c]/Nc - Sc[cp]/Ncp))
    return float(ts[int(np.argmax(d))])

def refine(k, r, rp, rep, rounds=80):
    lo = mpf(rep) - mpf('1e-3'); hi = mpf(rep) + mpf('1e-3')
    f = lambda tt: dphi_val(k, r, rp, tt)
    for _ in range(rounds):
        m1 = lo + (hi-lo)/3; m2 = hi - (hi-lo)/3
        if f(m1) < f(m2): lo = m1
        else: hi = m2
    return (lo+hi)/2

def orbit_fold(t):
    p = float(pi)
    cands = [t % (2*p), (p-t) % (2*p), (t+p) % (2*p), (2*p-t) % (2*p)]
    for x in cands:
        if p/2 < x < p: return x
    return None

def peak_full(k, r, rp):
    g = grid_peak(k, r, rp)
    rf = refine(k, r, rp, g)
    return g, rf

# ---------- part 1：D-Y0 回归 + D-Y1 闭式 + D-Y2 贡献矩阵 ----------
def run_part1():
    log = []
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    # D-Y0：Q 谱回归（整数零容差）+ b=0
    dy0_bad = []; ball_ok = True
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        for k in KS_REG:
            q = Q2_second(k, r, rp)
            ref = r29["DW2"][key][str(k)]
            ok = q["real_ok"] and ref["real_ok"] and q["a"] == ref["a"] and q["b"] == ref["b"] == 0
            if not ok:
                dy0_bad.append((key, k, q.get("a"), ref.get("a")))
            if q.get("b") != 0: ball_ok = False
    log.append("D-Y0 bad=%d (32 values, b==0 all: %s)" % (len(dy0_bad), ball_ok))
    # D-Y1：端点值闭式四条+块值闭式六条（Z4 精确恒等）
    dy1_bad = []; endpoint = {}
    for k in (3, 9, 17):
        p = (k+1)//2; q = k//2
        val, der, der2 = pi_values(k)
        lam_k = zpowN(LAM, k); lamn_k = zpowN(LAMm, k)
        for name, got, exp_ in (
            ("Pi1", val[1], zmul(zpow(1), lam_k)),
            ("Pi3", val[3], zmul(zpow(7), lam_k)),
            ("Pi5", val[5], zmul(zpow(1), lamn_k)),
            ("Pi7", val[7], zmul(zpow(7), lamn_k)),
            ("Pi2", val[2], (3**p, 0, 0, 0)),
            ("Pi6", val[6], (3**q, 0, 0, 0)),
        ):
            if got != exp_:
                dy1_bad.append(("block", k, name))
        T220 = (0,0,0,0); T814 = (0,0,0,0); T410 = (0,0,0,0); T1022 = (0,0,0,0)
        for m in range(8):
            T220 = zadd(T220, zmul(zadd((1,0,0,0), zscale(zpow(6*m), -1)), val[m]))
            T814 = zadd(T814, zmul(zmul(zpow(2*m), zadd((1,0,0,0), zscale(zpow(2*m), -1))), val[m]))
            T410 = zadd(T410, zmul(zadd(zpow(m), zscale(zpow(3*m), -1)), val[m]))
            T1022 = zadd(T1022, zmul(zadd(zpow(2*m), zscale(zpow(6*m), -1)), val[m]))
        c220 = zscale((3**p + 3**q, 0, 0, 0), 2)
        c814 = zscale(c220, -1)
        c410 = zscale(zmul(I4, zadd(zadd(lam_k, (3**p, 0, 0, 0)),
                                    zadd(zscale((3**q, 0, 0, 0), -1), zscale(lamn_k, -1)))), 2)
        c1022 = zscale(zmul(SQ2, zadd(lam_k, lamn_k)), -2)
        for name, got, exp_ in (("T220", T220, c220), ("T814", T814, c814),
                                ("T410", T410, c410), ("T1022", T1022, c1022)):
            endpoint["%s_k%d" % (name, k)] = [got[0], got[1], got[2], got[3]]
            if got != exp_:
                dy1_bad.append(("endpoint", k, name))
        if T814 != zadd(T220, zscale(zadd(val[2], val[6]), -4)):
            dy1_bad.append(("endpoint_consistency", k))
    log.append("D-Y1 endpoint/block Z4-exact bad=%d" % len(dy1_bad))
    # D-Y1③：对数导数闭式（mpmath 1e-12）
    a_ = mpf(2) - msqrt(mpf(2)); b_ = mpf(2) + msqrt(mpf(2))
    dy1l_bad = {}; Ltab = {}
    for k in (3, 9):
        p = (k+1)//2; q = k//2
        x = exp(1j*pi/2)
        w = exp(-1j*pi/4)
        def Am(m):
            zm = w**(m % 8)
            return 1 + zm*x + zm*zm*x*x
        def dAx(m):
            zm = w**(m % 8)
            return zm + 2*zm*zm*x
        Lnum = {
            1: p*(-dAx(1)/Am(1)) + q*(-dAx(3)/Am(3)),
            3: p*(-dAx(3)/Am(3)) + q*(-dAx(1)/Am(1)),
            5: p*(-dAx(5)/Am(5)) + q*(-dAx(7)/Am(7)),
            7: p*(-dAx(7)/Am(7)) + q*(-dAx(5)/Am(5)),
        }
        Lclo = {1: -a_ + 1j*k, 3: a_ + 1j*k, 5: -b_ + 1j*k, 7: b_ + 1j*k}
        for m in (1, 3, 5, 7):
            e = float(abs(Lnum[m] - Lclo[m]))
            Ltab["L%d_k%d" % (m, k)] = e
            if e > 1e-12:
                dy1l_bad.append((k, m, e))
    log.append("D-Y1 log-derivative bad=%d (max err %.3e)" % (len(dy1l_bad), max(Ltab.values())))
    # D-Y2：贡献矩阵分解（k=3,9,17 四对）
    dy2_bad = []; cmats = {}
    for k in (3, 9, 17):
        val, der, der2 = pi_values(k)
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            gam = gamma_m(k, r, rp)
            S = (0,0,0,0)
            rows = {}
            for m1 in range(8):
                for m2 in range(8):
                    pre = zmul(gam[m1], zconj(gam[m2]))
                    d2m = zadd(der2[m1], zscale(zmul(I4, der[m1]), -1))   # d/dt 口径：h''=P''-iP'（x=i）
                    d2n = zadd(der2[m2], zscale(zmul(I4, der[m2]), -1))
                    t1 = zmul(d2m, zconj(val[m2]))
                    t2 = zscale(zmul(der[m1], zconj(der[m2])), 2)
                    t3 = zmul(val[m1], zconj(d2n))
                    br = zadd(zadd(t1, t2), t3)
                    Cij = zmul(pre, br)
                    S = zadd(S, Cij)
                    rows["%d,%d" % (m1, m2)] = {"norm2": znorm(Cij)}
            qtot = Q2_second(k, r, rp)
            ok = bool(qtot["real_ok"] and S == (qtot["a"], qtot["b"], 0, -qtot["b"]))
            if not ok:
                dy2_bad.append((key, k))
            top = sorted(rows.items(), key=lambda t: -t[1]["norm2"])[:3]
            tot_n = sum(v["norm2"] for v in rows.values())
            cmats["%s_k%d" % (key, k)] = {
                "sum_ok": ok, "sum_quad": [S[0], S[1], S[2], S[3]],
                "top3": [{"pair": t[0], "norm2": t[1]["norm2"],
                          "share": t[1]["norm2"]/max(tot_n, 1)} for t in top],
            }
    log.append("D-Y2 contribution-sum bad=%d (12 matrices)" % len(dy2_bad))
    res = {"meta": {"script": "dpm2_remainder-v1.0-20260924.py",
                    "frozen": "2026-09-24T03:29:44"},
           "DY0": {"bad": dy0_bad}, "DY1": {"bad": dy1_bad, "logder_bad": dy1l_bad,
                                            "logder_err": Ltab, "endpoint": endpoint},
           "DY2": {"bad": dy2_bad, "mats": cmats}, "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

# ---------- part 2：D-Y3 延伸 k=19,21 + P-Y 记账 ----------
def run_part2():
    log = []
    out = {}
    for k in KS_EXT:
        row = {}
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            q = Q2_second(k, r, rp)
            g, rf = peak_full(k, r, rp)
            fo = orbit_fold(float(rf))
            row[key] = {"a": q.get("a"), "b": q.get("b"), "sign": q.get("sign"),
                        "raw_grid": g, "raw_refined": float(rf), "folded": fo}
            log.append("k=%d %s Q.a=%s sign=%s raw=%.12f fold=%s" %
                       (k, key, str(q.get("a"))[:24], q.get("sign"), float(rf), str(fo)))
        out[str(k)] = row
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    py = {}
    q17 = {key: r29["DW2"][key]["17"]["a"] for key in ("2|20", "8|14", "4|10")}
    q19 = {key: out["19"][key]["a"] for key in q17}
    q21 = {key: out["21"][key]["a"] for key in q17}
    py["P-Y1"] = {"s19": out["19"]["4|10"]["sign"], "s21": out["21"]["4|10"]["sign"],
                  "raw19": out["19"]["4|10"]["raw_refined"], "raw21": out["21"]["4|10"]["raw_refined"]}
    py["P-Y1_hit"] = bool(py["P-Y1"]["s19"] < 0 and py["P-Y1"]["s21"] < 0
                          and abs(py["P-Y1"]["raw19"] - float(3*pi/2)) < 1e-9
                          and abs(py["P-Y1"]["raw21"] - float(3*pi/2)) < 1e-9)
    py["P-Y2"] = {"s19_220": out["19"]["2|20"]["sign"], "s21_220": out["21"]["2|20"]["sign"],
                  "s19_814": out["19"]["8|14"]["sign"], "s21_814": out["21"]["8|14"]["sign"]}
    py["P-Y2_hit"] = all(v > 0 for v in py["P-Y2"].values())
    d17 = abs(q17["2|20"] - q17["8|14"]) / abs(q17["2|20"])
    d19 = abs(q19["2|20"] - q19["8|14"]) / abs(q19["2|20"])
    d21 = abs(q21["2|20"] - q21["8|14"]) / abs(q21["2|20"])
    t19a = out["19"]["2|20"]["folded"]; t19b = out["19"]["8|14"]["folded"]
    t21a = out["21"]["2|20"]["folded"]; t21b = out["21"]["8|14"]["folded"]
    dd19 = abs(t19a - t19b) if (t19a is not None and t19b is not None) else None
    dd21 = abs(t21a - t21b) if (t21a is not None and t21b is not None) else None
    py["P-Y3"] = {"rel17": d17, "rel19": d19, "rel21": d21, "t19_diff": dd19, "t21_diff": dd21}
    py["P-Y3_hit"] = bool(d19 < d17 and d21 < d19 and dd19 is not None and dd19 < 1e-6
                          and dd21 is not None and dd21 < 1e-6)
    lam4 = (3 + 2*msqrt(2))**2
    r_star = float(lam4 * 81)
    r17_19 = q19["2|20"] / q17["2|20"]; r19_21 = q21["2|20"] / q19["2|20"]
    py["P-Y4"] = {"r_star": r_star, "ratio_17_19": r17_19, "ratio_19_21": r19_21,
                  "dev_17_19": abs(r17_19/r_star - 1), "dev_19_21": abs(r19_21/r_star - 1)}
    py["P-Y4_hit"] = bool(py["P-Y4"]["dev_17_19"] < 0.03 and py["P-Y4"]["dev_19_21"] < 0.03
                          and py["P-Y4"]["dev_19_21"] < py["P-Y4"]["dev_17_19"])
    py["band_220"] = {"t19": t19a, "t21": t21a,
                      "in_band": bool(t19a is not None and 1.80 < t19a < 1.92
                                      and t21a is not None and 1.80 < t21a < 1.92)}
    res = {"meta": {"script": "dpm2_remainder-v1.0-20260924.py", "frozen": "2026-09-24T03:29:44"},
           "ext": out, "PY": py, "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("PY:", json.dumps(py, ensure_ascii=False, default=float)[:1200])
    return res

# ---------- part 3：D-Y4 maxdiff 比率 P-Y5 + 候选闭式判别 ----------
def run_part3():
    log = []
    md = {}
    KS = KS_REG + KS_EXT
    for k in KS:
        ts = np.linspace(0, 2*np.pi, 2**18, endpoint=False)
        x = np.exp(1j*ts)
        p = (k+1)//2; q = k//2
        w = np.conj(np.exp(2j*np.pi/8))
        Am = [1 + x*(w**m) + x*x*(w**(2*m)) for m in range(8)]
        M = (3**k - 3)//8
        Sc = {}
        for c in range(8):
            acc = np.zeros_like(x)
            for m in range(8):
                acc += np.exp(1j*np.pi/4*((m*c) % 8)) * (Am[m]**p) * (Am[(3*m) % 8]**q)
            Sc[c] = acc/8
        def dph(c, cp):
            Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
            return np.abs(Sc[c]/Nc - Sc[cp]/Ncp)
        dd = dph(0, 6) - dph(2, 4)
        md[str(k)] = float(np.max(np.abs(dd)))
        log.append("k=%d maxdiff=%.6e" % (k, md[str(k)]))
    ratios = {}
    ks = sorted((int(k) for k in md))
    for i in range(1, len(ks)):
        ratios["%d-%d" % (ks[i-1], ks[i])] = md[str(ks[i])] / md[str(ks[i-1])]
    r17_19 = ratios.get("17-19"); r19_21 = ratios.get("19-21")
    py5_hit = bool(r17_19 is not None and 0.094 <= r17_19 <= 0.128
                   and r19_21 is not None and 0.094 <= r19_21 <= 0.128)
    # 候选闭式判别：Q_{2|20} 全档（回归 R29 直读+延伸 part2 直读）
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    p2 = json.load(open(R30_P2, encoding="utf-8"))
    q220 = {k: r29["DW2"]["2|20"][str(k)]["a"] for k in KS_REG}
    for k in KS_EXT:
        q220[k] = p2["ext"][str(k)]["2|20"]["a"]
    qr = {}
    ks_all = sorted(q220)
    for i in range(1, len(ks_all)):
        qr["%d-%d" % (ks_all[i-1], ks_all[i])] = q220[ks_all[i]] / q220[ks_all[i-1]]
    lam4 = (3 + 2*msqrt(2))**2
    candA = float(lam4)          # λ^4 型（每两档 λ^4）
    candB = float(lam4 * 81)     # (3λ)^4 型
    fit = {}
    for name, cand in (("lambda4", candA), ("3lambda_4", candB)):
        devs = {rr: abs(v/cand - 1) for rr, v in list(qr.items())[-6:]}
        fit[name] = {"cand": cand, "devs": devs,
                     "max_dev_last6": max(devs.values())}
    winner = min(fit, key=lambda n: fit[n]["max_dev_last6"])
    log.append("winner=%s" % winner)
    res = {"meta": {"script": "dpm2_remainder-v1.0-20260924.py", "frozen": "2026-09-24T03:29:44"},
           "maxdiff": md, "ratios": ratios, "P-Y5_hit": py5_hit,
           "P-Y5": {"r17_19": r17_19, "r19_21": r19_21},
           "q220_ratios": qr, "cand_fit": fit, "winner": winner, "log": log}
    json.dump(res, open(OUT % "part3", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("ratios:", json.dumps(ratios, default=float))
    print("P-Y5 hit:", py5_hit, "winner:", winner)
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    {1: run_part1, 2: run_part2, 3: run_part3}[a.part]()

if __name__ == "__main__":
    main()
