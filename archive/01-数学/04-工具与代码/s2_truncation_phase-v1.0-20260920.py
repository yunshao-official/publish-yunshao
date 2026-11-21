# -*- coding: utf-8 -*-
"""
代数册·s₂偏置截断相位线性表示预注册判据书-v1.0-20260920 实算脚本
判据: Z0-Z3 (判据书 §三, 冻结文本零改动)
核心: S_c(4Z+ρ)=(M·S(Z))_c+τ(Z)·b_ρ(Z mod 3)_c 精确递推; D(4Z+ρ)=3D(Z)+τ(Z)g_ρ(Z mod 3);
      Gelfond 型显式界 |D(Y)|≤3^L−1; R17 八点轨迹复现; 例外集探索
"""
import json, time
from fractions import Fraction
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"

M = [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]  # R17 定理 S1 权循环卷积矩阵, 特征值 {3,3,0}
W = [1, -1, -1, 1]


def s2(n):
    return bin(n).count("1")


def tau(n):
    return 1 if s2(n) % 2 == 0 else -1


def b_rho(rho, m):
    """b_ρ(m)_c = Σ_{r<ρ} w_r·1_{m+r≡c (3)}"""
    b = [0, 0, 0]
    for r in range(rho):
        b[(m + r) % 3] += W[r]
    return b


def S_vec_digit(Y):
    """定理 Z-A1: base-4 数字逐位精确计算 (S(Y), τ(Y), Y mod 3)"""
    if Y == 0:
        return (0, 0, 0), 1, 0
    digits = []
    x = Y
    while x:
        digits.append(x % 4); x //= 4
    S = [0, 0, 0]; t = 1; m = 0
    for d in reversed(digits):
        newS = [sum(M[c][cp] * S[cp] for cp in range(3)) + t * b_rho(d, m)[c] for c in range(3)]
        t = t * W[d]
        m = (m + d) % 3
        S = newS
    return tuple(S), t, m


def D_digit(Y):
    """定理 Z-B: D 自治递推"""
    if Y == 0:
        return 0
    digits = []
    x = Y
    while x:
        digits.append(x % 4); x //= 4
    D = 0; t = 1; m = 0
    for d in reversed(digits):
        g = b_rho(d, m)[1] - b_rho(d, m)[2]
        D = 3 * D + t * g
        t = t * W[d]
        m = (m + d) % 3
    return D


def S_vec_enum(Y):
    """直接枚举 (整型精确)"""
    S = [0, 0, 0]
    for n in range(Y):
        S[n % 3] += (1 if s2(n) % 2 == 0 else -1)
    return tuple(S)


def n_c(Y, c):
    return (Y - c + 2) // 3


def gap(Y):
    """对称缺口 = |P_e(1)−P_e(2)| = |S₁/N₁−S₂/N₂|/2 (判据书 §一.1 冻结定义)"""
    S, _, _ = S_vec_digit(Y)
    return abs(S[1] / n_c(Y, 1) - S[2] / n_c(Y, 2)) / 2


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"首跑 {first_run}", flush=True)
    res = {"meta": {"first_run": first_run}}
    log_lines = []

    def log(m):
        log_lines.append(str(m)); print(m, flush=True)

    # ---------- Z0 递推 vs 枚举 零容差 ----------
    ok = True
    for Y in range(0, 2001):
        Se = S_vec_enum(Y)
        Sd, _, _ = S_vec_digit(Y)
        if Se != Sd:
            ok = False; log(f"Z0 失败 Y={Y}: enum {Se} vs digit {Sd}")
        Dd = D_digit(Y)
        if Dd != Sd[1] - Sd[2]:
            ok = False; log(f"Z0 D 失败 Y={Y}: D={Dd} vs {Sd[1]-Sd[2]}")
    pow_ok = all(D_digit(4 ** k) == 0 for k in range(0, 11))
    Z0 = bool(ok and pow_ok)
    res["Z0"] = {"grid_0_2000": bool(ok), "D_4k_zero": bool(pow_ok), "pass": Z0}
    log(f"Z0 递推 vs 枚举 Y=0..2000 零容差: {ok}; D(4^k)=0 k=0..10: {pow_ok} -> {Z0}")

    # ---------- Z1 R17 八点轨迹复现 ----------
    r17 = {25000: 0.0911, 50000: 0.0003, 100000: 0.0683, 150000: 0.0454,
           200000: 0.0002, 250000: 0.0003, 500000: 0.0545, 1000000: 0.0002}
    cmp_rows = {}
    worst = 0.0
    for Y, ref in r17.items():
        ours = gap(Y)
        diff = abs(ours - ref)
        worst = max(worst, diff)
        cmp_rows[str(Y)] = {"ours": round(ours, 6), "r17": ref, "diff": round(diff, 6)}
    Z1 = bool(worst <= 5e-4)
    res["Z1"] = {"rows": cmp_rows, "worst_diff": round(worst, 6), "pass": Z1}
    log(f"Z1 八点轨迹复现: 最差点差 {worst:.6f} -> {Z1}; 明细 {cmp_rows}")

    # ---------- Z2 显式界核对 ----------
    def digits4(Y):
        L = 0; x = Y
        while x:
            L += 1; x //= 4
        return max(L, 0)
    bound_ok = True
    max_ratio = 0.0
    for Y in range(1, 200001):
        D = D_digit(Y)
        if abs(D) > 3 ** digits4(Y) - 1:
            bound_ok = False; log(f"Z2 界失败 Y={Y}")
        r = abs(D) / (Y ** (0.792482500 + 0)) if Y > 1 else 0
        if r > max_ratio:
            max_ratio = r
    Z2 = bool(bound_ok)
    res["Z2"] = {"bound_ok": bool(bound_ok), "max_absD_over_Y_log4_3": round(max_ratio, 4), "pass": Z2}
    log(f"Z2 界 |D|≤3^L−1 (Y≤2e5): {bound_ok}; max|D|/Y^0.7925 = {max_ratio:.4f} -> {Z2}")

    # ---------- Z3 例外集探索 ----------
    zeros = [Y for Y in range(0, 1000001) if D_digit(Y) == 0]
    small_gap = [Y for Y in range(1, 1000001) if Y % 100 == 0 and gap(Y) < 1e-3]
    import math
    def is_2a5b(y):
        for a in range(0, 40):
            for b in range(0, 20):
                if 2 ** a * 5 ** b == y:
                    return True
        return False
    small_struct = {str(y): bool(is_2a5b(y)) for y in small_gap[:40]}
    r17_near_zero = [50000, 200000, 250000, 1000000]
    r17_check = {str(y): {"in_small_gap_sample": y % 100 == 0 and gap(y) < 1e-3, "is_2a5b": is_2a5b(y)} for y in r17_near_zero}
    res["Z3"] = {"zeros_count_le1e6": len(zeros), "zeros_first20": zeros[:20],
                 "zeros_last5": zeros[-5:] if zeros else [],
                 "small_gap_sample_100mult_count": len(small_gap),
                 "small_gap_2a5b_flag": small_struct,
                 "r17_near_zero_check": r17_check}
    log(f"Z3 例外集: |{{Y≤1e6: D=0}}|={len(zeros)}; 前20 {zeros[:20]}; 百倍数点 gap<1e-3 共 {len(small_gap)}")
    log(f"Z3 R17 四近零点核对: {r17_check}")

    res["log"] = log_lines
    (RES / f"s2_truncation_phase_result-{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
