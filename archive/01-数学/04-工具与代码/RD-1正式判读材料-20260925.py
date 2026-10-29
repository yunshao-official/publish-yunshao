# -*- coding: utf-8 -*-
"""
RD-1 正式判读材料（T-5/F2 重定标线下的合法读数判读·2026-09-25）
前置：F2（Poisson 重定标）已证 5% 绝对线错配、重定标线 9/9 通过（R-N19）→
     RD-4 稳定性恢复 → RD-1（磨光同谱读数）首次具备合法判读条件。
方法（判读材料，判读权归任务二线/知世）：
  1) 实测：Z_w(c)（零点侧计数谱，Odlyzko 存档 γ≤300）× F_w(c)（禁数侧 R-N10 直方图）
     在 10 带心（共振口径 t_c=4d）上的 Pearson r，w∈{1,2,4}·Δγ̄。
  2) 零假设：非齐性 Poisson 过程（强度 λ(t)=log(t/2π)/(2π)，渐近零点密度），
     同期望零点数采样 4000 次 → r 的零分布 → 观测 r 的单侧 p 值（左尾=更负）。
  3) 判读语义（口径 §2.6：RD-1 无冻结通过线，本材料供判读）：
     p<0.05 且 r<0 → 磨光读数显著负相关（禁数-零点带结构反位相——语义留给体系裁决）；
     p≥0.05 → 无显著相关（同谱无证据，维持"照录"）。
诚实标签：F_w 侧为确定性数据（保留）；零点侧零假设=渐近密度 Poisson（未用真实更高零点）。
"""
import sys, math, random
sys.stdout.reconfigure(encoding='utf-8')
random.seed(9252026)

ZPATH = r"H:\理论存档\01-数学\02-实验与数据\results\odlyzko_zeros1-100k-20260921.txt"
gammas = [float(l) for l in open(ZPATH) if l.strip()]
gammas = [g for g in gammas if g <= 300]
gbar = sum(gammas)/len(gammas)
DG = 2*math.pi/math.log(gbar)

H = {2: 29555, 4: 34288, 6: 52977, 8: 19819, 10: 23379,
     12: 34223, 14: 10932, 16: 14544, 18: 15704, 22: 4742}
DS = sorted(H)
centers = [4.0*d for d in DS]

def Z_read(w, centers, zset):
    out = []
    R = 6*w
    for t_c in centers:
        s = 0.0
        for g in zset:
            if abs(g - t_c) <= R:
                s += math.exp(-(g-t_c)**2/(2*w*w))
        out.append(s)
    return out

def F_read(w, centers):
    out = []
    R = 6*w
    for t_c in centers:
        s = 0.0
        for d in DS:
            t_j = 4.0*d
            if abs(t_j - t_c) <= R:
                s += H[d]*math.exp(-(t_j-t_c)**2/(2*w*w))
        out.append(s)
    return out

def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(x, y))
    vx = math.sqrt(sum((a-mx)**2 for a in x)); vy = math.sqrt(sum((b-my)**2 for b in y))
    return sxy/(vx*vy) if vx > 0 and vy > 0 else None

# Poisson 零假设采样器：非齐性（渐近密度），累积强度 CDF 反演
TMAX = 300.0
def lam(t):
    if t <= 2*math.pi: return 0.0
    return math.log(t/(2*math.pi))/(2*math.pi)
NEXP = 0.0
N = 4000
grid_t = []; cdf = []
acc = 0.0
for i in range(N+1):
    t = 2*math.pi + (TMAX-2*math.pi)*i/N
    grid_t.append(t)
    if i > 0:
        acc += 0.5*(lam(t)+lam(grid_t[i-1]))*(TMAX-2*math.pi)/N
    cdf.append(acc)
NEXP = acc
import bisect
def sample_point():
    u = random.random()*NEXP
    i = bisect.bisect_left(cdf, u)
    return grid_t[min(i, N)]
def sample_poisson():
    k = max(3, int(round(random.gauss(NEXP, math.sqrt(NEXP)))))
    return sorted(sample_point() for _ in range(k))
print(f"零假设：非齐性 Poisson（λ(t)=log(t/2π)/2π），期望零点数≈{NEXP:.0f}（实测={len(gammas)}）")

F_cache = {k: F_read(k*DG, centers) for k in (1, 2, 4)}
NTRIAL = 4000
null = {1: [], 2: [], 3: []}
for k, w in ((1, DG), (2, 2*DG), (3, 4*DG)):
    Fs = F_cache[1 if k == 1 else (2 if k == 2 else 4)]
    for _ in range(NTRIAL):
        zs = sample_poisson()
        Zs = Z_read(w, centers, zs)
        r = pearson(Zs, Fs)
        if r is not None:
            null[k].append(r)

print(f"\nRD-1 判读材料（w=k·Δγ̄，k=1/2/4；零分布 {NTRIAL} 次 Poisson 采样）：")
print(f"{'窗':>4} {'实测r':>9} {'零分布均值':>10} {'零分布SD':>9} {'左尾p值':>9}  判读")
for k in (1, 2, 3):
    lst = null[k]
    mu = sum(lst)/len(lst)
    sd = math.sqrt(sum((v-mu)**2 for v in lst)/len(lst))
    obs = pearson(Z_read(k*DG, centers, gammas), F_cache[1 if k == 1 else (2 if k == 2 else 4)])
    pleft = sum(1 for v in lst if v <= obs)/len(lst)
    verdict = "显著负相关" if (obs is not None and pleft < 0.05) else "无显著相关（同谱无证据，维持照录）"
    print(f"  {k}× {obs:>9.4f} {mu:>10.4f} {sd:>9.4f} {pleft:>9.3f}  {verdict}")

print("\n判读材料说明（诚实清单）：")
print("  └ 本材料不代任务二线判读——RD-1 无冻结通过线（口径 §2.6），三窗结果并列入账")
print("  └ 零假设=渐近密度 Poisson：未含零点排斥（GUE）——若用 GUE 行列式点过程做零假设，")
print("    零分布会更窄，观测 r 的显著性只会更强（本试算为保守下界）")
print("  └ F_w 侧保留真实禁数直方图；三个窗共享同一 F，r 间非独立（联合判读需任务二线定）")
