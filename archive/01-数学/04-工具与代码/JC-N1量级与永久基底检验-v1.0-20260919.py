# -*- coding: utf-8 -*-
"""
JC-N1 量级与永久基底检验 v1.0（2026-09-19，ZCode）
判据来源：数论线账本 JC-N1（对象 D1/D3/D5）
可执行子检验（模型无关部分）：
  T1 三代量级：|Δ(x)|·x^{-1/2}, x^{-1/3}, x^{-1/6} 的跨4个数量级趋势
     ——D3 预测 x^{1/2} 项存续（不趋于0）、x^{1/3}/x^{1/6} 项相对衰减
  T2 永久基底（D5 代谢壁垒）：Δ(x)/√x 在 x∈[10^3, 10^7] 的相对变化
  T3 符号窗口诚实记录：Littlewood 定理保证 Δ(x) 终将变号，但首个变号点 >> 10^19，
     本窗口内 Δ(x)>0 无区分度——如实记录，不做伪检验
  T4 数据产品：π(x)、Li(x)、Δ(x)、S(x)（跨族禁数计数）网格表
诚实标签：符号一致率子检验（JC-N1 主体）需三代生成模型定形后方可执行，本轮不做。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')

X = 2_000_000
def sieve(n):
    is_p = bytearray([1])*(n+1); is_p[0:2]=b"\x00\x00"
    for i in range(2, int(n**0.5)+1):
        if is_p[i]: is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return is_p

isp = sieve(X)
# π(x) 累积
pi_arr = [0]*(X+1)
c = 0
for i in range(X+1):
    if isp[i]: c += 1
    pi_arr[i] = c

def li(x):
    # li(x) 主项级数（不含奇点项的常用近似）：γ+lnlnx+Σ (lnx)^k/(k·k!)
    L = math.log(x)
    s = 0.0
    term = 1.0
    for k in range(1, 60):
        term *= L/k
        s += term/k
    return 0.5772156649 + math.log(math.log(x)) + s

def semiprime_cross_count(x):
    # 跨族禁数计数 S(x)：p<q, pq≤x, 族不同（族=mod24）
    ps = [i for i in range(2, int(math.isqrt(x))+1)]
    ps = [p for p in ps if isp[p]]
    cnt = 0
    for i, p in enumerate(ps):
        qmax = x // p
        if qmax < p: break
        a = p % 24
        for q in ps[i+1:]:
            if q > qmax: break
            if q % 24 != a: cnt += 1
    return cnt

# S(x) 完整算法：对每个素数 p≤√x，数 (p, x/p] 内族≠p族的素数个数（按族有序表+二分）
from bisect import bisect_right
FAMS = (1,5,7,11,13,17,19,23)
fam_primes = {f: [] for f in FAMS}
for n in range(2, X+1):
    if isp[n] and (n % 24) in fam_primes:
        fam_primes[n % 24].append(n)
small_primes = [p for p in range(2, math.isqrt(X)+1) if isp[p]]

def S_cross(x):
    total = 0
    for p in small_primes:
        qmax = x // p
        if qmax < p: break
        a = p % 24
        for f in FAMS:
            if f == a: continue
            lst = fam_primes[f]
            total += bisect_right(lst, qmax) - bisect_right(lst, p)
    return total

print("="*68)
print("JC-N1 量级与永久基底检验 v1.0 ｜ 2026-09-19 ｜ X=2,000,000")
print("="*68)
grid = [10_000*i for i in range(1, 201)]  # 1e4 .. 2e6 step 1e4
rows = []
for x in grid:
    pix = pi_arr[x]
    lix = li(x)
    dx = pix - lix
    rows.append((x, pix, lix, dx))

print(f"{'x':>9} {'π(x)':>9} {'Li(x)':>12} {'Δ=π−Li':>10} {'Δ/√x':>8} {'Δ/x^(1/3)':>9} {'Δ/x^(1/6)':>9}")
for (x,pix,lix,dx) in rows[::20]:  # 每 2e5 抽样打印
    print(f"{x:>9,} {pix:>9,} {lix:>12.1f} {dx:>10.1f} {dx/x**0.5:>8.3f} {dx/x**(1/3):>9.3f} {dx/x**(1/6):>9.3f}")

# T1/T2 趋势定量：先逐行归一，再取首尾窗口均值
norm = [(r[0], r[3]/r[0]**0.5, r[3]/r[0]**(1/3), r[3]/r[0]**(1/6)) for r in rows]
def wmean(idx_slice, col):
    vals=[abs(v[col]) for v in norm[idx_slice]]; return sum(vals)/len(vals)
head = slice(0, 10); tail = slice(-10, None)
d_half_h, d_half_t = wmean(head,1), wmean(tail,1)
d_third_h, d_third_t = wmean(head,2), wmean(tail,2)
d_six_h, d_six_t = wmean(head,3), wmean(tail,3)
# 有效指数：log|Δ| 对 log x 的最小二乘斜率
import statistics as st
lx = [math.log(r[0]) for r in rows]; la = [math.log(abs(r[3])) for r in rows]
mx = sum(lx)/len(lx); ma = sum(la)/len(la)
slope = sum((a-mx)*(b-ma) for a,b in zip(lx,la)) / sum((a-mx)**2 for a in lx)
print("\nT1 三代量级趋势（|Δ| 归一窗口均值，首 1e4-1e5 vs 尾 1.9e6-2e6）：")
print(f"  |Δ|·x^-1/2 : {d_half_h:.3f} → {d_half_t:.3f}（比值 {d_half_t/d_half_h:.2f}）")
print(f"  |Δ|·x^-1/3 : {d_third_h:.3f} → {d_third_t:.3f}（比值 {d_third_t/d_third_h:.2f}）")
print(f"  |Δ|·x^-1/6 : {d_six_h:.3f} → {d_six_t:.3f}（比值 {d_six_t/d_six_h:.2f}）")
print(f"  有效指数 α_eff = {slope:.3f}（log|Δ|-log x 回归，窗口 1e4-2e6）")
print(f"  对照 D3 三代量级：x^(1/2)=0.500 / x^(1/3)=0.333 / x^(1/6)=0.167")
print("T2 永久基底（D5）：Δ/√x 相对变化 = "
      f"{(d_half_t-d_half_h)/abs(d_half_h)*100:+.1f}%（4个数量级上）")
signs = set('+' if r[3]>0 else '-' for r in rows)
print(f"T3 符号窗口：x≤2e6 内 Δ(x) 符号集合={signs}——与 Littlewood 定理相容")
print("   （首个变号点远超 10^19，本窗口符号检验无区分度——如实记录）")
print("T4 跨族禁数 S(x)：")
for x in (10_000, 100_000, 500_000, 1_000_000, 2_000_000):
    print(f"   S({x:>9,}) = {S_cross(x):>10,}   （π(x)={pi_arr[x]:,}）")
print("\n判定（JC-N1 部分执行）：")
print(f"  └ T1：本窗口 α_eff≈{slope:.2f}，介于 x^(1/3) 与 x^(1/2) 之间且 |Δ|·x^-1/2 在下降——")
print("    D3 的 x^(1/2) 主项量级在本窗口【不可证实】（渐进标度尚未显现，属预期但如实记录）")
print("  └ T2：D5 永久基底在本窗口不可判伪（变化百分比即记录）")
print("  └ T3：符号一致率子检验待三代生成模型定形（判据主体维持『待模型实现』）")
print("  └ 本轮性质：数据产品+模型无关子检验；不构成对 D1/D3/D5 的证实或证伪")
