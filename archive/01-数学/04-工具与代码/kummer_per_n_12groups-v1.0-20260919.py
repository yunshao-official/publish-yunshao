# -*- coding: utf-8 -*-
"""
kummer_per_n_12groups-v1.0-20260919.py
代数册·逐N行质量×奇异级数对组分辨（全12组分辨尝试·R14 C4后继）
判据冻结：先于本脚本首跑落盘《代数册·逐N行质量×奇异级数对组分辨预注册判据书-v1.0-20260919.md》§二/§三
（NTFS 创建时间戳 2026-09-19 22:44:54 在档），本脚本运行于冻结之后；结果与解读分离。
C4 教训在案：预测值与结构断言分开（J1=结构定理附证明；J2/J3 实算判负照记）。
执行层主流数学：Kummer–Legendre / Hardy–Littlewood / CRT。体系常数零引用。
长算纪律：5 片分片+检查点（判据书 §一.1 冻结口径）。
"""
import json
import math
import numpy as np
from datetime import datetime

T0_CLOCK = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
RES = r"H:\理论存档\01-数学\02-实验与数据\results"
OUT = RES + r"\kummer_per_n_12groups_result-v1.0-20260919.json"
CKPT_FMT = RES + r"\kummer_per_n_checkpoint_{k}-v1.0-20260919.json"
SEED = 20260919
X_MAX = 200000           # 偶数 N ∈ [2, 200000]
N_EVEN = X_MAX // 2      # 100000
N_SLICES = 5
PAIRS = [(2, 10), (4, 20), (8, 16), (14, 22)]   # 四对组（R14 C3 冻结口径）
PERM_N = 10000
THRESH_P = 0.01
THRESH_D = 0.05

# ---------- 公共工具 ----------
def popcounts(ns):
    return np.bitwise_count(ns.astype(np.int64))

def spf_sieve(limit):
    """最小素因子筛（线性化试除；等价于逐 N 试除到 sqrt(N) 的精确分解）。"""
    spf = np.zeros(limit + 1, dtype=np.int64)
    spf[1] = 1
    for i in range(2, limit + 1):
        if spf[i] == 0:
            spf[i::i][spf[i::i] == 0] = i
    return spf

SPF = spf_sieve(X_MAX)

def log_s2(N):
    """log𝔖₂(N) = log2 + Σ_{p|N, p≥3} log((p-1)/(p-2))（逐 N 精确分解）。"""
    n = int(N)
    total = math.log(2.0)
    while n > 1:
        p = int(SPF[n])
        if p > 2:
            total += math.log((p - 1.0) / (p - 2.0))
        while n % p == 0:
            n //= p
    return total

def maxcarry_closed(N):
    """max_k v₂(C(N,k)) 闭式：⌊log₂(N+1)⌋ − v₂(N+1)（判据书 §一.2 冻结）。
    实现=bit_length(N+1)−1−v₂(N+1)（bit_length=⌊log₂⌋+1）。
    [bug 记录] 首版误用 bit_length(N+1)−v₂(N+1)（差 1，N=2 自检锚拦截），
    修正为判据口径后重跑；判据文本未动（R14 C5 先例）。"""
    m = int(N) + 1
    return m.bit_length() - 1 - (m & -m).bit_length() + 1

def W_row(N, cum):
    """行质量精确式 W(N)=2Σ_{k≤N}s₂(k)−(N+1)s₂(N)；cum=Σ_{k≤N}s₂(k) 前缀和。"""
    n = int(N)
    return 2.0 * int(cum[n]) - (n + 1) * int(n.bit_count())

def carries_low3(k, r8):
    a, b, carry, c = k, (r8 - k) % 8, 0, 0
    for j in range(3):
        s = ((a >> j) & 1) + ((b >> j) & 1) + carry
        carry = 1 if s >= 2 else 0
        c += carry
    return c

S3_SIG = {r8: tuple(sum(1 for k in range(8) if carries_low3(k, r8) == j) for j in range(4))
          for r8 in range(8)}

# ---------- maxcarry 闭式自检锚（判据书 §一.2：N≤1000 暴力对照，全对才继续） ----------
def v2_c(n, k):
    """Kummer–Legendre 式：v₂(C(n,k)) = s₂(k)+s₂(n−k)−s₂(n)（自 v₂(n!)=n−s₂(n) 导出）。"""
    return k.bit_count() + (n - k).bit_count() - n.bit_count()

selfcheck_ok = True
for N in range(2, 1001):
    sN = int(popcounts(np.array([N]))[0])
    brute = max(v2_c(N, k) for k in range(N + 1))
    if brute != maxcarry_closed(N):
        selfcheck_ok = False
        print("maxcarry 闭式自检失败 N=", N, brute, maxcarry_closed(N))
        break
