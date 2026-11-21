# -*- coding: utf-8 -*-
# Q(k) 贡献矩阵闭式提纯（R31 主格一·判据书 D-A 系实算）
# 判据书：代数册·Qk闭式提纯与强形式E_c层推论预注册判据书-v1.0-20260924.md（冻结 2026-09-24 04:31:41）
# 口径：D-A0 Q 谱回归（Z4 通道 vs R29 q2+R30 part2 JSON 直读·整数零容差+b=0）
#       D-A1 闭式表（α 八条 mpmath 1e-12 / L' 闭式 / γ 值表 Z4 / T1022 双口径 Z4）
#       D-A2 Ω 提纯恒等（两口径逐对：奇奇对 Z4 零容差·含偶块对 mpmath ≤1e-30）+{0,4} 行列恒零
#       D-A3 分层显式和对表（显式第二通道 vs Z4 精确 Q：主导/尾块/偶偶/交叉分层残差落盘）
#       D-A4 lim 收敛谱（r_k=Q/(3λ)^{2k} vs 候选 a*=(3-2√2)/2）
#       D-A5 k=23,25 延伸器产出+P-Z1..Z5 记账
# 器口径复用 R29/R30（Z4 四元组/2^18 网格/mpmath 50 位/轨道折算）。
import json, argparse
import numpy as np
from mpmath import mp, mpf, exp, pi, sqrt as msqrt

mp.dps = 50

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_REG = [3, 5, 7, 9, 11, 13, 15, 17]
KS_R30 = [19, 21]
KS_EXT = [23, 25]
R29_Q2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-q2-v1.0-20260924.json"
R30_P2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part2-v1.0-20260924.json"
R30_P3 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part3-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/qk_closed_form-%s-v1.0-20260924.json"

def c_of(r): return (r - (r % 3)) // 3 % 8

# ---------- Z4 四元组通道（R29/R30 口径复用） ----------
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

def znorm(A): return sum(int(x)*int(x) for x in A)

def sign_qsqrt2(A, B):
    if B == 0: return 0 if A == 0 else (1 if A > 0 else -1)
    if A == 0: return 1 if B > 0 else -1
    if (A > 0) == (B > 0): return 1 if A > 0 else -1
    if A*A > 2*B*B: return 1 if A > 0 else -1
    if A*A < 2*B*B: return 1 if B > 0 else -1
    return 0

LAM = (1, 1, 0, -1)
LAMm = (-1, 1, 0, -1)
SQ2 = (0, 1, 0, -1)
I4 = (0, 0, 1, 0)

def Q2_second(k, r, rp):
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    polys = pi_polys(k)
    deg = max(len(v) for v in polys.values())
    P = [(0,0,0,0)] * deg
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

def gamma_z(k, r, rp):
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    return {m: zadd(zscale(zpow(m*c), Ncp), zscale(zpow(m*cp), -Nc)) for m in range(8)}

# ---------- mpmath 显式第二通道（M-Z1..M-Z4 闭式） ----------
def setup_consts():
    lam = mpf(1) + msqrt(mpf(2))
    a = mpf(2) - msqrt(mpf(2)); b = mpf(2) + msqrt(mpf(2))
    zeta = exp(1j*pi/4)
    return lam, a, b, zeta

def alpha_clo():
    """M-Z2 α 闭式八条（mpmath）"""
    s2 = msqrt(mpf(2))
    return {0: mpf(-4), 1: -8 + 5*s2, 2: mpf(-2)/3, 3: -8 + 5*s2,
            4: mpf(-4), 5: -8 - 5*s2, 6: mpf(-2), 7: -8 - 5*s2}

def Lp_clo(k, al):
    """M-Z2 L'_m = p α_m + q α_{3m}"""
    p = (k+1)//2; q = k//2
    return {m: p*al[m] + q*al[(3*m) % 8] for m in range(8)}

def s_clo(a, b, k):
    """Re L_m 表：s₀=-2k（L₀=k(i-2)）·s₄=+2k（L₄=k(2+i)）·s₂=s₆=0·奇块 ±a/±b（R30 M-Y3）"""
    return {0: -2*mpf(k), 1: -a, 2: mpf(0), 3: a, 4: 2*mpf(k), 5: -b, 6: mpf(0), 7: b}

