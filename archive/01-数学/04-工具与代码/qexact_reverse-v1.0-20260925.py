# -*- coding: utf-8 -*-
# Q 全档精确闭式冲刺+逆序转移矩阵（R32 主格二+候补·判据书 D-D 系/D-E0 实算）
# 判据书：代数册·四型端点值判据与Q全档精确闭式预注册判据书-v1.0-20260925.md（冻结 2026-09-25 01:49:27）
# part1: D-D0 逐对回归锚（行列总和 zero_rowsum 直读+om_bad 复核）
#        D-D1 全档 64 对逐对 Z4+五层和=Q 零容差恒等（12 奇档×4 对组）
#        D-D2 显式闭式对照（主导层精确式 Z4/cross 整性/{0,4} 行列 28 对/k=3 残差定位）
#        D-D3 lim 常数第二证明（精确主导显式极限·mp）
# part2: D-E0 逆序转移矩阵（4^12 全域 D+rev(D) → 72×72 计数矩阵+候选判据对表）
import json, argparse
import numpy as np
from mpmath import mp, mpf, sqrt as msqrt

mp.dps = 50

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS_ALL = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
R31_P2 = "H:/理论存档/01-数学/02-实验与数据/results/qk_closed_form-part2-v1.0-20260924.json"
R29_Q2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_track_mech-q2-v1.0-20260924.json"
R30_P2 = "H:/理论存档/01-数学/02-实验与数据/results/dpm2_remainder-part2-v1.0-20260924.json"
R31_P3 = "H:/理论存档/01-数学/02-实验与数据/results/qk_closed_form-part3-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/qexact_reverse-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T01:49:27"

def c_of(r): return (r - (r % 3)) // 3 % 8

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

LAM = (1, 1, 0, -1)
I4 = (0, 0, 1, 0)

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
    return {"real_ok": (C == 0 and D == -B), "a": A, "b": B}

def pairs_contrib_Z4(k, r, rp):
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
    r29 = json.load(open(R29_Q2, encoding="utf-8"))
    r30 = json.load(open(R30_P2, encoding="utf-8"))
    r31 = json.load(open(R31_P3, encoding="utf-8"))
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

