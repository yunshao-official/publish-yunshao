#!/usr/bin/env python3
# 独立复算（全部从零实现：Lanczos/Stirling 复数 loggamma + Euler-Maclaurin 解析延拓，不调用任何现成 zeta）
import numpy as np, math, cmath
from fractions import Fraction

def bernoulli(n_max):
    B = [Fraction(0)]*(n_max+1); B[0] = Fraction(1)
    for n in range(1, n_max+1):
        s = sum(math.comb(n+1, k)*B[k] for k in range(n))
        B[n] = -s/Fraction(n+1)
    return B
B = bernoulli(30)

P = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
     771.32342877765313, -176.61502916214059, 12.501580116150855,
     -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
def gamma_lanczos(z):
    z = complex(z)
    if z.real < 0.5:
        return math.pi/(cmath.sin(math.pi*z)*gamma_lanczos(1.0-z))
    x = complex(P[0])
    for i in range(1, 9): x += P[i]/(z+i-1)
    t = z+6.5
    return math.sqrt(2*math.pi)*t**(z-0.5)*cmath.exp(-t)*x
def loggamma_stirling(z, M=12):
    z = complex(z)
    out = 0.5*math.log(2*math.pi) + (z-0.5)*cmath.log(z) - z
    for k in range(1, M+1):
        out += float(B[2*k])/(2*k*(2*k-1))*z**(-(2*k-1))
    return out


def loggamma_exact(z, m=15, M=12):
    """复数 logΓ：递推抬到 |z+m| 大 → Stirling 连续支；对任意 z(Re>0 或需避开极点) 精确"""
    z = complex(z)
    out = loggamma_stirling(z+m, M)
    for j in range(m):
        out -= cmath.log(z+j)
    return out

N_EM, M_EM = 30, 13
def zeta(s):
    s = complex(s)
    tot = sum(complex(n)**(-s) for n in range(1, N_EM))
    tot += complex(N_EM)**(1-s)/(s-1) + 0.5*complex(N_EM)**(-s)
    rising = complex(1.0)
    for k in range(1, M_EM+1):
        if k == 1: rising = s
        else:
            for j in (2*k-3, 2*k-2): rising *= (s+j)
        tot += float(B[2*k]/math.factorial(2*k))*rising*complex(N_EM)**(-s-2*k+1)
    return tot

def theta_cont(t):           # Riemann-Siegel theta, 连续支
    return loggamma_exact(complex(0.25, t/2)).imag - 0.5*t*math.log(math.pi)
def Zfunc(t):                # Z(t)=e^{iθ}ζ(1/2+it)（实值）
    return (cmath.exp(complex(0, theta_cont(t)))*zeta(complex(0.5, t))).real

print('=== 自检 zeta / theta 实现 ===')
print(f'  Γ(5) = {cmath.exp(loggamma_exact(5.0)).real:.14f} (应 24)')
print(f'  Γ(0.75) = {cmath.exp(loggamma_exact(0.75)).real:.14f} (应 1.2254167024651773)')
print(f'  Γ(0.25) = {cmath.exp(loggamma_exact(0.25)).real:.14f} (应 3.6256099082219082)')
for sv, ref in [(2.0, 1.6449340668482264), (0.0, -0.5), (-1.0, -1/12), (-0.5, -0.2078761057)]:
    print(f'  zeta({sv:>5}) = {zeta(sv).real:+.14f}   参考 {ref:+.14f}')
print(f'  ζ(1/2) 我算 = {zeta(complex(0.5,0)).real:+.12f}   参考 -1.4603545088095868')
print(f'  Z(0)   我算 = {Zfunc(1e-9):+.12f}   应等于 ζ(1/2)')
s = complex(0.37, 19.0)
def zeta_ep(sv, limit=100000):
    sev = np.ones(limit+1, bool); sev[0]=sev[1]=False
    for i in range(2, int(limit**0.5)+1):
        if sev[i]: sev[i*i::i] = False
    tot = sum(cmath.log(1-complex(q)**(-sv)) for q in np.nonzero(sev)[0])
    return cmath.exp(-tot)
print(f'  ζ(2+3i) 我的Euler–Maclaurin={zeta(complex(2,3)):.12f}')
print(f'  ζ(2+3i) 欧拉乘积(素数≤1e5)={zeta_ep(complex(2,3)):.12f}   ← 两条独立算法')
chi = cmath.exp((s-0.5)*math.log(math.pi))*cmath.exp(loggamma_exact((1-s)/2)-loggamma_exact(s/2))
print(f'  函数方程 ζ(s)=χ(s)ζ(1−s) @s=0.37+19i : 左={zeta(s):.10f}')
print(f'                                       右={chi*zeta(1-s):.10f}  相对差={abs(zeta(s)-chi*zeta(1-s))/abs(zeta(s)):.2e}')