assert selfcheck_ok, "maxcarry 闭式自检锚未过（判据书 §一.2 冻结：全对才继续）"
print("maxcarry 闭式自检锚 N≤1000 全对 ✓")

# ---------- 分片实算 + 检查点 ----------
evens_all = np.arange(2, X_MAX + 1, 2, dtype=np.int64)
s2_all = popcounts(evens_all)
cum_all = np.concatenate([[0], np.cumsum(popcounts(np.arange(0, X_MAX + 1, dtype=np.int64)))])
# cum_all[n] = Σ_{k=0..n} s₂(k)

slice_size = N_EVEN // N_SLICES
cols = {}
for s in range(N_SLICES):
    idx = slice(s * slice_size, (s + 1) * slice_size)
    ns = evens_all[idx]
    col = {
        "N": ns,
        "r": (ns % 24).astype(np.int64),
        "logS2": np.array([log_s2(int(n)) for n in ns]),
        "W": np.array([W_row(int(n), cum_all) for n in ns], dtype=float),
        "popcount": s2_all[idx].astype(np.int64),
        "maxcarry": np.array([maxcarry_closed(int(n)) for n in ns], dtype=np.int64),
    }
    cols.update({k: np.concatenate([cols[k], v]) for k, v in col.items()} if cols else col)
    # 检查点（断点续算支持）
    ck = {k: v.tolist() for k, v in col.items()}
    with open(CKPT_FMT.format(k=s + 1), "w", encoding="utf-8") as f:
        json.dump({"slice": s + 1, "range_even_index": [s * slice_size, (s + 1) * slice_size - 1],
                   "cols": ck, "clock": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                  f, ensure_ascii=False)
    print(f"片 {s+1}/{N_SLICES} 完成（N∈[{ns[0]},{ns[-1]}]），检查点已落盘 {datetime.now().strftime('%H:%M:%S')}")

N_arr, r_arr = cols["N"], cols["r"]
logS2, W, pc, mc = cols["logS2"], cols["W"], cols["popcount"], cols["maxcarry"]
assert len(N_arr) == N_EVEN

# ---------- W̃ 去趋势（全样本 OLS 一次拟合；判据书 §一.2 冻结口径） ----------
A1 = np.vstack([np.ones(N_EVEN), N_arr.astype(float)]).T
coef, _, _, _ = np.linalg.lstsq(A1, W, rcond=None)
Wt = W - (coef[0] + coef[1] * N_arr)
print(f"W 去趋势：W ≈ {coef[0]:.4f} + {coef[1]:.6f}·N；残差 std={Wt.std():.4f}")

# ---------- KS 检验（同构自实现 + scipy 若在则交叉核对） ----------
def ks_2samp_stat(a, b):
    comb = np.concatenate([a, b])
    cdf1 = np.searchsorted(np.sort(a), np.sort(comb), side="right") / len(a)
    cdf2 = np.searchsorted(np.sort(b), np.sort(comb), side="right") / len(b)
    return float(np.abs(cdf1 - cdf2).max())

def ks_2samp_p(D, n1, n2):
    ne = n1 * n2 / (n1 + n2)
    lam = D * (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne))   # Numerical Recipes 修正
    p = 0.0
    for j in range(1, 201):
        p += (-1) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam)
        if j > 2 and abs(math.exp(-2.0 * j * j * lam * lam)) < 1e-18:
            break
    return max(0.0, min(1.0, 2.0 * p))

try:
    import scipy.stats as st
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

def group_vals(arr, g):
    return arr[r_arr == g]

J2 = []
for (g1, g2) in PAIRS:
    a, b = group_vals(logS2, g1), group_vals(logS2, g2)
    Dst = ks_2samp_stat(a, b)
    p = ks_2samp_p(Dst, len(a), len(b))
    row = {"pair": [g1, g2], "n1": len(a), "n2": len(b), "D": Dst, "p_ours": p,
           "mean1": float(a.mean()), "mean2": float(b.mean())}
    if HAVE_SCIPY:
        sp = st.ks_2samp(a, b)
        row["p_scipy"] = float(sp.pvalue); row["D_scipy"] = float(sp.statistic)
    J2.append(row)
    print(f"J2 对组({g1},{g2}): D={Dst:.5f} p={p:.4f}" + (f" (scipy p={row['p_scipy']:.4f})" if HAVE_SCIPY else ""))

# ---------- 置换检验（1e4 次固定种子；双侧；统计量=均值差） ----------
rng = np.random.default_rng(SEED)
def perm_test(a, b, n_perm=PERM_N):
    v = np.concatenate([a, b])
    n1 = len(a)
    obs = abs(a.mean() - b.mean())
    cnt = 0
    for _ in range(n_perm):
        pv = rng.permutation(v)
        if abs(pv[:n1].mean() - pv[n1:].mean()) >= obs:
            cnt += 1
    return (cnt + 1) / (n_perm + 1)

