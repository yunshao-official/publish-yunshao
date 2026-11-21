# -*- coding: utf-8 -*-
"""
doeblin_step1_verify-v1.0-20260919.py
概率论册·遍历涌现截断定理步1·Doeblin 机器验证（乙22 裁决通道 P-E3 施工步1）
判据冻结：先于本脚本首跑落盘《概率论册·遍历涌现截断定理步1·Doeblin机器验证预注册判据书-v1.0-20260919.md》§二
（NTFS 创建时间戳 2026-09-19 22:43:40 在档），本脚本运行于冻结之后；结果与解读分离。
执行层主流数学：Doeblin 1938 / Levin–Peres–Wilmer 标准定理。体系常数零新断言
（α=1/8 为 [constants:v1.0] layer1 册内公理5.1 口径转述，体系内部定义·未验证）。
全部纯 numpy（无 scipy），固定种子。
"""
import json
import numpy as np
from datetime import datetime

T0_CLOCK = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT = r"H:\理论存档\01-数学\02-实验与数据\results\doeblin_step1_verify_result-v1.0-20260919.json"

D = 12                 # 12族投影向量维数（概率册定义5.3）
ALPHA = 1.0 / 8.0      # α=1/8（册内公理5.1 口径，[constants:v1.0] layer1）
DELTA = 0.10           # 注入混合率 δ（判据书 §一.4 冻结）
BETA = 1.0             # Boltzmann 逆温度 β（判据书 §一.3 冻结）
SEED = 20260919

# ---------------- 主验证级 Λ=1：4096 态全验证 ----------------
LAM = 1
NSTATES = (LAM + 1) ** D   # 4096
EPS = DELTA / NSTATES      # 一步 Doeblin 常数 ε = δ/|X_Λ|

def decode(states, lam):
    """整数编码 -> (n, D) 分量矩阵（分量∈{0..lam}）。base-(lam+1) 编码。"""
    s = np.asarray(states, dtype=np.int64).copy()
    out = np.empty((len(s), D), dtype=np.int64)
    for i in range(D):
        out[:, i] = s % (lam + 1)
        s //= (lam + 1)
    return out

def encode(bits, lam):
    """(n, D) 分量矩阵 -> 整数编码。"""
    b = np.asarray(bits, dtype=np.int64)
    code = np.zeros(len(b), dtype=np.int64)
    for i in range(D - 1, -1, -1):
        code = code * (lam + 1) + b[:, i]
    return code

def map_e(states, lam):
    """涌现修复算子 E 截断版（判据书 §一.2 冻结）：最高分量-1、最低分量+1，边界保护。"""
    bits = decode(states, lam)
    out = bits.copy()
    ok = (bits.max(1) != bits.min(1))          # 全相等态 -> 不动点
    a = np.argmax(bits, axis=1)                # 并列取最小索引
    b = np.argmin(bits, axis=1)
    xa = bits[np.arange(len(bits)), a]
    xb = bits[np.arange(len(bits)), b]
    move = ok & (xa > 0) & (xb < lam)          # 边界保护
    idx = np.arange(len(bits))[move]
    out[idx, a[move]] -= 1
    out[idx, b[move]] += 1
    return out, move

states = np.arange(NSTATES, dtype=np.int64)
Y = decode(states, LAM)                        # (4096, 12)

e_bits, moved = map_e(states, LAM)
e_codes = encode(e_bits, LAM)

# T0-①  e 良定义：e(x)∈X_Λ 逐态（构造上 0<=bits<=Λ 必然，机器逐态核对）
e_in = bool(np.all((e_bits >= 0) & (e_bits <= LAM)))
assert e_codes.min() >= 0 and e_codes.max() < NSTATES

# q̄：24 方向均匀混合 Boltzmann 重置核（判据书 §一.3）
qbar = np.zeros(NSTATES)
for i in range(D):
    for sgn in (+1, -1):
        w = np.exp(sgn * BETA * Y[:, i].astype(float))
        qbar += w / w.sum()
qbar /= 2 * D