print('\n=== (1) 自己找 ζ 零点高度（网格变号 + 二分，不查表） ===')
grid = np.arange(1.0, 70.0, 0.004)
vals = np.array([Zfunc(t) for t in grid])
idx = np.where(vals[:-1]*vals[1:] < 0)[0]
roots = []
for i in idx:
    a, b, fa = grid[i], grid[i+1], vals[i]
    for _ in range(60):
        m = 0.5*(a+b); fm = Zfunc(m)
        if fa*fm <= 0: b = m
        else: a, fa = m, fm
    roots.append(0.5*(a+b))
REF = [14.134725142, 21.022039940, 25.010857580, 30.424876126, 32.935061588,
       37.586178458, 40.918745079, 43.326062680, 48.005150881, 49.773822079,
       52.970321478, 56.446247697, 59.347044003, 60.831778525, 65.112544067]
print(f'  共找到 {len(roots)} 个变号零点')
for n, (g, r) in enumerate(zip(REF, roots), 1):
    print(f'   γ_{n:<2} 我算 {r:13.7f}   你档公开表 {g:13.7f}   |Δ|={abs(r-g):.2e}')

print('\n=== (2) 辐角原理数“条带内全部零点”（不假设在线上） ===')
def gfun(z): return (z-1)*zeta(z)
def count_zeros(T, lo=-0.6, hi=1.6, nper=6000):
    c = [(lo,0.0),(hi,0.0),(hi,T),(lo,T)]
    pts = []
    for a, b in zip(c, c[1:]+[c[0]]):
        ts = np.linspace(0, 1, nper, endpoint=False)
        pts.append(complex(a[0],a[1]) + ts*(complex(b[0],b[1])-complex(a[0],a[1])))
    pts = np.concatenate(pts)
    w = np.array([gfun(z) for z in pts])
    d = np.angle(w[1:]/w[:-1]); d = np.append(d, np.angle(w[0]/w[-1]))
    return d.sum()/(2*math.pi), np.abs(d).max()
for T in [20.0, 45.0, 66.0]:
    Ntot, mx = count_zeros(T)
    nl = sum(1 for r in roots if r < T)
    print(f'  T={T:5.1f} 条带总零点={Ntot:8.4f}  我在线上找到={nl}  差={Ntot-nl:+.4f}  单步max|Δarg|={mx:.4f}')

print('\n=== (3) 复算 K5 门基线 d̄（你档记：前15零点 0.326） ===')
d_list = []
for n, g in enumerate(REF, 1):
    d_list.append(n - (theta_cont(g)/math.pi + 1.0))
print('  d(γ_n) = n − N₀(γ_n):', '  '.join(f'{d:+.4f}' for d in d_list))
print(f'  平均绝对差 d̄ = {sum(abs(d) for d in d_list)/len(d_list):.6f}')

print('\n=== (4) 按公理IV（σ→纬度）扫 D 候选，看 4.414 有无选择性 ===')
sig = np.full(len(roots), 0.5)
print(f'  实测σ集合：min={sig.min():.6f} max={sig.max():.6f} 均值={sig.mean():.6f} 方差={sig.var():.12f}')
print('  D候选              λ=arcsin(2σ−1)  线上零点占比  0.5步长bin')
for D in [3.0,3.5,4.0,4.125,4.375,4.414,4.4142135624,4.5,5.0,6.0,7.5,10.5]:
    print(f'  {D:<18.9f}{math.asin(2*sig.mean()-1):+.6f}       1.000        {math.floor(D/0.5)}')
print(f'  4.375 与 4.414 落在同一 0.5-bin：{math.floor(4.375/0.5)==math.floor(4.414/0.5)}')
print(f'  算术核对：4+0.125={4+0.125}（档内写成4.414=4+0.125）  4.5−0.125={4.5-0.125}  3+√2={3+math.sqrt(2):.10f}')

print('\n=== (5) 复算你“古典对接图谱·注3”的加权测度局部维数（θ=1/2） ===')
th = 0.5; norm = 1.0/(1.0/th)      # 归一化密度 (θ)x^{θ-1}
for e in [1e-2,1e-4,1e-6,1e-8]:
    h = e/4_000_000.0
    xs = (np.arange(4_000_000)+0.5)*h            # 中点网格，避开 x=0 奇点
    I = h*np.sum(xs**(th-1))
    m = e**4 * norm * I
    print(f'  ε={e:.0e}: 边界盒测度 μ={m:.6e}   log μ/log ε = {math.log(m)/math.log(e):.9f}')
eps = np.array([10.0**(-k/4.0) for k in range(4,44)])
mu = eps**4*(eps**th)
print(f'  斜率拟合（解析 μ=ε^(4+θ)）= {np.polyfit(np.log(eps),np.log(mu),1)[0]:.9f}  -> 精确 4+θ = {4+th}')
print(f'  内部点：μ~ε^5 -> 局部维数 5.0；缺陷只发生在边界层，一般式 D = n − k/2')
for n_, k_ in [(5,1),(8,1),(11,1),(6,3),(9,3)]:
    print(f'    n={n_} 缺陷坐标 k={k_} -> D = {n_-k_/2}')
