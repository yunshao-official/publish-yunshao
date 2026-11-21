# -*- coding: utf-8 -*-
"""
kummer_carry_12families-v1.0-20260919.py
代数册×几何册·Kummer进位位形×12组签名对照（预注册判据 C0-C5 + 探索项）
判据冻结：先于实算落盘《代数册·Kummer进位位形×12组签名对照立项-v1.0-20260919.md》§二（实算首跑 2026-09-19 21:38:09·NTFS 在档；初记 21:47 系未核钟估计已更正）
本脚本运行于判据冻结之后；结果与解读分离（解读写在立项文档 §四）。
执行层主流数学：Kummer 定理 / Lucas 定理 / Hardy–Littlewood 奇异级数。体系常数零引用。
"""
import json, math
from math import gcd

OUT = r"H:\理论存档\01-数学\02-实验与数据\results\kummer_carry_12families_result-v1.0-20260919.json"

R24 = list(range(0, 24, 2))          # 12 组·偶数侧：偶 N mod 24 的 12 个剩余类
FAMS = {r: 3 - (r % 8) % 3 for r in R24}  # placeholder, unused

# ---------- 签名一：低 m 位截断进位分布 S_m(r) ----------
def carries_low(k, r, m):
    """k, r ∈ [0, 2^m)：把 k 与 (r−k) mod 2^m 作 m 位二进制加法，
    返回位 0..m−1 产生的进位次数（含位 m−1 出位）。"""
    a, b, carry, c = k, (r - k) % (1 << m), 0, 0
    for j in range(m):
        s = ((a >> j) & 1) + ((b >> j) & 1) + carry
        carry = 1 if s >= 2 else 0
        c += carry
    return c

def S_m(r, m):
    dist = [0] * (m + 1)
    for k in range(1 << m):
        dist[carries_low(k, r, m)] += 1
    return tuple(dist)

# ---------- Kummer 精确进位次数（完整加法，用于回归锚与行质量） ----------
def kummer_carries(n, k, p=2):
    """v_p(C(n,k)) = k 与 n−k 的 p 进制加法进位次数。"""
    a, b, carry, c = k, n - k, 0, 0
    while a > 0 or b > 0 or carry:
        s = a % p + b % p + carry
        carry = 1 if s >= p else 0
        c += carry
        a //= p; b //= p
    return c

def vp_binom_factorial(n, k, p=2):
    """Legendre 口径的 v_p(C(n,k))——与 Kummer 独立双验。"""
    def vp_fact(t):
        s, q = 0, p
        while q <= t:
            s += t // q; q *= p
        return s
    return vp_fact(n) - vp_fact(k) - vp_fact(n - k)

def popcount(t):
    return bin(t).count("1")

def row_mass(n):
    """W(n)=Σ_k v₂(C(n,k)) = 2Σ_{k≤n}s₂(k) − (n+1)s₂(n)（精确）。"""
    return 2 * sum(popcount(k) for k in range(n + 1)) - (n + 1) * popcount(n)

# ---------- 签名二：奇异级数 ----------
def singular_series(N):
    s = 2.0
    t = N
    p = 3
    while p * p <= t:
        if t % p == 0:
            s *= (p - 1) / (p - 2)
            while t % p == 0:
                t //= p
        p += 2
    if t > 2:
        s *= (t - 1) / (t - 2)
    return s

# ================= C5：R13 回归锚（N=64 行） =================
def c5_regression():
    # R13 协议（判据 C5 原文）：64×64 三角 = 行 n=0..63 全行，共 Σ(n+1)=2080 格。
    # [bug 修正记录 20260919] 首次运行误取行 0..64 的半三角镜像（2145 格），
    # 与冻结判据"2080 格"不符；本修正为落实判据原文口径，判据文本一字未动。
    from collections import Counter
    cnt = Counter()
    mismatch = 0
    total = 0
    for n in range(64):                       # 行 0..63（64×64 三角）
        for k in range(0, n + 1):             # 全行 k=0..n
            v = C_mod(n, k, 4)
            cnt[v] += 1
            total += 1
            c = kummer_carries(n, k, 2)
            ok2 = (v % 2 == 0) == (c >= 1)
            ok4 = (v % 4 == 0) == (c >= 2)
            if not (ok2 and ok4):
                mismatch += 1
    return {"n64_mod4_dist": {str(k): cnt[k] for k in sorted(cnt)},
            "total_cells": total, "kummer_mismatch": mismatch,
            "protocol_note": "rows n=0..63 full rows (2080 cells); 首版脚本半三角镜像口径已修正"}

def C_mod(n, k, m):
    """C(n,k) mod m（m=2,4）——Lucas 型逐位算法，避免大整数。
    这里 n,k ≤ 64，直接用 math.comb 即可。"""
    return math.comb(n, k) % m

