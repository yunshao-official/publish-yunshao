# -*- coding: utf-8 -*-
"""
代数册·混合谱单项式谱定理预注册判据书-v1.0-20260920 实算脚本
判据书冻结(NTFS): 创建时刻在先; 首跑前更正 P-a 模方符号(§四 披露); 首跑时钟必须晚于判据书全部改动时刻
判据: Y0-Y7 (判据书 §三, 冻结文本零改动)
核心: M=C_f·P3 单项式分解; 循环谱公式 spec(M)={A0,A4,±√(A1A3),±√(A2A6),±√(A5A7)};
      Q(√2,√3,i) Fraction 精确域算术; 循环块闭式演化端到端
"""
import json, math, time
from fractions import Fraction
import numpy as np
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
OMEGA = complex(-0.5, math.sqrt(3) / 2)

# ============ 精确域算术: Q(√2,√3,i), 基 (1,√2,√3,√6)×(1,i), 全 Fraction ============
F0 = Fraction(0)
QZERO4 = (F0, F0, F0, F0)
QONE4 = (Fraction(1), F0, F0, F0)
ONE_C = (QONE4, QZERO4)
E8 = ((Fraction(1, 8), F0, F0, F0), QZERO4)  # 1/8 (基 (1,√2,√3,√6) 上纯有理)

def qmul(a, b):
    a0, a1, a2, a3 = a; b0, b1, b2, b3 = b
    return (a0 * b0 + 2 * a1 * b1 + 3 * a2 * b2 + 6 * a3 * b3,
            a0 * b1 + a1 * b0 + 3 * a2 * b3 + 3 * a3 * b2,
            a0 * b2 + a2 * b0 + 2 * a1 * b3 + 2 * a3 * b1,
            a0 * b3 + a3 * b0 + a1 * b2 + a2 * b1)

def qadd(a, b):
    return tuple(x + y for x, y in zip(a, b))

def qscale(s, a):
    return tuple(s * x for x in a)

def cmul(z, w):
    zr, zi = z; wr, wi = w
    return (qadd(qmul(zr, wr), qscale(Fraction(-1), qmul(zi, wi))),
            qadd(qmul(zr, wi), qmul(zi, wr)))

def cadd(z, w):
    return (qadd(z[0], w[0]), qadd(z[1], w[1]))

def cconj(z):
    return (z[0], tuple(-x for x in z[1]))

def cabs2(z):
    """|z|^2 精确, 返回 Q(√2,√3) 实元素; 断言虚部恒零"""
    t = cmul(z, cconj(z))
    assert all(v == 0 for v in t[1]), "模方虚部非零"
    return t[0]

def qval(a):
    return float(a[0]) + float(a[1]) * math.sqrt(2) + float(a[2]) * math.sqrt(3) + float(a[3]) * math.sqrt(6)

def qstr(a):
    parts = [f"{float(x):.6f}*{b}" for x, b in zip(a, ("1", "√2", "√3", "√6")) if x != 0]
    return " + ".join(parts) if parts else "0"

def ctofloat(z):
    re = qval(z[0]); im = qval(z[1])
    return complex(re, im)

ZETA = ((F0, Fraction(1, 2), F0, F0), (F0, Fraction(1, 2), F0, F0))                        # ζ=e^{iπ/4}=√2/2+i√2/2
OMEGA_E = ((Fraction(-1, 2), F0, F0, F0), (F0, F0, Fraction(1, 2), F0))                    # ω
OMEGA2_E = ((Fraction(-1, 2), F0, F0, F0), (F0, F0, Fraction(-1, 2), F0))                  # ω²

def zeta_pow(n):
    if n == 0:
        return ONE_C
    e = ONE_C
    base = ZETA if n > 0 else cconj(ZETA)
    for _ in range(abs(n)):
        e = cmul(e, base)
    return e

def A_exact(j):
    """A_j = 1 + ω ζ^{-j} + ω² ζ^{-2j} 精确"""
    return cadd(cadd(ONE_C, cmul(OMEGA_E, zeta_pow(-j))), cmul(OMEGA2_E, zeta_pow(-2 * j)))

