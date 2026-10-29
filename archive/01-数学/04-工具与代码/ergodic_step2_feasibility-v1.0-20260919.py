# -*- coding: utf-8 -*-
"""
ergodic_step2_feasibility-v1.0-20260919.py
概率论册·遍历涌现步2可行性解剖（乙22 步2·一致收缩率定理 SA1 数值印证 + t_mix Λ 无关上界 SA2 + 纯 E∘D 链遍历性失败定量 SA3）
判据冻结：先于本脚本首跑落盘《概率论册·遍历涌现步2可行性解剖预注册判据书-v1.0-20260919.md》（NTFS 创建 2026-09-19 23:15:58 在档）
执行层主流数学：Dobrushin 型 TV 压缩/Markov 链标准不等式。体系常数零引用。纯 numpy。
数值范围 Λ=1,2,3（判据书 §一.2 冻结；Λ≥4 内存超限如实声明级差）。
"""
import json
import numpy as np
from datetime import datetime

T0_CLOCK = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT = r"H:\理论存档\01-数学\02-实验与数据\results\ergodic_step2_feasibility_result-v1.0-20260919.json"

D = 12
ALPHA = 1.0 / 8.0
DELTA = 0.10
BETA = 1.0
SEED = 20260919
N_STEPS = 400

def decode(states, lam):
    s = np.asarray(states, dtype=np.int64).copy()
    out = np.empty((len(s), D), dtype=np.int64)
    for i in range(D):
        out[:, i] = s % (lam + 1)
        s //= (lam + 1)
    return out

def encode(bits, lam):
    b = np.asarray(bits, dtype=np.int64)
    code = np.zeros(len(b), dtype=np.int64)
    for i in range(D - 1, -1, -1):
        code = code * (lam + 1) + b[:, i]
    return code

def map_e(states, lam):
    bits = decode(states, lam)
    out = bits.copy()
    ok = (bits.max(1) != bits.min(1))
    a = np.argmax(bits, axis=1)
    b = np.argmin(bits, axis=1)
    xa = bits[np.arange(len(bits)), a]
    xb = bits[np.arange(len(bits)), b]
    move = ok & (xa > 0) & (xb < lam)
    idx = np.arange(len(bits))[move]
    out[idx, a[move]] -= 1
    out[idx, b[move]] += 1
    return out

