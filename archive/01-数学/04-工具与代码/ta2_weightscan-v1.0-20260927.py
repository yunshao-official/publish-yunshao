# -*- coding: utf-8 -*-
"""
第二轮·实验A：权重扫描找临界β*
对象（冻结）：群塔 a_q=|PSL(2,q)|^{-β(s+1)}，L_mul(β,s)=exp(Σp_k/k)，p_k=Σ a_q^k
对照（冻结）：素数版 a_p=p^{-β(s+1)}（β=1 时=ζ(s+1) 的素数 Euler 闭包，精确）
判据：A-1 每档变号/真零点/min|L|，β*=从1往下第一个"真零点≥1或变号≥10"的档
      A-2 对表体系常数 1/8,1/6,1/12,1/3,1/2；A-3 素数版对照（预判：全程无零点）
预注册：《黎曼猜想·通俗图解-v4.0-20260927》§十二（NTFS 时间戳在先）
"""
import numpy as np, sympy as sp, json, platform, datetime

QMAX = 293
P_MAX = 10 ** 4
BETA_GROUP = [1.0, 0.75, 0.5, 0.4, 1/3, 0.28, 0.25, 0.24, 0.23]
BETA_PRIME = [1.0, 0.9, 0.8, 0.7, 0.67]
T_GRID = np.arange(0, 50.0001, 0.02)
SYS_CONST = {"1/2": 0.5, "1/3": 1/3, "1/8": 0.125, "1/6": 1/6, "1/12": 1/12}

orders = {q: q * (q * q - 1) // 2 for q in sp.primerange(7, QMAX + 1)}
c_group = np.array([np.log(orders[q]) for q in orders])          # ln|PSL|
primes_p = list(sp.primerange(2, P_MAX + 1))
c_prime = np.array([float(sp.log(p)) for p in primes_p])

def scan(c_arr, beta, t_grid, kmax_cap=3000):
    """p_k(t)=Σ exp(-k·β·c·(1+it))；L_mul=exp(Σ_k p_k/k)。返回变号/真零点/min|L|。"""
    kc = beta * c_arr                                            # 每塔的有效指数
    # kmax 自适应：Σ exp(-kmax·kc) < 1e-16
    k = 1
    while np.sum(np.exp(-k * kc)) > 1e-16 and k < kmax_cap:
        k += 1
    kmax = k
    ks = np.arange(1, kmax + 1)[:, None]
    w = np.exp(-ks * kc[None, :])                                # (kmax, n) 实权重
    signs = 0; zeros = []; minL = np.inf; prev_re = None
    for t in t_grid:
        ph = np.exp(-1j * ks * (kc[None, :] * t))                # 相位
        pk = (w * ph).sum(axis=1)                                # p_k(t)
        kk = np.arange(1, kmax + 1)
        L = np.exp(np.sum(pk / kk))
        if prev_re is not None and L.real * prev_re < 0:
            signs += 1
        if abs(L) < 1e-8:
            zeros.append(round(float(t), 4))
        minL = min(minL, abs(L))
        prev_re = L.real
    return signs, zeros, minL, kmax

print("===== 实验 A：权重扫描（判据冻结版）=====")
print("--- 群塔版（|PSL(2,q)| 权重，59 座 q≤293）---")
res_g = {}
for b in BETA_GROUP:
    sg, zg, ml, km = scan(c_group, b, T_GRID)
    res_g[b] = {"sign_changes": sg, "true_zeros": len(zg), "zeros": zg[:20], "min_abs": ml, "kmax": km}
    print(f"β={b:.4f}: 变号{sg:3d} 真零点{len(zg):2d} min|L|={ml:.4e} kmax={km}")

beta_star = None
for b in BETA_GROUP:
    if res_g[b]["true_zeros"] >= 1 or res_g[b]["sign_changes"] >= 10:
        beta_star = b
        break
print(f"\nA-1：β*（从1往下首个信号档）= {beta_star}")
hit = [k for k, v in SYS_CONST.items() if beta_star is not None and abs(beta_star - v) < 1e-9]
print(f"A-2：体系常数对表：{'命中 ' + ', '.join(hit) if hit else '无同档（β* 作独立实验常数入档）'}")

print("\n--- 素数版对照（p≤10⁴，1229 素数；β=1 ⟺ ζ(s+1) Euler 闭包）---")
res_p = {}
for b in BETA_PRIME:
    sg, zg, ml, km = scan(c_prime, b, T_GRID[::2], kmax_cap=2000)   # t 步长0.04减负
    res_p[b] = {"sign_changes": sg, "true_zeros": len(zg), "min_abs": ml}
    print(f"β={b:.4f}: 变号{sg:3d} 真零点{len(zg):2d} min|L|={ml:.4e} kmax={km}")
zeta_check = abs(complex(sp.zeta(1.5 + 1j * 14.1347)))
print(f"A-3 对照锚：ζ(1.5+14.13i)|={zeta_check:.4f}（ζ(s+1) 零点在 Re(s)=-1/2，预判 Re(s)=1/2 无零点）")

out = {"script": "ta2_weightscan-v1.0-20260927.py",
       "prereg": "黎曼猜想·通俗图解-v4.0-20260927 §十二（NTFS冻结在先）",
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "platform": platform.platform(),
       "A1_group": {str(k): v for k, v in res_g.items()}, "beta_star": beta_star,
       "A2_system_const_match": hit,
       "A3_prime": {str(k): v for k, v in res_p.items()},
       "note": "β≤2/9 级数发散（收敛域边界=发散即物理），网格下界 0.23"}
with open("results/ta2_A_weightscan_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n结果已写 results/ta2_A_weightscan_result-v1.0-20260927.json")
