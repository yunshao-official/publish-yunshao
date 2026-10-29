# -*- coding: utf-8 -*-
# Nc 组合计数定理 + {0,4} 块层清单角色（R33 主格一+主格二·判据书 D-F 系/D-G 系实算）
# 判据书：代数册·Nc组合计数定理与{0,4}块层清单角色预注册判据书-v1.0-20260925.md（冻结 2026-09-25 02:46）
# part1: D-F0 三通道互证（枚举/DP/Fourier x=1 口径）/ D-F1 F 谱闭式全档 / D-F3 偶 k F 谱
#        D-F2 γ 分化判定（F 口径 Q vs 在档真值·失配组型·8|14 纯差·M-Q2 破坏判定）
# part2: D-F4 偶 k Q 谱恢复（γ-A/γ-B 双候选·real_ok+主导显式偶版+ρ 连续带·P-Π3/P-Π4）
#        D-G0 行列 28 对闭式组装 Z4 通道 / D-G1 行列总和序列+变号点 / D-G2 修正层角色
#        D-G3 域外词前哨（|D|<=200 态数谱）
import json
import numpy as np
from fractions import Fraction

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_ALL = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
KS_EVEN = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
OUT = "H:/理论存档/01-数学/02-实验与数据/results/nc_combinatorics-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T02:46"

def c_of(r): return (r - (r % 3)) // 3 % 8

# ---------- Z4 算术（ζ^4=-1 约化·在档口径复用） ----------
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

LAM = (1, 1, 0, -1)      # 1+sqrt2
LAMm = (-1, 1, 0, -1)    # sqrt2-1 = lambda^{-1}
I4 = (0, 0, 1, 0)

def M_of(k): return (3**k - 3)//8   # k 奇
def v_of(k): return (3**k - 1)//8   # k 偶

# ---------- N 口径族（参数化） ----------
def N_gamma(k, c):
    """在档 γ 构造系数（k 奇锚）：M+1 if c in {0,1} else M"""
    M = M_of(k)
    return M+1 if c in (0, 1) else M

def F_closed(k):
    """F 谱闭式（M-N2）：k 奇 3+5 型 / k 偶 1+7 型"""
    if k % 2 == 1:
        M = M_of(k)
        return [M+1]*3 + [M]*5
    v = v_of(k)
    return [v+1] + [v]*7

def N_F(k, c):
    """F 谱（Phi 商类词计数）"""
    return F_closed(k)[c]

def N_gammaA(k, c):
    """γ-A 一式延拓：N^gamma = F - [c=2]（一切 k）"""
    return N_F(k, c) - (1 if c == 2 else 0)

def N_gammaB(k, c):
    """γ-B 朴素延拓：v + [c=0]（k 偶）"""
    return v_of(k) + (1 if c == 0 else 0)

NSPEC = {"gamma": N_gamma, "F": N_F, "gammaA": N_gammaA, "gammaB": N_gammaB}

# ---------- Π 多项式与链式贡献（在档口径复用） ----------
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

def gamma_z_N(k, r, rp, Nfun):
    c, cp = c_of(r), c_of(rp)
    return {m: zadd(zscale(zpow(m*c), Nfun(k, cp)), zscale(zpow(m*cp), -Nfun(k, c)))
            for m in range(8)}

def Q2_second_N(k, r, rp, Nfun):
    c, cp = c_of(r), c_of(rp)
    polys = pi_polys(k)
    deg = max(len(v) for v in polys.values())
    P = [(0,0,0,0)] * deg
    for m in range(8):
        zc = zpow(m*c); zcp = zpow(m*cp)
        for i, pm in enumerate(polys[m]):
            P[i] = zadd(P[i], zadd(zscale(zmul(zc, pm), Nfun(k, cp)), zscale(zmul(zcp, pm), -Nfun(k, c))))
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

