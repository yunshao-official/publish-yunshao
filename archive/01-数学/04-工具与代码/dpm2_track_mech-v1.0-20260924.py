# -*- coding: utf-8 -*-
# d=±2 轨迹机理（R29 主格一·判据书 D-W 系实算）
# 判据书：代数册·d±2轨迹机理与μ奇偶定理化预注册判据书-v1.0-20260921.md
#         （冻结 NTFS 2026-09-24 02:35:38 在先；文件名日期后缀笔误照记：20260921 实为 20260924，
#          按三不动不回改，时钟链以 NTFS 为准）
# 口径：四对组 (10,22)基线/(2,20)/(8,14)/(4,10)；k 奇 {3,5,7,9,11,13} 回归 + {15,17} 延伸；
#       载体 dphi 同 R28 peak_family_general 口径；Q(ζ) 精确二阶符号通道（Z4 整数四元组·ζ^4=-1）
#       + mpmath 50 位双通道；三块平衡方程 Re[U'/U]=0。
import json, argparse
import numpy as np
from mpmath import mp, mpf, mpc, exp, pi, cos, sin

mp.dps = 50
PI = pi

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_REG = [3, 5, 7, 9, 11, 13]
KS_EXT = [15, 17]

# R28 在档锚（peak_family_general-v1.0-20260921.json §DG3 + R27 六点）
ANCHORS = {
    "2|20": {"raw3": 1.5707963267948966, "raw5": 1.5707963267948966,
             7: 1.8465958697882512, 9: 1.8931445787811616,
             11: 1.8792212447809713, 13: 1.858891948406971},
    "8|14": {"raw3": 4.71238898038469, "raw5": 4.71238898038469,
             7: 1.8416075067664675, 9: 1.8930087023844302,
             11: 1.879211356745318, 13: 1.8588914582322886},
    "4|10": {"raw3": 4.71238898038469, "raw5": 4.71238898038469},
    "10|22": {5: 2.038761, 7: 1.969607, 9: 1.921042, 11: 1.886854,
              13: 1.861055, 15: 1.840694},
}

def c_of(r): return (r - (r % 3)) // 3 % 8

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

# ---------- D-W1 ①：未归一化 beta_m 表机器核 ----------
def beta_check():
    out = {}
    bad = []
    for (r, rp) in PAIRS:
        c, cp = c_of(r), c_of(rp)
        d = (cp - c) % 8
        key = "%d|%d" % (r, rp)
        errs = {}
        for m in range(8):
            bm = exp(1j*pi/4*((m*c) % 8)) * (1 - exp(1j*pi/4*((m*d) % 8)))
            errs[m] = complex(bm)
        out[key] = {"c": c, "cp": cp, "d": d, "beta": {str(m): errs[m] for m in range(8)}}
        # 2|20 与 8|14 的恒等断言
        if key == "2|20": b20 = errs
        if key == "8|14": b814 = errs
    for m in (1, 3, 5, 7):
        e = abs(b20[m] - b814[m])
        if e > 1e-30: bad.append(("odd_m_identity", m, float(e)))
    for m in (2, 6):
        e = abs(b20[m] / b814[m] + 1)
        if e > 1e-30: bad.append(("even_m_ratio_neg1", m, float(e)))
    # 块系数闭式（1e-30）
    for m in range(8):
        for key, coef in (("2|20", b20), ("8|14", b814)):
            v = coef[m]
            if m in (0, 4): expect = 0.0
            elif m in (2, 6): expect = 2.0 if key == "2|20" else -2.0
            elif m in (1, 5): expect = 1 + 1j if key == "2|20" else 1 + 1j
            else: expect = 1 - 1j
            e = abs(v - expect)
            if e > 1e-30: bad.append(("closed_form", key, m, float(e)))
    return out, bad

