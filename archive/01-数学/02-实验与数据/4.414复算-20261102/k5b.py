#!/usr/bin/env python3
# 终版：高精度 ζ（Euler-Maclaurin, N=200, 最优截断）→ 零点表 T≤200 + 双参数自检 + 辐角原理对数 + K5 门
import math, cmath, numpy as np

def bernoulli(n_max):
    Bv = [Fraction0]*(n_max+1); Bv[0] = F(1)
    for n in range(1, n_max+1):
        s = sum(math.comb(n+1, k)*Bv[k] for k in range(n))
        Bv[n] = -s/F(n+1)
    return Bv
from fractions import Fraction as F
Fraction0 = F(0)
B = bernoulli(130)
BF = [float(B[2*k]/math.factorial(2*k)) for k in range(1, 26)]

def zeta(s, N=200):
    """EM: sum_{n<N} n^-s + N^{1-s}/(s-1) + N^-s/2 + sum B_2k/(2k)! (s)_{2k-1} N^{-s-2k+1}
       项递减到最小处截断 -> 误差 ~ 最小项"""
    s = complex(s)
    tot = sum(complex(n)**(-s) for n in range(1, N))
    tot += complex(N)**(1-s)/(s-1) + 0.5*complex(N)**(-s)
    logN = math.log(N)
    rising = complex(1.0); prev = None; used = 0; lastmag = None
    for k in range(1, 26):
        if k == 1: rising = s
        else:
            for j in (2*k-3, 2*k-2): rising *= (s+j)
        term = BF[k-1]*rising*cmath.exp((-s-2*k+1)*logN)
        m = abs(term)
        if prev is not None and m > prev: break
        tot += term; prev = m; used = k; lastmag = m
    return tot, used, lastmag

def loggamma_stirling(z, M=14):
    z = complex(z)
    out = 0.5*math.log(2*math.pi) + (z-0.5)*cmath.log(z) - z
    for k in range(1, M+1):
        out += float(B[2*k])/(2*k*(2*k-1))*z**(-(2*k-1))
    return out
def loggamma_exact(z, m=15):
    z = complex(z); out = loggamma_stirling(z+m)
    for j in range(m): out -= cmath.log(z+j)
    return out
def theta(t):
    return loggamma_exact(complex(0.25, t/2)).imag - 0.5*t*math.log(math.pi)
def Z(t, N=200):
    return (cmath.exp(complex(0, theta(t)))*zeta(complex(0.5, t), N)[0]).real

print('=== ζ 实现自检（高精度版）===')
for sv, ref in [(complex(2,0), math.pi**2/6), (complex(0,0), -0.5), (complex(-1,0), -1/12),
                (complex(-0.5,0), -0.2078761057335925), (complex(0.5,0), -1.4603545088095868)]:
    v, u, lm = zeta(sv)
    print(f'  ζ({sv}): {v.real:+.15f}  参考 {ref:+.15f}  差={abs(v.real-ref):.2e}  用了{u}项 最小项={lm:.1e}')
s = complex(0.37, 19.0)
chi = cmath.exp((s-0.5)*math.log(math.pi))*cmath.exp(loggamma_exact((1-s)/2)-loggamma_exact(s/2))
print(f'  函数方程 ζ(0.37+19i) vs χζ(0.63-19i): 相对差={abs(zeta(s)[0]-chi*zeta(1-s)[0])/abs(zeta(s)[0]):.2e}')

print('\n=== 零点表 T ≤ 200（自己算，双 N 参数自检）===')
TMAX = 200.0
grid = np.arange(4.0, TMAX, 0.01)
vals = np.array([Z(t) for t in grid])
idx = np.where(vals[:-1]*vals[1:] < 0)[0]
roots = []
for i in idx:
    a, b, fa = grid[i], grid[i+1], vals[i]
    for _ in range(50):
        m = 0.5*(a+b); fm = Z(m)
        if fa*fm <= 0: b = m
        else: a, fa = m, fm
    roots.append(0.5*(a+b))