rng = np.random.default_rng(SEED)
results = {}
for LAM in (1, 2, 3):
    NS = (LAM + 1) ** D
    states = np.arange(NS, dtype=np.int64)
    Y = decode(states, LAM).astype(float)
    e_codes = encode(map_e(states, LAM), LAM)
    # q̄：24 方向均匀混合 Boltzmann 重置核
    qbar = np.zeros(NS)
    for i in range(D):
        for sgn in (+1, -1):
            w = np.exp(sgn * BETA * Y[:, i])
            qbar += w / w.sum()
    qbar /= 2 * D
    m = np.bincount(e_codes, weights=qbar, minlength=NS).astype(float)
    C_DE = (1.0 - DELTA) * (1.0 - ALPHA)
    C_M = (1.0 - DELTA) * ALPHA

    def matvec_P(v):
        """完整核 P_Λ 的 matvec（含 δ·Unif 项）。"""
        return (C_DE * np.bincount(e_codes, weights=v, minlength=NS)
                + C_M * m * v.sum() + DELTA / NS)

    # π_Λ（幂法；一致收缩率保证 0.9^400 < 2e-18）
    mu = np.full(NS, 1.0 / NS)
    for _ in range(400):
        mu = matvec_P(mu)
    pi = mu / mu.sum()

    # SA1：两初始分布 TV(n) ≤ (1-δ)^n 全点（理论 μP−νP = (1−δ)^n(μ−ν) 精确保持，逐点核对）
    mu_a = np.zeros(NS); mu_a[0] = 1.0
    mu_b = np.full(NS, 1.0 / NS)
    tvs = np.empty(N_STEPS)
    for k in range(N_STEPS):
        mu_a = matvec_P(mu_a)
        mu_b = matvec_P(mu_b)
        tvs[k] = 0.5 * np.abs(mu_a - mu_b).sum()
    bound = (1.0 - DELTA) ** np.arange(1, N_STEPS + 1)
    sa1_upper = bool(np.all(tvs <= bound + 1e-15))
    # 结构自检（实现层，非判据）：TV(μ0P,ν0P) ≤ (1−δ)(1−α)·TV(μ0,ν0) ≤ (1−δ)(1−α)
    # [bug 记录] 首版自检公式误写 0.5(1−1/NS)（未计一步收缩与 α·m 散布压缩），SA1 判据书冻结
    # 条件本为 upper bound 全点；修正为本结构自检后重跑，判据未动。
    struct_check = bool(tvs[0] <= (1.0 - DELTA) * (1.0 - ALPHA) + 1e-12)
    sa1_pass = bool(sa1_upper and struct_check)
    sa1_t0 = float(tvs[0])
    # SA2：t_mix(0.01)（与 π 比）
    tv_pi = np.empty(N_STEPS)
    v = np.zeros(NS); v[0] = 1.0
    for k in range(N_STEPS):
        v = matvec_P(v)
        tv_pi[k] = 0.5 * np.abs(v - pi).sum()
    t_mix = int(np.argmax(tv_pi < 0.01) + 1) if np.any(tv_pi < 0.01) else -1
    sa2_ok = bool(0 < t_mix <= 44)

    # SA3：纯 E∘D（δ=0）连通类数。结构定理：{I}=单一 SCC + 每个非像点单点 SCC ⟹ 类数 = 1 + |X| − |I|
    img_sorted = np.unique(e_codes)
    I_size = int(len(img_sorted))
    if LAM == 1:
        # 结构定理 SCC = {I} ∪ 单点（非像点入度=0）+ 逐态入度核对（4096 态全验证）；
        # 与步1 T2 记录的 2047（全图双向闭包实算）交叉核对
        indeg = np.bincount(e_codes, minlength=NS)          # e 边的入度
        in_from_I = np.zeros(NS, dtype=bool)
        in_from_I[img_sorted[m[img_sorted] > 0]] = True
        zero_in = (indeg == 0) & (~in_from_I)
        # x∈I 的点：入度来自全空间 e 边+m 边；x∉I 但 e(y)=x 存在的点是像点（矛盾）——故非像点⟺入度0
        n_scc_structural = 1 + int(zero_in.sum())
        I_check = int((m > 0).sum())
        sa3 = {"Lambda": LAM, "I_size": I_size, "m_support_size": I_check,
               "scc_full_count": n_scc_structural,
               "scc_matches_step1_T2_2047": bool(n_scc_structural == 2047),
               "identity_1_plus_X_minus_I": bool(n_scc_structural == 1 + NS - I_size),
               "method": "结构定理 SCC=1+|X|−|I| + 逐态入度核对（4096 态全验证）"}
    else:
        # Λ=2/3：结构定理恒等式核对（全图 BFS 边数 |X|·|I| 不可行的级差如实声明）
        # 抽验：①I 内互达（构造恒真 m(y)>0 ∀y∈I，随机 1000 对抽核 e 边/m 支撑一致）；②随机 1000 非像点入度 0
        indeg = np.bincount(e_codes, minlength=NS)
        nonimg_sample = rng.choice(np.nonzero(m == 0)[0], size=min(1000, int((m == 0).sum())), replace=False)
        zero_in_ok = bool(np.all(indeg[nonimg_sample] == 0))
        img_sample = rng.choice(np.nonzero(m > 0)[0], size=min(1000, int((m > 0).sum())), replace=False)
        img_in_ok = bool(np.all((m[img_sample] > 0) & (indeg[img_sample] > 0)))
        n_scc_structural = 1 + NS - I_size
        sa3 = {"Lambda": LAM, "I_size": I_size, "scc_structural": n_scc_structural,
               "nonimg_zero_indeg_sample_ok": zero_in_ok,
               "img_in_sample_ok": img_in_ok,
               "identity_1_plus_X_minus_I": bool(n_scc_structural == 1 + NS - I_size),
               "greater_than_1": bool(n_scc_structural > 1),
               "method": "结构定理 SCC=1+|X|−|I| + 抽样核对（全图 BFS 边数 |X|·|I| 不可行·级差如实声明）"}

    results[LAM] = {
        "Nstates": NS,
        "SA1": {"upper_bound_all_points": sa1_upper, "struct_check_tv1_le_7875": struct_check,
                "tv_at_1": float(tvs[0]), "tv_at_400": float(tvs[-1]),
                "theory_tv1_bound": (1.0 - DELTA) * (1.0 - ALPHA),
                "pass": sa1_pass},
        "SA2": {"t_mix_0.01": t_mix, "upper_bound_44": 44, "pass": sa2_ok},
        "SA3": sa3,
    }
    print(f"Λ={LAM} |X|={NS}: SA1 upper={sa1_upper} (TV400={tvs[-1]:.2e}) | "
          f"SA2 t_mix={t_mix} (≤44) | SA3 SCC={sa3.get('scc_full_count', sa3.get('scc_structural'))} I={I_size}")

overall = bool(all(results[L]["SA1"]["pass"] and results[L]["SA2"]["pass"] for L in (1, 2, 3))
               and results[1]["SA3"]["scc_matches_step1_T2_2047"]
               and results[2]["SA3"]["greater_than_1"] and results[3]["SA3"]["greater_than_1"])

result = {
    "script_clock_first_run": T0_CLOCK,
    "frozen_evidence": "判据书NTFS创建 2026-09-19 23:15:58（本脚本首跑晚于冻结）",
    "params": {"D": D, "alpha": ALPHA, "delta": DELTA, "beta": BETA, "seed": SEED,
               "n_steps": N_STEPS, "lambda_range": [1, 2, 3],
               "lambda4_note": "Λ≥4 |X|=2.44×10⁸ 内存超限，级差如实声明（判据书 §一.2 冻结）"},
    "per_Lambda": results,
    "SA4": {"formalization_a": "含均匀注入：SA1+SA2 ⇒ 一致混合控制成立，步2 一致性技术障碍不存在；但遍历性承担者是注入项（外生），'E 具有遍历性'原句未被证明",
            "formalization_b": "纯 E∘D：SA3 ⇒ 不强连通不遍历（Λ=1 碎 2047 类）⇒ 该语义下步2 定量失败 → 按乙22 预冻结判读转路径乙",
            "note": "两条后果陈列供乙22 定谳引用，不代定谳（判据书 §二 SA4 冻结口径）"},
    "overall_SA1_SA2_SA3": overall,
    "clock_finished": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("=== 步2 可行性解剖总裁决 ===")
print("SA1 一致收缩率数值印证（Λ=1,2,3）+SA2 t_mix≤44（Λ=1,2,3）+SA3 纯 E∘D 类数>1：", overall)
print("SA4 语义二分判别材料已陈列（见 JSON/判据书）")
