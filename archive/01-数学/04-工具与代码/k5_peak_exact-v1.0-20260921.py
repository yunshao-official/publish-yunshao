# -*- coding: utf-8 -*-
# k=3/5 的 2|20 峰位=π/2 解析证明（R24 候补格·判据书 C 系实算）
# C0 锚 / C1 驻点定理全档 / C2 精确值 / C3 二阶系数符号谱（判别预测） / C4 总裁决
# 口径：Q(ζ) 整型基（ζ^4=−1）精确算术；Δφ=e^{itd}(S_c/N_c−S_cp/N_cp)（R22 P 系正本口径）
import json
from fractions import Fraction
from mpmath import mp, mpf, exp as mpexp, pi as mpi, sqrt as mpsqrt

mp.dps = 50

# ---------- Q(ζ) 精确算术（Fraction 系数 4 维向量，基 1,ζ,ζ²,ζ³；ζ⁴=−1） ----------
def qmul(a, b):
    r = [Fraction(0)] * 4
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj == 0:
                continue
            k = i + j
            if k >= 4:
                r[k - 4] -= ai * bj      # ζ⁴ = −1
            else:
                r[k] += ai * bj
    return r

def qadd(a, b):
    return [x + y for x, y in zip(a, b)]

def qsub(a, b):
    return [x - y for x, y in zip(a, b)]

def qscal(s, a):
    return [s * x for x in a]

def qconj(a):
    # conj(ζ)=ζ⁷=−ζ³、conj(ζ²)=−ζ²、conj(ζ³)=−ζ
    return [a[0], -a[3], -a[2], -a[1]]

def qpow(a, e):
    r = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    b = a
    while e:
        if e & 1:
            r = qmul(r, b)
        b = qmul(b, b); e >>= 1
    return r

def q_to_real(a):
    """实元素 → (P, Q) with a = P + Q√2；非实返回 None。ζ−ζ³=√2、ζ²=i"""
    if a[2] != 0 or a[1] != a[3]:
        return None
    return a[0], a[1] - a[3]

def sign_real(PQ):
    P, Q = PQ
    if Q == 0:
        return (P > 0) - (P < 0)
    if P == 0:
        return (Q > 0) - (Q < 0)
    lhs = P * P; rhs = 2 * Q * Q
    mag = 1 if lhs > rhs else (-1 if lhs < rhs else 0)
    return ((P > 0) - (P < 0)) * mag

def zpow(n):
    """ζ^n，n 任意整"""
    n = n % 8
    if n < 4:
        v = [Fraction(0)] * 4
        v[n] = Fraction(1)
        return v
    v = [Fraction(0)] * 4
    v[n - 4] = Fraction(-1)
    return v

def conv_z2(a):
    """Q(ζ) 元素 × i（=ζ²）"""
    r = [Fraction(0)] * 4
    for i, v in enumerate(a):
        if v == 0:
            continue
        k = i + 2
        if k >= 4:
            r[k - 4] -= v
        else:
            r[k] += v
    return r

def poly_mul(A, B):
    r = [None] * (len(A) + len(B) - 1)
    for i, ai in enumerate(A):
        if all(v == 0 for v in ai):
            continue
        for j, bj in enumerate(B):
            if all(v == 0 for v in bj):
                continue
            prod = qmul(ai, bj)
            if r[i + j] is None:
                r[i + j] = prod
            else:
                r[i + j] = qadd(r[i + j], prod)
    return [(v if v is not None else [Fraction(0)] * 4) for v in r]

def poly_pow(A, e):
    R = [[Fraction(1), Fraction(0), Fraction(0), Fraction(0)]]
    B = A
    while e:
        if e & 1:
            R = poly_mul(R, B)
        B = poly_mul(B, B); e >>= 1
    return R

def build_S_coeffs(k):
    """S_c(x)=(1/8)Σ_m ζ^{mc} Π_m(x), Π_m=(1+ζ^{−m}x+ζ^{−2m}x²)^p(1+ζ^{−3m}x+ζ^{−6m}x²)^q"""
    p = (k + 1) // 2; q = k // 2
    S = []
    for c in range(8):
        acc = [[Fraction(0)] * 4 for _ in range(2 * k + 1)]
        for m in range(8):
            zm = zpow(-m); z3m = zpow(-3 * m)
            f = [[Fraction(0)] * 4 for _ in range(3)]
            g = [[Fraction(0)] * 4 for _ in range(3)]
            f[0] = qadd(f[0], zpow(0)); f[1] = qadd(f[1], zm); f[2] = qadd(f[2], zpow(-2 * m))
            g[0] = qadd(g[0], zpow(0)); g[1] = qadd(g[1], z3m); g[2] = qadd(g[2], zpow(-6 * m))
            Pis = poly_mul(poly_pow(f, p), poly_pow(g, q))
            zmc = zpow(m * c)
            for n in range(len(Pis)):
                acc[n] = qadd(acc[n], qmul(zmc, Pis[n]))
        S.append([[Fraction(v, 8) for v in coef] for coef in acc])
    return S