res = [abs(zeta(complex(0.5, g))[0]) for g in roots]
print(f'  找到 {len(roots)} 个；最大残差 |ζ(1/2+iγ)| = {max(res):.2e}')
alt = []
for g in roots:
    a, b = g-0.02, g+0.02
    fa = Z(a, N=120)
    for _ in range(40):
        m = 0.5*(a+b); fm = Z(m, N=120)
        if fa*fm <= 0: b = m
        else: a, fa = m, fm
    alt.append(0.5*(a+b))
print(f'  N=200 与 N=120 两套参数的高度差 max = {max(abs(x-y) for x,y in zip(roots,alt)):.2e}')
print('  前 20 个零点高度:  ' + '  '.join(f'{g:.6f}' for g in roots[:20]))
print(f'  你档锚点 14.134725142 vs 我算 {roots[0]:.9f}  差={abs(roots[0]-14.134725142):.2e}')

print('\n=== 辐角原理：条带 σ∈[−0.6,1.6] 内总零点数（不假设在线上）===')
def gfun(z): return (z-1)*zeta(z)[0]
def count(T, lo=-0.6, hi=1.6, step=0.006):
    c = [(lo,0.02),(hi,0.02),(hi,T),(lo,T)]
    pts = []
    for a, b in zip(c, c[1:]+[c[0]]):
        L = abs(complex(b[0],b[1])-complex(a[0],a[1])); n = max(300, int(L/step))
        ts = np.linspace(0, 1, n, endpoint=False)
        pts.append(complex(a[0],a[1]) + ts*(complex(b[0],b[1])-complex(a[0],a[1])))
    pts = np.concatenate(pts)
    w = np.array([gfun(z) for z in pts])
    d = np.append(np.angle(w[1:]/w[:-1]), np.angle(w[0]/w[-1]))
    return d.sum()/(2*math.pi), np.abs(d).max()
for T in [20.0, 66.0, 100.0, 150.0, 200.0]:
    Nt, mx = count(T); nl = sum(1 for r in roots if r < T)
    print(f'  T={T:6.1f}: 条带总零点={Nt:7.3f}  线上找到={nl:4d}  → 不在线上={Nt-nl:+.3f}  max|Δarg|={mx:.3f}')

print('\n=== K5 门 d̄ 复算（口径A: d=n−N₀；口径B: d=n−1/2−N₀；N₀=θ/π+1）===')
for nn in [15, 30, 79]:
    A = sum(abs(n-(theta(g)/math.pi+1)) for n, g in enumerate(roots[:nn], 1))/nn
    Bv = sum(abs((n-0.5)-(theta(g)/math.pi+1)) for n, g in enumerate(roots[:nn], 1))/nn
    mg = sum((n-(theta(g)/math.pi+1)) for n, g in enumerate(roots[:nn], 1))/nn
    print(f'  前{nn:3d}: d̄_A={A:.4f}  d̄_B={Bv:.4f}  带符号均值={mg:+.4f}')
print('  （你档记录 前15零点 d̄=0.326；我在这两种口径下都没有复现出 0.326 → 该门口径需在判据书里冻结）')

with open('/tmp/k5_zeros_raw.csv','w') as f:
    f.write('n,gamma_me,sigma,N0=theta/pi+1,d_A=n-N0,d_B=n-0.5-N0\n')
    for n, g in enumerate(roots, 1):
        N0 = theta(g)/math.pi+1
        f.write(f'{n},{g:.10f},0.5,{N0:.10f},{n-N0:.10f},{n-0.5-N0:.10f}\n')
print('\n原始数据: /tmp/k5_zeros_raw.csv')
print('sha256:', end=' ')
import hashlib; print(hashlib.sha256(open('/tmp/k5_zeros_raw.csv','rb').read()).hexdigest()[:32])