# ---------- part1：D-D0..D-D3 ----------
def run_part1():
    log = []
    r31 = json.load(open(R31_P2, encoding="utf-8"))
    qref = load_qref()
    # D-D0：k=3,9,17 行列总和直读对照+om_bad zint 复核
    dd0_bad = []; dd0 = {}
    for k in (3, 9, 17):
        C = pairs_contrib_Z4(k, 2, 20)
        lay = layer_sums(C)
        ref = r31["DA2"]["zero_rowsum"]["2|20_k%d" % k][0]
        got = lay["zero"][0]
        dd0["2|20_k%d" % k] = {"got": got, "ref": ref, "ok": got == ref}
        if got != ref: dd0_bad.append(("zero_rowsum", k))
    zint_in_bad = [b for b in r31["DA2"]["bad"] if b and b[0] == "zint"]
    if zint_in_bad: dd0_bad.append(("zint_residue", len(zint_in_bad)))
    log.append("D-D0 bad=%d (zint-residue=%d)" % (len(dd0_bad), len(zint_in_bad)))
    # D-D1：全档 64 对逐对 Z4+五层和=Q 零容差
    dd1_bad = []; dd1 = {}
    for k in KS_ALL:
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            C = pairs_contrib_Z4(k, r, rp)
            lay = layer_sums(C)
            tot = (0,0,0,0)
            for name in LAYERS: tot = zadd(tot, lay[name])
            qa = Q2_second(k, r, rp)["a"]
            ok = (tot == (qa, 0, 0, 0)) and (lay["dom"][1:] != (0,0,0) or True)
            if not ok: dd1_bad.append((key, k))
            dd1["%s_k%d" % (key, k)] = {
                "per": {"%d,%d" % pl: list(C[pl]) for pl in sorted(C.keys())},
                "layers": {n: list(lay[n]) for n in LAYERS}, "total": list(tot), "Q": qa}
    log.append("D-D1 six-layer-sum==Q bad=%d /48 (exact Z4; five-layer frozen form NEGATED->oddodd 8-pair completion)" % len(dd1_bad))
    # D-D2①：主导层精确显式 Z4（2|20 与 8|14 全档）
    dom_bad = []; dom_chk = {}
    for k in KS_ALL:
        M = (3**k - 3)//8
        # 2|20：λ^{2k}[8a²(2M²+2M+1)+4kα₁]·8a²=48−32√2·α₁=−8+5√2（M-R1 修正读法：系数 8a²）
        A1 = 48*(2*M*M+2*M+1) - 32*k
        B1 = -32*(2*M*M+2*M+1) + 20*k
        expr = zmul(zpowN(LAM, 2*k), (A1, B1, 0, -B1))
        C20 = layer_sums(pairs_contrib_Z4(k, 2, 20))["dom"]
        ok20 = (expr == C20)
        # 8|14：16a²M²λ^{2k}·16a²=96−64√2
        A8 = 96*M*M; B8 = -64*M*M
        expr8 = zmul(zpowN(LAM, 2*k), (A8, B8, 0, -B8))
        C8 = layer_sums(pairs_contrib_Z4(k, 8, 14))["dom"]
        ok8 = (expr8 == C8)
        if not ok20: dom_bad.append(("2|20", k))
        if not ok8: dom_bad.append(("8|14", k))
        dom_chk["2|20_k%d" % k] = ok20; dom_chk["8|14_k%d" % k] = ok8
    log.append("D-D2 dom-explicit bad=%d (2|20 & 8|14, all k)" % len(dom_bad))
    # D-D2②：cross 层整性（b 分量=0）全档（P-Ω4）
    cr_bad = []; cr = {}
    for k in KS_ALL:
        for (r, rp) in PAIRS:
            key = "%d|%d" % (r, rp)
            lay = layer_sums(pairs_contrib_Z4(k, r, rp))
            cz = lay["cross"]
            cr["%s_k%d" % (key, k)] = list(cz)
            if cz[1] != 0 or cz[3] != 0: cr_bad.append((key, k))
    log.append("D-D2 cross-integrality bad=%d (P-Omega4)" % len(cr_bad))
    # D-D2③：{0,4} 行列 28 对逐对落盘（2|20/4|10·k=3,9,17）+总和锚
    zero28 = {}
    for k in (3, 9, 17):
        for (r, rp) in [(2, 20), (4, 10)]:
            C = pairs_contrib_Z4(k, r, rp)
            zero28["%d|%d_k%d" % (r, rp, k)] = {
                "per": {"%d,%d" % pl: list(C[pl]) for pl in LAYERS["zero"]},
                "rowsum": list(layer_sums(C)["zero"])}
    log.append("D-D2 zero28 pairs dumped (k=3,9,17 × 2|20,4|10)")
    # D-D2④：k=3 残差定位（R31 double 层 vs Z4 精确层）
    resid = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        z4lay = layer_sums(pairs_contrib_Z4(3, r, rp))
        d31 = r31["DA3"]["layers"]["%s_k3" % key]["lay"]
        resid[key] = {n: {"z4_exact": float(z4lay[n][0] + z4lay[n][1]*msqrt(mpf(2))),
                          "r31_double": (None if n not in d31 else d31[n])} for n in LAYERS}
    log.append("D-D2 k=3 residual localization dumped")
    # D-D3：lim 第二证明（精确主导显式）
    lam = mpf(1) + msqrt(mpf(2))
    a_star = (mpf(3) - 2*msqrt(mpf(2)))/2
    lim2 = {}; dev = {}
    for k in (13, 17, 21, 25):
        M = (3**k - 3)//8
        A1 = 48*(2*M*M+2*M+1) - 32*k
        B1 = -32*(2*M*M+2*M+1) + 20*k
        domv = mpf(A1) + mpf(B1)*msqrt(mpf(2))
        r_k = float(domv * lam**int(2*k) / (mpf(3)*lam)**int(2*k))
        lim2[str(k)] = r_k; dev[str(k)] = abs(r_k - float(a_star))
    # 8|14 lim：16a²M²λ^{2k}/(3λ)^{2k} → 16a²/64=a²/4
    M25 = (3**25 - 3)//8
    lim8 = float((mpf(96) - mpf(64)*msqrt(mpf(2))) * mpf(M25)**2 * lam**50 / (mpf(3)*lam)**50)
    mono = dev["25"] < dev["21"] < dev["17"] < dev["13"]
    dd3 = {"r220": lim2, "dev": dev, "mono": mono, "lim8_14_k25": lim8,
           "a_star": float(a_star), "analytic": "a^2/4 both"}
    log.append("D-D3 lim-2nd-proof dev13=%.5f dev21=%.6f dev25=%.8f mono=%s lim8=%.6f" %
               (dev["13"], dev["21"], dev["25"], mono, lim8))
    res = {"meta": {"script": "qexact_reverse-v1.0-20260925.py", "frozen": FROZEN},
           "DD0": {"bad": dd0_bad, "chk": dd0},
           "DD1": {"bad": dd1_bad, "data": dd1},
           "DD2": {"dom_bad": dom_bad, "dom_chk": dom_chk, "cross_bad": cr_bad,
                   "cross": cr, "zero28": zero28, "resid_k3": resid},
           "DD3": dd3,
           "P-Omega4": bool(not cr_bad), "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    print("P-Omega4:", res["P-Omega4"])
    return res

# ---------- part2：D-E0 逆序转移矩阵 ----------
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
def dp_layers(L=12):
    Gtab = np.array(G, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for _ in range(L):
        Ds4 = np.concatenate([Ds*3 + ts*Gtab[r][ms] for r in range(4)])
        fac = np.array([1, -1, -1, 1], dtype=np.int64)
        ts4 = np.concatenate([ts * fac[r] for r in range(4)])
        ms4 = np.concatenate([(ms + r) % 3 for r in range(4)])
        ys4 = np.concatenate([ys*4 + r for r in range(4)])
        ys, Ds, ts, ms = ys4, Ds4, ts4, ms4
    return ys, Ds

def run_part2():
    log = []
    ys, Ds = dp_layers(12)
    N = Ds.shape[0]
    log.append("domain N=%d D-range=[%d,0]" % (N, int(Ds.min())))
    # 逆序映射（12 位 4 进制倒排）
    rev = np.zeros(N, dtype=np.int64)
    y = ys.copy()
    for _ in range(12):
        rev = rev*4 + (y % 4)
        y //= 4
    Drev = Ds[rev]
    # 72×72 矩阵（档 c=0..−71 → 索引 −c）
    Mat = np.zeros((72, 72), dtype=np.int64)
    c1 = -Ds; c2 = -Drev
    in1 = (c1 >= 0) & (c1 < 72); in2 = (c2 >= 0) & (c2 < 72)
    mask = in1 & in2
    np.add.at(Mat, (c1[mask], c2[mask]), 1)
    n_out = int((~mask).sum())
    rowsum = Mat.sum(axis=1)
    diag = np.diag(Mat)
    top1 = Mat.max(axis=1)
    top1_frac = np.divide(top1, rowsum, out=np.zeros(72), where=rowsum > 0)
    diag_dom = int(((diag >= top1) & (rowsum > 0)).sum())
    top1_dom = int(((top1_frac > 0.5)).sum())
    nonempty = int((rowsum > 0).sum())
    # 候选判据
    cand_i = bool(diag_dom > 36)
    cand_ii = bool(top1_dom > 36)
    # 对角谱样本+继承档行样本
    samples = {}
    for c in (0, 3, 9, 27, 55, 45, 35, 63, 6, 30):
        nz = np.nonzero(Mat[c])[0]
        if len(nz):
            order = nz[np.argsort(-Mat[c][nz])][:4]
            samples[str(c)] = {str(int(j)): int(Mat[c][j]) for j in order}
    log.append("D-E0 nonempty-rows=%d diag-dominant=%d/72 top1>0.5=%d/72 outside=%d" %
               (nonempty, diag_dom, top1_dom, n_out))
    log.append("candidates: (i)=%s (ii)=%s" % (cand_i, cand_ii))
    res = {"meta": {"script": "qexact_reverse-v1.0-20260925.py", "frozen": FROZEN},
           "DE0": {"N": int(N), "nonempty_rows": nonempty, "diag_dominant": diag_dom,
                   "top1_half": top1_dom, "outside_bucket": n_out,
                   "cand_i": cand_i, "cand_ii": cand_ii, "samples": samples,
                   "rowsum_nonzero": int(nonempty),
                   "matrix_nonzero_cells": int((Mat > 0).sum())},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    {1: run_part1, 2: run_part2}[a.part]()

if __name__ == "__main__":
    main()
