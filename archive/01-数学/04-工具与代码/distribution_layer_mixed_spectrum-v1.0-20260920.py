# -*- coding: utf-8 -*-
"""
代数册·分布层混合谱·特征函数循环块分解预注册判据书-v1.0-20260920 实算脚本
判据: V0-V7 (判据书 §三, 冻结文本零改动; V3③ 更正在首跑前已披露 §四)
核心: M(t) 一般 t 单项式谱定理; 12组商类映射同循环归属; 3^k 档理论分布;
      理论 KS vs W2@2e6 实测对表(预测值判负照记); 慢模幅度表; P-e 域内精确判定
"""
import json, math, time
from fractions import Fraction
import numpy as np
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
OMEGA = complex(-0.5, math.sqrt(3) / 2)

# ============ 精确 surd 域算术 Q(√2,√3,√6) 全 Fraction (R18 Y3 同套) ============
F0 = Fraction(0)

def qmul(a, b):
    a0, a1, a2, a3 = a; b0, b1, b2, b3 = b
    return (a0*b0 + 2*a1*b1 + 3*a2*b2 + 6*a3*b3,
            a0*b1 + a1*b0 + 3*a2*b3 + 3*a3*b2,
            a0*b2 + a2*b0 + 2*a1*b3 + 2*a3*b1,
            a0*b3 + a3*b0 + a1*b2 + a2*b1)

def qstr(a):
    parts = [f"{float(x):.6f}*{b}" for x, b in zip(a, ("1", "√2", "√3", "√6")) if x != 0]
    return " + ".join(parts) if parts else "0"

# ============ 矩阵实现 ============

def build_M_ref():
    """实现A: R18 gd_high_bits_spectrum-v1.0-20260920.py build_M 逐字引用(在档口径)"""
    M = np.zeros((8, 8), dtype=complex)
    for c in range(8):
        for cp in range(8):
            d = (c - 3 * cp) % 8
            if d in (0, 1, 2):
                M[c, cp] = OMEGA ** d
    return M

def build_M_def(t):
    """实现B: 判据书 §一.1 定义式 M(t)(c,c')=e^{it((c-3c') mod 8)}·1_{∈{0,1,2}}"""
    return np.array([[complex(math.cos(t * ((c - 3 * cp) % 8)), math.sin(t * ((c - 3 * cp) % 8)))
                      if (c - 3 * cp) % 8 in (0, 1, 2) else 0.0 + 0.0j
                      for cp in range(8)] for c in range(8)], dtype=complex)

def A_of(t, j):
    """A_j(t)=1+e^{it}ζ^{-j}+e^{2it}ζ^{-2j}"""
    z1 = complex(math.cos(t), math.sin(t))
    zeta = complex(math.cos(2 * math.pi / 8), math.sin(2 * math.pi / 8))
    return 1.0 + z1 * zeta ** (-j) + z1 ** 2 * zeta ** (-2 * j)

def spec_closed(t):
    """定理 V-A 闭式谱"""
    return [A_of(t, 0), A_of(t, 4),
            (A_of(t, 1) * A_of(t, 3)) ** 0.5, -((A_of(t, 1) * A_of(t, 3)) ** 0.5),
            (A_of(t, 2) * A_of(t, 6)) ** 0.5, -((A_of(t, 2) * A_of(t, 6)) ** 0.5),
            (A_of(t, 5) * A_of(t, 7)) ** 0.5, -((A_of(t, 5) * A_of(t, 7)) ** 0.5)]

def s3(n):
    s = 0
    while n > 0:
        s += n % 3; n //= 3
    return s

def s2(n):
    return bin(n).count("1")

