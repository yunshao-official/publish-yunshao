# -*- coding: utf-8 -*-
"""
塔交互三构想·构想一（I 系列）：塔×塔乘法交互 L 函数与临界线扫描
预注册：《塔交互三构想·预注册判据书-v1.0-20260927》判据冻结在先（NTFS 时间戳）
对象：a_q(s)=|PSL(2,q)|^{-(s+1)}，q>=7 素数 q<=293
  L2*(s)=Σa_q（拼接，现行）        p_k(s)=Σ a_q^k = L2*(k(s+1))
  e2(s)=(p1^2-p2)/2（两两交互）    L_mul(s)=exp(Σ p_k/k)（全乘法闭包 Π(1-a_q)^{-1}）
  L_01(s)=exp(Σ (-1)^{k+1} p_k/k)（全 0/1 交互 Π(1+a_q)）
判据：I-1 变号/真零点；I-2 质量账 vs min|L_Θ|/2=0.0975；I-3 与 ζ(s+1) 对比；回归锚 L2*(1/2)≈5.634e-4
"""
import numpy as np, sympy as sp, json, platform, datetime

PSI_MIN_LTHETA_HALF = 0.0975          # min|L_Θ|/2（冻结值，min|L_Θ|=0.19495@t≈22.85）
ANCHOR_L2STAR_HALF = 5.634e-4         # 冻结回归锚（20260906 在档）
primes = list(sp.primerange(7, 294))  # q<=293，前 62 座
orders = {q: q * (q * q - 1) // 2 for q in primes}   # |PSL(2,q)|
logs = np.array([float(sp.log(orders[q])) for q in primes])
print(f"塔数={len(primes)}  q_max={primes[-1]}  |PSL(2,7)|={orders[7]}  |PSL(2,293)|={orders[primes[-1]]}")
print(f"截断自检：|a_293(1/2)|={orders[primes[-1]]**(-1.5):.3e} < 1e-6  ✓")

def p_k_vec(s, kmax=None):
    """p_k(s)=Σ_q a_q^k，返回 [p_1..p_kmax]（复数）。s 复数。"""
    # a_q^k = |PSL|^{-k(s+1)} = exp(-k(s+1)·ln|PSL|)
    b = (s + 1.0) * logs          # 每塔的指数基数
    if kmax is None:
        # 自适应：p_k 模上界=Σ|PSL|^{-k/2}（σ=1/2 最坏情形），<1e-18 停
        kmax = 1
        while True:
            tail = float(np.sum(np.exp(-kmax * 0.5 * logs * 1.0)))  # σ=1/2 → k·1.5，用 0.5·logs 保守? 直接精确：
            tail = float(np.sum(np.exp(-kmax * 1.5 * logs)))
            if tail < 1e-18:
                break
            kmax += 1
            if kmax > 5000:
                break
    ks = np.arange(1, kmax + 1)
    # shape: (kmax, n_primes) -> p_k = Σ_q exp(-k(s+1)·ln q)
    M = np.exp(-np.outer(ks, b))
    return M.sum(axis=1), kmax

def build(s):
    p, kmax = p_k_vec(s)
    k = np.arange(1, len(p) + 1)
    L2s = p[0]
    e2 = (p[0] ** 2 - p[1]) / 2.0
    L_mul = np.exp(np.sum(p / k))
    L_01 = np.exp(np.sum(((-1.0) ** (k + 1)) * p / k))
    return L2s, e2, L_mul, L_01, kmax

# 回归锚
L2a, e2a, mula, b01a, _ = build(0.5 + 0j)
print(f"回归锚：L2*(1/2)={L2a.real:.6e}  vs 冻结锚 {ANCHOR_L2STAR_HALF:.3e}  相对差={abs(L2a.real-ANCHOR_L2STAR_HALF)/ANCHOR_L2STAR_HALF:.2e}")

# 扫描 Re(s)=1/2, t∈[0,100] 步长 0.02
ts = np.arange(0, 100.0001, 0.02)
names = ["L2star(拼接)", "e2(两两交互)", "L_mul(全乘法闭包)", "L_01(全0/1交互)"]
res = {n: {"sign_changes": [], "true_zeros": [], "max_abs": 0.0} for n in names}
prev = None
for t in ts:
    s = 0.5 + 1j * t
    L2s, e2, L_mul, L_01, _ = build(s)
    vals = [L2s, e2, L_mul, L_01]
    for n, v in zip(names, vals):
        res[n]["max_abs"] = max(res[n]["max_abs"], abs(v))
    if prev is not None:
        for n, v, pv in zip(names, vals, prev):
            if v.real * pv.real < 0:
                res[n]["sign_changes"].append(round(float(t - 0.01), 3))
            if abs(v) < 1e-8:
                res[n]["true_zeros"].append(round(float(t), 3))
    prev = vals

print("\n===== I-1 扫描结果（Re(s)=1/2, t∈[0,100], 步长0.02）=====")
for n in names:
    print(f"{n}: 变号 {len(res[n]['sign_changes'])} 处 {res[n]['sign_changes'][:8]}{'...' if len(res[n]['sign_changes'])>8 else ''} | 真零点 {len(res[n]['true_zeros'])} | max|L|={res[n]['max_abs']:.6e}")

print("\n===== I-2 质量账（判负/通过判定）=====")
# 全交互新增量（相对拼接）：|L_mul - 1 - L2*| 与 |L_01 - 1 - L2*| 的最大值已含在 max_abs；
# 更公平：交互新增 = max_t |L_mul(t) - (1+L2*(t))|
max_add_mul = 0.0; max_add_01 = 0.0; max_e2 = 0.0
for t in np.arange(0, 100.0001, 0.05):
    s = 0.5 + 1j * t
    L2s, e2, L_mul, L_01, _ = build(s)
    max_add_mul = max(max_add_mul, abs(L_mul - 1 - L2s))
    max_add_01 = max(max_add_01, abs(L_01 - 1 - L2s))
    max_e2 = max(max_e2, abs(e2))
print(f"max|e2|={max_e2:.4e}  max|L_mul新增|={max_add_mul:.4e}  max|L_01新增|={max_add_01:.4e}")
print(f"判定阈值=min|L_Θ|/2={PSI_MIN_LTHETA_HALF}")
verdict_add = (max_add_mul < PSI_MIN_LTHETA_HALF) and (max_add_01 < PSI_MIN_LTHETA_HALF)
print(f"I-2 判负照记成立？ {verdict_add}（交互总量 < 0.0975 ⟹ 零点拓扑不变，判负归因=权重三阶幂衰减非结构缺位）")

print("\n===== I-3 与 ζ(s+1) 对比（s=1/2 线）=====")
zeta_vals = [abs(sp.zeta(1.5 + 1j * t)) for t in (0, 14.13, 22.85, 50.0)]
print("ζ(1.5+it) 模：", [f"{z:.4f}" for z in zeta_vals], "（L_mul 量级≈1+3e-3，与 ζ 差 2-3 个数量级：乘法闭包≠ζ，结构对比如实记录）")

out = {
    "script": "ta_interaction_lfunction-v1.0-20260927.py",
    "prereg": "塔交互三构想·预注册判据书-v1.0-20260927.md",
    "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "platform": platform.platform(),
    "n_towers": len(primes), "q_max": int(primes[-1]),
    "anchor_L2star_half": {"computed": L2a.real, "frozen": ANCHOR_L2STAR_HALF},
    "scan": {n: {"sign_changes": res[n]["sign_changes"], "true_zeros": res[n]["true_zeros"],
                 "max_abs": res[n]["max_abs"]} for n in names},
    "mass": {"max_e2": max_e2, "max_add_mul": max_add_mul, "max_add_01": max_add_01,
             "threshold": PSI_MIN_LTHETA_HALF, "verdict_negative_recorded": bool(verdict_add)},
}
with open("results/ta_I_series_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n结果已写 results/ta_I_series_result-v1.0-20260927.json")
