# -*- coding: utf-8 -*-
"""
代数册·逐N高位结构G-D修订预注册判据书-v1.0-20260920 实算脚本
判据书冻结(NTFS): 2026-09-20 02:32:34 —— 本脚本首跑必须晚于该时刻
判据: W0-W6 (判据书 §三, 冻结文本零改动; 谱表初版残留值 1.0733/1.0000 已于首跑前更正, NTFS 修改时间在档)
核心: omega-特征传递矩阵 M(omega) 谱刻画 (定理 W-B) + 三档 X 同奇偶 12 对 KS 轨迹
数据源: range_analytic_s3_by_r-v1.0-20260920.npy (本轮值域效应脚本在档, 零重算)
"""
import json, math, time
import numpy as np
from pathlib import Path
from scipy import stats as st

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
OMEGA = complex(-0.5, math.sqrt(3) / 2)
ZETA = complex(math.cos(2 * math.pi / 8), math.sin(2 * math.pi / 8))

# 对组 r -> (d_r, c_r mod 8)
PAIR = {2: (2, 0), 8: (2, 2), 14: (2, 4), 20: (2, 6), 4: (1, 1), 10: (1, 3), 16: (1, 5), 22: (1, 7)}
CS_EVEN = [0, 2, 4, 6]
CS_ODD = [1, 3, 5, 7]


def build_M():
    # c ≡ 3c' + d (mod 8)  =>  d ≡ c - 3c' (mod 8)
    M = np.zeros((8, 8), dtype=complex)
    for c in range(8):
        for cp in range(8):
            d = (c - 3 * cp) % 8
            if d in (0, 1, 2):
                M[c, cp] = OMEGA ** d
    return M


def s3(n):
    s = 0
    while n > 0:
        s += n % 3; n //= 3
    return s