def c_of(r):
    """商类映射 c(r)=(r-(r mod 3))/3 mod 8"""
    d = r % 3
    return ((r - d) // 3) % 8

PAIRS12 = [(2, 8), (2, 14), (2, 20), (8, 14), (8, 20), (14, 20),
           (4, 10), (4, 16), (4, 22), (10, 16), (10, 22), (16, 22)]
CYCLES = [(0,), (4,), (1, 3), (2, 6), (5, 7)]

def cycle_of(c):
    for cy in CYCLES:
        if c in cy:
            return cy
    raise ValueError

def pair_cycle_relation(r, rp):
    """返回 (同循环?, 循环标签/说明)"""
    c1, c2 = c_of(r), c_of(rp)
    if c1 == c2:
        return False, f"同类({c1})"
    cy1, cy2 = cycle_of(c1), cycle_of(c2)
    if cy1 == cy2 and len(cy1) == 2:
        return True, f"cycle({cy1[0]},{cy1[1]})"
    return False, f"跨块 {c1}({cy1})|{c2}({cy2})"


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}"]

    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"first_run": first_run,
                    "freeze_note": "判据书冻结+V3③首跑前更正时刻以 NTFS 为准（§四 回填）"}}

    # ---------- V0 自检锚 ----------
    Mref = build_M_ref()
    Mdef = build_M_def(2 * math.pi / 3)
    d01 = float(np.max(np.abs(Mref - Mdef)))
    # 商类映射精确判定: r = 3*c(r)+d 恰在 mod 24 意义下 (3c+d ≡ r mod 24, c<8, d<3)
    map_exact = all((3 * c_of(r) + (r % 3)) % 24 == r for r in range(0, 24, 2))
    s3_shift = all(s3(3 * Q + d) == s3(Q) + d for Q in range(0, 100001) for d in (0, 1, 2))
    V0 = bool(d01 <= 1e-15 and map_exact and s3_shift)
    res["V0"] = {"diff_Mref_Mdef": d01, "map_exact_12to8": bool(map_exact),
                 "s3_shift_identity_1e5": bool(s3_shift), "pass": V0}
    log(f"V0 自检锚: M重构差 {d01:.2e} / 商类映射 {map_exact} / s3移位恒等 Q≤1e5 {s3_shift} -> {V0}")

    # ---------- V1 一般 t 谱定理 ----------
    r18_ref = [2.109381, 2.109381, 2.000000, 1.414214, 1.414214, 0.670440, 0.670440, 0.000000]
    v1 = {}
    V1 = True
    for name, t in [("pi/3", math.pi / 3), ("pi/2", math.pi / 2), ("2pi/3", 2 * math.pi / 3), ("pi", math.pi)]:
        Mt = build_M_def(t)
        eig = np.linalg.eigvals(Mt)
        pred = spec_closed(t)
        remaining = list(eig)
        worst = 0.0
        for p in pred:
            dd = [abs(p - e) for e in remaining]
            i = int(np.argmin(dd))
            worst = max(worst, dd[i]); remaining.pop(i)
        v1[name] = {"match_max_dist": worst}
        if worst > 1e-9:
            V1 = False; log(f"V1 失败 t={name}: {worst:.3e}")
    abs_sorted = sorted((abs(e) for e in np.linalg.eigvals(build_M_def(2 * math.pi / 3))), reverse=True)
    r18_diff = max(abs(a - b) for a, b in zip(abs_sorted, r18_ref))
    v1["r18_table_diff"] = r18_diff
    if r18_diff > 1e-6:
        V1 = False
    res["V1"] = {**v1, "pass": bool(V1)}
    log(f"V1 一般t谱定理: 四t点最差 {max(v1[k]['match_max_dist'] for k in ('pi/3','pi/2','2pi/3','pi')):.3e} / R18对表 {r18_diff:.3e} -> {V1}")

    # ---------- V2 同循环归属表 ----------
    table = {}
    for r, rp in PAIRS12:
        same, tag_ = pair_cycle_relation(r, rp)
        table[f"{r}|{rp}"] = {"c": [c_of(r), c_of(rp)], "same_cycle": same, "relation": tag_}
    same_set = sorted([k for k, v in table.items() if v["same_cycle"]])
    target = sorted(["4|10", "8|20", "16|22"])
    V2 = bool(same_set == target)
    res["V2"] = {"table": table, "same_cycle_set": same_set, "pass": V2}
    log(f"V2 同循环归属: {same_set} vs 预测 {target} -> {V2}")

    # ---------- V3 理论分布机器印证 ----------
    X = 2_000_000
    K13 = 13
    Y13 = 3 ** K13
    # H 枚举: Q < 3^13 按 (Q mod 8) 直方图 + 复特征
    H13 = [dict() for _ in range(8)]  # H13[c][s] = count, Q<3^13
    G13 = np.zeros(8, dtype=complex)  # sum omega^{s3(Q)}
    for Q in range(Y13):
        c = Q % 8
        s = s3(Q)
        H13[c][s] = H13[c].get(s, 0) + 1
        G13[c] += OMEGA ** s
    # ① k=1..6: 切片枚举 vs M^k 演化
    worst_k = 0.0
    G1 = np.zeros(8, dtype=complex); G1[0] = 1.0  # Y=1: Q=0 in class 0
    Mk = np.linalg.matrix_power(Mref, 0)
    for k in range(1, 7):
        Mk = Mk @ Mref
        Yk = 3 ** k
        Ge = np.zeros(8, dtype=complex)
        for Q in range(Yk):
            Ge[Q % 8] += OMEGA ** s3(Q)
        diff = float(np.max(np.abs(Mk @ G1 - Ge)))
        worst_k = max(worst_k, diff)
    # k=13 档: M^13 · G(1) vs 枚举 G13
    M13 = np.linalg.matrix_power(Mref, K13)
    diff13 = float(np.max(np.abs(M13 @ G1 - G13)))
    # H 直方图 vs 特征和自洽: Σ_s H13[c][s]·ω^s == G13[c]
    diff_HG = max(abs(sum(cnt * OMEGA ** s for s, cnt in H13[c].items()) - G13[c]) for c in range(8))
    # ② 三个截断上限
    caps = [X // 3 if (X - d) % 3 == 0 else (X - d) // 3 for d in (0, 1, 2)]
    caps = [((X - d) // 3) for d in (0, 1, 2)]
    caps_equal = (caps[0] == caps[1] == caps[2])
    # ③ 总质量 = 组样本数
    QMAX = caps[0]  # 666666
    mass = [0] * 8
    for Q in range(QMAX + 1):
        mass[Q % 8] += 1
    mass_rows = {}
    mass_ok = True
    for r in range(0, 24, 2):
        n_theory = mass[c_of(r)]
        n_group = (X - r) // 24 + 1
        mass_rows[str(r)] = {"theory": n_theory, "group": n_group}
        if n_theory != n_group:
            mass_ok = False; log(f"V3③ 质量不符 r={r}: {n_theory} vs {n_group}")
    V3 = bool(worst_k <= 1e-9 and diff13 <= 1e-6 and diff_HG <= 1e-9 and caps_equal and mass_ok)
    res["V3"] = {"recursion_k1_6_worst": worst_k, "k13_diff": diff13, "H_vs_G_diff": diff_HG,
                 "caps": caps, "caps_equal": bool(caps_equal), "mass_rows": mass_rows,
                 "mass_ok": bool(mass_ok), "pass": V3}
    log(f"V3 理论分布: 递推k1-6 {worst_k:.2e} / k13 {diff13:.2e} / H-G {diff_HG:.2e} / 上限同 {caps_equal} / 质量 {mass_ok} -> {V3}")

    # ---------- V4 预测值 (理论 KS vs W2 实测, 判负照记) ----------
    # 理论 CDF per 组: H_{c(r)} 平移 d, 上限 QMAX (三上限同为 666666, 已 V3② 验证)
    # H_QMAX[c][s] 用 Q≤666666 枚举 (与 H13 的差: 只计 Q≤666666)
    HQ = [dict() for _ in range(8)]
    for Q in range(QMAX + 1):
        c = Q % 8
        s = s3(Q)
        HQ[c][s] = HQ[c].get(s, 0) + 1
    def theo_cdf(r):
        c = c_of(r); d = r % 3
        items = sorted(((s + d, cnt) for s, cnt in HQ[c].items()))
        tot = sum(cnt for _, cnt in items)
        xs = [0.0]; cum = 0
        for s, cnt in items:
            cum += cnt
            xs.append(cum / tot)
        ss = [items[0][0] - 1] + [s for s, _ in items] + [items[-1][0] + 10]  # 末挡板: CDF(>max)=1
        xs.append(1.0)
        return ss, xs
    theo_ks = {}
    for r, rp in PAIRS12:
        s1, x1 = theo_cdf(r)
        s2_, x2 = theo_cdf(rp)
        alls = sorted(set(s1) | set(s2_))
        def val_at(ss, xs, q):
            import bisect
            i = bisect.bisect_right(ss, q)
            return xs[min(i, len(xs) - 1)]
        ks = max(abs(val_at(s1, x1, q) - val_at(s2_, x2, q)) for q in alls)
        theo_ks[f"{r}|{rp}"] = ks
    # W2 实测 @2e6
    w2 = json.loads((RES / "gd_high_bits_result-v1.0-20260920.json").read_text(encoding="utf-8"))
    w2_meas = {k: v["stat"] for k, v in w2["W2"]["by_X"]["2000000"].items()}
    keys = [f"{r}|{rp}" for r, rp in PAIRS12]
    try:
        from scipy.stats import spearmanr
        rho_sp, _ = spearmanr([theo_ks[k] for k in keys], [w2_meas[k] for k in keys])
        rho_sp = float(rho_sp)
    except Exception:
        # 手写秩相关
        def ranks(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2 + 1
                for m in range(i, j + 1):
                    rk[order[m]] = avg
                i = j + 1
            return rk
        r1, r2 = ranks([theo_ks[k] for k in keys]), ranks([w2_meas[k] for k in keys])
        n = len(keys)
        cova = sum((a - sum(r1) / n) * (b - sum(r2) / n) for a, b in zip(r1, r2))
        va = math.sqrt(sum((a - sum(r1) / n) ** 2 for a in r1))
        vb = math.sqrt(sum((b - sum(r2) / n) ** 2 for b in r2))
        rho_sp = cova / (va * vb)
    theo_bottom3 = sorted(theo_ks, key=theo_ks.get)[:3]
    pred_bottom3 = sorted(["16|22", "4|10", "8|20"])
    V4 = bool(rho_sp >= 0.5 and sorted(theo_bottom3) == pred_bottom3)
    res["V4"] = {"theo_ks": {k: round(v, 6) for k, v in theo_ks.items()},
                 "w2_meas_2e6": {k: round(v, 6) for k, v in w2_meas.items()},
                 "spearman": round(rho_sp, 4), "theo_bottom3": theo_bottom3,
                 "pred_bottom3": pred_bottom3, "pass": V4,
                 "note": "预测值判据(判负照记)"}
    log(f"V4 预测: Spearman {rho_sp:.4f} (≥0.5?) / 理论bottom3 {theo_bottom3} vs {pred_bottom3} -> {V4}")

    # ---------- V5 慢模幅度表 (记录项) + P-g 噪声底判读 ----------
    def fourier_blocks(v):
        """8 维复向量 → 5 块幅度 (Fourier 系数 per j, 按循环分块聚合)"""
        vh = np.fft.fft(v) / 8  # v̂_j = (1/8)Σ_c v_c ζ^{-jc} 约定记录用
        amps = {}
        for cy in CYCLES:
            amps[str(cy)] = float(np.sqrt(sum(abs(vh[j]) ** 2 for j in cy)))
        return amps
    block_table = {}
    for r, rp in PAIRS12:
        v = np.zeros(8, dtype=complex)
        v[c_of(r)] += 1; v[c_of(rp)] -= 1
        amps = fourier_blocks(v)
        row = {k: round(x, 4) for k, x in amps.items()}
        same, tag_ = pair_cycle_relation(r, rp)
        if same:
            cykey = tag_.replace("cycle", "")  # "(1,3)"
            key = [k for k in amps if k.replace(" ", "") == cykey][0]
            row["own_block_amp"] = row[key]
            row["own_block_max_ratio"] = round(amps[key] / max(amps.values()), 4)
        block_table[f"{r}|{rp}"] = row
    # P-g: @2e7 KS·√X 底比值
    pg = {}
    for k, v in w2["W2"]["by_X"]["20000000"].items():
        pg[k] = round(v["stat"] * math.sqrt(2e7), 3)
    res["V5"] = {"block_amps": block_table, "pg_2e7_ks_sqrtX": pg,
                 "pg_note": "P-g 噪声底判读(记录): @2e7 实测 KS ≈ C·X^{-1/2}, 比值=C"}
    log(f"V5 幅度表+P-g 落盘; @2e7 KS·√X 比值范围 [{min(pg.values()):.2f},{max(pg.values()):.2f}]")

    # ---------- V6 P-e 域内精确判定 ----------
    TWO = (Fraction(2), F0, F0, F0)
    S6 = (F0, F0, F0, Fraction(6))
    rho2 = (TWO[0] + S6[0], TWO[1], TWO[2], TWO[3] + S6[3])  # 2+√6
    rho2 = (Fraction(2), F0, F0, Fraction(1))
    cube = qmul(qmul(rho2, rho2), rho2)  # (2+√6)^3
    cube_target = (Fraction(81), F0, F0, F0)
    cube_neq81 = (cube != cube_target)
    int_neq = (18 ** 2 * 6 != 37 ** 2)  # 1944 vs 1369
    expo = 0.5 * math.log(2 + math.sqrt(6), 3) - 1
    expo_gap = abs(expo - (-1 / 3))
    V6 = bool(cube_neq81 and int_neq)
    res["V6"] = {"rho2_surd": qstr(rho2), "cube_surd": qstr(cube),
                 "cube_neq_81_exact": bool(cube_neq81), "1944_neq_1369": bool(int_neq),
                 "exponent": round(expo, 6), "exponent_minus_minus1_3": round(expo_gap, 6),
                 "paper_note": "Q(3^{1/3}) 次数3 ⊄ Q(√6) 次数2 (纸面次数论证)",
                 "pass": V6}
    log(f"V6 P-e: (2+√6)³={qstr(cube)} ≠ 81 [{cube_neq81}]; 1944≠1369 [{int_neq}]; 指数 {expo:.6f}, 与-1/3差 {expo_gap:.6f} -> {V6}")

    # ---------- V7 总裁决 ----------
    struct = V0 and V1 and V2 and V3 and V6
    res["verdict"] = {"structure_pass": bool(struct), "prediction_V4_pass": bool(V4),
                      "final": ("分布层混合谱定理成立【复算一致】: 一般t单项式谱+商类映射同循环归属=分布层形式基础" if struct
                                else "如实入账(见分项, 判负照记)")}
    log(f"V7 总裁决: {res['verdict']['final']}")
    res["log"] = log_lines
    (RES / f"distribution_layer_mixed_spectrum_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
