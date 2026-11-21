# -*- coding: utf-8 -*-
"""
JC-N1 三代禁数模型 v0.2 · 零点相位项+T<κ代谢冻结（2026-09-19，ZCode）
v0.1→v0.2 三项升级（方向由 v0.1 三缺陷指明，R-N09）：
  U1 零点相位项（对接数论册 §4/§8 显式公式）：Δ_osc = B·(√x/ln x)·Σ_{n≤30} sin(γ_n·ln x)/γ_n
     γ_n = ζ 前 30 个非平凡零点纵标（主流公认常数表）
  U2 T<κ 代谢冻结（原文 §6.5-6.6）：张力按 T_{n+1}=T_n−κT_n² 离散代谢，T≤κ 冻结；
     冻结后衰减停止 → 每禁数衰减因子=exp(−Σ_{n<freeze} T_n^g)（逐档预计算，仅10个T₀）
  U3 训练/验证分割：x≤10^6 拟合 (A,B,c)，x∈(10^6,2×10^6] 留出验证
检验：
  W1 留出域 R²/斜率（对照 v0.1 全窗拟合）
  W2 模型首次变号预测（外推 N_d(x)≈C_d·x/log²x，扫描至 10^20）
     对照已证事实：Δ(x)<0 至少到 10^14（Kotnik 类验算）——若模型提前翻正即判伪
诚实标签：外推 N_d 用平滑近似（校准于 2×10⁶）；零点取 30 个（更高零点贡献次要）。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
X = 2_000_000
ALPHA, KAPPA = 1/8, 1/32
FAMS8 = {1,5,7,11,13,17,19,23}
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
primes = [i for i in range(2, X+1) if isp[i]]

def gen_exp(d):
    T = d/24
    return 1 if T <= ALPHA else (2 if T <= 1/math.sqrt(6) else 3)

# 每族差档的冻结衰减因子：log d(τ) = -Σ_{n=1}^{min(τ,n_f)} T_n^{g}，T_{n+1}=T_n−κT_n²
DS = [2,4,6,8,10,12,14,16,18,22]
MAXTAU = int(math.ceil(20*math.log(X)))   # τ=c·ln x，c≤20 足够
def freeze_logdecay(d, tau):
    T = d/24; g = gen_exp(d)
    s = 0.0
    n = 0
    while n < tau and T > KAPPA:
        s += T**g
        T = T - KAPPA*T*T
        n += 1
    return -s, n   # log d 与冻结步数
pre = {d: [freeze_logdecay(d, t) for t in range(MAXTAU+1)] for d in DS}
nf = {d: pre[d][MAXTAU][1] for d in DS}

# 数据：N_d(x) 网格 + π/Li/Δ（同 v0.1 管线）
grid = [10_000*i for i in range(1, 201)]
Nd = {d: [0]*len(grid) for d in DS}
pairs = []
for i, p in enumerate(primes):
    if p*p > X: break
    a = p % 24
    if a not in FAMS8: continue
    for q in primes[i+1:]:
        if p*q > X: break
        b = q % 24
        if b in FAMS8 and b != a:
            pairs.append((p*q, abs(a-b)))
pairs.sort()
counts = {d:0 for d in DS}; ptr = 0
for gi, x in enumerate(grid):
    while ptr < len(pairs) and pairs[ptr][0] <= x:
        counts[pairs[ptr][1]] += 1; ptr += 1
    for d in DS: Nd[d][gi] = counts[d]

pi_arr=[0]*(X+1); c0=0
for i in range(X+1):
    if isp[i]: c0+=1
    pi_arr[i]=c0
def li(x):
    L=math.log(x); s=0.0; term=1.0
    for k in range(1,60): term*=L/k; s+=term/k
    return 0.5772156649+math.log(math.log(x))+s
delta=[pi_arr[x]-li(x) for x in grid]

def core_at(gi_, x, c):
    tau = min(int(c*math.log(x)), MAXTAU)
    return sum(Nd[d][gi_]*math.exp(pre[d][tau][0]) for d in DS)
def osc(x):
    Lx = math.log(x)
    return (math.sqrt(x)/Lx)*sum(math.sin(g*Lx)/g for g in ZEROS)

# 线性拟合 (A,B)：Δ ≈ -A·F + B·G，F=core(无振荡)，G=osc
def fitAB(c, idxs):
    F = [core_at(i, grid[i], c) for i in idxs]
    G = [osc(grid[i]) for i in idxs]
    Y = [delta[i] for i in idxs]
    n=len(idxs)
    sFF=sum(f*f for f in F); sGG=sum(g*g for g in G); sFG=sum(f*g for f,g in zip(F,G))
    sFY=sum(f*y for f,y in zip(F,Y)); sGY=sum(g*y for g,y in zip(G,Y)); sY=sum(Y)
    det = sFF*sGG - sFG*sFG
    if abs(det) < 1e-300: return None
    A = (sGG*sFY - sFG*sGY)/det
    B = (sFF*sGY - sFG*sFY)/det
    pred=[-A*f+B*g for f,g in zip(F,G)]
    my=sum(Y)/n
    r2 = 1 - sum((y-p)**2 for y,p in zip(Y,pred))/sum((y-my)**2 for y in Y)
    return A, B, r2

train = [i for i in range(len(grid)) if grid[i] <= 1_000_000]
val   = [i for i in range(len(grid)) if grid[i] >  1_000_000]
print("="*66)
print("JC-N1 三代禁数模型 v0.2 · 相位项+T<κ冻结 ｜ 2026-09-19")
print("="*66)
print(f"冻结档位：各 d 的代谢冻结步数 n_f（T≤κ=1/32 即冻结）=")
print("  " + ", ".join(f"d{d}:{nf[d]}" for d in DS))
best=None
for ci in range(0, 2001):
    c = ci*0.01
    r = fitAB(c, train)
    if r and (best is None or r[2] > best[2]):
        best = (c,)+r
c_b, A_b, B_b, r2_tr = best
# 留出验证
Fv=[core_at(i, grid[i], c_b) for i in val]; Gv=[osc(grid[i]) for i in val]
Yv=[delta[i] for i in val]
pred=[-A_b*f+B_b*g for f,g in zip(Fv,Gv)]
my=sum(Yv)/len(Yv)
r2_val = 1 - sum((y-p)**2 for y,p in zip(Yv,pred))/sum((y-my)**2 for y in Yv)
print(f"\nW1 拟合（训练域 x≤1e6）：c={c_b:.2f}  A={A_b:.4g}  B={B_b:.4g}  R²_train={r2_tr:.4f}")
print(f"   留出验证（x∈(1e6,2e6]）：R²_val={r2_val:.4f}")
print(f"   振荡项符号：B{'>0' if B_b>0 else '<0'}（|B|/|A|={abs(B_b/A_b):.3g}）")

# W2 外推首次变号
print("\nW2 首次变号预测（外推 N_d(x)≈C_d·x/log²x，C_d 校准于 x=2e6；外推至 1e20）：")
Cd = {d: Nd[d][-1]*math.log(X)**2/X for d in DS}
def model_at(x):
    tau = min(int(c_b*math.log(x)), MAXTAU)
    core = sum(Cd[d]*(x/math.log(x)**2)*math.exp(pre[d][tau][0]) for d in DS)
    return -A_b*core + B_b*osc(x)
xstar = None
xx = X*1.01
while xx < 1e20:
    v = model_at(xx)
    if v > 0:
        xstar = xx; break
    xx *= 1.02
if xstar:
    print(f"  模型预测首次 Δ>0 于 x* ≈ {xstar:.3g}")
    if xstar < 1e14:
        print("  判伪：与已验算事实（Δ(x)<0 至 10^14 量级）冲突 → v0.2 振荡项参数被否")
    else:
        print("  与已验算事实相容（未在 10^14 前翻正）——v0.2 通过最低一致性检验")
else:
    print("  至 1e20 无变号——与已验算事实相容；与 Littlewood 定理的相容性依赖更高项/更长程振荡")
print("\nW1b 对照：冻结-only 分支（B=0，同 c 扫描）")
bestf=None
for ci in range(0, 2001):
    c = ci*0.01
    idxs=train
    F=[core_at(i, grid[i], c) for i in idxs]; Y=[delta[i] for i in idxs]
    n=len(idxs); sF=sum(F); sY=sum(Y)
    sFF=sum(f*f for f in F); sFY=sum(f*y for f,y in zip(F,Y))
    det=sFF*n-sF*sF
    if abs(det)<1e-300: continue
    A=(n*sFY-sF*sY)/det; a0=(sY-A*sF)/n
    pred=[-A*f+a0 for f in F]
    my=sum(Y)/n
    r2=1-sum((y-p)**2 for y,p in zip(Y,pred))/sum((y-my)**2 for y in Y)
    if bestf is None or r2>bestf[2]: bestf=(c,A,a0,r2)
c_f,A_f,a0_f,r2_f=bestf
Fv=[core_at(i,grid[i],c_f) for i in val]; Yv=[delta[i] for i in val]
predv=[-A_f*f+a0_f for f in Fv]; myv=sum(Yv)/len(Yv)
r2v=1-sum((y-p)**2 for y,p in zip(Yv,predv))/sum((y-myv)**2 for y in Yv)
lx=[math.log(grid[i]) for i in val]; ls=[math.log(abs(-A_f*f+a0_f)) for f in Fv]
mx=sum(lx)/len(lx); ms=sum(ls)/len(ls)
sl_val=sum((a-mx)*(b-ms) for a,b in zip(lx,ls))/sum((a-mx)**2 for a in lx)
print(f"   c={c_f:.2f} A={A_f:.4g} 常数项a0={a0_f:.1f} R²_train={r2_f:.4f} R²_val={r2v:.4f} 留出域模型斜率={sl_val:.3f}（数据0.382参照）")

print("\n判定（模型 v0.2）：")
print(f"  └ 相位项使符号翻转在结构上成为可能（Littlewood 相容性修复）")
print(f"  └ 冻结机制（U2）是否抬高 gen1 占比、指数是否靠拢 0.382——见上方 R²/占比输出")
print(f"  └ v0.2 性质：禁数骨架+显式公式相位项的混合模型；拟合参数非体系常数，仅模型参数")