def delta_poly(k, r, rp):
    """Δφ_{r|rp} 多项式（A 口径乘公分母）：e^{itd} 因子省略（模长无关）。
    返回系数列表 b_n（Q(ζ)）与公分母说明。"""
    S = build_S_coeffs(k)
    M = (3 ** k - 3) // 8
    Ns = [M + 1 if c in (0, 1) else M for c in range(8)]
    c, cp = ((r - (r % 3)) // 3) % 8, ((rp - (rp % 3)) // 3) % 8
    L = max(len(S[c]), len(S[cp]))
    num = [None] * L
    for n in range(L):
        a = S[c][n] if n < len(S[c]) else [Fraction(0)] * 4
        b = S[cp][n] if n < len(S[cp]) else [Fraction(0)] * 4
        num[n] = qsub(qscal(Fraction(Ns[cp]), a), qscal(Fraction(Ns[c]), b))
    return num, Fraction(Ns[c] * Ns[cp])

def F_coeffs(num):
    """F=Δφ·conjΔφ 的系数 c_j（j=−D..D），Q(ζ)；conjΔφ=Σ conj(b_n) x^{−n}"""
    D = len(num) - 1
    conj = [qconj(b) for b in num]          # conj(b_n) x^{−n}
    c = {}
    for i, bi in enumerate(num):
        if all(v == 0 for v in bi):
            continue
        for j_, cj in enumerate(conj):
            if all(v == 0 for v in cj):
                continue
            expo = i - j_                    # x^{i−j_}
            prod = qmul(bi, cj)              # Q(ζ)×Q(ζ) 卷积
            c[expo] = qadd(c.get(expo, [Fraction(0)] * 4), prod)
    return c, D

def deriv_at_i(c, D, order):
    """F^(order)(π/2) = Σ_j c_j (ij)^order i^j；返回 Q(√2) (P,Q) 或 None（非实）"""
    tot = [Fraction(0)] * 4
    for j, cj in c.items():
        # (i j)^order · i^j = j^order · i^{j+order}
        pw = (j + order) % 4
        fac = [1, 1j, -1, -1j][pw]
        re, im = (1, 0) if fac == 1 else ((0, 1) if fac == 1j else ((-1, 0) if fac == -1 else (0, -1)))
        term = [Fraction(0)] * 4
        if re:
            term = qadd(term, qscal(Fraction(re), cj))
        if im:
            term = qadd(term, qscal(Fraction(im), conv_z2(cj)))   # ×i = ×ζ²
        tot = qadd(tot, qscal(Fraction(j ** order), term))
    return q_to_real(tot)

def F_at_i(c):
    """F(π/2)=Σ_j c_j i^j"""
    tot = [Fraction(0)] * 4
    for j, cj in c.items():
        pw = j % 4
        if pw == 0:
            tot = qadd(tot, cj)
        elif pw == 1:
            tot = qadd(tot, conv_z2(cj))
        elif pw == 2:
            tot = qsub(tot, cj)
        else:
            tot = qsub(tot, conv_z2(cj))
    return tot

def main():
    res = {}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    # ---- C0 锚 ----
    L("== C0 ==")
    num, den = delta_poly(3, 2, 20)
    c, D = F_coeffs(num)
    Fv = q_to_real(F_at_i(c))
    # |Δφ(π/2)|²=F(π/2)/(den²)
    P = Fv[0] / (den * den); Q = Fv[1] / (den * den)
    # 2/3 的平方=4/9
    ok = (P == Fraction(4, 9)) and (Q == 0)
    res["C0"] = {"F2_pi2": [str(P), str(Q)], "equals_4_9_exact": bool(ok)}
    L(json.dumps(res["C0"]))

    # ---- C1 驻点定理（精确 F'(π/2)=0 全档 + 数值对称差分） ----
    L("== C1 ==")
    c1 = {"exact_F1_zero": {}, "numerical_max": 0.0}
    for k in range(3, 12):
        num, den = delta_poly(k, 2, 20)
        c, D = F_coeffs(num)
        d1 = deriv_at_i(c, D, 1)
        c1["exact_F1_zero"]["k=%d" % k] = bool(d1 is not None and d1[0] == 0 and d1[1] == 0)
    import numpy as np
    N = 1 << 18
    tg = np.linspace(0, 2 * np.pi, N, endpoint=False)
    zeta = np.exp(2j * np.pi / 8)
    def dphi_grid(k, r, rp):
        p = (k + 1) // 2; q = k // 2
        M = (3 ** k - 3) // 8
        x = np.exp(1j * tg)
        Sc = {}
        for cc in (0, 6):
            acc = np.zeros_like(x)
            for m in range(8):
                zm = np.exp(-1j * np.pi / 4 * (m % 8))
                z3m = np.exp(-1j * np.pi / 4 * ((3 * m) % 8))
                acc += np.exp(1j * np.pi / 4 * ((m * cc) % 8)) * (1 + zm * x + zm**2 * x**2)**p * (1 + z3m * x + z3m**2 * x**2)**q
            Sc[cc] = acc / 8
        Ns0 = M + 1 if 0 in (0, 1) else M
        Ns6 = M + 1 if 6 in (0, 1) else M
        return np.abs(np.exp(1j * (r % 3) * tg) * (Sc[0] / Ns0 - Sc[6] / Ns6))
    g = dphi_grid(5, 2, 20)
    # π/2 邻域一阶对称差分（反射对称推论）
    j0 = int(round((np.pi / 2) / (2 * np.pi) * N))
    c1["numerical_max"] = float(np.max(np.abs(g[j0 + 1] - g[j0 - 1])))
    res["C1"] = c1
    L(json.dumps(c1))

    # ---- C2 精确值 k=5 vs 在档 0.279569892473 ----
    L("== C2 ==")
    num, den = delta_poly(5, 2, 20)
    c, D = F_coeffs(num)
    Fv = q_to_real(F_at_i(c))
    P = Fv[0] / (den * den); Q = Fv[1] / (den * den)
    def frac2mpf(fr):
        return mpf(fr.numerator) / mpf(fr.denominator)
    val = mpsqrt(frac2mpf(P) + frac2mpf(Q) * mpsqrt(2))
    err = abs(val - mpf("0.279569892473"))
    res["C2"] = {"F2_P": str(P), "F2_Q": str(Q), "abs_val_50d": float(val),
                 "err_vs_archive": float(err)}
    L(json.dumps(res["C2"]))

    # ---- C3 二阶符号谱 ----
    L("== C3 ==")
    rows = {}
    for k in range(3, 12):
        num, den = delta_poly(k, 2, 20)
        c, D = F_coeffs(num)
        d2 = deriv_at_i(c, D, 2)
        if d2 is None:
            rows["k=%d" % k] = "non-real (unexpected)"
            continue
        P, Q = d2[0] / (den * den), d2[1] / (den * den)
        s = sign_real((P, Q))
        rows["k=%d" % k] = {"D2_P": str(P), "D2_Q": str(Q), "sign": int(s),
                            "max_at_pi2": bool(s < 0)}
    res["C3"] = rows
    L(json.dumps(rows))
    pred_ok = all(rows["k=%d" % k]["sign"] < 0 for k in (3, 5)) and \
              all(rows["k=%d" % k]["sign"] >= 0 for k in (7, 9, 11))
    res["C3_pred"] = {"k35_negative": bool(all(rows["k=%d" % k]["sign"] < 0 for k in (3, 5))),
                      "k7_9_11_nonneg": bool(all(rows["k=%d" % k]["sign"] >= 0 for k in (7, 9, 11))),
                      "prediction_pass": bool(pred_ok)}
    L(json.dumps(res["C3_pred"]))

    res["verdict"] = {
        "C0": bool(res["C0"]["equals_4_9_exact"]),
        "C1": bool(all(c1["exact_F1_zero"].values()) and c1["numerical_max"] <= 1e-12),
        "C2": bool(err < mpf("5e-10")),
        "C3_pred": bool(pred_ok),
        "peak_proof_established": bool(res["C0"]["equals_4_9_exact"] and all(c1["exact_F1_zero"].values())
                                       and c1["numerical_max"] <= 1e-12 and err < mpf("5e-10") and pred_ok),
    }
    res["log"] = log
    L("VERDICT %s" % json.dumps(res["verdict"]))
    with open("H:/理论存档/01-数学/02-实验与数据/results/k5_peak_exact_result-v1.0-20260921.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
