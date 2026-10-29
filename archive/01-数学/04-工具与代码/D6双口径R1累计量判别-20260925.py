# -*- coding: utf-8 -*-
"""
D6 双口径 R1 累计量读法判别 v1.0（2026-09-25，知世"都试试"）
前置：密度读法已判负（JC-N3）；磨光读法旧口径退化（RD-1 材料）。本轮=唯一未试的合法读法 R1（累计量）：
  口径B（共振 t=96T）：累计零点数 N_zero(96·T_k) vs 累计禁数 C(T_k)=Σ_{d'≤d_k} N_{d'}
  口径A（旧 t=α/T）：t=α/T ∈[0.136,1.5] 全部落首零点下方 → 累计零点数恒 0（结构退化）
数据：零点侧=Odlyzko 100k 存档实际计数（γ≤300 内 138 个，另用全表计数核对高带）；禁数侧=R-N10 十档。
诚实标签：执行层读法实验；Spearman/L1 形状对比；判读留账本（R-N22）。
"""
import sys, math, bisect
sys.stdout.reconfigure(encoding='utf-8')
ZPATH = r"H:\理论存档\01-数学\02-实验与数据\results\odlyzko_zeros1-100k-20260921.txt"
gammas = [float(l) for l in open(ZPATH) if l.strip()]
H = {2: 29555, 4: 34288, 6: 52977, 8: 19819, 10: 23379,
     12: 34223, 14: 10932, 16: 14544, 18: 15704, 22: 4742}
DS = sorted(H)
ALPHA = 1/8

# 累计禁数 C(T_k)
cum = 0; C = []; Ts = []
for d in DS:
    cum += H[d]; C.append(cum); Ts.append(d/24)
Ctot = C[-1]
Cfrac = [c/Ctot for c in C]

# 实际零点累计计数函数（全表 100k）
def Nz(t):
    return bisect.bisect_right(gammas, t)

def spearman(x, y):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); r = [0]*len(v)
        for i, j in enumerate(s): r[j] = i
        return r
    rx, ry = rk(x), rk(y)
    n = len(x); mx = sum(rx)/n; my = sum(ry)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a-mx)**2 for a in rx)); vy = math.sqrt(sum((b-my)**2 for b in ry))
    return sxy/(vx*vy) if vx and vy else None

print("="*66)
print("D6 双口径 R1 累计量读法判别 ｜ 2026-09-25")
print("="*66)
print(f"{'T':>7} {'d':>3} {'累计禁数':>9} {'占比':>7} {'口径B:t=96T':>10} {'实际零点≤t':>9} {'口径B占比':>8} {'口径A:t=α/T':>10} {'A零点数':>7}")
Bfrac = []
Afrac = []
normB = Nz(96*Ts[-1])
for k in range(10):
    tB = 96*Ts[k]; tA = ALPHA/Ts[k]
    zB = Nz(tB); zA = Nz(tA)
    Bfrac.append(zB/normB if normB > 0 else 0)
    Afrac.append(0.0 if zA == 0 else zA)
    print(f"{Ts[k]:>7.4f} {DS[k]:>3} {C[k]:>9,} {Cfrac[k]:>7.3f} {tB:>10.1f} {zB:>9} {Bfrac[k]:>8.3f} {tA:>10.3f} {zA:>7}")

rhoB = spearman(Cfrac, Bfrac)
rhoA = spearman(Cfrac, Afrac) if any(a > 0 for a in Afrac) else None
# L1 形状距离（归一化累计曲线）
l1B = sum(abs(a-b) for a, b in zip(Cfrac, Bfrac))/len(Cfrac)
l1A = sum(abs(a-b) for a, b in zip(Cfrac, Afrac))/len(Cfrac)
print(f"\n结果（R1 累计量，归一化形状对比）：")
print(f"  口径B：Spearman ρ={rhoB:.4f}｜L1 形状距离={l1B:.4f}")
print(f"  口径A：累计零点数恒 0（全部 t=α/T≤1.5<γ₁）→ 结构退化，ρ 无定义，L1={l1A:.3f}")
print(f"  最大带对比：末带（d=22）累计占比 禁数=1.000 vs 口径B 零点={Bfrac[-1]:.3f}；首带（d=2）禁数={Cfrac[0]:.3f} vs B={Bfrac[0]:.3f}")

print("\n判读（R1 累计量，留账本 R-N22）：")
print(f"  └ 口径A：密度读法判负（JC-N3）+ 磨光读法退化（RD-1）+ 累计读法恒零（本试）——三种合法读法下均无信息，")
print("    旧口径的结构性无信息至此三读法闭合")
print(f"  └ 口径B：方向成立（单调增对单调增，ρ={rhoB:.2f}），但 L1={l1B:.2f} 说明形状非重合——")
print("    '累计同谱'在 10 档分辨率下为粗粒度成立/细形状不成立的中间态；")
print("    更细判别需禁数侧有超出 10 档的分辨率（结构上限，见 RD-1 材料 10 原子注）")
print("  └ 综合三读法：D6 二选一的裁决材料完整——A 全读法无信息；B 唯一有数据口径但细形状未合")