def fpow(e, n):
    r = ONE_C
    for _ in range(n):
        r = cmul(r, e)
    return r

# ============ 矩阵构造 ============

def build_M():
    """本脚本按判据书 §一.1 冻结定义独立实现"""
    M = np.zeros((8, 8), dtype=complex)
    for c in range(8):
        for cp in range(8):
            d = (c - 3 * cp) % 8
            if d in (0, 1, 2):
                M[c, cp] = OMEGA ** d
    return M

def build_CF():
    C = np.zeros((8, 8), dtype=complex)
    for c in range(8):
        for u in range(8):
            d = (c - u) % 8
            if d in (0, 1, 2):
                C[c, u] = OMEGA ** d
    return C

def build_P3():
    P = np.zeros((8, 8), dtype=complex)
    for u in range(8):
        P[u, (3 * u) % 8] = 1.0
    return P

def s3(n):
    s = 0
    while n > 0:
        s += n % 3; n //= 3
    return s

def enum_G(kmax):
    out = {}
    for k in range(0, kmax + 1):
        Y = 3 ** k
        G = np.zeros(8, dtype=complex)
        for Q in range(Y):
            G[Q % 8] += OMEGA ** s3(Q)
        out[k] = G
    return out

def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}"]

    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"first_run": first_run,
                    "freeze_note": "判据书创建+首跑前P-a更正时刻以 NTFS 为准（§四 回填）"}}

    Aex = [A_exact(j) for j in range(8)]
    Af = [ctofloat(a) for a in Aex]

    # ---------- Y0 自检锚 ----------
    M = build_M()
    diff_decomp = float(np.max(np.abs(M - build_CF() @ build_P3())))
    enum = enum_G(6)
    mat_ok = all(np.allclose(M @ enum[k - 1], enum[k], atol=1e-9) for k in range(1, 7))
    trace_M = complex(np.trace(M))
    rowsum_max = float(np.max(np.abs(M @ np.ones(8, dtype=complex))))
    Y0 = bool(diff_decomp <= 1e-15 and mat_ok and abs(trace_M - (Af[0] + Af[4])) <= 1e-12 and rowsum_max <= 1e-12)
    res["Y0"] = {"diff_CF_P3": diff_decomp, "matrix_recursion": bool(mat_ok),
                 "trace_abs": abs(trace_M),
                 "trace_pred": {"re": float((Af[0] + Af[4]).real), "im": float((Af[0] + Af[4]).imag)},
                 "rowsum_max": rowsum_max, "pass": Y0}
    log(f"Y0 自检锚: C_f·P3 {diff_decomp:.2e} / 递推 {mat_ok} / trace {trace_M} vs {Af[0]+Af[4]:.6f} / 行和 {rowsum_max:.2e} -> {Y0}")

    # ---------- Y1 Fourier 单项式型 ----------
    Fm = np.array([[complex(math.cos(2 * math.pi * j * c / 8), math.sin(2 * math.pi * j * c / 8))
                    for j in range(8)] for c in range(8)], dtype=complex)
    Finv = Fm.conj().T / 8
    Mhat = np.zeros((8, 8), dtype=complex)
    for j in range(8):
        Mhat[j, (3 * j) % 8] = Af[j]
    diff_four = float(np.max(np.abs(Fm @ Mhat @ Finv - M)))
    Y1 = bool(diff_four <= 1e-12)
    res["Y1"] = {"diff_Finv_Mhat_F_vs_M": diff_four, "pass": Y1}
    log(f"Y1 Fourier 单项式型: max|F·M̂·F⁻¹−M| = {diff_four:.3e} -> {Y1}")

    # ---------- Y2 循环谱公式 ----------
    eig = np.linalg.eigvals(M)

    def csqrt(z):
        return complex(z) ** 0.5

    pred = [Af[0], Af[4],
            csqrt(Af[1] * Af[3]), -csqrt(Af[1] * Af[3]),
            csqrt(Af[2] * Af[6]), -csqrt(Af[2] * Af[6]),
            csqrt(Af[5] * Af[7]), -csqrt(Af[5] * Af[7])]
    remaining = list(eig)
    worst = 0.0
    for p in pred:
        d = [abs(p - e) for e in remaining]
        i = int(np.argmin(d))
        worst = max(worst, d[i]); remaining.pop(i)
    abs_sorted = sorted((abs(e) for e in eig), reverse=True)
    pred_abs_sorted = sorted((abs(p) for p in pred), reverse=True)
    shape_diff = max(abs(a - b) for a, b in zip(abs_sorted, pred_abs_sorted))
    r17_ref = [2.109381, 2.109381, 2.000000, 1.414214, 1.414214, 0.670440, 0.670440, 0.000000]
    r17_diff = max(abs(a - b) for a, b in zip(abs_sorted, r17_ref))
    Y2 = bool(worst <= 1e-9 and shape_diff <= 1e-9 and r17_diff <= 1e-6)
    res["Y2"] = {"match_max_dist": worst, "shape_diff": shape_diff, "r17_table_diff": r17_diff,
                 "eig_abs_sorted": [round(float(x), 9) for x in abs_sorted], "pass": Y2}
    log(f"Y2 循环谱公式: 配对 {worst:.3e} / 形状 {shape_diff:.3e} / R17对表 {r17_diff:.3e} -> {Y2}")

    # ---------- Y3 精确 |λ|⁴ 域算术 (cabs2(A_jA_3j) = |λ|⁴/对) ----------
    pairs = [(1, 3), (2, 6), (5, 7)]
    exact_abs2 = {}
    for a, b in pairs:
        exact_abs2[f"{a}{b}"] = cabs2(cmul(Aex[a], Aex[b]))
    all8_exact = []
    for k_ in exact_abs2:
        all8_exact += [qval(exact_abs2[k_])] * 2
    all8_exact += [16.0, 0.0]  # |A4|⁴=16, |A0|⁴=0
    all8_exact.sort(reverse=True)
    numpy_abs4 = sorted((float(abs(e) ** 4) for e in eig), reverse=True)
    diff_y3 = max(abs(x - y) for x, y in zip(numpy_abs4, all8_exact))
    Y3 = bool(diff_y3 <= 1e-9)
    res["Y3"] = {"exact_abs2": {k_: {"num": qval(exact_abs2[k_]), "surds": qstr(exact_abs2[k_]),
                                     "coeffs": [str(x) for x in exact_abs2[k_]]} for k_ in exact_abs2},
                 "A_exact_surds": {f"A{j}": qstr(Aex[j][0]) + " | i(" + qstr(Aex[j][1]) + ")" for j in range(8)},
                 "diff_full": diff_y3, "pass": Y3}
    log(f"Y3 精确域算术: 全8对表 {diff_y3:.3e}; " +
        "; ".join(f"|A{a}A{b}|²={qstr(exact_abs2[f'{a}{b}'])}={qval(exact_abs2[f'{a}{b}']):.9f}" for a, b in pairs))
    log(f"Y3 -> {Y3}")

    # ---------- Y4 预测一 (精确恒等式, 判负照记) ----------
    CABS_TARGET = sorted([(Fraction(10), F0, F0, Fraction(4)),   # (2+√6)² = 10+4√6
                          (Fraction(4), F0, F0, F0),              # 2²
                          (Fraction(10), F0, F0, Fraction(-4))],  # (√6−2)² = 10−4√6
                         key=qval)
    vals_sorted = sorted(exact_abs2.values(), key=qval)
    pa_ok = all(x == y for x, y in zip(vals_sorted, CABS_TARGET))
    prod = qmul(exact_abs2["13"], exact_abs2["57"])
    pb_ok = (prod == (Fraction(4), F0, F0, F0))
    Y4 = bool(pa_ok and pb_ok)
    res["Y4"] = {"Pa_multiset_exact": bool(pa_ok), "Pb_pairing_exact": bool(pb_ok),
                 "prod_13_57_surds": qstr(prod), "pass": Y4}
    log(f"Y4 预测一: P-a 多重集 {pa_ok} / P-b 配对恒等式 {pb_ok} (积={qstr(prod)}) -> {Y4}")

    # ---------- Y5 预测二 (幂次对齐判别, 判负照记口径) ----------
    def is_pow2_family(cabs2v):
        """等价精确口径: 模值∈{2^k, 2^k√2} ⟺ cabs2∈{4^k, 2·4^k} (纯有理幂, 无 surd 分量)"""
        if any(x != 0 for x in cabs2v[1:]):
            return False
        v = cabs2v[0]
        for k in range(-9, 10):
            p = Fraction(4) ** k if k >= 0 else Fraction(1, 4 ** (-k))
            if v == p or v == 2 * p:
                return True
        return False
    align = {f"{a}{b}": is_pow2_family(exact_abs2[f"{a}{b}"]) for a, b in pairs}
    Y5 = not any(align.values())  # 预期全否
    res["Y5"] = {"align_tests": align,
                 "verdict": ("三者皆非 2 的分数幂（'与 2 的分数幂对齐'判负=近似巧合; 精确闭式=surd 结构 10±4√6）" if Y5
                             else "存在精确 2 的分数幂恒等（对齐部分成立, 如实记录）"),
                 "pass": bool(Y5)}
    log(f"Y5 幂次对齐判别: {align} -> 判据通过口径(全否=对齐判负) {Y5}")

    # ---------- Y6 谱闭式演化端到端 ----------
    Y6 = True
    for k in range(1, 7):
        Ghat = {}
        Ghat[0] = (QZERO4, QZERO4)                      # A0=0, k≥1
        Ghat[4] = cmul(fpow(Aex[4], k), E8)             # A4^k / 8
        for a, b in pairs:
            Pab = cmul(Aex[a], Aex[b])
            if k % 2 == 0:
                h = fpow(Pab, k // 2)
                Ghat[a] = cmul(h, E8); Ghat[b] = cmul(h, E8)
            else:
                h = fpow(Pab, (k - 1) // 2)
                Ghat[a] = cmul(cmul(Aex[a], h), E8)
                Ghat[b] = cmul(cmul(Aex[b], h), E8)
        for c in range(8):
            acc = (QZERO4, QZERO4)
            for j in range(8):
                acc = cadd(acc, cmul(Ghat[j], zeta_pow(j * c)))
            diff = abs(ctofloat(acc) - enum[k][c])
            if diff > 1e-9:
                Y6 = False; log(f"Y6 失败 k={k} c={c} diff={diff:.3e}")
    res["Y6"] = {"pass": bool(Y6), "kmax": 6}
    log(f"Y6 谱闭式演化端到端 k=1..6 -> {Y6}")

    # ---------- Y7 总裁决 + P-d 报告口径 ----------
    struct = Y0 and Y1 and Y2 and Y3 and Y6
    rho = max(abs(e) for e in eig)
    expo = math.log(rho, 3) - 1
    expo_pred = 0.5 * math.log(2 + math.sqrt(6), 3) - 1
    res["Pd_report"] = {"rho_numeric": float(rho), "rho_pred_sqrt2p6": math.sqrt(2 + math.sqrt(6)),
                        "exponent_numeric": expo, "exponent_pred": expo_pred,
                        "r17_rho": 2.1093813649464086, "r17_quoted_exponent": -0.317,
                        "r17_quote_diff": abs(expo - (-0.317))}
    res["verdict"] = {"structure_pass": bool(struct), "prediction_Y4_pass": bool(Y4), "prediction_Y5_pass": bool(Y5),
                      "final": ("混合谱单项式谱定理成立【复算一致】: G-D 机制谱层收口" if struct
                                else "如实入账(见分项, 判负照记)")}
    log(f"Y7 总裁决: {res['verdict']['final']}")
    log(f"P-d: ρ={rho:.9f} vs √(2+√6)={math.sqrt(2+math.sqrt(6)):.9f}; 指数 {expo:.6f} vs 预测 {expo_pred:.6f} vs R17引用 −0.317 (差 {abs(expo+0.317):.6f})")
    res["log"] = log_lines
    (RES / f"mixed_spectrum_result-{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