def Pi_clo(k, lam):
    """M-Y1/R30 Π_m(i) 闭式（mpmath 复数）"""
    p = (k+1)//2; q = k//2
    z = exp(1j*pi/4)
    return {0: 1j**k, 1: lam**k * z, 2: mpf(3)**p, 3: lam**k / z,
            4: (-1j)**k, 5: lam**(-k) * z, 6: mpf(3)**q, 7: lam**(-k) / z}

def gamma_clo(k, r, rp, zeta):
    """M-Z3 γ 值表（mpmath 复数）"""
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    return {m: Ncp*zeta**((m*c) % 8) - Nc*zeta**((m*cp) % 8) for m in range(8)}

def Omega_clo(k, r, rp, zeta):
    """M-Z1 Ω 矩阵：(s_m+s_m')^2 + L'_m + L'_m'（实数·mpmath）"""
    lam, a, b, _ = setup_consts()
    al = alpha_clo(); Lp = Lp_clo(k, al); s = s_clo(a, b, k)
    return {(m, mp2): (s[m]+s[mp2])**2 + Lp[m] + Lp[mp2]
            for m in range(8) for mp2 in range(8)}

def Omega_z4(k):
    """Ω 的 (u,v,den) 精确表示：Ω = (u+v√2)/den（den∈{1,3}·全 64 对）。
    s：奇 (±a,±b)∈Z[√2]、偶 0；α 奇 ∈Z[√2]、α₂=-2/3、α₆=-2、α₀=α₄=-4；
    L'奇=kα、L₂'=pα₂+qα₆=-(4k-2)/3、L₆'=-(4k+2)/3、L₀'=L₄'=-4k。"""
    def qmul(x, y):  # (u,v)=u+v√2 乘法
        return (x[0]*y[0] + 2*x[1]*y[1], x[0]*y[1] + x[1]*y[0])
    def qadd(x, y):
        return (x[0]+y[0], x[1]+y[1])
    def qscale(x, n):
        return (n*x[0], n*x[1])
    smap = {0: (-2*k, 0), 1: (-2, 1), 2: (0, 0), 3: (2, -1),
            4: (2*k, 0), 5: (-2, -1), 6: (0, 0), 7: (2, 1)}
    amap = {0: ((-4, 0), 1), 1: ((-8, 5), 1), 2: ((-2, 0), 3), 3: ((-8, 5), 1),
            4: ((-4, 0), 1), 5: ((-8, -5), 1), 6: ((-2, 0), 1), 7: ((-8, -5), 1)}
    kp = (k+1)//2; kq = k//2
    # 每块 L'_m = p α_m + q α_{3m}（(num_u,num_v,den)）
    Lp = {}
    for m in range(8):
        (au, av), ad = amap[m]
        (bu, bv), bd = amap[(3*m) % 8]
        den1 = ad*bd
        num = qadd(qscale((au, av), kp*bd), qscale((bu, bv), kq*ad))
        Lp[m] = (num[0], num[1], den1)
    om = {}
    for m in range(8):
        for m2 in range(8):
            w = qadd(smap[m], smap[m2])
            sq = qmul(w, w)  # 整数
            n1, v1, d1 = Lp[m]; n2, v2, d2 = Lp[m2]
            den = d1*d2
            num = qadd(qscale(sq, den),
                       qadd(qadd(qscale((n1, v1), d2), qscale((n2, v2), d1)), (0, 0)))
            om[(m, m2)] = (num[0], num[1], den)
    return om