# m(y) = Σ_{z: e(z)=y} q̄(z)（q̄ 在 e 下的推前）
m = np.bincount(e_codes, weights=qbar, minlength=NSTATES).astype(float)

# 实装公式（判据书 §一.4）：P(x,y) = (1-δ)(1-α)·1{y=e(x)} + (1-δ)α·m(y) + δ/|X_Λ|
C_DE = (1.0 - DELTA) * (1.0 - ALPHA)
C_M = (1.0 - DELTA) * ALPHA
P = np.full((NSTATES, NSTATES), C_M * m[None, :] + DELTA / NSTATES)
P[np.arange(NSTATES), e_codes] += C_DE        # I_e 项（每行恰一单点加成）

row_sums = P.sum(axis=1)
t0_rowdev = float(np.abs(row_sums - 1.0).max())
t0_qbar = float(abs(qbar.sum() - 1.0))

# T1  Doeblin 逐元素
p_min = float(P.min())
t1_pass = bool(p_min >= EPS)

# T2  不可约+非周期（构造复核）
support = P > 1e-18
# 正支撑图强连通：正向 BFS 从态 0 + 反向 BFS 全覆盖
def bfs(adj_lists, root):
    seen = np.zeros(len(adj_lists), dtype=bool)
    seen[root] = True
    stack = [root]
    while stack:
        x = stack.pop()
        for y in adj_lists[x]:
            if not seen[y]:
                seen[y] = True
                stack.append(y)
    return seen

out_adj = [np.nonzero(support[x])[0] for x in range(NSTATES)]
sup_fwd = bfs(out_adj, 0)
in_support = support.T
in_adj = [np.nonzero(in_support[x])[0] for x in range(NSTATES)]
sup_bwd = bfs(in_adj, 0)
t2_scc_all = bool(sup_fwd.all() and sup_bwd.all())
diag_min = float(np.diag(P).min())
t2_aper = bool(diag_min > 0)

# 去注入复合核 (E∘D) 支撑图连通分量数（记录项）：边 = e(x) 与 {y: m(y)>0}
ed_support_rows = []
for x in range(NSTATES):
    ed_support_rows.append(set([int(e_codes[x])] + np.nonzero(m > 0)[0].tolist()))
# Kosaraju（迭代式）
n = NSTATES
ed_out = [sorted(s) for s in ed_support_rows]
ed_in = [[] for _ in range(n)]
for x in range(n):
    for y in ed_out[x]:
        ed_in[y].append(x)
comp = np.full(n, -1, dtype=np.int64)
nc = 0
for root in range(n):
    if comp[root] >= 0:
        continue
    stack = [root]; comp[root] = nc
    while stack:
        x = stack.pop()
        for y in ed_out[x]:
            if comp[y] < 0:
                comp[y] = nc; stack.append(y)
    nc += 1
# Kosaraju 需第二遍按反图收敛计数——此处用简单法：分量数=反向图上不可互相达类。
# 改用双向闭包精确计数（n 小）：
und_seen = np.zeros(n, dtype=bool)
n_scc = 0
for root in range(n):
    if und_seen[root]:
        continue
    fwd = bfs(ed_out, root)
    bwd = bfs(ed_in, root)
    scc = fwd & bwd
    und_seen |= scc
    n_scc += 1
t2_record_ed_components = int(n_scc)

# T3  唯一平稳分布：幂法 × 线性方程组双通道
rng = np.random.default_rng(SEED)
mu = np.full(NSTATES, 1.0 / NSTATES)
def matvec(v):
    """μP 用实装公式（快速路径）：(1-δ)(1-α)·scatter_e(μ) + (1-δ)α·m·(Σμ) + δ/|X|"""
    return C_DE * np.bincount(e_codes, weights=v, minlength=NSTATES) + C_M * m * v.sum() + DELTA / NSTATES
for _ in range(4000):
    mu = matvec(mu)
pi_power = mu / mu.sum()