# ---------- D-W1 ②：载体差恒等式（未归一化层，mpmath 50 位） ----------
def carrier_diff_identity():
    """T_{8|14} - T_{2|20} + 4(Pi2+Pi6) == 0（T:=S_c-S_c'，逐 t 逐 k）"""
    bad = []
    detail = {}
    for k in (3, 7):
        for tt in (0.9, 1.2, 1.85, 2.4, 3.0):
            t = mpf(tt)
            S0 = build_S(k, t)  # S_c 全表
            p = (k+1)//2; q = k//2
            x = exp(1j*t)
            w = exp(-1j*pi/4)
            Pi = {}
            for m in range(8):
                zm = w**(m % 8); z3m = w**((3*m) % 8)
                Pi[m] = (1 + zm*x + zm**2*x**2)**p * (1 + z3m*x + z3m**2*x**2)**q
            # T:=Σβ_mΠ_m（判据书 §二定义，未除 8）；build_S 输出已除 8 ⟹ 补 ×8（实现层修正披露）
            resid = (S0[2] - S0[4] - (S0[0]-S0[6]))*8 + 4*(Pi[2]+Pi[6])
            e = float(abs(resid))
            detail["k%d_t%.2f" % (k, tt)] = e
            if e > 1e-30: bad.append((k, tt, e))
    return detail, bad

# ---------- D-W1 ③：M1 模恒等判定 + 归一化层差闭式 ----------
def M1_verdict():
    out = {}
    for k in KS_REG:
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
        dd = dph(0, 6) - dph(2, 4)   # 2|20 与 8|14 的 |Δφ| 逐 t 差（δ 因子 |e^{iδt}|=1 已略）
        out[str(k)] = float(np.max(np.abs(dd)))
    return out

def norm_layer_closure():
    """归一化层差闭式 δ_m - δhat_m == -1（m 奇）/ 4M+3（m∈{2,6}）机器核（记录级补充）"""
    out = {}
    for k in (3, 7):
        M = (3**k - 3)//8
        row = {}
        okall = True
        for m in range(8):
            z = exp(1j*pi/4)
            delta_220 = 1 - 0  # δ_m = z^{0}·N6 - z^{6m}·N0 = M - (M+1) z^{6m}
            d220 = M - (M+1)*exp(1j*pi/4*((6*m) % 8))
            d814 = M*(exp(1j*pi/4*((2*m) % 8)) - exp(1j*pi/4*((4*m) % 8)))
            dd = d220 - d814
            expect = -(4*M+3) if m in (2, 6) else (-1 if m % 2 == 1 else 0)
            e = float(abs(dd - expect))
            if e > 1e-30: okall = False
            row[str(m)] = e
        out["k%d" % k] = {"all_ok": okall, "errs": row}
    return out

# ---------- 块率谱（D-W1 ④） ----------
def block_ratio(k, t_hat):
    p = (k+1)//2; q = k//2
    x = exp(1j*t_hat)
    w = exp(-1j*pi/4)
    Pi = {}
    for m in range(8):
        zm = w**(m % 8); z3m = w**((3*m) % 8)
        Pi[m] = (1 + zm*x + zm**2*x**2)**p * (1 + z3m*x + z3m**2*x**2)**q
    num = abs(Pi[2] + Pi[6])
    S0m = sum(Pi[m] for m in range(8))
    den = abs(S0m)  # T_{2|20}=S0-S6, 未归一化载体的量级用 |S0-S6|
    S6m = sum(exp(1j*pi/4*((m*6) % 8))*Pi[m] for m in range(8))
    return float(num/abs(S0m - S6m)), float(num/max(abs(Pi[3]), 1e-300))

# ---------- D-W2：二阶符号谱 Q(ζ) 精确通道 ----------
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

def sign_qsqrt2(A, B):
    """sign(a + b*sqrt(2)) 精确判别"""
    if B == 0: return 0 if A == 0 else (1 if A > 0 else -1)
    if A == 0: return 1 if B > 0 else -1
    if (A > 0) == (B > 0): return 1 if A > 0 else -1
    # 异号：|A| vs |B|√2 精确比较
    if A*A > 2*B*B: return 1 if A > 0 else -1
    if A*A < 2*B*B: return 1 if B > 0 else -1
    return 0