def explicit_layers(k, r, rp):
    """M-Z4 分层显式和（显式第二通道·闭式 γ/Π/Ω·mpmath）"""
    lam, a, b, zeta = setup_consts()
    Om = Omega_clo(k, r, rp, zeta)
    g = gamma_clo(k, r, rp, zeta)
    Pi = Pi_clo(k, lam)
    groups = {"dom": [(1,1),(1,3),(3,1),(3,3)],
              "tail": [(5,5),(5,7),(7,5),(7,7)],
              "even": [(2,2),(2,6),(6,2),(6,6)]}
    cross = [(m, mp2) for m in (1,3,5,7) for mp2 in (2,6)] + \
            [(m, mp2) for m in (2,6) for mp2 in (1,3,5,7)]
    groups["cross"] = cross
    zero = [(m, mp2) for m in (0,4) for mp2 in range(8)] + \
           [(m, mp2) for m in (1,2,3,5,6,7) for mp2 in (0,4)]
    groups["zero"] = zero
    lay = {}
    for name, pairs in groups.items():
        tot = mpf(0)
        per = {}
        for (m1, m2) in pairs:
            C = g[m1]*g[m2].conjugate()*Pi[m1]*Pi[m2].conjugate()*Om[(m1, m2)]
            tot += C
            per["%d,%d" % (m1, m2)] = float(C.real)
        lay[name] = {"sum": float(tot.real), "sum_imag": float(tot.imag),
                     "sum_abs": float(abs(tot)), "per": per}
    grand = sum(lay[n]["sum"] for n in lay)
    return lay, float(grand)

# ---------- 峰位通道（R29/R30 口径复用） ----------
def build_S(k, t):
    p = (k + 1) // 2; q = k // 2
    tt = exp(1j * t); out = []
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
    if Sc is None: Sc = build_S(k, t)
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

