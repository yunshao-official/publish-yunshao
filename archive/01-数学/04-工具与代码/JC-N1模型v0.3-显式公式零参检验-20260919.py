# -*- coding: utf-8 -*-
"""
JC-N1 模型 v0.3 · 零自由参数显式公式 + 禁数修正项检验（2026-09-19，ZCode）
v0.2→v0.3（路线收敛后按 R-N12 执行）：
  U1 放弃自由振幅：改用 von Mangoldt ψ 的截断显式公式（系数 1/ρ 理论固定，零拟合参数）
     ψ_trunc(x) = x − 2·Re[Σ_{n≤30} x^{ρ_n}/ρ_n] − ln(2π)，ρ_n=1/2+iγ_n
     对照对象：精确 ψ(x)=Σ_{p^k≤x} ln p（筛法直算）
  U2 检验一（主流公式质量，零参数）：R²(ψ_exact vs ψ_trunc) 全窗+训练/留出
  U3 检验二（体系对接）：显式公式残差 r(x)=ψ_exact−ψ_trunc 与跨族禁数密度增量的相关
     ——禁数骨架降为修正项后，修正项是否解释 30 零点之外的部分
诚实标签：ψ₀ 的 ln(1−x^{-2})/2 项在 x>10 后可忽略（<0.005）；30 零点截断的 Gibbs 影响如实报告。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
X = 2_000_000
ZEROS = [14.134725,21.022040,25.010858,30.424876,30.424876]  # 占位防重复——真实表见下
ZEROS = [14.134725,21.022040,25.010858,30.424876,32.935062,37.586178,40.918719,
         43.327073,48.005151,49.773832,52.970321,56.446248,59.347044,60.831779,
         65.112544,67.079811,69.546402,72.067158,75.704691,77.144840,79.337375,
         82.910381,84.735493,87.425275,88.809111,92.491899,94.651344,95.870634,
         98.831194,101.317853]

def sieve(n):
    is_p = bytearray([1])*(n+1); is_p[0:2]=b"\x00\x00"
    for i in range(2, int(n**0.5)+1):
        if is_p[i]: is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return is_p
isp = sieve(X)

# 精确 ψ(x)：Σ_{p^k≤x} ln p（前缀数组）
psi_arr = [0.0]*(X+1)
acc = 0.0
for n in range(2, X+1):
    if isp[n]:
        pk = n
        while pk <= X:
            acc += math.log(n)
            pk *= n
    psi_arr[n] = acc

# 跨族禁数增量（修正项用）：S(x) 网格增量
FAMS8 = {1,5,7,11,13,17,19,23}
from bisect import bisect_right
fam_primes = {f: [] for f in FAMS8}
for n in range(2, X+1):
    if isp[n] and (n % 24) in fam_primes:
        fam_primes[n % 24].append(n)
small_primes = [p for p in range(2, math.isqrt(X)+1) if isp[p]]
def S_cross(x):
    t = 0
    for p in small_primes:
        qmax = x // p
        if qmax < p: break
        a = p % 24
        for f in FAMS8:
            if f == a: continue
            lst = fam_primes[f]
            t += bisect_right(lst, qmax) - bisect_right(lst, p)
    return t

grid = [10_000*i for i in range(1, 201)]
psi_exact = [psi_arr[x] for x in grid]
psi_trunc = []
for x in grid:
    Lx = math.log(x); sq = math.sqrt(x)
    s = 0.0
    for g in ZEROS:
        # Re[x^ρ/ρ] = √x·Re[e^{iγLx}/(1/2+iγ)] = √x·(0.5·cos+γ·sin)/(0.25+γ²)
        denom = 0.25 + g*g
        s += sq*(0.5*math.cos(g*Lx) + g*math.sin(g*Lx))/denom
    psi_trunc.append(x - 2*s - math.log(2*math.pi))

def r2(a, b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    sxy=sum((u-ma)*(v-mb) for u,v in zip(a,b))
    va=sum((u-ma)**2 for u in a); vb=sum((v-mb)**2 for v in b)
    return sxy*sxy/(va*vb), sxy/(n*ma*mb if ma*mb else 1)

print("="*66)
print("JC-N1 模型 v0.3 · 零参数显式公式 + 禁数修正项 ｜ 2026-09-19")
print("="*66)
r2_all, corr_all = r2(psi_exact, psi_trunc)
print(f"U1 ψ 零参数截断公式（30 零点，系数 1/ρ 理论固定）：")
print(f"  全窗：R²={r2_all:.6f}  相关 corr={corr_all:.6f}")
tr = [i for i in range(200) if grid[i] <= 1_000_000]
va = [i for i in range(200) if grid[i] > 1_000_000]
r2t,_ = r2([psi_exact[i] for i in tr],[psi_trunc[i] for i in tr])
r2v,_ = r2([psi_exact[i] for i in va],[psi_trunc[i] for i in va])
print(f"  训练域（x≤1e6）R²={r2t:.6f}｜留出域（x>1e6）R²={r2v:.6f}")
err = [abs(psi_exact[i]-psi_trunc[i]) for i in range(200)]
print(f"  绝对误差：中位 {sorted(err)[100]:.1f}｜最大 {max(err):.1f}（ψ(2e6)≈{psi_exact[-1]:.0f}，相对≈{max(err)/psi_exact[-1]*100:.2f}%）")

# U3 残差 vs 禁数修正项
resid = [psi_exact[i]-psi_trunc[i] for i in range(200)]
Sv = [S_cross(x) for x in grid]
# 禁数密度增量（窗口增量，去光滑趋势：对 S(x) 减 x/log²x 拟合）
fitS = [x/math.log(x)**2 for x in grid]
mx=sum(fitS)/len(fitS); my=sum(Sv)/len(Sv)
beta=sum((f-mx)*(s-my) for f,s in zip(fitS,Sv))/sum((f-mx)**2 for f in fitS)
Sres = [s-(beta*f+ (my-beta*mx)) for s,f in zip(Sv,fitS)]
r2m, crm = r2(resid, Sres)
print(f"\nU3 显式公式残差 r(x)（30 零点之外）× 跨族禁数密度增量：")
print(f"  相关 corr={crm:.4f}（R²={r2m:.4f}）")
r2d, crd = r2([delta/1 for delta in [psi_exact[i]-psi_trunc[i] for i in range(200)]], Sres)  # 占位
# Δ(x) 与禁数增量的直接相关（v0.1 问题的零参数重问）
pi_arr=[0]*(X+1); c0=0
for i in range(X+1):
    if isp[i]: c0+=1
    pi_arr[i]=c0
def Li(x):
    L=math.log(x); s=0.0; term=1.0
    for k in range(1,60): term*=L/k; s+=term/k
    return 0.5772156649+math.log(math.log(x))+s
Dv=[pi_arr[x]-Li(x) for x in grid]
r2dd, crdd = r2(Dv, Sres)
print(f"  附：Δ(x)=π−Li × 禁数密度增量：corr={crdd:.4f}（v0.1 问题的零参数版回答）")

print("\n判定（模型 v0.3）：")
print(f"  └ U1：零参数显式公式在全窗 R²={r2_all:.4f}——主流公式对本域数据的直接质量分（无任何拟合）")
print(f"  └ U3：残差×禁数相关 corr={crm:.3f}——若≈0：30零点之外的残差由更高零点主导（主流预期），")
print(f"    禁数修正项在该域无显著解释力；若显著非零：禁数骨架获得修正项定位的首个实证")
print(f"  └ 模型线总结论待 U3 数字——无论结果均入账（判负也是进展）")