def cohens_d(a, b):
    m1, m2 = a.mean(), b.mean()
    s = math.sqrt(((len(a) - 1) * a.std() ** 2 + (len(b) - 1) * b.std() ** 2) / (len(a) + len(b) - 2))
    return abs(m1 - m2) / s

J3 = []
for sig_name, sig in [("W_trend_removed", Wt), ("popcount", pc.astype(float)), ("maxcarry", mc.astype(float))]:
    for (g1, g2) in PAIRS:
        a, b = group_vals(sig, g1), group_vals(sig, g2)
        p = perm_test(a, b)
        d = cohens_d(a, b)
        sep = (p < THRESH_P) and (d > THRESH_D)
        J3.append({"signature": sig_name, "pair": [g1, g2], "p": p, "d": d,
                   "mean1": float(a.mean()), "mean2": float(b.mean()), "separable": bool(sep)})
        print(f"J3 {sig_name} 对组({g1},{g2}): p={p:.4f} d={d:.5f} 可分={sep}")

# ---------- J4 回归锚 ----------
# ①C1：每组全成员 S₃ 一致（S₃ 只依赖 N mod 8，构造恒真，机器核对 12×12=144 对）
s3_of_group = {r: S3_SIG[r % 8] for r in range(0, 24, 2)}
c1_pairs_total, c1_pairs_ok = 0, 0
for r1 in range(0, 24, 2):
    for r2 in range(0, 24, 2):
        c1_pairs_total += 1
        same_sig = s3_of_group[r1] == s3_of_group[r2]
        same_mod8 = (r1 % 8) == (r2 % 8)
        if same_sig == same_mod8:
            c1_pairs_ok += 1
# 组级良定义：组内成员 r mod 8 恒同（由 r 定义恒真，机器核对实际数据）
c1_welldef = bool(all((N_arr[r_arr == r] % 8 == r % 8).all() for r in range(0, 24, 2)))
# ②C2：3∣N / 3∤N 组均值比
S2_vals = np.exp(logS2)
gmeans = {r: float(S2_vals[r_arr == r].mean()) for r in range(0, 24, 2)}
m_div3 = float(np.mean([gmeans[r] for r in [0, 6, 12, 18]]))
m_ndiv3 = float(np.mean([gmeans[r] for r in [2, 4, 8, 10, 14, 16, 20, 22]]))
ratio = m_div3 / m_ndiv3
print(f"J4: C1 144对判对 {c1_pairs_ok}/{c1_pairs_total}（组级良定义核对={c1_welldef}）；C2 组间比={ratio:.4f}")

# ---------- 汇总 ----------
j2_pass = bool(all(row["p_ours"] > THRESH_P for row in J2))
j3_any = bool(any(row["separable"] for row in J3))
j4_pass = bool(c1_pairs_ok == c1_pairs_total and c1_welldef and 1.9 <= ratio <= 2.1)
result = {
    "script_clock_first_run": T0_CLOCK,
    "frozen_evidence": "判据书NTFS创建 2026-09-19 22:44:54（本脚本首跑晚于冻结）",
    "params": {"X_max": X_MAX, "n_even": N_EVEN, "slices": N_SLICES, "seed": SEED,
               "perm_n": PERM_N, "thresh_p": THRESH_P, "thresh_d": THRESH_D,
               "have_scipy": HAVE_SCIPY,
               "W_ols": {"a": float(coef[0]), "b": float(coef[1])},
               "maxcarry_selfcheck_Nle1000": "all_pass"},
    "J2": J2, "J2_pass_all_p_gt_0.01": j2_pass,
    "J3": J3, "J3_any_separable": j3_any,
    "J4": {"c1_pairs_ok": c1_pairs_ok, "c1_pairs_total": c1_pairs_total,
           "c1_welldefined": c1_welldef, "c2_ratio_div3_ndiv3": ratio,
           "group_means": gmeans, "mean_div3": m_div3, "mean_ndiv3": m_ndiv3,
           "pass": j4_pass},
    "J5_verdict": ("分辨成功（J3 至少一检验通过）——升级待判别" if j3_any
                    else "分辨不成功（本签名集与样本量口径下四对组不可分；𝔖₂ 侧由 J1 定理精确）"),
    "clock_finished": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("=== 总裁决 ===")
print("J1 定理入档（证明在判据书 §二）| J2 全不拒绝 =", j2_pass, "| J3 任一可分 =", j3_any, "| J4 回归锚 =", j4_pass)
print("J5:", result["J5_verdict"])