def sign_qsqrt2(A, B):
    """Q(√2) 实数 a+b√2 的符号（整型精确）"""
    if A == 0 and B == 0: return 0
    if A > 0 and B > 0: return 1
    if A < 0 and B < 0: return -1
    if A*A > 2*B*B: return 1 if A > 0 else -1
    if A*A < 2*B*B: return 1 if B > 0 else -1
    return 0

def pairs_contrib_Z4_N(k, r, rp, Nfun):
    val, der, der2 = pi_values(k)
    gam = gamma_z_N(k, r, rp, Nfun)
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
    return C

LAYERS = {
    "dom": [(1,1),(1,3),(3,1),(3,3)],
    "tail": [(5,5),(5,7),(7,5),(7,7)],
    "even": [(2,2),(2,6),(6,2),(6,6)],
    "cross": ([(m, m2) for m in (1,3,5,7) for m2 in (2,6)] +
              [(m, m2) for m in (2,6) for m2 in (1,3,5,7)]),
    "oddodd": [(m, m2) for m in (1,3) for m2 in (5,7)] + [(m, m2) for m in (5,7) for m2 in (1,3)],
    "zero": ([(m, m2) for m in (0,4) for m2 in range(8)] +
             [(m, m2) for m in (1,2,3,5,6,7) for m2 in (0,4)]),
}

def layer_sums(C):
    lay = {}
    for name, pls in LAYERS.items():
        acc = (0,0,0,0)
        for pl in pls: acc = zadd(acc, C[pl])
        lay[name] = acc
    return lay

def load_qref():
    R29 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-q2-v1.0-20260924.json"
    R30 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part2-v1.0-20260924.json"
    R31 = "H:/理论存档/01-数学/02-实验与数据/results/qk_closed_form-part3-v1.0-20260924.json"
    r29 = json.load(open(R29, encoding="utf-8"))
    r30 = json.load(open(R30, encoding="utf-8"))
    r31 = json.load(open(R31, encoding="utf-8"))
    qref = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        qref[key] = {}
        for k in (3, 5, 7, 9, 11, 13, 15, 17):
            qref[key][k] = r29["DW2"][key][str(k)]["a"]
        for k in (19, 21):
            qref[key][k] = r30["ext"][str(k)][key]["a"]
        for k in (23, 25):
            qref[key][k] = r31["ext"][str(k)][key]["a"]
    return qref

# ---------- D-F0/F1/F3：三通道 F 谱 + 闭式 ----------
def f_enum(kmax=12):
    """枚举通道（k<=kmax）"""
    import itertools
    out = {}
    for k in range(1, kmax+1):
        cnt = [0]*8
        for w in itertools.product(range(3), repeat=k):
            p = (k+1)//2
            phi = sum(w[:p]) + 3*sum(w[p:])
            cnt[phi % 8] += 1
        out[k] = cnt
    return out

def f_dp(ks):
    """DP 通道：state=(phi mod 8, s1)"""
    out = {}
    for k in ks:
        p = (k+1)//2; q = k//2
        weights = [1]*p + [3]*q
        # state[c][s] 计数
        cur = [[0]*(2*k+1) for _ in range(8)]
        cur[0][0] = 1
        for t in range(k):
            nxt = [[0]*(2*k+1) for _ in range(8)]
            w = weights[t]
            for c in range(8):
                for s in range(2*k+1):
                    v0 = cur[c][s]
                    if v0 == 0: continue
                    for d in range(3):
                        nxt[(c + w*d) % 8][s+d] += v0
            cur = nxt
        out[k] = [sum(cur[c]) for c in range(8)]
    return out