def Q2_second(k, r, rp):
    """Q(k) = d^2|dphi|^2/dt^2 at t=pi/2（|Δφ|²∝|P(e^{it})|²，P=Ncp·Sc块和−Nc·Scp块和）
    精确：g''(π/2) = -Σ_n n² c_n ζ^{2n}，c_n=Σ_i P_i conj(P_{i-n})"""
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M
    Ncp = M+1 if cp in (0,1) else M
    p = (k+1)//2; q = k//2
    # Π_m(x) 多项式（Z4 系数）
    polys = {}
    for m in range(8):
        zm = zpow(-m); z3m = zpow(-3*m)
        Am = [(1,0,0,0), zm, zmul(zm, zm)]
        A3 = [(1,0,0,0), z3m, zmul(z3m, z3m)]
        polys[m] = poly_mul(poly_pow(Am, p), poly_pow(A3, q))
    deg = max(len(v) for v in polys.values())
    # P(x) = Ncp·Σζ^{mc}Π_m − Nc·Σζ^{mc'}Π_m
    P = [(0,0,0,0)] * deg
    for m in range(8):
        zc = zpow(m*c); zcp = zpow(m*cp)
        for i, pm in enumerate(polys[m]):
            P[i] = zadd(P[i], zadd(zscale(zmul(zc, pm), Ncp), zscale(zmul(zcp, pm), -Nc)))
    # g''：c_n = Σ_i P_i conj(P_{i-n})
    L = len(P)
    res = (0,0,0,0)
    for i in range(L):
        if P[i] == (0,0,0,0): continue
        for j in range(L):
            if P[j] == (0,0,0,0): continue
            n = i - j
            if n == 0: continue
            term = zmul(P[i], zconj(P[j]))
            coef = n * n
            term = zscale(term, -coef)       # g'' = -Σ n² c_n ζ^{2n}：先 -n²
            tw = zmul(term, zpow(2*n))
            res = zadd(res, tw)
    # 实性自检：应 (A,B,0,-B)
    A, B, C, D = res
    real_ok = (C == 0 and D == -B)
    if not real_ok:
        return {"real_ok": False, "raw": [A, B, C, D]}
    sgn = sign_qsqrt2(A, B)
    return {"real_ok": True, "a": A, "b": B, "sign": sgn}

def Q2_numeric(k, r, rp, h=mpf('1e-6')):
    """同比例数值通道：|P(e^{it})|² 的二阶中心差分（P=Ncp·Sc−Nc·Scp·与精确通道同载体）"""
    t0 = pi/2
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3)//8
    Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
    def f(tt):
        Sc = build_S(k, tt)
        return abs(Ncp*Sc[c] - Nc*Sc[cp])**2
    fp = f(t0+h); fm = f(t0-h); f0 = f(t0)
    return (fp + fm - 2*f0) / (h*h)

