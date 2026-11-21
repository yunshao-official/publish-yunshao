# -*- coding: utf-8 -*-
"""
代数册·λ层简并组次层分辨预注册判据书-v1.0-20260921 实算脚本
判据: K0-K5 (判据书 §三, 冻结文本零改动, NTFS 2026-09-21 03:14:13)
定理 K-A..K-D 机器印证: 偶k完全恒等+闭式公共值 / 奇k补数自映射分裂 / 非整齐档完全分裂 / 3^13预测
"""
import json, time, math
import numpy as np
from pathlib import Path

RES = Path("H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260921"
NMAX = 10 ** 6
PAIRS4 = {"4|16": (1, 5), "4|22": (1, 7), "10|16": (3, 5), "10|22": (3, 7)}
PAIRS12 = {"2|14": (0, 4), "4|16": (1, 5), "4|22": (1, 7), "10|16": (3, 5), "10|22": (3, 7),
           "2|8": (0, 2), "2|20": (0, 6), "8|14": (2, 4), "14|20": (4, 6),
           "8|20": (2, 6), "4|10": (1, 3), "16|22": (5, 7)}
DMAP = {"2|14": 2, "4|16": 1, "4|22": 1, "10|16": 1, "10|22": 1,
        "2|8": 2, "2|20": 2, "8|14": 2, "14|20": 2, "8|20": 2, "4|10": 1, "16|22": 1}


def enum_S_c(X):
    """直接枚举: S_c = Σ_{Q<X, Q≡c(8)} i^{s3(Q)}, i^{s3}=i^{s3 mod 4}"""
    Q = np.arange(X, dtype=np.int64)
    s3 = np.zeros(X, dtype=np.int64)
    t = Q.copy()
    while t.max() > 0:
        s3 += t % 3
        t //= 3
    c8 = Q % 8
    w = np.array([1, 1j, -1, -1j], dtype=complex)[s3 % 4]
    S = np.array([w[c8 == c].sum() for c in range(8)])
    N = np.array([int((c8 == c).sum()) for c in range(8)])
    return S, N, s3, c8


def closed_S_c(k):
    """I-D 八项闭式 (R20 更正版): S_c = (1/8) Σ_m ζ^{mc} A_m^p A_{3m mod 8}^q, t=π/2"""
    zeta = np.exp(2j * np.pi / 8)
    p, q = (k + 1) // 2, k // 2
    A = np.array([1 + (1j) * zeta ** (-m) - zeta ** (-2 * m) for m in range(8)], dtype=complex)
    Pi = np.array([A[m] ** p * A[(3 * m) % 8] ** q for m in range(8)], dtype=complex)
    S = np.array([sum(zeta ** (m * c) * Pi[m] for m in range(8)) / 8 for c in range(8)])
    return S


def dphi_direct(S, N, pair, d):
    c, cp = pair
    return (1j ** d) * (S[c] / N[c] - S[cp] / N[cp])


def main():
    t0 = time.time()
    logs = []
    res = {"meta": {"script_start": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "freeze": "判据书冻结 NTFS 2026-09-21 03:14:13"}}

    def log(m):
        logs.append(str(m))
        print(m, flush=True)

    # ============ K0 闭式自检 ============
    ok = True
    worst = 0.0
    for k in (10, 11, 12):
        Sc, Nc, _, _ = enum_S_c(3 ** k)
        Scl = closed_S_c(k)
        d = float(np.max(np.abs(Sc - Scl)))
        worst = max(worst, d / max(1.0, float(np.max(np.abs(Sc)))))
        if d > 1e-6 * max(1.0, float(np.max(np.abs(Sc)))):
            ok = False
        log(f"K0: k={k} 闭式vs枚举 最差 |ΔS_c| = {d:.3e} (相对 {d / max(1.0, float(np.max(np.abs(Sc)))):.3e})")
    K0 = bool(ok)
    res["K0"] = {"worst_rel": worst, "pass": K0}
    log(f"K0 -> {K0}")

    # ============ K1 偶 k 完全恒等 (3^12) ============
    S12, N12, _, _ = enum_S_c(3 ** 12)
    A12 = S12 / N12
    vals12 = {name: dphi_direct(S12, N12, PAIRS4[name], 1) for name in PAIRS4}
    names = list(PAIRS4)
    pw = max(abs(vals12[a] - vals12[b]) for i, a in enumerate(names) for b in names[i + 1:])
    lam2 = (1 + math.sqrt(2))
    mu2 = (math.sqrt(2) - 1)
    # 精确有理: (λ^12−μ^12) = 2·b·√2, b=13860 (Pell); |Δφ| = 2√2·2b√2/(3^12−1) = 8b/(3^12−1) = 110880/531440 = 1386/6643
    b12 = 13860
    from fractions import Fraction
    exact = Fraction(8 * b12, 3 ** 12 - 1)
    common_mod = abs(vals12["4|16"])
    err_exact = abs(common_mod - float(exact))
    r20_ref = 0.208640674
    first9 = float(f"{common_mod:.9f}") == float(f"{r20_ref:.9f}")
    mu = A12 * (1j ** (-np.arange(8)))  # μ_c = i^{-c} A_c
    mu_real_err = float(np.max(np.abs(mu.imag)))
    mu_rel = {"mu3+mu1": abs(mu[3] + mu[1]), "mu5+mu1": abs(mu[5] + mu[1]), "mu7-mu1": abs(mu[7] - mu[1])}
    K1 = bool(pw <= 1e-12 and err_exact <= 1e-12 and first9
              and mu_real_err <= 1e-12
              and all(v <= 1e-12 for v in mu_rel.values()))
    res["K1"] = {"pairwise_complex_gap": pw, "common_mod": common_mod,
                 "exact_fraction": str(exact), "err_vs_exact": err_exact,
                 "r20_ref_9digit_match": first9,
                 "mu_imag_max": mu_real_err, "mu_relations": mu_rel, "pass": K1}
    log(f"K1: 四对复数两两差 {pw:.3e}; 公共模 {common_mod:.12f} vs 精确 {exact} 差 {err_exact:.3e}; "
        f"R20 九位对照 {first9}; μ 虚部 {mu_real_err:.1e}; μ 关系 {mu_rel} -> {K1}")

    # ============ K2 奇 k 分裂 (3^11) ============
    S11, N11, _, _ = enum_S_c(3 ** 11)
    comp = float(np.max(np.abs(S11 + np.conj(S11[(2 - np.arange(8)) % 8]))))
    A11 = S11 / N11
    a37 = abs(A11[3] - A11[7])
    v11 = {name: dphi_direct(S11, N11, PAIRS4[name], 1) for name in PAIRS4}
    mods11 = {n: abs(v) for n, v in v11.items()}
    n11 = names
    gap11 = min(abs(mods11[a] - mods11[b]) for i, a in enumerate(n11) for b in n11[i + 1:])
    zero_1022 = abs(v11["10|22"])
    K2 = bool(comp <= 1e-12 and a37 <= 1e-12 and zero_1022 <= 1e-12 and gap11 >= 1e-4)
    res["K2"] = {"complement_sym_max": comp, "A3_A7_gap": a37,
                 "dphi_10_22_abs": zero_1022, "mods": mods11, "min_gap": gap11, "pass": K2}
    log(f"K2: 补数对称 {comp:.1e}; A3−A7 {a37:.1e}; |Δφ_10|22| {zero_1022:.1e}; "
        f"四值 {mods11} 最小间隔 {gap11:.4f} -> {K2}")

    # ============ K3 3^13 新档预测 (预测值·判负照记) ============
    S13, N13, _, _ = enum_S_c(3 ** 13)
    A13 = S13 / N13
    v13 = {name: dphi_direct(S13, N13, PAIRS4[name], 1) for name in PAIRS4}
    mods13 = {n: abs(v) for n, v in v13.items()}
    c1 = abs(v13["10|22"]) <= 1e-12
    n13 = names
    gap13 = min(abs(mods13[a] - mods13[b]) for i, a in enumerate(n13) for b in n13[i + 1:])
    c2 = gap13 >= 1e-4
    c3 = (mods13["4|16"] > mods13["4|22"] > mods13["10|16"] > mods13["10|22"])
    K3 = bool(c1 and c2 and c3)
    res["K3"] = {"mods_3_13": mods13, "zero_1022_ok": c1, "distinct_ok": c2,
                 "order_ok": c3, "min_gap": gap13, "pass": K3,
                 "note": "预注册预测: 10|22=0 / 四对两两不同 / 排序 4|16>4|22>10|16>10|22=0"}
    log(f"K3(3^13 预测): mods {mods13}; 零 {c1}; 两两不同 {c2} (gap {gap13:.4f}); 排序 {c3} -> {K3}")

    # ============ K4 非整齐档 ============
    # 666666: 枚举 Q<=666666
    X = 666666
    Q = np.arange(X + 1, dtype=np.int64)
    s3 = np.zeros(X + 1, dtype=np.int64)
    t = Q.copy()
    while t.max() > 0:
        s3 += t % 3
        t //= 3
    c8 = Q % 8
    w = np.array([1, 1j, -1, -1j], dtype=complex)[s3 % 4]
    S6 = np.array([w[c8 == c].sum() for c in range(8)])
    N6 = np.array([int((c8 == c).sum()) for c in range(8)])
    mu6 = (S6 / N6) * (1j ** (-np.arange(8)))
    eps = np.array([(-1) ** (c // 2) for c in range(8)])
    d12 = {}
    for name, (c, cp) in PAIRS12.items():
        d12[name] = -(eps[c] * mu6[c] - eps[cp] * mu6[cp])
    mods6 = {n: abs(v) for n, v in d12.items()}
    n4 = list(PAIRS4)
    gap6 = min(abs(mods6[a] - mods6[b]) for i, a in enumerate(n4) for b in n4[i + 1:])
    # W1 在档对照 (零重算): R20 i_feature_layer_result I6.cmp_vs_w1.detail 的 w1_on_file
    w1_pairs = {}
    try:
        r20 = json.loads((RES / "i_feature_layer_result-v1.0-20260920.json").read_text(encoding="utf-8"))
        det = r20["I6"]["cmp_vs_w1"]["detail"]
        for name in PAIRS4:
            w1_pairs[name] = det[name]["w1_on_file"]
        w1_match = {"w1_on_file": w1_pairs,
                    "round4_match": all(abs(round(mods6[n], 4) - w1_pairs[n]) <= 6e-5 for n in PAIRS4)}
    except Exception as e:
        w1_match = {"error": str(e)}
    # 10^6 新档
    S7, N7, _, _ = enum_S_c(NMAX + 1)
    v7 = {name: dphi_direct(S7, N7, PAIRS4[name], 1) for name in PAIRS4}
    mods7 = {n: abs(v) for n, v in v7.items()}
    gap7 = min(abs(mods7[a] - mods7[b]) for i, a in enumerate(n4) for b in n4[i + 1:])
    K4 = bool(gap6 >= 1e-3 and gap7 >= 1e-3)
    res["K4"] = {"mods_666666": mods6, "dphi_12pairs_666666": {k: str(v) for k, v in d12.items()},
                 "min_gap_666666": gap6, "mods_1e6": mods7, "min_gap_1e6": gap7,
                 "w1_ref_lookup": w1_match, "pass": K4}
    log(f"K4: 666666 四对 {mods6} 间隔 {gap6:.4f}; 10^6 四对 {mods7} 间隔 {gap7:.4f} -> {K4}")

    # ============ K5 总裁决 ============
    struct = K0 and K1 and K2 and K4
    res["verdict"] = {"structure_pass": bool(struct),
                      "K3_prediction": ("通过" if K3 else "判负照记"),
                      "final": ("λ 层简并组次层分辨成立【复算一致】: K-A 偶k不可分辨定理(复数级精确简并+闭式 "
                                "2√2(λ^k−μ^k)/(3^k−1)) + K-B 奇k补数自映射分裂(A₃=A₇, 10|22 精确零) + "
                                "K-C 非整齐完全分裂 + K-D 分辨率阶梯" if struct else "如实入账(见分项, 判负照记)")}
    log(f"K5 总裁决: {res['verdict']['final']} (K3 预测: {res['verdict']['K3_prediction']})")
    res["log"] = logs
    res["elapsed_sec"] = round(time.time() - t0, 1)
    (RES / f"lambda_degeneracy_resolution_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time() - t0:.1f}s）")


if __name__ == "__main__":
    main()
