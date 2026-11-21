# -*- coding: utf-8 -*-
# 四型端点值判据×停驻/游移二分（R32 主格一·判据书 D-C 系实算）
# 判据书：代数册·四型端点值判据与Q全档精确闭式预注册判据书-v1.0-20260925.md（冻结 2026-09-25 01:49:27）
# part1: D-C0 回归锚（Q 谱 k=3..25 直读 vs Z4 重算+端点值四型闭式 Z4+峰位锚）
#        D-C1 M-Q1 定理化（恒等式 Q=2(|P'|²+Re(P̄P'')) mp 核+10|22 P(i)=0/P'≠0/Q=2|P'|² Z4 全档）
#        D-C2 符号不变性（8|14/2|20 符号谱逐 k 全同+相对差谱）
#        D-C3 承载层判据映射全档对表（M-Q3 表·零反例判定）
#        D-C5 层竞争比率 ρ_k 谱（2|20 偶偶/主导 Z4 模）
# part2: D-C4 偶 k 域器产+试探（M-N1 回归+偶 k Q 谱+四型重组+P-Ω2/P-Ω3）
# 器口径复用 R29-R31（Z4 四元组/mpmath 50 位）。
import json, argparse
import numpy as np
from mpmath import mp, mpf, exp, pi, sqrt as msqrt

mp.dps = 50

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_ALL = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
KS_EVEN = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
R29_Q2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-q2-v1.0-20260924.json"
R30_P2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part2-v1.0-20260924.json"
R31_P3 = "H:/理论存档/01-数学/02-实验与数据/results/qk_closed_form-part3-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/fourtype_criterion-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T01:49:27"

def c_of(r): return (r - (r % 3)) // 3 % 8

# ---------- Z4 四元组通道（R29-R31 口径复用） ----------
def zmul(A, B):
    a, b, c, d = A; e, f, g, h = B
    return (a*e - (b*h + c*g + d*f),
            a*f + b*e - (c*h + d*g),
            a*g + b*f + c*e - d*h,
            a*h + b*g + c*f + d*e)

def zconj(A):
    a, b, c, d = A
    return (a, -d, -c, -b)

def zscale(A, n): return (A[0]*n, A[1]*n, A[2]*n, A[3]*n)
def zadd(A, B): return (A[0]+B[0], A[1]+B[1], A[2]+B[2], A[3]+B[3])

Z = {0: (1,0,0,0), 1: (0,1,0,0), 2: (0,0,1,0), 3: (0,0,0,1),
     4: (-1,0,0,0), 5: (0,-1,0,0), 6: (0,0,-1,0), 7: (0,0,0,-1)}
def zpow(n): return Z[n % 8]

def poly_mul(A, B):
    out = [(0,0,0,0)] * (len(A) + len(B) - 1)
    for i, a in enumerate(A):
        if a == (0,0,0,0): continue
        for j, b in enumerate(B):
            if b == (0,0,0,0): continue
            out[i+j] = zadd(out[i+j], zmul(a, b))
    return out

def poly_pow(A, n):
    R = [(1,0,0,0)]; B = list(A)
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

def sign_qsqrt2(A, B):
    if B == 0: return 0 if A == 0 else (1 if A > 0 else -1)
    if A == 0: return 1 if B > 0 else -1
    if (A > 0) == (B > 0): return 1 if A > 0 else -1
    if A*A > 2*B*B: return 1 if A > 0 else -1
    if A*A < 2*B*B: return 1 if B > 0 else -1
    return 0

LAM = (1, 1, 0, -1)
LAMm = (-1, 1, 0, -1)
I4 = (0, 0, 1, 0)

_NC_CACHE = {}