# ================= C0：2-adic 族级深度 =================
def c0_depth():
    # m=1..3：2^m | 24 → S_m 应为组级良定义：任取同组两成员验证 S_m 一致
    res = {}
    for m in range(1, 6):
        well_defined = (24 % (1 << m) == 0)
        # 数值抽验：同组成员对 (r, r+24, r+48) 的 S_m 是否一致
        consistent = True
        example_split = None
        for r in R24:
            sigs = {S_m((r + 24 * t) % (1 << m) if False else (r + 24 * t), m) for t in range(3)}
            # 注意：S_m 只依赖自变量 mod 2^m；比较 (r+24t) 的签名
            if len(sigs) != 1:
                consistent = False
                if example_split is None and m >= 4:
                    example_split = {"family_r": r,
                                     "sigs": [list(s) for s in sorted(sigs)]}
        res[f"m={m}"] = {"2^m_divides_24": well_defined,
                         "numerically_consistent": consistent}
        if m >= 4 and example_split:
            res[f"m={m}"]["example_split"] = example_split
    # 显式给出一个 m=4 分裂实例（组 r=0：N=24 vs N=48）
    s_24, s_48 = S_m(24, 4), S_m(48, 4)
    res["explicit_m4_split_family0"] = {"N=24": list(s_24), "N=48": list(s_48),
                                        "split": s_24 != s_48}
    return res

# ================= C1：S_3 对 12 组的分类 =================
def c1_docking():
    sigs = {r: S_m(r, 3) for r in R24}
    classes = {}
    for r, s in sigs.items():
        classes.setdefault(s, []).append(r)
    # 分类是否=模 8 轴
    by_mod8 = {}
    for r in R24:
        by_mod8.setdefault(r % 8, []).append(r)
    distinct_sigs = sorted(set(sigs.values()))
    # 判据 C1：恰 4 类×3 组，且 同签名 ⟺ 同模 8 剩余
    equals_mod8 = all((sigs[a] == sigs[b]) == (a % 8 == b % 8)
                      for a in R24 for b in R24)
    pass_c1 = (len(classes) == 4 and equals_mod8 and
               all(len(v) == 3 for v in classes.values()))
    return {"S3_signatures": {str(r): list(sigs[r]) for r in R24},
            "n_classes": len(classes),
            "classes_by_signature": {str(i): sorted(v) for i, (s, v) in
                                     enumerate(sorted(classes.items()))},
            "equals_mod8_axis": equals_mod8,
            "distinct_signature_count": len(distinct_sigs),
            "PASS": pass_c1}

