# -*- coding: utf-8 -*-
"""
JC-N3 双张力口径判别实验 v1.0（2026-09-19，ZCode）
判据来源：《云韶数论×主流数学·数论卷v1.0》§五 JC-N3
对象：数论册 §4.2 旧口径 T=α/|t| vs §11 修正口径 T=αt/12（α=1/8）
映射主张（§4.2 原话）："零点在临界线上的密度对应着该张力范围内禁数的出现频率"
方法：
  1) 实测：筛素数至 X，统计素数对 (p,q)（跨族，pq≤X）按张力 T=|a-b|/24 的频率直方图
  2) 两口径预测：禁数密度(T) := 零点密度 ρ(t(T))，ρ(t)=ln(t/2π)/(2π)（Riemann-von Mangoldt）
     口径A：t=α/T；口径B：t=12T/α
  3) 各口径预测曲线与实测直方图做形状相关（Pearson，尺度无关）
附：4096 压缩信息容量复核 + 177 步半衰期复算（离散 Riccati，κ=1/32,T₀=1/8）
诚实标签：执行层数值实验；奇异级数按族对均匀近似（未逐对加权）。
"""
import sys, math
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
ALPHA = 1/8
FAMS = [1,5,7,11,13,17,19,23]          # 模24互素八族 = (Z/24)^× ≅ C₂³
X = 2_000_000                           # 素数对扫描上限

def sieve(n):
    is_p = bytearray([1])*(n+1); is_p[0:2] = b"\x00\x00"
    for i in range(2, int(n**0.5)+1):
        if is_p[i]: is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return [i for i in range(n+1) if is_p[i]]

primes = sieve(X)
fam = {p: p % 24 for p in primes}

# 实测：跨族素数对 (p<q, pq≤X) 按张力 T=|a-b|/24 的数量
# 修正（R-N10）：2、3 的剩余类不属八族，含 2/3 的对不入禁数定义（初版污染已剔除）
FAMS8 = {1,5,7,11,13,17,19,23}
hist = Counter()
npairs = 0
for i, p in enumerate(primes):
    if p*p > X: break
    a = fam[p]
    if a not in FAMS8: continue
    for q in primes[i+1:]:
        if p*q > X: break
        b = fam[q]
        if b in FAMS8 and b != a:
            hist[abs(a-b)] += 1
            npairs += 1

ds = sorted(set(abs(a-b) for a in FAMS for b in FAMS if a != b))   # 可能的族差
actual = [hist.get(d,0) for d in ds]
Ts = [d/24 for d in ds]

# 两口径预测（尺度无关，只比形状）
def rho(t):  # Riemann-von Mangoldt 密度
    return math.log(t/(2*math.pi))/(2*math.pi) if t > 2*math.pi else float('nan')

predA, predB, validA = [], [], 0
for T in Ts:
    a_val = rho(ALPHA/T)          # 口径A：t=α/T
    b_val = rho(12*T/ALPHA)       # 口径B：t=12T/α
    predA.append(a_val); predB.append(b_val)
    if a_val == a_val: validA += 1   # nan 计数

def pearson(x, y):
    n=len(x); ok=[(x[i],y[i]) for i in range(n) if x[i]==x[i] and y[i]==y[i]]
    if len(ok)<3: return None, len(ok)
    xs=[v for v,_ in ok]; ys=[w for _,w in ok]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    sxy=sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    sx=math.sqrt(sum((a-mx)**2 for a in xs)); sy=math.sqrt(sum((b-my)**2 for b in ys))
    return (sxy/(sx*sy) if sx and sy else None), len(ok)

rA, nA = pearson(actual, predA)
rB, nB = pearson(actual, predB)

print("="*64)
print("JC-N3 双张力口径判别实验 v1.0 ｜ 2026-09-19")
print("="*64)
print(f"参数：α=1/8，X={X:,}，有效跨族素数对 N={npairs:,}")
print(f"族差集合（可取 d）：{ds}")
print(f"实测直方图（d:count）：")
for d in ds:
    print(f"   d={d:>2} (T={d/24:.4f}): {hist.get(d,0):>9,}")
print(f"\n口径A（T=α/|t|，即 t=α/T）预测：ρ(α/T)")
print(f"  区间有效性：{validA}/{len(Ts)} 个张力档给出正值密度（其余 t≤2π 密度无定义/负）")
print(f"口径B（T=αt/12，即 t=12T/α=96T）预测：ρ(96T)")
print(f"  区间有效性：{len(Ts)}/{len(Ts)}（全档正值）")
print(f"\n形状相关（Pearson，剔除无效档）：")
print(f"  口径A vs 实测：r={rA if rA is None else round(rA,4)}（有效档 {nA}/{len(Ts)}）")
print(f"  口径B vs 实测：r={rB if rB is None else round(rB,4)}（有效档 {nB}/{len(Ts)}）")

# 定性判定
verdict = []
if validA < len(Ts):
    verdict.append("口径A在大部分张力档（T>α/2π≈0.0199，即 d>0.48 的全部档）预测密度为负/无定义——区间失效")
if rB is not None and rB < 0:
    verdict.append("口径B趋势方向与实测相反（实测峰在中段族差，log增曲线单调——负相关）")
best = max([r for r in (rA, rB) if r is not None], default=None)
print("\n判定（JC-N3）：")
if best is not None and best > 0.8:
    print(f"  最高相关 r={best:.4f}>0.8 → 对应口径存活")
else:
    print("  两套口径与『零点密度=禁数密度』的直接映射均不自洽（A区间失效/B方向相反）")
    print("  → 按 P-19 判据优先：该读法判负入档；注意这只判负『密度=密度』这一种映射读法，")
    print("    不判负零点-禁数对应本身（累计量/权重加权/反向映射等读法留待轨道②澄清后重测）")
for v in verdict: print("  └ "+v)

print("\n" + "="*64)
print("附1：4096 倍压缩信息容量复核（JC-N5 相关）")
print(f"  12族口径：族对组合 ≤12×12=144 → 信息量 ≤ log2(144)={math.log2(144):.2f} bit")
print(f"   8族口径：族对组合 8×8=64      → 信息量 ≤ log2(64)={math.log2(64):.2f} bit")
print(f"  定理9.1 声称压缩 2^12=4096 倍 = 12 bit —— 超出纯剩余类信息容量（对表差异#2 维持）")
print("\n附2：半衰期复算（离散 Riccati，κ=1/32，T₀=1/8）")
step = 1 - (1/32)*(1/8)
print(f"  每步衰减因子 1-κT₀ = 1-1/256 = {step} = 255/256")
print(f"  半衰期 n = ln(0.5)/ln(255/256) = {math.log(0.5)/math.log(step):.1f} 步 → ≈177 步（新常数口径自洽值）")
