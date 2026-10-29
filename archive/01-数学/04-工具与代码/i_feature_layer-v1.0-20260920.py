# -*- coding: utf-8 -*-
"""
代数册·i特征层·代数分解与商类谱闭式预注册判据书-v1.0-20260920 实算脚本
判据: I0-I7 (判据书 §三, 冻结文本零改动, NTFS 2026-09-20 05:54:03)
核心: i^{s3}=i^Q(-1)^β 代数分解; A_c=i^c·μ_c 实结构; M(π/2) 实谱闭式;
      商类 i 特征量八项谱闭式; 衰减律/干净档排序(预测值判负照记)
"""
import json, math, time, itertools
import numpy as np
from pathlib import Path

RES = Path("H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
ZETA = complex(math.cos(2 * math.pi / 8), math.sin(2 * math.pi / 8))
PAIRS12 = [(2, 8), (2, 14), (2, 20), (8, 14), (8, 20), (14, 20),
           (4, 10), (4, 16), (4, 22), (10, 16), (10, 22), (16, 22)]
ZERO_PAIRS = {(8, 20), (4, 10), (16, 22)}      # 零主项三对 (推论 I-D.3)
TOP4 = {(2, 14), (4, 16), (4, 22), (10, 16)}   # P-i1 top-4
NONZERO9 = [p for p in PAIRS12 if p not in ZERO_PAIRS]
RHO_STAR = (3 + 2 * math.sqrt(2)) / 9          # ≈0.64760
KEY = lambda pr: f"{pr[0]}|{pr[1]}"


def c_of(r):
    d = r % 3
    return ((r - d) // 3) % 8


def s3_beta(n):
    """(s3, beta): 三进制数字和与奇位(j奇)数字和"""
    s = b = j = 0
    while n > 0:
        d = n % 3
        s += d
        if j % 2 == 1:
            b += d
        n //= 3
        j += 1
    return s, b


def build_M(t):
    """R19 V 系在档口径: M(t)(c,c')=e^{it((c-3c') mod 8)}·1_{∈{0,1,2}}"""
    return np.array([[complex(math.cos(t * ((c - 3 * cp) % 8)), math.sin(t * ((c - 3 * cp) % 8)))
                      if (c - 3 * cp) % 8 in (0, 1, 2) else 0j
                      for cp in range(8)] for c in range(8)], dtype=complex)


def hist_all_class(xmax):
    """一次遍历 Q<=xmax: 返回 H[8] (s3 直方图 per 商类) 与 N[8]"""
    H = [dict() for _ in range(8)]
    for Q in range(xmax + 1):
        s = s3_beta(Q)[0]
        c = Q % 8
        H[c][s] = H[c].get(s, 0) + 1
    return H, [sum(h.values()) for h in H]


def A_c_of(H, N, c):
    return sum(cnt * 1j ** s for s, cnt in H[c].items()) / N[c]


def dphi_pair(H, N, r, rp):
    c, cp = c_of(r), c_of(rp)
    return (1j ** (r % 3)) * A_c_of(H, N, c) - (1j ** (rp % 3)) * A_c_of(H, N, cp)


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    logs = [f"首跑时间 {first_run}"]
    res = {"meta": {"first_run": first_run,
                    "freeze": "判据书冻结 NTFS 2026-09-20 05:54:03 (§四 回填)"}}

    def log(m):
        logs.append(str(m)); print(m, flush=True)

    # ============ I0 代数分解恒等式 (Q<=1e5, 离散标签零容差) ============
    bad = 0
    for Q in range(100001):
        s, b = s3_beta(Q)
        lab1 = s % 4                      # i^{s3} 相位标签
        if lab1 != (Q + 2 * b) % 4:       # i^Q(-1)^β = i^{Q+2β}
            bad += 1
        if lab1 != (Q % 8 + 2 * b) % 4:   # i^c(-1)^β, c=Q mod 8
            bad += 1
    I0 = bool(bad == 0)
    res["I0"] = {"violations": bad, "checks": 200010, "pass": I0}
    log(f"I0 代数分解恒等式: 违反 {bad}/200010 检验 -> {I0}")

    # ============ 666666 档直方图 + A/μ ============
    H66, N66 = hist_all_class(666666)
    A66 = [A_c_of(H66, N66, c) for c in range(8)]
    mu66 = [A66[c] / (1j ** c) for c in range(8)]
    dp12 = {KEY(pr): dphi_pair(H66, N66, *pr) for pr in PAIRS12}

    # ============ I1 商类实结构 ============
    struct_err = max(abs(A66[c].imag) if c % 2 == 0 else abs(A66[c].real) for c in range(8))
    dphi_im = max(abs(v.imag) for v in dp12.values())
    eps = [(-1) ** (c // 2) for c in range(8)]
    clo_err = max(abs(-(eps[c_of(r)] * mu66[c_of(r)] - eps[c_of(rp)] * mu66[c_of(rp)])
                      - dp12[KEY((r, rp))].real) for r, rp in PAIRS12)
    I1 = bool(struct_err <= 1e-12 and dphi_im <= 1e-12 and clo_err <= 1e-12)
    res["I1"] = {"A_structure_err": struct_err, "dphi_imag_err": dphi_im,
                 "closure_err": clo_err,
                 "A66": [f"{v.real:+.12f}{v.imag:+.12f}j" for v in A66],
                 "mu66_66": [round(v.real, 12) for v in mu66],
                 "dphi_pi2_66": {k: round(v.real, 9) for k, v in dp12.items()},
                 "pass": I1}
    log(f"I1 实结构: A结构 {struct_err:.2e} / Δφ虚部 {dphi_im:.2e} / 闭式差 {clo_err:.2e} -> {I1}")

    # ============ I2 M(π/2) 实谱闭式 ============
    sq2 = math.sqrt(2)
    # A 因子闭式表 (按 j=0..7 序; 判据书定理 I-C)
    A_factors = [1j,
                 (1 + sq2 / 2) * (1 + 1j),
                 3.0 + 0j,
                 (1 + sq2 / 2) * (1 - 1j),
                 -1j,
                 (1 - sq2 / 2) * (1 + 1j),
                 1.0 + 0j,
                 (1 - sq2 / 2) * (1 - 1j)]
    fac_err = 0.0
    for j in range(8):
        v = 1.0 + 1j * (ZETA ** (-j)) - (ZETA ** (-2 * j))
        fac_err = max(fac_err, abs(v - A_factors[j]))
    Mp2 = build_M(math.pi / 2)
    ev = list(np.linalg.eigvals(Mp2))
    closed_spec = [1 + sq2, -(1 + sq2), math.sqrt(3), -math.sqrt(3),
                   sq2 - 1, 1 - sq2, 1j, -1j]
    best = min(max(abs(ev[k] - closed_spec[p[k]]) for k in range(8))
               for p in itertools.permutations(range(8)))
    I2 = bool(fac_err <= 1e-12 and best <= 1e-10)
    res["I2"] = {"A_factor_err": fac_err, "spec_match_err": best,
                 "eigvals": [f"{v.real:+.10f}{v.imag:+.10f}j" for v in ev],
                 "pass": I2}
    log(f"I2 M(π/2) 谱: 因子 {fac_err:.2e} / 特征值匹配 {best:.2e} -> {I2}")

    # ============ 八项谱闭式与干净档直方图 ============
    AM = [1.0 + 1j * (ZETA ** (-m)) - (ZETA ** (-2 * m)) for m in range(8)]

    def S_closed(k):
        # 修正后公式 (首跑拦截更正): S_c=(1/8)Σ_m ζ^{+mc}A_m^p A_{3m}^q
        p, q = (k + 1) // 2, k // 2
        Pi = [(AM[m] ** p) * (AM[(3 * m) % 8] ** q) for m in range(8)]
        return [sum((ZETA ** ((m * c) % 8)) * Pi[m] for m in range(8)) / 8 for c in range(8)]

    def N_c(k, c):
        total = 3 ** k
        return total // 8 + (1 if c < total % 8 else 0)

    clean = {}   # k -> (H, N) 直方图口径 (一次枚举, I3/I4/I5/I6 共用)
    for k in (8, 10, 11, 12):
        H = [dict() for _ in range(8)]
        for Q in range(3 ** k):
            s = s3_beta(Q)[0]
            c = Q % 8
            H[c][s] = H[c].get(s, 0) + 1
        clean[k] = (H, [sum(h.values()) for h in H])

    # ============ I3 八项谱闭式 vs 直接枚举 ============
    k_detail = {}
    for k in (2, 4, 6, 8, 10, 12):
        sc = S_closed(k)
        if k in clean:
            H, N = clean[k]
            se = [sum(cnt * 1j ** s for s, cnt in H[c].items()) for c in range(8)]
        else:
            se = [0j] * 8
            for Q in range(3 ** k):
                s = s3_beta(Q)[0]
                se[Q % 8] += 1j ** s
        k_detail[f"k{k}"] = max(abs(sc[c] - se[c]) for c in range(8))
    nc_ok = all(N_c(k, c) == clean[k][1][c] for k in (8, 10, 11, 12) for c in range(8))
    abs_small = max(v for kk, v in k_detail.items() if kk != "k12")
    rel12 = k_detail["k12"] / max(1.0, max(abs(S_closed(12)[c]) for c in range(8)))
    I3 = bool(abs_small <= 1e-10 and rel12 <= 1e-8 and nc_ok)
    res["I3"] = {"k_detail_abs": {kk: f"{v:.3e}" for kk, v in k_detail.items()},
                 "abs_err_k2_10": abs_small, "rel_err_k12": rel12,
                 "N_c_integer_ok": nc_ok, "pass": I3}
    log(f"I3 八项闭式: k2-10 绝对 {abs_small:.2e} / k12 相对 {rel12:.2e} / N_c 整型 {nc_ok} -> {I3}")

    # ============ I4 衰减律 (9 个非零主项对) ============
    d = {k: {KEY(pr): dphi_pair(*clean[k], *pr) for pr in PAIRS12} for k in (8, 10, 11, 12)}
    det4, n4 = {}, 0
    for pr in NONZERO9:
        key = KEY(pr)
        r12 = abs(d[12][key]) / abs(d[10][key])
        r08 = abs(d[10][key]) / abs(d[8][key])
        ok = (RHO_STAR - 0.05 <= r12 <= RHO_STAR + 0.05
              and abs(r12 - RHO_STAR) < abs(r08 - RHO_STAR))
        det4[key] = {"rho_10_12": round(r12, 6), "rho_8_10": round(r08, 6), "ok": bool(ok)}
        n4 += int(ok)
    I4 = bool(n4 == 9)
    res["I4"] = {"rho_star": RHO_STAR, "detail": det4, "pass_count": n4, "pass": I4,
                 "note": "预测值判据(判负照记)"}
    log(f"I4 衰减律: {n4}/9 对 ∈ ρ*±0.05 且单调逼近 -> {'通过' if I4 else '判负照记'}")

    # ============ I5 干净档排序预言 (X=3^12-1) ============
    order = sorted(PAIRS12, key=lambda pr: abs(d[12][KEY(pr)]))
    bottom3 = set(order[:3])
    top4 = set(order[-4:])
    z820 = abs(d[12]["8|20"])
    c1, c2, c3 = bottom3 == ZERO_PAIRS, top4 == TOP4, z820 <= 1e-12
    I5 = bool(c1 and c2 and c3)
    res["I5"] = {"bottom3": sorted(KEY(x) for x in bottom3),
                 "top4": sorted(KEY(x) for x in top4),
                 "zero_8_20": z820,
                 "cond": {"bottom3_ok": bool(c1), "top4_ok": bool(c2), "zero_ok": bool(c3)},
                 "full_order_asc": [KEY(x) for x in order],
                 "values_3_12": {KEY(pr): round(abs(d[12][KEY(pr)]), 9) for pr in PAIRS12},
                 "pass": I5, "note": "预测值判据(判负照记)"}
    log(f"I5 干净档排序: bottom3 {'=' if c1 else '≠'}{sorted(KEY(x) for x in bottom3)} / "
        f"top4 {'=' if c2 else '≠'}{sorted(KEY(x) for x in top4)} / 8|20={z820:.2e} -> "
        f"{'通过' if I5 else '判负照记'}")

    # ============ I6 记录项 ============
    w1 = json.loads((RES / "distribution_profile_result-v1.0-20260920.json").read_text(
        encoding="utf-8"))["W1"]["detail"]
    cmp66, worst = {}, 0.0
    for pr in PAIRS12:
        key = KEY(pr)
        v, w = abs(dp12[key]), w1[key]["max_abs"]
        worst = max(worst, abs(v - w))
        cmp66[key] = {"w1_on_file": w, "this_round": round(v, 6)}
    c66 = worst <= 5e-6  # W1 落盘 6 位舍入口径
    NT = 3600
    sym_err = 0.0
    argmax_info = {}
    for r, rp in PAIRS12:
        c, cp = c_of(r), c_of(rp)
        dd, dp2 = r % 3, rp % 3
        prof = []
        for kk in range(NT):
            t = 2 * math.pi * kk / NT
            z1 = sum(v * complex(math.cos(t * s), math.sin(t * s)) for s, v in H66[c].items()) / N66[c]
            z2 = sum(v * complex(math.cos(t * s), math.sin(t * s)) for s, v in H66[cp].items()) / N66[cp]
            prof.append(abs((1j ** dd) * z1 - (1j ** dp2) * z2))
        for kk in range(NT):
            sym_err = max(sym_err, abs(prof[kk] - prof[(NT - kk) % NT]))
        mx = max(prof)
        idx = [kk for kk in range(NT) if abs(prof[kk] - mx) < 1e-12]
        argmax_info[KEY((r, rp))] = {
            "n_argmax": len(idx),
            "positions_over_pi": sorted(round(2 * math.pi * kk / NT / math.pi, 6) for kk in idx)}
    odd_820 = abs(d[11]["8|20"])
    I6 = {"cmp_vs_w1": {"worst_diff": worst, "ok_6digit": bool(c66), "detail": cmp66},
          "symmetry_err": sym_err,
          "argmax": argmax_info,
          "k_odd_8_20_at_3_11_minus1": odd_820,
          "mu_table_66": [round(v.real, 9) for v in mu66],
          "note": "记录项(无裁决效力); W1'恒在0.25'实现层口径=np.argmax 首个最大"}
    res["I6"] = I6
    log(f"I6 记录: W1 对照 worst={worst:.2e}({c66}) / 对称 {sym_err:.2e} / k奇 8|20={odd_820:.6f}")
    log(f"   argmax 示例 2|14: {argmax_info['2|14']}")

    # ============ I7 总裁决 ============
    struct = I0 and I1 and I2 and I3
    res["verdict"] = {
        "structure_pass": bool(struct),
        "prediction_I4_pass": bool(I4), "prediction_I5_pass": bool(I5),
        "final": ("i特征层定理化成立【复算一致】: i^{s3}代数分解(I-A)+商类实结构(I-B)+M(π/2)实谱闭式(I-C)+八项谱闭式(I-D); 零主项三对=W1 bottom-3 层析定理解释" if struct
                  else "如实入账(见分项, 判负照记)")}
    log(f"I7 总裁决: {res['verdict']['final']}")
    res["log"] = logs
    (RES / f"i_feature_layer_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time() - t0:.1f}s）")


if __name__ == "__main__":
    main()