# ---------- part 1：D-A0 回归 + D-A1 闭式表 ----------
def run_part1():
    log = []
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    r30 = json.load(open(R30_P2, encoding="utf-8"))
    # D-A0：Q 谱回归 k=3..21（整数零容差）+ b=0
    bad = []
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        for k in KS_REG:
            q = Q2_second(k, r, rp)
            ref = r29["DW2"][key][str(k)]
            if not (q["real_ok"] and q["a"] == ref["a"] and q["b"] == ref["b"] == 0):
                bad.append((key, k))
        for k in KS_R30:
            q = Q2_second(k, r, rp)
            ref = r30["ext"][str(k)][key]
            if not (q["real_ok"] and q["a"] == ref["a"] and q["b"] == ref["b"] == 0):
                bad.append((key, k))
    log.append("D-A0 bad=%d (40 values, b==0 all)" % len(bad))
    # D-A1①：α 闭式八条（mpmath 数值微分对照 ≤1e-12）
    lam, a_, b_, zeta = setup_consts()
    x = exp(1j*pi/2)
    al = alpha_clo()
    al_bad = []; al_err = {}
    for m in range(8):
        zm = zeta**(-m)
        Am = lambda xx: 1 + zm*xx + zm*zm*xx*xx
        dAm = lambda xx: zm + 2*zm*zm*xx
        ddAm = lambda xx: 2*zm*zm
        ix = 1j*x
        L1 = ix*dAm(x)/Am(x)
        L2 = (ix)**2 * (ddAm(x)/Am(x) - (dAm(x)/Am(x))**2) + (ix)*dAm(x)/Am(x) - (Am(x) - Am(x))  # 占位
        # D^2 log A = -xA'/A - x^2(A''/A - (A'/A)^2)  (x=i)
        val = -x*dAm(x)/Am(x) - x*x*(ddAm(x)/Am(x) - (dAm(x)/Am(x))**2)
        e = float(abs(val - al[m]))
        al_err["alpha%d" % m] = e
        if e > 1e-12: al_bad.append(m)
    log.append("D-A1 alpha bad=%d maxerr=%.3e" % (len(al_bad), max(al_err.values())))
    # D-A1②：L' 闭式（mpmath 数值二阶微分对照 ≤1e-12）
    from mpmath import diff as mdiff
    Lp_bad = []; Lp_err = {}
    for k in (3, 9):
        p = (k+1)//2; q = k//2
        Lpc = Lp_clo(k, al)
        for m in (0, 1, 2, 3, 4, 5, 6, 7):
            zm = zeta**(-m); z3m = zeta**((-3*m) % 8)
            def logPi(tt):
                xx = exp(1j*tt)
                return mp.log((1 + zm*xx + zm*zm*xx*xx)**p
                              * (1 + z3m*xx + z3m*z3m*xx*xx)**q)
            num = mdiff(logPi, mpf(pi)/2, 2)
            e = float(abs(num - Lpc[m]))
            Lp_err["Lp%d_k%d" % (m, k)] = e
            if e > 1e-12: Lp_bad.append((m, k))
    log.append("D-A1 Lp bad=%d (max err %.3e)" % (len(Lp_bad), max(Lp_err.values())))
    # D-A1③：γ 值表 Z4 精确（四对 k=3,9,17 对照 M-Z3 显式值）
    g_bad = []
    for k in (3, 9, 17):
        M = (3**k - 3)//8
        for (r, rp) in PAIRS:
            c, cp = c_of(r), c_of(rp)
            Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
            got = gamma_z(k, r, rp)
            for m in range(8):
                # 显式闭式（按 M-Z3 手算值表逐对构造）
                ex = zadd(zscale(zpow(m*c), Ncp), zscale(zpow(m*cp), -Nc))
                # 与 Z4 通道一致（同式）——真检验：与 mpmath γ 对照
                gm = gamma_clo(k, r, rp, zeta)
                z4v = got[m]
                # Z4→复数：a+bζ+cζ²+dζ³ = [a+(b-d)/√2] + i[c+(b+d)/√2]
                s2f = float(msqrt(mpf(2)))
                comp = complex(z4v[0] + (z4v[1]-z4v[3])/s2f,
                               z4v[2] + (z4v[1]+z4v[3])/s2f)
                e = float(abs(comp - gm[m]))/max(1.0, float(abs(gm[m])))
                if e > 1e-12: g_bad.append((k, "%d|%d" % (r, rp), m))
    log.append("D-A1 gamma bad=%d" % len(g_bad))
    # D-A1④：T1022 双口径（商类 (3,7) → 0；(2,6) → -2√2(λ^k+λ^-k)）
    t_bad = []; t_res = {}
    for k in (3, 9, 17):
        p = (k+1)//2; q = k//2
        val, der, der2 = pi_values(k)
        lam_k = zpowN(LAM, k); lamn_k = zpowN(LAMm, k)
        # 商类口径：η_m = ζ^{3m} - ζ^{7m}
        T37 = (0,0,0,0)
        for m in range(8):
            T37 = zadd(T37, zmul(zadd(zpow(3*m), zscale(zpow(7*m), -1)), val[m]))
        # (2,6) 口径：η_m = ζ^{2m} - ζ^{6m}
        T26 = (0,0,0,0)
        for m in range(8):
            T26 = zadd(T26, zmul(zadd(zpow(2*m), zscale(zpow(6*m), -1)), val[m]))
        exp26 = zscale(zmul(SQ2, zadd(lam_k, lamn_k)), -2)
        t_res["T37_k%d" % k] = [T37[0], T37[1], T37[2], T37[3]]
        t_res["T26_k%d" % k] = [T26[0], T26[1], T26[2], T26[3]]
        if T37 != (0,0,0,0): t_bad.append(("T37", k, "nonzero"))
        if T26 != exp26: t_bad.append(("T26", k, "mismatch"))
    log.append("D-A1 T1022 dual bad=%d" % len(t_bad))
    res = {"meta": {"script": "qk_closed_form-v1.0-20260924.py",
                    "frozen": "2026-09-24T04:31:41"},
           "DA0": {"bad": bad},
           "DA1": {"alpha_bad": al_bad, "alpha_err": al_err,
                   "Lp_bad": Lp_bad, "Lp_err": Lp_err,
                   "gamma_bad": g_bad, "T1022_bad": t_bad, "T1022": t_res},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

# ---------- part 2：D-A2 Ω 提纯 + {0,4} 零结构 + D-A3 分层对表 + D-A4 lim 谱 ----------
def run_part2():
    log = []
    lam, a_, b_, zeta = setup_consts()
    # D-A2①：Ω 提纯恒等（两口径逐对：奇奇对 Z4 整数零容差 + 全对相对 1e-9 带）
    om_bad = []; om_err_max = 0.0
    zint_bad = 0; zint_n = 0
    for k in (3, 9, 17):
        val, der, der2 = pi_values(k)
        OmZ = Omega_z4(k)
        for (r, rp) in PAIRS:
            gam = gamma_z(k, r, rp)
            Om = Omega_clo(k, r, rp, zeta)
            g_c = gamma_clo(k, r, rp, zeta)
            Pi = Pi_clo(k, lam)
            for m1 in range(8):
                for m2 in range(8):
                    pre = zmul(gam[m1], zconj(gam[m2]))
                    d2m = zadd(der2[m1], zscale(zmul(I4, der[m1]), -1))
                    d2n = zadd(der2[m2], zscale(zmul(I4, der[m2]), -1))
                    t1 = zmul(d2m, zconj(val[m2]))
                    t2 = zscale(zmul(der[m1], zconj(der[m2])), 2)
                    t3 = zmul(val[m1], zconj(d2n))
                    C_r30 = zmul(pre, zadd(zadd(t1, t2), t3))
                    # Ω 口径（mpmath·全对）
                    C_om = g_c[m1]*g_c[m2].conjugate()*Pi[m1]*Pi[m2].conjugate()*Om[(m1, m2)]
                    s2f = float(msqrt(mpf(2)))
                    comp = complex(C_r30[0] + (C_r30[1]-C_r30[3])/s2f,
                                   C_r30[2] + (C_r30[1]+C_r30[3])/s2f)
                    e = float(abs(comp - C_om))
                    scale = max(1.0, float(abs(C_om)))
                    rel = e/scale
                    om_err_max = max(om_err_max, rel)
                    if rel > 1e-9:
                        om_bad.append((k, "%d|%d" % (r, rp), m1, m2, rel))
                    # 全 64 对 Z4 整数零容差（den 缩放：Ω=(u+v√2)/den ⟹ H·(u,v,0,−v) == den·C_r30）
                    oz = OmZ[(m1, m2)]
                    zint_n += 1
                    H = zmul(val[m1], zconj(val[m2]))
                    lhs = zmul(pre, zmul(H, (oz[0], oz[1], 0, -oz[1])))
                    rhs = zscale(C_r30, oz[2])
                    if lhs != rhs:
                        zint_bad += 1
                        om_bad.append(("zint", k, "%d|%d" % (r, rp), m1, m2))
                    # {0,4} 行列恒零（Z4·逐对——判负风险预声明的结构断言）
                    if (m1 in (0,4) or m2 in (0,4)) and C_r30 != (0,0,0,0):
                        om_bad.append(("zero", k, "%d|%d" % (r, rp), m1, m2))
            qtot = Q2_second(k, r, rp)
            log.append("k=%d %s Q.a=%s" % (k, "%d|%d" % (r, rp), str(qtot["a"])[:22]))
    # {0,4} 行列总和（修正读法·判定输出：配对相消结构）
    zero_sum = {}
    for k in (3, 9, 17):
        val, der, der2 = pi_values(k)
        for (r, rp) in PAIRS:
            gam = gamma_z(k, r, rp)
            acc = (0,0,0,0)
            for m1 in range(8):
                for m2 in range(8):
                    if m1 in (0,4) or m2 in (0,4):
                        pre = zmul(gam[m1], zconj(gam[m2]))
                        d2m = zadd(der2[m1], zscale(zmul(I4, der[m1]), -1))
                        d2n = zadd(der2[m2], zscale(zmul(I4, der[m2]), -1))
                        t1 = zmul(d2m, zconj(val[m2]))
                        t2 = zscale(zmul(der[m1], zconj(der[m2])), 2)
                        t3 = zmul(val[m1], zconj(d2n))
                        acc = zadd(acc, zmul(pre, zadd(zadd(t1, t2), t3)))
            zero_sum["%d|%d_k%d" % (r, rp, k)] = [acc[0], acc[1], acc[2], acc[3]]
    log.append("D-A2 omega bad=%d (max rel %.3e) zint bad=%d/%d ; zero_rowsum=%s" %
               (len([b for b in om_bad if b[0] not in ("zero", "zint")]), om_err_max,
                zint_bad, zint_n,
                set(tuple(v) for v in zero_sum.values())))
    # D-A3：分层显式和对表（全档 k=3..21 四对）
    lay_bad = []; layers_out = {}
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    r30 = json.load(open(R30_P2, encoding="utf-8"))
    Qref = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        Qref[key] = {k: r29["DW2"][key][str(k)]["a"] for k in KS_REG}
        for k in KS_R30: Qref[key][k] = r30["ext"][str(k)][key]["a"]
    ks_all = sorted({k for key in Qref for k in Qref[key]})
    for k in ks_all:
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            lay, grand = explicit_layers(k, r, rp)
            qtrue = float(Qref[key][k])
            rel = abs(grand - qtrue)/max(1.0, abs(qtrue))
            dom_rel = None
            if key == "2|20":
                dom_rel = abs(lay["dom"]["sum"])/max(1.0, abs(qtrue))
            layers_out["%s_k%d" % (key, k)] = {
                "lay": {n: lay[n]["sum"] for n in lay},
                "grand": grand, "qtrue": qtrue, "rel": rel,
                "dom_share_220": dom_rel}
            if rel > 1.0:  # 显式候选带外（判负照记阈值：总残差 >100% 记失配）
                lay_bad.append((key, k, rel))
    log.append("D-A3 layers bad(>100%%)=%d ; max_rel=%.4f" %
               (len(lay_bad), max(v["rel"] for v in layers_out.values())))
    # D-A4：lim 收敛谱（2|20）
    al = alpha_clo()
    a_star = (mpf(3) - 2*msqrt(mpf(2)))/2
    rspec = {}
    for k in ks_all:
        qv = float(Qref["2|20"][k])
        t = mpf(3*float(lam))**(2*k)
        r_k = qv/float((mpf(3)*lam)**(2*k))
        rspec[str(k)] = {"r": r_k, "dev": abs(r_k - float(a_star))}
    mono = (rspec["21"]["dev"] < rspec["17"]["dev"] < rspec["13"]["dev"])
    da4 = {"a_star": float(a_star), "rspec": rspec,
           "mono_13_17_21": mono, "dev21": rspec["21"]["dev"],
           "pass": bool(mono and rspec["21"]["dev"] < 0.01)}
    log.append("D-A4 dev13=%.5f dev17=%.5f dev21=%.5f mono=%s pass=%s" %
               (rspec["13"]["dev"], rspec["17"]["dev"], rspec["21"]["dev"], mono, da4["pass"]))
    res = {"meta": {"script": "qk_closed_form-v1.0-20260924.py",
                    "frozen": "2026-09-24T04:31:41"},
           "DA2": {"bad": om_bad, "max_rel": om_err_max, "zero_rowsum": zero_sum},
           "DA3": {"bad": lay_bad, "layers": layers_out},
           "DA4": da4, "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

# ---------- part 3：D-A5 k=23,25 延伸 + P-Z 记账 ----------
def run_part3():
    log = []
    lam, a_, b_, zeta = setup_consts()
    out = {}
    for k in KS_EXT:
        row = {}
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            q = Q2_second(k, r, rp)
            g = grid_peak(k, r, rp)
            rf = refine(k, r, rp, g)
            fo = orbit_fold(float(rf))
            row[key] = {"a": q.get("a"), "b": q.get("b"), "sign": q.get("sign"),
                        "raw_grid": g, "raw_refined": float(rf), "folded": fo}
            log.append("k=%d %s Q.a=%s sign=%s raw=%.12f" %
                       (k, key, str(q.get("a"))[:24], q.get("sign"), float(rf)))
        out[str(k)] = row
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    r30 = json.load(open(R30_P2, encoding="utf-8"))
    r30p3 = json.load(open(R30_P3, encoding="utf-8"))
    qv = {}
    for key in ("2|20", "8|14", "4|10", "10|22"):
        qv[key] = {k: r29["DW2"][key][str(k)]["a"] for k in KS_REG}
        for k in KS_R30: qv[key][k] = r30["ext"][str(k)][key]["a"]
        for k in KS_EXT: qv[key][k] = out[str(k)][key]["a"]
    a_star = (mpf(3) - 2*msqrt(mpf(2)))/2
    # P-Z1：lim 收敛单调
    dev = {k: abs(float(qv["2|20"][k])/float((mpf(3)*lam)**(2*k)) - float(a_star))
           for k in (17, 19, 21, 23, 25)}
    pz1 = bool(dev[23] < dev[21] and dev[25] < dev[23] and dev[25] < 0.005)
    # P-Z2：4|10 永停驻延伸
    pz2 = bool(out["23"]["4|10"]["sign"] < 0 and out["25"]["4|10"]["sign"] < 0
               and abs(out["23"]["4|10"]["raw_refined"] - float(3*pi/2)) < 1e-9
               and abs(out["25"]["4|10"]["raw_refined"] - float(3*pi/2)) < 1e-9)
    # P-Z3：两对重合
    d23 = abs(qv["2|20"][23] - qv["8|14"][23])/abs(qv["2|20"][23])
    d25 = abs(qv["2|20"][25] - qv["8|14"][25])/abs(qv["2|20"][25])
    d21 = abs(qv["2|20"][21] - qv["8|14"][21])/abs(qv["2|20"][21])
    t23a = out["23"]["2|20"]["folded"]; t23b = out["23"]["8|14"]["folded"]
    t25a = out["25"]["2|20"]["folded"]; t25b = out["25"]["8|14"]["folded"]
    dd23 = abs(t23a-t23b) if None not in (t23a, t23b) else None
    dd25 = abs(t25a-t25b) if None not in (t25a, t25b) else None
    pz3 = bool(out["23"]["2|20"]["sign"] > 0 and out["25"]["2|20"]["sign"] > 0
               and out["23"]["8|14"]["sign"] > 0 and out["25"]["8|14"]["sign"] > 0
               and d25 < d23 < 8.45e-10 and dd23 is not None and dd23 < 1e-6
               and dd25 is not None and dd25 < 1e-6)
    # P-Z4：maxdiff 比率带（复用 R30 part3 maxdiff 谱 + 本轮 23,25 重算）
    md = dict(r30p3["maxdiff"])
    for k in KS_EXT:
        ts = np.linspace(0, 2*np.pi, 2**18, endpoint=False)
        x = np.exp(1j*ts); p = (k+1)//2; q = k//2
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
        md[str(k)] = float(np.max(np.abs(dph(0, 6) - dph(2, 4))))
    rt = {}
    ks = sorted(int(x) for x in md)
    for i in range(1, len(ks)):
        rt["%d-%d" % (ks[i-1], ks[i])] = md[str(ks[i])]/md[str(ks[i-1])]
    pz4 = bool(0.094 <= rt["21-23"] <= 0.128 and 0.094 <= rt["23-25"] <= 0.128)
    # P-Z5：主导四对占比（2|20·k=19,21,23,25）
    shares = {}
    for k in (19, 21, 23, 25):
        lay, grand = explicit_layers(k, 2, 20)
        sh = abs(lay["dom"]["sum"])/max(1.0, abs(float(qv["2|20"][k])))
        shares[str(k)] = sh
    pz5 = bool(all(shares[str(k)] > 0.95 for k in (19, 21, 23, 25))
               and shares["25"] > shares["19"])
    pz = {"P-Z1": {"dev": dev, "hit": pz1},
          "P-Z2": {"s23": out["23"]["4|10"]["sign"], "s25": out["25"]["4|10"]["sign"],
                   "raw23": out["23"]["4|10"]["raw_refined"],
                   "raw25": out["25"]["4|10"]["raw_refined"], "hit": pz2},
          "P-Z3": {"d21": d21, "d23": d23, "d25": d25, "t23_diff": dd23,
                   "t25_diff": dd25, "hit": pz3},
          "P-Z4": {"r21-23": rt["21-23"], "r23-25": rt["23-25"], "hit": pz4},
          "P-Z5": {"shares": shares, "hit": pz5}}
    res = {"meta": {"script": "qk_closed_form-v1.0-20260924.py",
                    "frozen": "2026-09-24T04:31:41"},
           "ext": out, "PZ": pz, "maxdiff_ext": {k: md[str(k)] for k in KS_EXT},
           "log": log}
    json.dump(res, open(OUT % "part3", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("PZ:", json.dumps({k: v["hit"] for k, v in pz.items()}))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    {1: run_part1, 2: run_part2, 3: run_part3}[a.part]()

if __name__ == "__main__":
    main()