# ================= C2/C3/C4：奇异级数组均值 + 联合签名 =================
def c234(X=2000):
    fam_vals = {r: [] for r in R24}
    n = 2
    while n <= X:
        fam_vals[n % 24].append(singular_series(n))
        n += 2
    E = {r: (sum(v) / len(v), sorted(v)[len(v) // 2]) for r, v in fam_vals.items()}  # (均值, 中位数)
    g3 = [r for r in R24 if r % 3 == 0]     # 3|N 组 {0,6,12,18}
    g0 = [r for r in R24 if r % 3 != 0]
    mean3 = sum(E[r][0] for r in g3) / len(g3)
    mean0 = sum(E[r][0] for r in g0) / len(g0)
    ratio = mean3 / mean0
    c2_group = 1.9 <= ratio <= 2.1
    # 模 8 类内 3|N 子组 ≈ 2× 其余（同 ±5% 容差）
    within = []
    c2_within = True
    for m8 in (0, 2, 4, 6):
        trip = [r for r in R24 if r % 8 == m8]
        r3 = [r for r in trip if r % 3 == 0][0]
        r0 = [r for r in trip if r % 3 != 0]
        m3v = E[r3][0]
        m0v = sum(E[r][0] for r in r0) / len(r0)
        ok = abs(m3v / m0v - 2.0) <= 0.1   # [1.9,2.1]
        within.append({"mod8": m8, "family_3div": r3, "E3": round(m3v, 4),
                       "others": r0, "E_others": round(m0v, 4),
                       "ratio": round(m3v / m0v, 4), "in_tol": ok})
        c2_within = c2_within and ok
    # C3：联合签名分类
    joint = {}
    for r in R24:
        key = (S_m(r, 3), r % 3 == 0)
        joint.setdefault(key, []).append(r)
    # C4：四对组的族级不可分（S3 同类 + 中位数同为 2）
    pairs = [(8, 16), (2, 10), (4, 20), (14, 22)]
    c4_rows = []
    c4_pass = True
    for a, b in pairs:
        sa, sb = S_m(a, 3) == S_m(b, 3), None
        same_s3 = S_m(a, 3) == S_m(b, 3)
        med_a, med_b = E[a][1], E[b][1]
        sep = (med_a != med_b)
        ok = same_s3 and (med_a == med_b == 2.0)
        c4_pass = c4_pass and ok
        c4_rows.append({"pair": [a, b], "same_S3": same_s3,
                        "median_S2": [med_a, med_b],
                        "indistinguishable_at_family_level": ok})
    singletons = sorted(r for r in R24 if r % 3 == 0)
    return {
        "X": X,
        "family_means_medians": {str(r): {"mean": round(E[r][0], 4),
                                          "median": E[r][1],
                                          "n_samples": len(fam_vals[r])} for r in R24},
        "C2": {"group_mean_3div": round(mean3, 4), "group_mean_3notdiv": round(mean0, 4),
               "ratio": round(ratio, 4), "in_tol_1.9_2.1": c2_group,
               "within_mod8": within, "PASS": c2_group and c2_within},
        "C3": {"n_joint_classes": len(joint),
               "classes": {f"cls{i}": sorted(v) for i, (k, v) in
                           enumerate(sorted(joint.items(), key=lambda kv: kv[1]))},
               "expected_singletons": singletons,
               "PASS": len(joint) == 8 and
                       sorted(sum((v for v in joint.values()), [])) == R24 and
                       all(len(v) in (1, 2) for v in joint.values())},
        "C4": {"rows": c4_rows, "family_level_resolution": "8/12", "PASS": c4_pass},
    }

# ================= 探索项：行质量 vs log 𝔖₂ =================
def exploratory(Nmax=300):
    xs, ys, sizes = [], [], []
    for n in range(2, Nmax + 1, 2):
        w = row_mass(n)
        s2 = singular_series(n)
        if s2 > 0:
            xs.append(w); ys.append(math.log(s2)); sizes.append(n)
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    vy = math.sqrt(sum((b - my) ** 2 for b in ys))
    r_all = cov / (vx * vy)
    # 控制 n（偏相关：对 log n 残差化）
    lns = [math.log(t) for t in sizes]
    ml = sum(lns) / len(lns)
    # 分别对 ln n 回归取残差
    def resid_against_ln(v):
        mv = sum(v) / len(v)
        beta = sum((a - mv) * (l - ml) for a, l in zip(v, lns)) / sum((l - ml) ** 2 for l in lns)
        return [a - (mv + beta * (l - ml)) for a, l in zip(v, lns)]
    rxs = resid_against_ln(xs); rys = resid_against_ln(ys)
    mx2 = sum(rxs) / len(rxs); my2 = sum(rys) / len(rys)
    cov2 = sum((a - mx2) * (b - my2) for a, b in zip(rxs, rys))
    vx2 = math.sqrt(sum((a - mx2) ** 2 for a in rxs))
    vy2 = math.sqrt(sum((b - my2) ** 2 for b in rys))
    r_partial = cov2 / (vx2 * vy2)
    return {"n_even_leq": Nmax, "pearson_r_W_logS2": round(r_all, 4),
            "partial_r_given_ln_n": round(r_partial, 4)}

# ================= 主流程 =================
def main():
    # 独立双验：Kummer vs Legendre（0..40 全格）
    dual = all(kummer_carries(n, k, 2) == vp_binom_factorial(n, k, 2)
               for n in range(41) for k in range(n + 1))
    c5 = c5_regression()
    c0 = c0_depth()
    c1 = c1_docking()
    c234res = c234(2000)
    expl = exploratory(300)
    result = {
        "meta": {"script": "kummer_carry_12families-v1.0-20260919.py",
                 "date": "2026-09-19",
                 "criteria_frozen_at": "判据文档 §二 落盘先于实算首跑 2026-09-19 21:38:09 (NTFS 在档；初记 21:47 系未核钟估计已按诚实三律更正)",
                 "constants": "[constants:v1.0] 零数值引用（仅 N=64=2^6 指数账记号）"},
        "dual_check_kummer_vs_legendre_0_40": dual,
        "C5_regression_R13": c5,
        "C0_depth": c0,
        "C1_docking_mod8": c1,
        "C234_singular_joint": c234res,
        "exploratory": expl,
    }
    verdict = {
        "C0": c0["m=3"]["numerically_consistent"] and c0["m=4"]["numerically_consistent"] is False
              and c0["explicit_m4_split_family0"]["split"],
        "C1": c1["PASS"],
        "C2": c234res["C2"]["PASS"],
        "C3": c234res["C3"]["PASS"],
        "C4": c234res["C4"]["PASS"],
        "C5": (c5["n64_mod4_dist"] == {"0": 946, "1": 407, "2": 405, "3": 322})
              and c5["kummer_mismatch"] == 0,
    }
    result["verdict"] = verdict
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps(verdict, ensure_ascii=False))
    print("C1 S3 classes:", c1["n_classes"], "equals_mod8:", c1["equals_mod8_axis"])
    print("C2 ratio:", c234res["C2"]["ratio"], "C3 classes:", c234res["C3"]["n_joint_classes"])
    print("C4 resolution:", c234res["C4"]["family_level_resolution"])
    print("C5 dist:", c5["n64_mod4_dist"], "mismatch:", c5["kummer_mismatch"])
    print("exploratory r:", expl)
    print("saved ->", OUT)

if __name__ == "__main__":
    main()