def f_fourier(ks):
    """Fourier 通道：F_c=(1/8)Σζ^{mc}Π_m(1)·Π_m(1)=系数和（x=1 口径 Z4 精确）"""
    out = {}; bad = []
    for k in ks:
        polys = pi_polys(k)
        P1 = {}
        for m in range(8):
            acc = (0,0,0,0)
            for ci in polys[m]: acc = zadd(acc, ci)
            P1[m] = acc
        Fc = []
        for c in range(8):
            acc = (0,0,0,0)
            for m in range(8):
                acc = zadd(acc, zmul(zpow(m*c), P1[m]))
            if acc[1] != 0 or acc[2] != 0 or acc[3] != 0 or acc[0] % 8 != 0:
                bad.append((k, c, list(acc)))
                Fc.append(None)
            else:
                Fc.append(acc[0]//8)
        out[k] = Fc
    return out, bad

def run_part1():
    log = []
    ks_all = KS_ALL + KS_EVEN
    # D-F0：三通道互证
    en = f_enum(12)
    dp = f_dp(ks_all)
    fo, fo_bad = f_fourier(ks_all)
    tri_bad = []
    for k in ks_all:
        ref = dp[k]
        if k in en and en[k] != ref: tri_bad.append(("enum", k))
        if fo[k] != ref: tri_bad.append(("fourier", k))
    log.append("D-F0 three-channel bad=%d (fourier-extract bad=%d)" % (len(tri_bad), len(fo_bad)))
    # D-F1/F3：F 谱闭式全档
    clo_bad = []
    for k in ks_all:
        if F_closed(k) != dp[k]: clo_bad.append(k)
    log.append("D-F1/F3 closed-form bad=%d /23" % len(clo_bad))
    # M-N1 平反机器面：Fourier 式=枚举（在 fo 无 bad 且 tri_bad 无 fourier 项时成立）
    mn1_rehab = bool(not fo_bad) and not any(t[0] == "fourier" for t in tri_bad)
    # D-F2：γ 分化判定（F 口径 Q vs 在档真值）
    qref = load_qref()
    div = {}; div_bad_pairs = {}
    for k in KS_ALL:
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            qF = Q2_second_N(k, r, rp, N_F)
            refk = qref[key][k]
            same = (qF.get("real_ok") and qF["a"] == refk)
            div["%s_k%d" % (key, k)] = {"aF": qF.get("a"), "ref": refk, "same": bool(same)}
            div_bad_pairs.setdefault(key, []).append(k) if not same else None
    # 失配组型
    fail_groups = sorted(div_bad_pairs.keys())
    # 8|14 纯差核：在档口径 γ₀/γ₄ vs F 口径
    g0 = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        gam_g = gamma_z_N(9, r, rp, N_gamma)
        gam_F = gamma_z_N(9, r, rp, N_F)
        g0[key] = {"gamma0_ingest": list(gam_g[0]), "gamma0_F": list(gam_F[0]),
                   "gamma4_ingest": list(gam_g[4]), "gamma4_F": list(gam_F[4])}
    # M-Q2 破坏判定：8|14 F 口径 vs 2|20 在档口径逐 k 全同性
    mq2_break = []
    for k in KS_ALL:
        q814F = Q2_second_N(k, 8, 14, N_F)
        ref220 = qref["2|20"][k]
        if not (q814F.get("real_ok") and q814F["a"] == ref220):
            mq2_break.append(k)
    log.append("D-F2 fail-groups=%s (expect ['8|14']) ; M-Q2-break-at-k=%s" %
               (str(fail_groups), str(mq2_break[:6]) + ("..." if len(mq2_break) > 6 else "")))
    res = {"meta": {"script": "nc_combinatorics-v1.0-20260925.py", "frozen": FROZEN},
           "DF0": {"bad": tri_bad, "fourier_extract_bad": fo_bad, "mn1_rehab": mn1_rehab,
                   "F_dp": {str(k): dp[k] for k in ks_all}},
           "DF1": {"bad": clo_bad},
           "DF2": {"div": div, "fail_groups": fail_groups, "gamma0": g0,
                   "mq2_break_ks": mq2_break},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

# ---------- part2：D-F4 偶 k 恢复 + D-G 系 ----------
def z4_abs2(A):
    return zmul(A, zconj(A))[0]

def fit_quintic_int(ks, xs):
    """解 X_k = A v^2 + B v + C + k D v + k E（A..E ∈ Z[√2] 各分量独立·Fraction 精确消元）
    xs[k] = X_k 的一个整分量。返回 (A,B,C,D,E) 分量列表或 None（非整/无解）"""
    ks5 = ks[:5]
    rows = []
    for k in ks5:
        v = v_of(k)
        rows.append([Fraction(v*v), Fraction(v), Fraction(1), Fraction(k*v), Fraction(k)])
    rhs = [Fraction(xs[k]) for k in ks5]
    # 高斯消元
    M = [rows[i][:] + [rhs[i]] for i in range(5)]
    for col in range(5):
        piv = None
        for r in range(col, 5):
            if M[r][col] != 0: piv = r; break
        if piv is None: return None
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [x / pv for x in M[col]]
        for r in range(5):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [a - f*b for a, b in zip(M[r], M[col])]
    sol = [M[i][5] for i in range(5)]
    if any(s.denominator != 1 for s in sol): return None
    return [int(s) for s in sol]

def run_part2():
    log = []
    # D-F4：偶 k 双候选
    cand_res = {}
    for cname in ("gammaA", "gammaB"):
        Nfun = NSPEC[cname]
        qeven = {}; ro_bad = []
        for k in KS_EVEN:
            row = {}
            for (r, rp) in PAIRS:
                q = Q2_second_N(k, r, rp, Nfun)
                row["%d|%d" % (r, rp)] = {"a": q.get("a"), "b": q.get("b"),
                                          "sign": q.get("sign"), "real_ok": q.get("real_ok")}
                if not q.get("real_ok"): ro_bad.append((k, "%d|%d" % (r, rp)))
            qeven[str(k)] = row
        # 主导显式：X_k = C_dom·LAMm^{2k}（应实型 (x,y,0,-y)）
        dom_seq = {}; nonreal = []
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            seq = {}
            for k in KS_EVEN:
                C = pairs_contrib_Z4_N(k, r, rp, Nfun)
                dom = layer_sums(C)["dom"]
                X = zmul(dom, zpowN(LAMm, 2*k))
                seq[k] = list(X)
                if not (X[2] == 0 and X[3] == -X[1]): nonreal.append((key, k))
            dom_seq[key] = seq
        # 修正读法（首跑拦截后纸面重推·偶 k s₁=s₃=0 ⟹ 4a² 项结构性消失）：
        #   2|20（两候选同）：dom = 8kα₁v²λ^{2k}
        #   8|14 γ-B（(v,v) 对称）：dom = 8kα₁v²λ^{2k}
        #   8|14 γ-A（(v−1,v)）：dom = 8kα₁(v−1)²λ^{2k}
        #   4|10（(v+1,v) γ-A / (v+1,v) γ-B 同）：γ_m=N_{cp}ζ^{mc}−N_cζ^{mc′}，(c,cp)=(1,3)：
        #     γ₁=N₃ζ¹−N₁ζ³·γ₃=N₃ζ³−N₁ζ⁹=N₃ζ³−N₁ζ·γ₁+γ₃=(N₃−N₁)(ζ+ζ³)
        #     dom = 2kα₁|γ₁+γ₃|²λ^{2k} = 2kα₁(N₃−N₁)²|ζ+ζ³|²λ^{2k}·|ζ+ζ³|²=|ζ(1+ζ²)|²=|ζ(1+i)|²=2
        #     ⟹ dom = 4kα₁(N₃−N₁)²λ^{2k}
        #   10|22（(3,7)）：γ₁=N₇ζ³−N₃ζ⁷·γ₃=N₇ζ⁹−N₃ζ^{21}=N₇ζ−N₃ζ·γ₁+γ₃=(N₇−N₃)(ζ³+ζ)=(N₇−N₃)ζ(1+ζ²)
        #     dom = 2kα₁(N₇−N₃)²·2·λ^{2k} = 4kα₁(N₇−N₃)²λ^{2k}
        # 冻结候选（判据书 M-N5② 字面：16a²v²λ^{2k}）检验保留=判负证据
        dom_expl = {}; frozen_bad = []
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            seq = dom_seq[key]
            if (r, rp) == (2, 20):
                expr_ok = {}
                for k in KS_EVEN:
                    v = v_of(k)
                    expr_ok[k] = (tuple(seq[k]) == (-64*k*v*v, 40*k*v*v, 0, -40*k*v*v))
                dom_expl[key] = expr_ok
            elif (r, rp) == (8, 14):
                expr_ok = {}
                for k in KS_EVEN:
                    v = v_of(k)
                    if cname == "gammaB":
                        n2, n4 = v, v
                    else:
                        n2, n4 = v-1, v
                    # γ₁=N₄ζ²−N₂ζ⁴·γ₃=N₄ζ⁶−N₂ζ^{12}=N₄ζ⁶+N₂
                    # γ₁+γ₃=N₄(ζ²+ζ⁶)+N₂(1−ζ⁴)=N₄(i−i)+N₂(1+1)=2N₂
                    # dom = 2kα₁|γ₁+γ₃|²λ^{2k} = 8kα₁N₂²λ^{2k}
                    expr_ok[k] = (tuple(seq[k]) == (-64*k*n2*n2, 40*k*n2*n2, 0, -40*k*n2*n2))
                dom_expl[key] = expr_ok
            elif (r, rp) == (4, 10):
                # 机器结构事实：4|10 偶档主导层全零（两候选·强于 M-Q3' 端点抵消——整层消失）
                expr_ok = {}
                for k in KS_EVEN:
                    expr_ok[k] = (tuple(seq[k]) == (0, 0, 0, 0))
                dom_expl[key] = expr_ok
            else:
                expr_ok = {}
                for k in KS_EVEN:
                    v = v_of(k)
                    n3 = Nfun(k, 3); n7 = Nfun(k, 7)
                    # 10|22 偶版：dom = 4kα₁(N₇+N₃)²λ^{2k}（16kα₁v² 两候选同·k=4 手验命中）
                    dd = (n7+n3)**2
                    expr_ok[k] = (tuple(seq[k]) == (-32*k*dd, 20*k*dd, 0, -20*k*dd))
                dom_expl[key] = expr_ok
        # 冻结候选 16a²v²λ^{2k}（γ-B 8|14）字面检验（判负证据保留）
        b814 = {}
        for k in KS_EVEN:
            v = v_of(k)
            expr = zmul(zpowN(LAM, 2*k), (96*v*v, -64*v*v, 0, 64*v*v))
            got = tuple(dom_seq["8|14"][k])
            b814[k] = bool(expr == got)
        dom_expl_frozen_neg = {str(k): b814[k] for k in KS_EVEN if not b814[k]}
        # ρ 谱（偶档·候选口径）+奇偶连续带
        rho = {}
        for k in KS_EVEN:
            for (r, rp) in PAIRS:
                C = pairs_contrib_Z4_N(k, r, rp, Nfun)
                lay = layer_sums(C)
                de = z4_abs2(lay["even"]); dm = z4_abs2(lay["dom"])
                rho["%d|%d_k%d" % (r, rp, k)] = (de, dm)
        cand_res[cname] = {"qeven": qeven, "realok_bad": ro_bad, "dom_seq": dom_seq,
                           "nonreal": nonreal, "dom_expl": dom_expl,
                           "frozen_neg": dom_expl_frozen_neg, "rho": rho}
    # 结构锚汇总（修正读法口径·冻结候选判负证据单列）
    anchor = {}
    for cname in ("gammaA", "gammaB"):
        c = cand_res[cname]
        a1 = len(c["realok_bad"]) == 0 and len(c["nonreal"]) == 0
        a2 = all(c["dom_expl"]["2|20"].values())
        a3 = all(c["dom_expl"]["8|14"].values())
        a4 = all(c["dom_expl"]["4|10"].values()) and all(c["dom_expl"]["10|22"].values())
        anchor[cname] = {"anchor1_real": bool(a1), "anchor_dom220": bool(a2),
                         "anchor_dom814": bool(a3), "anchor_dom_410_1022": bool(a4)}
    # P-Π4：4|10 偶档符号（两候选分别）
    p4 = {}
    for cname in ("gammaA", "gammaB"):
        signs = [cand_res[cname]["qeven"][str(k)]["4|10"]["sign"] for k in KS_EVEN]
        p4[cname] = {"signs": signs, "any_pos": any(s is not None and s > 0 for s in signs)}
    # ρ 奇偶连续带（在档奇档 ρ 重算 vs 偶档·2|20·两候选同 γ 口径奇域）
    rho_odd = {}
    for k in KS_ALL:
        C = pairs_contrib_Z4_N(k, 2, 20, N_gamma)
        lay = layer_sums(C)
        rho_odd[k] = (z4_abs2(lay["even"]), z4_abs2(lay["dom"]))
    def rho_val(pair):
        de, dm = pair
        return (de/dm)**0.5 if dm else None
    band_bad = []
    def rho_in_band(s, lo, hi):
        """整型交叉乘判 min(lo,hi)<=sqrt(s0/s1)<=max(lo,hi)（lo,hi=(de,dm) 对）"""
        def ge(a, b):  # sqrt(a0/a1) >= b0/b1 ⟺ a0*b1 >= a1*b0
            return a[0]*b[1] >= a[1]*b[0]
        return (ge(s, lo) and ge(hi, s))
    for k in KS_EVEN:
        for cname in ("gammaA", "gammaB"):
            de, dm = cand_res[cname]["rho"]["2|20_k%d" % k]
            lo = rho_odd[k-1]; hi = rho_odd[k+1]
            if not rho_in_band((de, dm), lo, hi):
                band_bad.append((cname, k))
    log.append("D-F4 anchors A=%s B=%s ; P-Pi4 any_pos A=%s B=%s ; rho-band bad=%d" %
               (str(anchor["gammaA"]), str(anchor["gammaB"]),
                p4["gammaA"]["any_pos"], p4["gammaB"]["any_pos"], len(band_bad)))
    # D-G0：{0,4} 行列 28 对闭式组装 Z4 通道（独立 Π(i)/γ/Ω 闭式表）
    def PI_clo(k):
        p = (k+1)//2 if k % 2 == 1 else k//2; q = k//2
        PI = {0: zpow(2*k), 1: zmul(zpowN(LAM, k), Z[1]), 2: (3**p, 0, 0, 0),
              3: zmul(zpowN(LAM, k), Z[7]), 4: zpow(-2*k),
              5: zmul(zpowN(LAMm, k), Z[1]), 6: (3**q, 0, 0, 0),
              7: zmul(zpowN(LAMm, k), Z[7])}
        return PI
    SQ2 = (0, 1, 0, -1)
    def zs2(u, v, den=1):
        """(u+v√2)/den 的 Z[√2] 表示（den 缩放通道）"""
        return (u, v, den)
    def alpha_of(m, k):
        """α_m 的 (u,v,den)（M-Z2 表）"""
        if m in (1, 3): return (-8, 5, 1)
        if m in (5, 7): return (-8, -5, 1)
        if m in (0, 4): return (-4, 0, 1)
        if m == 6: return (-2, 0, 1)
        if m == 2: return (-(4*k-2), 0, 3)
        raise ValueError
    def Lp_of(m, k):
        """L'_m 的 (u,v,den)（M-Z2 表·s₀/s₄ 补块闭式）"""
        p = (k+1)//2; q = k//2
        if m == 0: return (-4*k, 0, 1)
        if m == 4: return (-4*k, 0, 1)
        if m == 2: return (2-4*k, 0, 3)
        if m == 6: return (-(4*k+2), 0, 3)
        am = alpha_of(m, k); a3 = alpha_of(3*m % 8, k)
        # p·α_m + q·α_{3m}（den 取 lcm）
        d = am[2]*a3[2]//math.gcd(am[2], a3[2])
        u = am[0]*(d//am[2])*p + a3[0]*(d//a3[2])*q
        vv = am[1]*(d//am[2])*p + a3[1]*(d//a3[2])*q
        return (u, vv, d)
    def s_of(m, k):
        # M-Z2 表：s₀=−2k·s₄=+2k·s₁=−a·s₃=+a·s₅=−b·s₇=+b·s₂=s₆=0
        # a=2−√2=(2,−1)·b=2+√2=(2,1)·(u,v) 表示 u+v√2
        tbl = {0: (-2*k, 0), 1: (-2, 1), 2: (0, 0), 3: (2, -1),
               4: (2*k, 0), 5: (-2, -1), 6: (0, 0), 7: (2, 1)}
        return tbl[m]
    def omega_of(m, mp, k):
        """Ω_{m,mp}=(s_m+s_mp)²+L'_m+conj(L'_{mp}) 的 (u,v,den)·L' 全实"""
        s1 = s_of(m, k); s2v = s_of(mp, k)
        su = s1[0]+s2v[0]; sv = s1[1]+s2v[1]
        # (su+sv√2)² = (su²+2sv², 2·su·sv)
        w2 = (su*su + 2*sv*sv, 2*su*sv, 1)
        L1 = Lp_of(m, k); L2 = Lp_of(mp, k)
        d = w2[2]*L1[2]*L2[2]
        u = w2[0]*(d//w2[2]) + L1[0]*(d//L1[2]) + L2[0]*(d//L2[2])
        vv = w2[1]*(d//w2[2]) + L1[1]*(d//L1[2]) + L2[1]*(d//L2[2])
        g = math.gcd(math.gcd(abs(u), abs(vv)), d)
        if g: u //= g; vv //= g; d //= g
        return (u, vv, d)
    import math
    def z4_mul_zs2(A, om):
        """Z4 × (u+v√2)/den：先乘 (u+v√2) 的 Z4 化 (u,v,0,-v)·返回 (Z4, den)"""
        Zom = (om[0], om[1], 0, -om[1])
        return zmul(A, Zom), om[2]
    dg0_bad = []; dg0 = {}
    for k in (3, 9, 17):
        PI = PI_clo(k)
        for (r, rp) in PAIRS:
            gam = gamma_z_N(k, r, rp, N_gamma)
            C_chain = pairs_contrib_Z4_N(k, r, rp, N_gamma)
            for (m, m2) in LAYERS["zero"]:
                pre = zmul(zmul(gam[m], zconj(gam[m2])), zmul(PI[m], zconj(PI[m2])))
                cand, den = z4_mul_zs2(pre, omega_of(m, m2, k))
                ref = zscale(C_chain[(m, m2)], den)
                ok = (cand == ref)
                if not ok:
                    dg0_bad.append((k, "%d|%d" % (r, rp), "%d,%d" % (m, m2)))
            dg0["%d|%d_k%d" % (r, rp, k)] = True
    log.append("D-G0 omega-table 28-pair rebuild bad=%d (k=3,9,17 × 4 pairs)" % len(dg0_bad))
    # D-G1：行列总和序列（2|20·k 奇 12 档）+变号点
    zsum = {}
    for k in KS_ALL:
        C = pairs_contrib_Z4_N(k, 2, 20, N_gamma)
        zsum[k] = list(layer_sums(C)["zero"])
    zsum410 = {}
    for k in KS_ALL:
        C = pairs_contrib_Z4_N(k, 4, 10, N_gamma)
        zsum410[k] = list(layer_sums(C)["zero"])
    signchange = [k for k in KS_ALL if zsum[k][0] * zsum[3][0] < 0]
    # D-G2：修正层角色——六层和 Q vs 去 {0,4} 层 Q 的符号对比+占比
    role = {}
    for k in KS_ALL:
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            C = pairs_contrib_Z4_N(k, r, rp, N_gamma)
            lay = layer_sums(C)
            tot = (0,0,0,0)
            for name in LAYERS: tot = zadd(tot, lay[name])
            noz = (0,0,0,0)
            for name in LAYERS:
                if name != "zero": noz = zadd(noz, lay[name])
            role["%s_k%d" % (key, k)] = {
                "Q": list(tot), "Q_nozero": list(noz), "zero": list(lay["zero"]),
                "sign_flip": sign_qsqrt2(tot[0], tot[1]) != sign_qsqrt2(noz[0], noz[1]),
                "zero_ratio": float(z4_abs2(lay["zero"]) / max(1, z4_abs2(tot)))}
    # D-G3：域外词前哨 |D|≤200
    G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
    Gtab = np.array(G, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for _ in range(12):
        Ds4 = np.concatenate([Ds*3 + ts*Gtab[r][ms] for r in range(4)])
        fac = np.array([1, -1, -1, 1], dtype=np.int64)
        ts4 = np.concatenate([ts * fac[r] for r in range(4)])
        ms4 = np.concatenate([(ms + r) % 3 for r in range(4)])
        ys4 = np.concatenate([ys*4 + r for r in range(4)])
        ys, Ds, ts, ms = ys4, Ds4, ts4, ms4
    aD = -Ds
    hist200 = np.bincount(aD[aD <= 200], minlength=201)
    in71 = int((aD <= 71).sum()); in200 = int((aD <= 200).sum())
    nonzero200 = [int(d) for d in range(201) if hist200[d] > 0]
    gaps = [ (nonzero200[i], nonzero200[i+1]) for i in range(len(nonzero200)-1) if nonzero200[i+1]-nonzero200[i] > 1]
    log.append("D-G3 |D|<=71: %d words ; |D|<=200: %d ; support-200 size=%d ; gaps=%s" %
               (in71, in200, len(nonzero200), str(gaps[:8])))
    res = {"meta": {"script": "nc_combinatorics-v1.0-20260925.py", "frozen": FROZEN},
           "DF4": {"candidates": {cn: {"qeven": cand_res[cn]["qeven"],
                                        "realok_bad": cand_res[cn]["realok_bad"],
                                        "dom_seq": {kk: {str(k): vv for k, vv in seq.items()}
                                                    for kk, seq in cand_res[cn]["dom_seq"].items()},
                                        "nonreal": cand_res[cn]["nonreal"],
                                        "dom_expl_ok": {kk: {str(k): bool(vv) for k, vv in ex.items()}
                                                        for kk, ex in cand_res[cn]["dom_expl"].items()},
                                        "frozen_16a2_neg": sorted(str(k) for k in cand_res[cn]["frozen_neg"])}
                                   for cn in ("gammaA", "gammaB")},
                    "anchors": anchor, "P_Pi4": p4, "rho_band_bad": band_bad,
                    "rho_odd_220": {str(k): rho_odd[k] for k in KS_ALL}},
           "DG0": {"bad": dg0_bad, "data": dg0},
           "DG1": {"zsum_220": {str(k): zsum[k] for k in KS_ALL},
                   "zsum_410": {str(k): zsum410[k] for k in KS_ALL},
                   "signchange_ks": signchange},
           "DG2": role,
           "DG3": {"hist200_head": [int(x) for x in hist200[:201]],
                   "in71": in71, "in200": in200,
                   "support200": nonzero200, "gaps": [list(g) for g in gaps]},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

if __name__ == "__main__":
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("all", "part1"): run_part1()
    if part in ("all", "part2"): run_part2()