# 线性方程组精解 (I - P^T + J) π = 1
A = np.eye(NSTATES) - P.T + np.ones((NSTATES, NSTATES))
b = np.ones(NSTATES)
pi_solve = np.linalg.solve(A, b)
pi_solve = pi_solve / pi_solve.sum()

t3_resid = float(np.abs(pi_power @ P - pi_power).sum())
t3_pos = bool((pi_power > 0).all())
t3_sum = float(abs(pi_power.sum() - 1.0))
t3_cross = float(np.abs(pi_power - pi_solve).sum())

# T4  收敛：三初始分布
fp_states = [0, NSTATES - 1]                   # e 不动点：全 0 态与全 1 态
mu0s = {
    "single_allzero": np.eye(NSTATES)[0],
    "uniform": np.full(NSTATES, 1.0 / NSTATES),
    "e_fixed_points": np.array([0.5 if x in fp_states else 0.0 for x in range(NSTATES)]),
}
t4_all = {}
doeblin_bound = (1.0 - EPS) ** np.arange(1, 1501)
for name, mu0 in mu0s.items():
    v = mu0.copy()
    tvs = np.empty(1500)
    for k in range(1500):
        v = matvec(v)
        tvs[k] = 0.5 * np.abs(v - pi_power).sum()
    upper_ok = bool(np.all(tvs <= doeblin_bound + 1e-15))
    final_ok = bool(tvs[-1] < 1e-6)
    mono_ok = bool(np.all(np.diff(tvs) <= 1e-12))
    t_mix = int(np.argmax(tvs < 0.01) + 1) if np.any(tvs < 0.01) else -1
    t4_all[name] = {
        "upper_bound_all_points": upper_ok,
        "tv_1500": float(tvs[-1]),
        "final_lt_1e-6": final_ok,
        "monotone": mono_ok,
        "t_mix_0.01": t_mix,
        "tv_max": float(tvs.max()),
    }

# T5  谱隙估计（后段 TV 衰减率的几何平均 -> |λ₂| 估计）
v = rng.random(NSTATES); v /= v.sum()
tvs5 = []
for k in range(600):
    v = matvec(v)
    if k >= 300:
        tvs5.append(0.5 * np.abs(v - pi_power).sum())
tvs5 = np.array(tvs5)
ratios = tvs5[1:] / np.maximum(tvs5[:-1], 1e-300)
lam2_est = float(np.exp(np.mean(np.log(np.maximum(ratios, 1e-300)))))
spectral_gap = float(1.0 - lam2_est)

# ---------------- 抽查级 Λ=2：531441 态 ----------------
LAM2 = 2
NS2 = (LAM2 + 1) ** D          # 531441
EPS2 = DELTA / NS2
st2 = np.arange(NS2, dtype=np.int64)
Y2 = decode(st2, LAM2)
e2_bits, _ = map_e(st2, LAM2)
e2_codes = encode(e2_bits, LAM2)
t6_e_in = bool(np.all((e2_bits >= 0) & (e2_bits <= LAM2)))
qbar2 = np.zeros(NS2)
for i in range(D):
    for sgn in (+1, -1):
        w = np.exp(sgn * BETA * Y2[:, i].astype(float))
        qbar2 += w / w.sum()
qbar2 /= 2 * D
m2 = np.bincount(e2_codes, weights=qbar2, minlength=NS2).astype(float)
rng2 = np.random.default_rng(SEED + 1)
xs = rng2.integers(0, NS2, size=10000)
ys = rng2.integers(0, NS2, size=10000)
def P_value(x, y):
    return C_DE * (1.0 if e2_codes[x] == y else 0.0) + C_M * m2[y] + DELTA / NS2
t6_doeblin_sample = bool(all(P_value(int(x), int(y)) >= EPS2 for x, y in zip(xs, ys)))
samp = rng2.integers(0, NS2, size=10000)
t6_qbar_pos = bool((qbar2[samp] > 0).all())
# e 良定义 10^6 采样
big = rng2.integers(0, NS2, size=1_000_000)
bb, _ = map_e(big, LAM2)
t6_e_1e6 = bool(np.all((bb >= 0) & (bb <= LAM2)))