def enum_G(kmax):
    """直接枚举 G_c(3^k), k=0..kmax (递推: G(3Y)=M G(Y) 验证对象)"""
    out = {}
    Y = 1
    G = np.zeros(8, dtype=complex)
    G[0] = 1.0 + 0j  # Q=0: s3=0, c=0
    out[0] = G.copy()
    for k in range(1, kmax + 1):
        # 全枚举到 3^k
        Y = 3 ** k
        G = np.zeros(8, dtype=complex)
        for Q in range(Y):
            G[Q % 8] += OMEGA ** s3(Q)
        out[k] = G
    return out


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}（判据书冻结 2026-09-20 02:32:34 NTFS 在先；谱表初版残留值已于 02:33 前更正，修改时间在档）"]
    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"criterion_freeze_ntfs": "2026-09-20 02:32:34", "first_run": first_run}}

    # ---------- W0 自检锚 ----------
    M = build_M()
    row0_ok = (M[0, 0] == 1 and M[0, 5] == OMEGA and M[0, 2] == OMEGA ** 2
               and abs(M[0, 1]) == 0 and abs(M[0, 3]) == 0)
    enum = enum_G(7)
    # 矩阵递推 vs 枚举: G(3^{k}) = M @ G(3^{k-1})
    mat_ok = True
    for k in range(1, 8):
        Gm = M @ enum[k - 1]
        if not np.allclose(Gm, enum[k], atol=1e-9):
            mat_ok = False; log(f"W0 矩阵递推失败 k={k}")
    # 旁路引理抽样
    bypass_ok = all(((1 if s3(Q) % 2 == 0 else -1) == (1 if Q % 2 == 0 else -1)) for Q in range(1, 10001))
    W0 = bool(row0_ok and mat_ok and bypass_ok)
    res["W0"] = {"row0": bool(row0_ok), "matrix_recurrence": bool(mat_ok), "bypass_1e4": bool(bypass_ok), "pass": W0}
    log(f"W0 自检锚: 行0 {row0_ok} / 矩阵递推 {mat_ok} / 旁路 {bypass_ok} -> {W0}")
    if not W0:
        res["verdict"] = {"W0_fail_abort": True}
        (RES / f"gd_high_bits_result-{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    # ---------- W1 谱表核对 ----------
    eig = np.linalg.eigvals(M)
    eig_sorted = sorted(eig, key=lambda z: -abs(z))
    spec_theory = {"lambda0": 0.0, "lambda4_abs": 2.0, "rho2": 2.9318}
    lam1 = 1 + OMEGA * ZETA ** 5 + OMEGA ** 2 * ZETA ** 2
    lam2 = 1 + OMEGA * ZETA ** 10 + OMEGA ** 2 * ZETA ** 4
    lam3 = 1 + OMEGA * ZETA ** 15 + OMEGA ** 2 * ZETA ** 6
    theory_vals = [abs(lam1), abs(lam2), abs(lam3)]
    rho2_num = max(abs(e) for e in eig if abs(e - 0) > 1e-9 and abs(abs(e) - 2.0) > 1e-9)
    check0 = min(abs(e) for e in eig) < 1e-9
    check4 = any(abs(abs(e) - 2.0) < 1e-9 for e in eig)
    lam1_close = min(abs(abs(e) - abs(lam1)) for e in eig) < 1e-9
    lam2_close = min(abs(abs(e) - abs(lam2)) for e in eig) < 1e-9
    lam3_close = min(abs(abs(e) - abs(lam3)) for e in eig) < 1e-9
    W1 = bool(check0 and check4 and lam1_close and lam2_close and lam3_close
              and abs(rho2_num - spec_theory["rho2"]) <= 0.001)
    res["W1"] = {"eig_abs_sorted": [round(float(abs(e)), 6) for e in eig_sorted],
                 "rho2_numeric": float(rho2_num), "rho2_theory": 2.9318,
                 "lam1_abs": float(abs(lam1)), "lam2_abs": float(abs(lam2)), "lam3_abs": float(abs(lam3)),
                 "lambda0_zero": bool(check0), "lambda4_abs2": bool(check4), "pass": W1}
    log(f"W1 谱表: eig|.|={res['W1']['eig_abs_sorted']}; rho2={rho2_num:.6f} vs 2.9318 -> {W1}")

    # ---------- W5 精确锚 (mu_c(3^k) 矩阵 vs 枚举, k=2..7) ----------
    W5 = True
    for k in range(2, 8):
        Gm = np.linalg.matrix_power(M, k) @ np.array([1.0 + 0j] + [0j] * 7)
        if not np.allclose(Gm, enum[k], atol=1e-9):
            W5 = False; log(f"W5 失败 k={k}")
    res["W5"] = {"pass": bool(W5)}
    log(f"W5 精确锚 k=2..7: {W5}")

    # ---------- 数据加载 ----------
    s3arr = np.load(RES / f"range_analytic_s3_by_r-{TAG}.npy")
    X3 = 20_000_000
    per_r_total = {r: (X3 - r) // 24 + 1 for r in PAIR}
    d_r = {r: PAIR[r][0] for r in PAIR}

    def strip_sample(X):
        """返回 {r: 去末位 s3(Q) 数组}"""
        out = {}
        for r in PAIR:
            n_r = (X - r) // 24 + 1
            arr = s3arr[r, :n_r].astype(np.int16)
            out[r] = arr - d_r[r]
        return out

    def ks_pairs(samp):
        """同奇偶 12 对 KS: 返回 {(ca,cb): (stat, p)}"""
        rows = {}
        for grp in (CS_EVEN, CS_ODD):
            r_of = {PAIR[r][1]: r for r in PAIR}
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    ca, cb = grp[i], grp[j]
                    ra, rb = r_of[ca], r_of[cb]
                    ks = st.ks_2samp(samp[ra], samp[rb])
                    rows[f"{ra}|{rb}"] = (float(ks.statistic), float(ks.pvalue))
        return rows

    all_rows = {}
    for X in (200000, 2000000, 20000000):
        samp = strip_sample(X)
        all_rows[X] = ks_pairs(samp)
        log(f"X={X}: 12 对 KS 完成 ({time.time()-t0:.1f}s)")
    res["W2"] = {"by_X": {str(X): {k: {"stat": v[0], "p": v[1]} for k, v in all_rows[X].items()} for X in all_rows}}

    # 与 R16 在档子集对表 (@2e5: 8|14 p=0.0215, 16|22 p=0.9987)
    ref = {"8|14": 0.0215, "16|22": 0.9987}
    agree = {}
    for k, pv in ref.items():
        ours = all_rows[200000][k][1]
        agree[k] = {"r16": pv, "ours": ours, "same_order": bool((ours < 0.05) == (pv < 0.05))}
    res["W2"]["r16_ref_check"] = agree
    log(f"W2 R16 子集对表: {agree}")

    # ---------- W3 定向预测 ----------
    meds = {X: float(np.median([v[1] for v in all_rows[X].values()])) for X in all_rows}
    W3 = bool(meds[20000000] < meds[2000000] < meds[200000])
    res["W3"] = {"median_p_by_X": {str(X): meds[X] for X in sorted(meds)}, "pred": "2e7 < 2e6 < 2e5", "pass": W3}
    log(f"W3 p 值中位数: 2e5={meds[200000]:.3e}, 2e6={meds[2000000]:.3e}, 2e7={meds[20000000]:.3e} -> {W3}")

    # ---------- W4 理论排序对照 ----------
    import math as _m
    def theo_sep(key):
        ra, rb = key.split("|")
        ca, cb = PAIR[int(ra)][1], PAIR[int(rb)][1]
        return 2 * _m.sin(_m.pi * abs(ca - cb) / 8)
    stats_2e7 = [all_rows[20000000][k][0] for k in all_rows[20000000]]
    theo = [theo_sep(k) for k in all_rows[20000000]]
    sp = st.spearmanr(stats_2e7, theo)
    W4 = bool(sp.statistic >= 0.6)
    res["W4"] = {"spearman": float(sp.statistic), "p": float(sp.pvalue), "threshold": 0.6, "pass": W4}
    log(f"W4 Spearman(实测 KS stat, 理论 2sin(pi*d/8)) = {sp.statistic:.4f} -> {W4}")

    # ---------- W6 总裁决 ----------
    struct = W0 and W1 and W2 and W5
    pred_ok = W3 and W4
    res["verdict"] = {"structure_pass": bool(struct), "predictive_pass": bool(pred_ok),
                      "final": ("G-D 修订成立【复算一致】: 逐 N 高位结构=omega-特征传递矩阵谱残留(不衰减)" if (struct and pred_ok)
                                else "如实入账(见分项)")}
    log(f"W6 总裁决: {res['verdict']['final']}")
    res["log"] = log_lines
    (RES / f"gd_high_bits_result-{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
