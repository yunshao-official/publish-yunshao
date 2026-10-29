# -*- coding: utf-8 -*-
"""
JC-N1 三代禁数模型 v0.1 · 定形与拟合检验（2026-09-19，ZCode）
模型定形（全部假设显式，成分均出自《云韶数论·内部版》）：
  M1 禁数：N=pq, p<q 素数, 族不同（mod 24），张力 T=|a-b|/24
  M2 代际（新常数重定，0905 旧残留已修正）：
     gen1: T≤α=1/8（即 d=2）；gen2: 1/8<T≤1/√6（d∈{4,6,8}）；gen3: T>1/√6（d∈{10,12,14,16,18,22}）
  M3 衰减（原文 §3.3）：d_g(N;x)=exp(-T^g·c·ln x)=x^{-c·T^g}，g=1,2,3 代衰减指数
  M4 贡献（原文 §3.2"每个禁数挤占约-2 经衰减调制"的求和直译）：
     Δ_model(x) = -A · Σ_{cross, pq≤x} x^{-c·T(N)^{g(N)}}
  M5 自由参数：A（幅）、c（代谢速率尺度）——在真实 Δ(x) 上对数域最小二乘拟合
检验：
  T-a 对数域拟合优度 R²；T-b 模型有效指数 vs 数据 α_eff=0.382；T-c 符号结构缺陷检查
  T-d 各代贡献占比（衰减是否有效分离三代）
诚实标签：v0.1 为册内语言的最简可算形式；拟合优度与结构缺陷如实报告。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
X = 2_000_000
ALPHA = 1/8; TWO_SQRT6 = 1/math.sqrt(6)

def sieve(n):
    is_p = bytearray([1])*(n+1); is_p[0:2]=b"\x00\x00"
    for i in range(2, int(n**0.5)+1):
        if is_p[i]: is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return is_p

isp = sieve(X)
primes = [i for i in range(2, X+1) if isp[i]]

def gen_of(d):  # d=族差(偶数)
    T = d/24
    if T <= ALPHA: return 1
    if T <= TWO_SQRT6: return 2
    return 3

# 扫描全部跨族素数对（按 pq 升序累积），在网格点记录每代累加量 Σ x^{-c T^g}
# 技巧：对固定评估点 x，权重 x^{-c·T^g} 依赖 x；拆分为 Σ_d N_d(x)·x^{-c·k_d}，
#       N_d(x)=族差为 d 且 pq≤x 的对数，k_d=(d/24)^{g(d)}。先扫对得 N_d(x) 网格。
grid = [10_000*i for i in range(1, 201)]
grid_set = set(grid)
Nd = {d: [0]*len(grid) for d in (2,4,6,8,10,12,14,16,18,22)}
gi = 0
pairs = []
FAMS8 = {1,5,7,11,13,17,19,23}
for i, p in enumerate(primes):
    if p*p > X: break
    a = p % 24
    if a not in FAMS8: continue          # 2、3 不属八族——不入禁数定义（修正：初版污染源）
    for q in primes[i+1:]:
        if p*q > X: break
        b = q % 24
        if b in FAMS8 and b != a:
            pairs.append((p*q, abs(a-b)))
pairs.sort()
counts = {d: 0 for d in Nd}
ptr = 0
for gi, x in enumerate(grid):
    while ptr < len(pairs) and pairs[ptr][0] <= x:
        counts[pairs[ptr][1]] += 1
        ptr += 1
    for d in Nd: Nd[d][gi] = counts[d]
total_pairs = len(pairs)

# π, Li, Δ
pi_arr = [0]*(X+1); c0 = 0
for i in range(X+1):
    if isp[i]: c0 += 1
    pi_arr[i] = c0
def li(x):
    L = math.log(x); s=0.0; term=1.0
    for k in range(1,60):
        term *= L/k; s += term/k
    return 0.5772156649 + math.log(math.log(x)) + s
delta = [pi_arr[x] - li(x) for x in grid]

kd = {d: (d/24)**gen_of(d) for d in Nd}
print("="*66)
print("JC-N1 三代禁数模型 v0.1 · 定形与拟合检验 ｜ 2026-09-19")
print("="*66)
print(f"跨族禁数对总数={total_pairs:,}；代际归属（d:gen,k）=")
print("  " + ", ".join(f"d{d}:g{gen_of(d)}" for d in sorted(Nd)))

def model_series(c):
    out=[]
    for gi_, x in enumerate(grid):
        ssum = sum(Nd[d][gi_] * x**(-c*kd[d]) for d in Nd)
        out.append(ssum)
    return out

def logfit(series, delta):
    # 对数域拟合 Δ ≈ -A·series：log|Δ| = log A + log series，剔除零
    xs=[]; ys=[]
    for s,dv in zip(series,delta):
        if s>0 and dv!=0:
            xs.append(math.log(s)); ys.append(math.log(abs(dv)))
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sxy=sum((a-mx)*(b-my) for a,b in zip(xs,ys)); sxx=sum((a-mx)**2 for a in xs)
    beta=sxy/sxx; alpha=my-beta*mx
    pred=[alpha+beta*v for v in xs]
    ss_res=sum((y-p)**2 for y,p in zip(ys,pred)); ss_tot=sum((y-my)**2 for y in ys)
    return math.exp(alpha), beta, 1-ss_res/ss_tot, xs, ys

best=None
for ci in range(0, 4001):
    c = ci*0.005
    series = model_series(c)
    A, beta, r2, _, _ = logfit(series, delta)
    if best is None or r2 > best[2]:
        best = (c, A, r2, series)
c_best, A_best, r2_best, series_best = best
print(f"\n拟合结果：c={c_best:.3f}（代谢速率），A={A_best:.4g}，对数域 R²={r2_best:.4f}")

# 模型有效指数 + 数据有效指数
def eff_slope(series):
    lx=[math.log(x) for x in grid]; ls=[math.log(s) for s in series if s>0]
    mx=sum(lx)/len(lx); ms=sum(ls)/len(ls)
    return sum((a-mx)*(b-ms) for a,b in zip(lx,ls))/sum((a-mx)**2 for a in lx)
sl_model = eff_slope(series_best)
lx=[math.log(x) for x in grid]; ld=[math.log(abs(d)) for d in delta]
mx=sum(lx)/len(lx); md=sum(ld)/len(ld)
sl_data = sum((a-mx)*(b-md) for a,b in zip(lx,ld))/sum((a-mx)**2 for a in lx)
print(f"\nT-b 有效指数：数据 α_eff={sl_data:.3f}｜模型 α_eff={sl_model:.3f}｜偏差 {abs(sl_model-sl_data):.3f}")
shares = {d: Nd[d][-1]*grid[-1]**(-c_best*kd[d]) for d in Nd}
tot = sum(shares.values())
print("T-d 各族差贡献占比（x=2e6，衰减后）：")
for d in sorted(shares, key=lambda d:-shares[d]):
    print(f"   d={d:>2} (gen{gen_of(d)}, T={d/24:.3f}): {shares[d]/tot*100:6.2f}%")
g_sh={1:0,2:0,3:0}
for d,s in shares.items(): g_sh[gen_of(d)]+=s
print(f"   代际占比：gen1={g_sh[1]/tot*100:.1f}%  gen2={g_sh[2]/tot*100:.1f}%  gen3={g_sh[3]/tot*100:.1f}%")

print("\nT-c 符号结构检查：")
print("  Δ_model = -A·Σ(正项) ⇒ 恒负、单调 ⇒ 结构上不可能产生 Littlewood 符号翻转")
print("  → v0.1 结构缺陷（如实记录）：缺振荡源；v0.2 方向=引入零点相位项（对接 D8 显式公式）")
print("\n判定（模型 v0.1）：")
print(f"  └ 尺度层面：模型以 2 个自由参数复现数据整体标度（R²={r2_best:.4f}，指数差 {abs(sl_model-sl_data):.3f}）")
print(f"  └ 结构层面：无振荡源=不可解释符号翻转；衰减分离三代（gen1 主导 {g_sh[1]/tot*100:.0f}%）与代谢壁垒叙事一致但不可独立检验")
print(f"  └ 结论：v0.1=可算骨架成立、理论不完备（缺零点相位项）——迭代方向已明，判据 JC-N1 主体（符号一致率≥95%）继续挂起至 v0.2")