def nc_pq(k, p, q):
    """N_c 计数：奇 k 用在档公式 (3^k-3)/8+[c∈{0,1}]；偶 k 用 M-N1 Fourier 公式"""
    if k % 2 == 1:
        M = (3**k - 3)//8
        return lambda c: M + (1 if c in (0, 1) else 0)
    if k in _NC_CACHE:
        return _NC_CACHE[k]
    polys = pi_polys_pq(k, p, q)
    z4v = {}
    for c in range(8):
        acc = (0,0,0,0)
        for m in range(8):
            acc = zadd(acc, zmul(zpow(-m*c), polys[m][0]))  # Π_m(1)=系数和
        z4v[c] = acc
    assert all(v[1] == 0 and v[2] == 0 and v[3] == 0 and v[0] % 8 == 0 for v in z4v.values()), "M-N1 non-integer"
    tab = {c: z4v[c][0]//8 for c in range(8)}
    _NC_CACHE[k] = (lambda c: tab[c])
    return _NC_CACHE[k]

def pi_polys_pq(k, p, q):
    polys = {}
    for m in range(8):
        zm = zpow(-m); z3m = zpow(-3*m)
        Am = [(1,0,0,0), zm, zmul(zm, zm)]
        A3 = [(1,0,0,0), z3m, zmul(z3m, z3m)]
        polys[m] = poly_mul(poly_pow(Am, p), poly_pow(A3, q))
    return polys

def pi_polys(k):
    return pi_polys_pq(k, (k+1)//2, k//2)

def pi_values_pq(polys):
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

def pi_values(k):
    return pi_values_pq(pi_polys(k))

def gamma_z(k, r, rp, nc_fn=None):
    c, cp = c_of(r), c_of(rp)
    if nc_fn is None:
        M = (3**k - 3)//8
        nc_fn = lambda cc: M + (1 if cc in (0, 1) else 0)
    return {m: zadd(zscale(zpow(m*c), nc_fn(cp)), zscale(zpow(m*cp), -nc_fn(c))) for m in range(8)}

def Q2_second(k, r, rp):
    p = (k+1)//2; q = k//2
    nc = nc_pq(k, p, q)
    c, cp = c_of(r), c_of(rp)
    polys = pi_polys_pq(k, p, q)
    deg = max(len(v) for v in polys.values())
    P = [(0,0,0,0)] * deg
    Nc, Ncp = nc(c), nc(cp)
    for m in range(8):
        zc = zpow(m*c); zcp = zpow(m*cp)
        for i, pm in enumerate(polys[m]):
            P[i] = zadd(P[i], zadd(zscale(zmul(zc, pm), Ncp), zscale(zmul(zcp, pm), -Nc)))
    L = len(P); res = (0,0,0,0)
    for i in range(L):
        if P[i] == (0,0,0,0): continue
        for j in range(L):
            if P[j] == (0,0,0,0): continue
            n = i - j
            if n == 0: continue
            term = zmul(P[i], zconj(P[j]))
            res = zadd(res, zmul(zscale(term, -(n*n)), zpow(2*n)))
    A, B, C, D = res
    if not (C == 0 and D == -B):
        return {"real_ok": False, "raw": [A, B, C, D]}
    return {"real_ok": True, "a": A, "b": B, "sign": sign_qsqrt2(A, B)}

def pairs_contrib_Z4(k, r, rp):
    """64 对逐对 Z4 贡献（R30 D-Y2 口径）+ 五层分组"""
    val, der, der2 = pi_values(k)
    gam = gamma_z(k, r, rp)
    C = {}
    for m1 in range(8):
        for m2 in range(8):
            pre = zmul(gam[m1], zconj(gam[m2]))
            d2m = zadd(der2[m1], zscale(zmul(I4, der[m1]), -1))
            d2n = zadd(der2[m2], zscale(zmul(I4, der[m2]), -1))
            t1 = zmul(d2m, zconj(val[m2]))
            t2 = zscale(zmul(der[m1], zconj(der[m2])), 2)
            t3 = zmul(val[m1], zconj(d2n))
            C[(m1, m2)] = zmul(pre, zadd(zadd(t1, t2), t3))
    layers = {
        "dom": [(1,1),(1,3),(3,1),(3,3)],
        "tail": [(5,5),(5,7),(7,5),(7,7)],
        "even": [(2,2),(2,6),(6,2),(6,6)],
    }
    layers["cross"] = [(m, m2) for m in (1,3,5,7) for m2 in (2,6)] + \
                      [(m, m2) for m in (2,6) for m2 in (1,3,5,7)]
    layers["zero"] = [(m, m2) for m in (0,4) for m2 in range(8)] + \
                     [(m, m2) for m in (1,2,3,5,6,7) for m2 in (0,4)]
    lay = {}
    for name, pls in layers.items():
        acc = (0,0,0,0)
        for pl in pls: acc = zadd(acc, C[pl])
        lay[name] = acc
    return C, lay

# ---------- mpmath 显式通道（M-Q1 恒等式核） ----------
def z4_to_mp(z4):
    """Z4 四元组的实部（mpf·精确算术非 double）"""
    s2 = msqrt(mpf(2))
    return mpf(z4[0]) + (mpf(z4[1]) - mpf(z4[3]))/s2

def setup_consts():
    lam = mpf(1) + msqrt(mpf(2))
    return lam

def z4_to_complex(z4):
    s2f = float(msqrt(mpf(2)))
    return complex(z4[0] + (z4[1]-z4[3])/s2f, z4[2] + (z4[1]+z4[3])/s2f)

def load_qref():
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    r30 = json.load(open(R30_P2, encoding="utf-8"))
    r31 = json.load(open(R31_P3, encoding="utf-8"))
    qref = {}; peaks = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        qref[key] = {}
        for k in (3, 5, 7, 9, 11, 13, 15, 17):
            e = r29["DW2"][key][str(k)]
            qref[key][k] = (e["a"], e["b"], e["sign"])
        for k in (19, 21):
            e = r30["ext"][str(k)][key]
            qref[key][k] = (e["a"], e["b"], e["sign"])
        for k in (23, 25):
            e = r31["ext"][str(k)][key]
            qref[key][k] = (e["a"], e["b"], e["sign"])
            peaks[(key, k)] = e.get("raw_refined")
    return qref, peaks

# ---------- part1 ----------
def run_part1():
    log = []
    qref, peaks = load_qref()
    # D-C0① Q 谱回归（k=3..25 全档零容差）
    bad = []
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        for k in KS_ALL:
            q = Q2_second(k, r, rp)
            ra, rb, rsg = qref[key][k]
            if not (q["real_ok"] and q["a"] == ra and q["b"] == rb == 0 and q["sign"] == rsg):
                bad.append((key, k))
    log.append("D-C0 Q-spectrum bad=%d (48 values)" % len(bad))
    # D-C0② 端点值四型闭式 Z4 核（奇 k·η 口径 T=Ση_mΠ_m）
    et_bad = []; et_res = {}
    for k in (3, 9, 17, 25):
        val, der, der2 = pi_values(k)
        lam_k = zpowN(LAM, k); lamn_k = zpowN(LAMm, k)
        p = (k+1)//2; q = k//2
        Tp3 = zadd(zscale((3**p, 0, 0, 0), 2), zscale((3**q, 0, 0, 0), 2))
        for (r, rp), expect in [((2, 20), Tp3), ((8, 14), zscale(Tp3, -1)),
                                ((4, 10), None), ((10, 22), (0,0,0,0))]:
            c, cp = c_of(r), c_of(rp)
            T = (0,0,0,0)
            for m in range(8):
                eta = zadd(zpow(m*c), zscale(zpow(m*cp), -1))
                T = zadd(T, zmul(eta, val[m]))
            if (r, rp) == (4, 10):
                # 2i[λ^k+3^p−3^q−λ^{−k}]
                inner = zadd(zadd(lam_k, (3**p, 0, 0, 0)), zadd(zscale((3**q, 0, 0, 0), -1), zscale(lamn_k, -1)))
                expect = zmul(I4, zscale(inner, 2))
            if T != expect: et_bad.append((k, "%d|%d" % (r, rp)))
            et_res["T_%d|%d_k%d" % (r, rp, k)] = [T[0], T[1], T[2], T[3]]
    log.append("D-C0 endpoint-4type bad=%d" % len(et_bad))
    # D-C0③ 峰位锚（4|10 raw=3π/2·k=23,25 直读）
    pk_bad = []
    for k in (23, 25):
        v = peaks.get(("4|10", k))
        if v is None or abs(v - float(3*mp.pi/2)) > 1e-9: pk_bad.append(k)
    log.append("D-C0 peak-anchor bad=%d" % len(pk_bad))
    # D-C1① 恒等式 Q=2(|P'|²+Re(P̄P'')) mp 核（四对 k=3,9,17）
    id_bad = []; id_err = {}
    lam = setup_consts()
    for k in (3, 9, 17):
        val, der, der2 = pi_values(k)
        for (r, rp) in PAIRS:
            gam = gamma_z(k, r, rp)
            v = (0,0,0,0); d1 = (0,0,0,0); d2 = (0,0,0,0)
            for m in range(8):
                gm = gam[m]
                v = zadd(v, zmul(gm, val[m]))
                d1 = zadd(d1, zmul(gm, der[m]))
                d2 = zadd(d2, zmul(gm, der2[m]))
            Qz = Q2_second(k, r, rp)
            lhs = mpf(Qz["a"]) + mpf(Qz["b"])*msqrt(mpf(2))
            n2 = zmul(d1, zconj(d1))
            d2t = zadd(d2, zscale(zmul(I4, d1), -1))  # t-口径：P_t″=P_x″−iP_x′（R30 D-Y2 链式）
            xbar = zmul(zconj(v), d2t)
            re2 = zadd(xbar, zconj(xbar))
            rhs = 2*mpf(n2[0]) + z4_to_mp(re2)
            e = float(abs(lhs - rhs))
            id_err["Q_%d|%d_k%d" % (r, rp, k)] = e
            if e > 1e-9: id_bad.append((k, "%d|%d" % (r, rp)))
    log.append("D-C1 identity bad=%d (max %.3e)" % (len(id_bad), max(id_err.values())))
    # D-C1② 10|22：P(i)=0/P'≠0/Q=2|P'|² Z4 全档
    t22_bad = {}; t22_rec = {}
    for k in KS_ALL:
        val, der, der2 = pi_values(k)
        gam = gamma_z(k, 10, 22)
        v = (0,0,0,0); d1 = (0,0,0,0)
        for m in range(8):
            v = zadd(v, zmul(gam[m], val[m]))
            d1 = zadd(d1, zmul(gam[m], der[m]))
        n2 = zscale(zmul(d1, zconj(d1)), 2)
        qz = Q2_second(k, 10, 22)
        ok0 = (v == (0,0,0,0)); okn = (d1 != (0,0,0,0))
        okq = (n2[0] == qz["a"] and n2[1] == qz["b"] and n2[2] == 0 and n2[3] == -n2[1])
        if not (ok0 and okn and okq): t22_bad[k] = [ok0, okn, okq]
        t22_rec[str(k)] = {"P_i_zero": ok0, "Pp_nonzero": okn, "Q_eq_2Pp2": okq}
    log.append("D-C1 10|22 bad-k=%d" % len(t22_bad))
    # D-C2 符号不变性（8|14 vs 2|20 逐 k 全同+相对差谱）
    s_bad = []; diff_spec = {}
    for k in KS_ALL:
        s2 = qref["2|20"][k][2]; s8 = qref["8|14"][k][2]
        if s2 != s8: s_bad.append(k)
        d = abs(qref["2|20"][k][0] - qref["8|14"][k][0])/abs(qref["2|20"][k][0])
        diff_spec[str(k)] = d
    log.append("D-C2 sign-mismatch-k=%d" % len(s_bad))
    # D-C3 判据映射全档对表（M-Q3 表）
    map_bad = []
    for k in KS_ALL:
        rows = [("2|20", qref["2|20"][k][2], "flip"), ("8|14", qref["8|14"][k][2], "flip"),
                ("4|10", qref["4|10"][k][2], "neg"), ("10|22", qref["10|22"][k][2], "pos")]
        for key, sg, typ in rows:
            if typ == "neg" and sg >= 0: map_bad.append((key, k, "neg"))
            if typ == "pos" and sg <= 0: map_bad.append((key, k, "pos"))
    # 翻转谱结构：k∈{3,5} 负 / k≥7 正
    for k in KS_ALL:
        want = -1 if k in (3, 5) else 1
        if qref["2|20"][k][2] != want: map_bad.append(("2|20", k, "flip"))
        if qref["8|14"][k][2] != want: map_bad.append(("8|14", k, "flip"))
    log.append("D-C3 mapping bad=%d -> %s" % (len(map_bad), "CRITERION HOLDS (odd-k)" if not map_bad else "NEGATED"))
    # D-C5 ρ_k 谱（2|20 Z4 模偶偶/主导）
    rho = {}
    for k in KS_ALL:
        C, lay = pairs_contrib_Z4(k, 2, 20)
        dom = zmul(lay["dom"], zconj(lay["dom"]))
        ev = zmul(lay["even"], zconj(lay["even"]))
        rho[str(k)] = float(msqrt(mpf(ev[0])) / msqrt(mpf(dom[0])))
    rho_keys = sorted(int(x) for x in rho)
    mono = all(rho[str(rho_keys[i+1])] < rho[str(rho_keys[i])] for i in range(len(rho_keys)-1))
    dc5 = {"rho": rho, "strict_mono": mono, "rho3": rho["3"], "rho7": rho["7"],
           "cross_band": bool(rho["3"] > 1 and rho["7"] < 1)}
    log.append("D-C5 rho3=%.4f rho5=%.4f rho7=%.4f mono=%s band=%s" %
               (rho["3"], rho["5"], rho["7"], mono, dc5["cross_band"]))
    # P-Ω1
    p1 = bool(rho["3"] > 1 and rho["7"] < 1 and mono and all(rho[str(KS_ALL[i+1])] < rho[str(KS_ALL[i])] for i in range(len(KS_ALL)-1)))
    res = {"meta": {"script": "fourtype_criterion-v1.0-20260925.py", "frozen": FROZEN},
           "DC0": {"bad": bad, "endpoint_bad": et_bad, "peak_bad": pk_bad, "T": et_res},
           "DC1": {"identity_bad": id_bad, "identity_err": id_err, "t22_bad": t22_bad, "t22": t22_rec},
           "DC2": {"sign_bad": s_bad, "rel_diff": diff_spec},
           "DC3": {"map_bad": map_bad, "verdict": "HOLDS" if not map_bad else "NEGATED"},
           "DC5": dc5, "P-Omega1": p1, "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("P-Omega1:", p1)
    return res

# ---------- part2：偶 k 域（D-C4） ----------
def run_part2():
    log = []
    # ① M-N1 回归（两方向 ζ^{±mc} 核查·奇 k 锚）
    n_bad = []; n_res = {}
    for k in (3, 9, 17, 25):
        polys = pi_polys(k)
        for sgn in (1, -1):
            for c in range(8):
                acc = (0,0,0,0)
                for m in range(8):
                    acc = zadd(acc, zmul(zpow(sgn*m*c), polys[m][0]))
                M = (3**k - 3)//8
                want = M + (1 if c in (0, 1) else 0)
                ok = (acc == (want*8, 0, 0, 0))
                if not ok: n_bad.append((k, "sgn%+d" % sgn, c, acc, want))
                n_res["N_sgn%+d_c%d_k%d" % (sgn, c, k)] = [acc[0], acc[1], acc[2], acc[3]]
    log.append("D-C4 M-N1 regression bad=%d (both directions NEGATED -> 挂账：N_c 组合计数推导)" % len(n_bad))
    # ② 偶 k 域 Q 谱（M-N1 值做 N_c——被错值污染·如实标记 invalid_Nc）
    qeven = {}; bad_ro = []
    for k in KS_EVEN:
        row = {}
        for (r, rp) in PAIRS:
            q = Q2_second(k, r, rp)
            row["%d|%d" % (r, rp)] = {"a": q.get("a"), "b": q.get("b"), "sign": q.get("sign"),
                                      "real_ok": q.get("real_ok")}
            if not q.get("real_ok"): bad_ro.append((k, "%d|%d" % (r, rp)))
        qeven[str(k)] = row
    log.append("D-C4 even-k real_ok bad=%d ; Q-spectrum INVALID (N_c=M-N1 wrong values, contaminated)" % len(bad_ro))
    # ③ 偶 k 端点值四型重组 Z4 核（η 口径·零 N_c 依赖·k=4,12,24·P-Ω2）
    rec_bad = []; rec = {}
    for k in (4, 12, 24):
        val, der, der2 = pi_values(k)
        for (r, rp) in PAIRS:
            c, cp = c_of(r), c_of(rp)
            eta1 = zadd(zpow(c), zscale(zpow(cp), -1))
            eta3 = zadd(zpow(3*c), zscale(zpow(3*cp), -1))
            dom = zadd(zmul(eta1, val[1]), zmul(eta3, val[3]))
            rec["dom_%d|%d_k%d" % (r, rp, k)] = [dom[0], dom[1], dom[2], dom[3]]
            if (r, rp) == (4, 10):
                if dom != (0,0,0,0): rec_bad.append(("dom-410-nonzero", k))  # 预测：主导抵消=0
            else:
                if dom == (0,0,0,0): rec_bad.append(("dom-zero", "%d|%d" % (r, rp), k))  # 预测：不抵消
    log.append("D-C4 even-k 4type reorg bad=%d (M-Q3' hit=%s)" % (len(rec_bad), not rec_bad))
    # ④ P-Ω3：偶 k Q 谱降级（N_c 污染）→ 判负照记（无法执行）
    p3 = False
    cls = {"note": "invalid (N_c contaminated); demoted per frozen exit"}
    log.append("P-Omega3 NEGATED-by-execution (even-k Q demoted; N_c 组合计数=新挂账)")
    res = {"meta": {"script": "fourtype_criterion-v1.0-20260925.py", "frozen": FROZEN},
           "DC4": {"mn1_bad": n_bad, "mn1": n_res, "realok_bad": bad_ro,
                   "reorg_bad": rec_bad, "reorg": rec, "qeven": qeven,
                   "qeven_valid": False, "cls": cls},
           "P-Omega2": bool(not rec_bad), "P-Omega3": p3, "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("P-Omega2:", res["P-Omega2"], "P-Omega3:", p3)
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    {1: run_part1, 2: run_part2}[a.part]()

if __name__ == "__main__":
    main()