# ---------- D-W3：三块平衡方程 ----------
def balance_roots(k, pair="2|20"):
    """U = b3*Pi3 + b1*Pi1 + b2*Pi2（2|20 未归一化系数）；Re[U'/U]=0 求根（记录级+P-W5）"""
    p = (k+1)//2; q = k//2
    w = exp(-1j*pi/4)
    if pair == "2|20":
        beta = {1: 1+1j, 3: 1-1j, 2: 2+0j}
    else:
        beta = {1: 1+1j, 3: 1-1j, 2: -2+0j}
    def UU(t):
        x = exp(1j*t)
        Pi = {}; dPi = {}
        for m in (1, 3, 2):
            zm = w**(m % 8); z3m = w**((3*m) % 8)
            Am = 1 + zm*x + zm**2*x**2
            A3 = 1 + z3m*x + z3m**2*x**2
            dAm = 1j*(zm*x + 2*zm**2*x**2)
            dA3 = 1j*(z3m*x + 2*z3m**2*x**2)
            Pi[m] = Am**p * A3**q
            dPi[m] = Pi[m] * (p*dAm/Am + q*dA3/A3)
        U = beta[1]*Pi[1] + beta[3]*Pi[3] + beta[2]*Pi[2]
        dU = beta[1]*dPi[1] + beta[3]*dPi[3] + beta[2]*dPi[2]
        return dU/U
    # 扫描找根
    roots = []
    a0 = mpf('1.60'); b0 = mpf('2.60'); ngrid = 400
    prev_t = a0; prev_f = None
    for i in range(ngrid+1):
        t = a0 + (b0-a0)*i/ngrid
        fv = float(mp.re(UU(t)))
        if prev_f is not None and prev_f == 0.0:
            roots.append(prev_t)
        if prev_f is not None and prev_f * fv < 0:
            lo, hi = prev_t, t
            flo = prev_f
            for _ in range(100):
                mid = (lo+hi)/2
                fm = float(mp.re(UU(mid)))
                if flo * fm <= 0: hi = mid
                else: lo = mid; flo = fm
            roots.append((lo+hi)/2)
        prev_t, prev_f = t, fv
    return roots

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    args = ap.parse_args()
    res = {"meta": {"script": "dpm2_track_mech-v1.0-20260924.py",
                    "frozen": "2026-09-24T02:35:38"}, "notes": {}}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    if args.part == 1:
        L("== D-W0 轨迹回归（t̂ 折算口径对照） ==")
        dw0 = {}; bad = []
        for (r, rp) in [(2, 20), (8, 14), (4, 10)]:
            key = "%d|%d" % (r, rp)
            g3 = grid_peak(3, r, rp); g5 = grid_peak(5, r, rp)
            anch = ANCHORS[key]
            e3 = abs(g3 - anch["raw3"]); e5 = abs(g5 - anch["raw5"])
            if e3 > 1e-6: bad.append((key, 3, e3))
            if e5 > 1e-6: bad.append((key, 5, e5))
            ent = {"g3": g3, "g5": g5, "e3": e3, "e5": e5}
            for k in (7, 9, 11, 13):
                if k in anch:
                    g = grid_peak(k, r, rp)
                    # 半周期反演（R23 Q-B 在档）⟹ argmax 有等值对径点：折算到 (π/2,π) 后对照锚
                    gf = orbit_fold(g)
                    rf = float(refine(k, r, rp, gf))
                    e = abs(rf - anch[k])
                    ent["t%d" % k] = rf; ent["e%d" % k] = e
                    if e > 1e-6: bad.append((key, k, e))
            dw0[key] = ent
            L("%s done e_all=%s" % (key, [ent.get("e%d" % k) for k in (7, 9, 11, 13) if "e%d" % k in ent]))
        # 基线六点（折算口径）
        gk = {}
        for k in (5, 7, 9, 11, 13, 15):
            g = grid_peak(k, 10, 22)
            gf = orbit_fold(g)
            rf = float(refine(k, 10, 22, gf))
            gk[k] = rf
            e = abs(rf - ANCHORS["10|22"][k])
            if e > 1e-6: bad.append(("10|22", k, e))
        dw0["10|22"] = {str(k): v for k, v in gk.items()}
        res["DW0"] = dw0; res["DW0_bad"] = [str(x) for x in bad]
        L("D-W0 bad=%s" % bad)

        L("== D-W1 系数恒等+载体差闭式 ==")
        bt, bbad = beta_check()
        ci, cbad = carrier_diff_identity()
        m1 = M1_verdict()
        nlc = norm_layer_closure()
        m1_fail = {k: v for k, v in m1.items() if v > 1e-12}
        res["DW1"] = {"beta_errs": bbad, "carrier_identity_max": max(ci.values()),
                      "carrier_bad": cbad, "M1_maxdiff": m1,
                      "M1_verdict": "REJECTED" if m1_fail else "IDENTITY",
                      "norm_closure": nlc}
        L("beta_bad=%s carrier_bad=%s M1=%s" % (bbad, cbad, res["DW1"]["M1_verdict"]))
        L("M1_maxdiff=%s" % json.dumps(m1))
        # 块率谱
        brs = {}
        for k in (3, 5, 7, 9, 11, 13):
            g = grid_peak(k, 2, 20)
            th = refine(k, 2, 20, g)
            br1, br2 = block_ratio(k, th)
            brs[str(k)] = {"ratio_vs_carrier": br1, "ratio_vs_Pi3": br2}
        res["DW1"]["block_ratio"] = brs
        L("block_ratio=%s" % json.dumps(brs))

    if args.part == 2:
        L("== D-W2 二阶符号谱 ==")
        dw2 = {}
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            ent = {}
            for k in KS_REG + KS_EXT:
                qex = Q2_second(k, r, rp)
                qn = Q2_numeric(k, r, rp)
                ent[str(k)] = qex
                if qex.get("real_ok"):
                    av = float(qex["a"]) + float(qex["b"])*2**0.5
                    ent[str(k)]["numeric"] = float(qn)
                    ent[str(k)]["absdiff"] = float(abs(mpf(av) - qn))
            dw2[key] = ent
            L("%s signs=%s" % (key, {k: ent[k].get("sign") for k in ent if isinstance(ent[k], dict)}))
        res["DW2"] = dw2

        L("== D-W4 k=15,17 延伸峰位 ==")
        dw4 = {}
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            ent = {}
            for k in KS_EXT:
                g = grid_peak(k, r, rp)
                rf = float(refine(k, r, rp, g))
                of = orbit_fold(rf)
                ent[str(k)] = {"raw": rf, "folded": of}
            dw4[key] = ent
            L("%s k15/17=%s" % (key, json.dumps(ent)))
        res["DW4"] = dw4
        # P-W 预测记账（4|10 停驻=σρ 轨道端点 {π/2,3π/2} 等值类·R28「π/2 端点像」口径）
        pw = {}
        def endpoint_dist(raw):
            x = raw % (2*float(pi))
            return min(abs(x - 3*float(pi)/2), abs(x - float(pi)/2))
        e410_15 = endpoint_dist(dw4["4|10"]["15"]["raw"])
        e410_17 = endpoint_dist(dw4["4|10"]["17"]["raw"])
        pw["PW1_stop_410"] = {"e15": e410_15, "e17": e410_17,
                              "hit": bool(e410_15 <= 1e-9 and e410_17 <= 1e-9)}
        s15 = dw2["2|20"]["15"].get("sign"); s17 = dw2["2|20"]["17"].get("sign")
        s13 = dw2["2|20"]["13"].get("sign")
        pw["PW2_220_wander"] = {"s13": s13, "s15": s15, "s17": s17,
                                "hit": bool(s13 == 1 and s15 == 1 and s17 == 1)}
        t15a = dw4["2|20"]["15"]["folded"]; t15b = dw4["8|14"]["15"]["folded"]
        t17a = dw4["2|20"]["17"]["folded"]; t17b = dw4["8|14"]["17"]["folded"]
        d15 = abs(t15a - t15b) if (t15a and t15b) else None
        d17 = abs(t17a - t17b) if (t17a and t17b) else None
        pw["PW3_asym_coincide"] = {"d15": d15, "d17": d17,
                                   "hit": bool(d15 is not None and d15 < 1e-5 and d17 is not None and d17 < 1e-6)}
        w15 = t15a is not None and 1.80 < t15a < 1.92
        w17 = t17a is not None and 1.80 < t17a < 1.92
        pw["PW4_wander_band"] = {"t15": t15a, "t17": t17a, "hit": bool(w15 and w17)}
        res["PW"] = pw
        L("PW=%s" % json.dumps(pw))

    if args.part == 3:
        L("== D-W3 三块平衡方程 ==")
        dw3 = {}
        for pair, rp, r in (("2|20", 2, 20), ("8|14", 8, 14)):
            ent = {}
            for k in (7, 9, 11, 13):
                g = grid_peak(k, r, rp)
                gf = orbit_fold(g)
                th = float(refine(k, r, rp, gf))   # t̂ 折算口径（对径点等值·R23 Q-B）
                roots = balance_roots(k, pair)
                near = min(roots, key=lambda z: abs(z - th)) if roots else None
                ent[str(k)] = {"t_hat": th, "roots": [float(z) for z in roots],
                               "nearest": float(near) if near is not None else None,
                               "absdiff": float(abs(near - th)) if near is not None else None}
            dw3[pair] = ent
            L("%s diffs=%s" % (pair, {k: ent[k]["absdiff"] for k in ent}))
        res["DW3"] = dw3
        hits = 0
        for k in ("9", "11", "13"):
            v = dw3["2|20"][k]["absdiff"]
            if v is not None and v < 1e-4: hits += 1
        res["PW5"] = {"k9_11_13_hits": hits, "need": 2, "hit": bool(hits >= 2)}
        L("P-W5 hits=%d/3 hit=%s" % (hits, res["PW5"]["hit"]))

    outp = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-%s-v1.0-20260924.json" % (
        {1: "reg", 2: "q2", 3: "balance"}[args.part])
    res["log"] = log
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