# ---------------- 汇总 ----------------
result = {
    "script_clock_first_run": T0_CLOCK,
    "frozen_evidence": "判据书NTFS创建 2026-09-19 22:43:40（本脚本首跑晚于冻结）",
    "params": {"D": D, "Lambda_main": LAM, "Nstates_main": NSTATES, "alpha": ALPHA,
               "delta": DELTA, "beta": BETA, "eps": EPS, "seed": SEED,
               "Lambda_check": LAM2, "Nstates_check": NS2, "eps2": EPS2},
    "T0": {"e_well_defined_all_states": e_in, "row_sum_max_dev": t0_rowdev,
           "qbar_sum_dev": t0_qbar, "pass": bool(e_in and t0_rowdev < 1e-12 and t0_qbar < 1e-12)},
    "T1": {"min_P": p_min, "eps": EPS, "pass": t1_pass},
    "T2": {"support_strongly_connected": t2_scc_all, "diag_min": diag_min,
           "aperiodic_all_selfloop_pos": t2_aper,
           "record_ed_components": t2_record_ed_components,
           "note": "去注入(E∘D)支撑图连通分量数=记录项（预期可能>1：注入项是连通性承担者）",
           "pass": bool(t2_scc_all and t2_aper)},
    "T3": {"piP_minus_pi_L1": t3_resid, "pi_all_positive": t3_pos,
           "pi_sum_dev": t3_sum, "power_vs_solve_L1": t3_cross,
           "pass": bool(t3_resid < 1e-9 and t3_pos and t3_sum < 1e-12 and t3_cross < 1e-6)},
    "T4": {k: v4 for k, v4 in t4_all.items()},
    "T4_pass": bool(all(v4["upper_bound_all_points"] and v4["final_lt_1e-6"] and v4["monotone"]
                        for v4 in t4_all.values())),
    "T5": {"t_mix_0.01_per_seq": {k: v4["t_mix_0.01"] for k, v4 in t4_all.items()},
           "lam2_est": lam2_est, "spectral_gap_est": spectral_gap,
           "pi_min": float(pi_power.min()), "pi_max": float(pi_power.max()),
           "doeblin_bound_at_1500": float(doeblin_bound[-1])},
    "T6": {"e_well_defined_1e6": t6_e_1e6, "doeblin_sample_1e4": t6_doeblin_sample,
           "qbar_pos_1e4": t6_qbar_pos, "note": "抽查级：不跑幂迭代（级差如实声明）",
           "pass": bool(t6_e_1e6 and t6_doeblin_sample and t6_qbar_pos)},
    "overall_T0_T4": None,
    "clock_finished": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
result["overall_T0_T4"] = bool(result["T0"]["pass"] and result["T1"]["pass"] and
                               result["T2"]["pass"] and result["T3"]["pass"] and result["T4_pass"])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("=== Doeblin 步1 机器验证（判据冻结后实算）===")
print("首跑时钟:", T0_CLOCK, "| 冻结: 2026-09-19 22:43:40 (NTFS)")
print(f"T0 pass={result['T0']['pass']}  T1 pass={t1_pass} (min_P={p_min:.6e}, eps={EPS:.6e})")
print(f"T2 pass={result['T2']['pass']} (强连通={t2_scc_all}, 对角min={diag_min:.4f}, 去注入分量数={t2_record_ed_components})")
print(f"T3 pass={result['T3']['pass']} (残差={t3_resid:.2e}, 双通道差={t3_cross:.2e})")
for k, v4 in t4_all.items():
    print(f"T4[{k}] upper={v4['upper_bound_all_points']} final_TV={v4['tv_1500']:.2e} mono={v4['monotone']} t_mix={v4['t_mix_0.01']}")
print(f"T4_pass={result['T4_pass']}  T5 谱隙估计={spectral_gap:.4f} (λ₂≈{lam2_est:.5f})")
print(f"T6 pass={result['T6']['pass']}")
print("总裁决 T0-T4 全过 =", result["overall_T0_T4"])
