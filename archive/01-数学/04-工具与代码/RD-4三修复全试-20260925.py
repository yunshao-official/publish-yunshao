# -*- coding: utf-8 -*-
"""
RD-4 三修复全试（T-5·知世"都做都试试"2026-09-25 批准执行）
三个修复方案（上轮判负后的三选一，本轮全试）：
  F1 带心加密：带心从 10 个加密为细网格（两读数经高斯磨光后为 t 的连续函数，
     在细网格上评估稳定性——数据不变，评估点加密）
  F2 判读线重定标：按"纯磨光滑化零假设"重定 5% 线——用同强度齐性 Poisson
     零点过程做代理，估计单纯平滑化带来的预期偏差基线，判读线=基线中位数+2×MAD
  F3 读数降维：点值偏差改为秩判读——Spearman ρ（跨窗宽秩稳定）+ 单调性判定
数据与核：全部沿用口径 v1.0 冻结（Odlyzko 100k 存档 γ≤300；R-N10 十档直方图；
高斯核；共振口径 t_c=4d）。诚实标签：试探执行，判读留账本。
"""
import sys, math, random
sys.stdout.reconfigure(encoding='utf-8')
random.seed(20260925)

ZPATH = r"H:\理论存档\01-数学\02-实验与数据\results\odlyzko_zeros1-100k-20260921.txt"
gammas_all = [float(l) for l in open(ZPATH) if l.strip()]
gammas = [g for g in gammas_all if g <= 300]
gbar = sum(gammas)/len(gammas)
DG = 2*math.pi/math.log(gbar)

H = {2: 29555, 4: 34288, 6: 52977, 8: 19819, 10: 23379,
     12: 34223, 14: 10932, 16: 14544, 18: 15704, 22: 4742}
DS = sorted(H)

def Z_read(w, t_c):
    R = 6*w; s = 0.0
    for g in gammas:
        if abs(g - t_c) <= R:
            s += math.exp(-(g-t_c)**2/(2*w*w))
    return s

def Za_read(w, t_c):
    R = 6*w; s = 0.0
    for g in gammas:
        if abs(g - t_c) <= R:
            s += math.exp(-(g-t_c)**2/(2*w*w))/math.hypot(0.5, g)
    return s

def F_read(w, t_c):
    R = 6*w; s = 0.0
    for d in DS:
        t_j = 4.0*d
        if abs(t_j - t_c) <= R:
            s += H[d]*math.exp(-(t_j-t_c)**2/(2*w*w))
    return s

def reads_at(w, t_c):
    return (Z_read(w, t_c), Za_read(w, t_c), F_read(w, t_c))

# ============ F1 带心加密 ============
print("="*66)
print("F1 带心加密：带心 10 → 161（t∈[8,88] 步长 0.5），读数为连续函数的加密评估")
print("="*66)
fine = [8 + 0.5*i for i in range(161)]
viol = 0; items = 0
for name, fi in (("计数谱", 0), ("振幅谱", 1), ("禁数侧", 2)):
    P = {}
    for k in (1, 2, 4):
        w = k*DG
        P[k] = [reads_at(w, t)[fi] for t in fine]
    for (a, b) in ((1, 2), (2, 4), (1, 4)):
        ds = []
        for pa, pb in zip(P[a], P[b]):
            m = (abs(pa)+abs(pb))/2
            if m > 0: ds.append(abs(pa-pb)/m)
        dv = max(ds)
        items += 1
        flag = "超5%" if dv > 0.05 else "通过"
        if dv > 0.05: viol += 1
        print(f"   {name} w{a}vs{b}: 最大相对偏差 {dv*100:7.2f}%  {flag}（超线点 {sum(1 for d0 in ds if d0>0.05)}/{len(ds)}）")
print(f"   F1 小结：{viol}/{items} 项超线（加密本身不消除平滑化差异——预期内，见 F2）")

# ============ F2 判读线重定标（Poisson 代理零假设） ============
print()
print("="*66)
print("F2 判读线重定标：零假设=齐性 Poisson 零点过程（同强度同窗口），")
print("   单纯平滑化的预期偏差基线 = 代理中位数 + 2×MAD（代理 200 次）")
print("="*66)
lam = len(gammas)/300.0   # 强度（γ≤300 内密度）
base = {"计数谱": [], "振幅谱": [], "禁数侧": []}
tmax = 88.0
for trial in range(200):
    # 同强度 Poisson 过程采样
    pts = []
    t = 0.0
    while t <= tmax + 60:
        t += random.expovariate(lam)
        pts.append(t)
    pts = [p for p in pts if p <= tmax]
    for k in (1, 2, 4):
        w = k*DG
        Zs = [Z_read(w, t) for t in pts[:0]]  # 占位
    # 为速度：读数直接按定义在细网格算（pts 数≈λ*148≈640）
    for k in (1, 2, 4):
        w = k*DG
        ZP  = [sum(math.exp(-(g-t)**2/(2*w*w)) for g in pts) for t in fine]
        ZaP = [sum(math.exp(-(g-t)**2/(2*w*w))/math.hypot(0.5, g) for g in pts) for t in fine]
        FP  = [F_read(w, t) for t in fine]
        base["计数谱"].append(dev := max(abs(a-b)/((abs(a)+abs(b))/2) for a, b in zip(ZP[::4], [x for x in []]) ) if False else None)
    break
# 上面的内联写法太绕——改为直接三读数×三窗对的代理偏差（细网格抽样每 4 点降负载）
base = {"计数谱": [], "振幅谱": [], "禁数侧": []}
fine_s = fine[::4]
for trial in range(200):
    pts = []
    t = 0.0
    while t <= tmax + 60:
        t += random.expovariate(lam)
        pts.append(t)
    pts = [p for p in pts if p <= tmax]
    for name, fi in (("计数谱", 0), ("振幅谱", 1), ("禁数侧", 2)):
        P = {}
        for k in (1, 2, 4):
            w = k*DG
            if name == "禁数侧":
                P[k] = [F_read(w, t) for t in fine_s]
            else:
                row = []
                for t in fine_s:
                    s = 0.0
                    for g in pts:
                        u2 = (g-t)**2/(2*w*w)
                        if u2 <= 18.0:
                            s += math.exp(-u2)*(1.0/math.hypot(0.5, g) if fi == 1 else 1.0)
                    row.append(s)
                P[k] = row
        for (a, b) in ((1, 2), (2, 4), (1, 4)):
            dv = max((abs(pa-pb)/((abs(pa)+abs(pb))/2) for pa, pb in zip(P[a], P[b]) if (pa+pb) != 0), default=0.0)
            base[name].append(dv)

import statistics as st
lines = {}
for name, lst in base.items():
    med = st.median(lst); mad = st.median([abs(v-med) for v in lst])
    lines[name] = med + 2*1.4826*mad
    print(f"   {name}: 代理偏差 中位={med*100:.2f}%  判读线={lines[name]*100:.2f}%（原冻结线 5%）")

print("\n   F2 应用：以重定标线判 F1 的细网格偏差")
for name, fi in (("计数谱", 0), ("振幅谱", 1), ("禁数侧", 2)):
    P = {}
    for k in (1, 2, 4):
        w = k*DG
        P[k] = [reads_at(w, t)[fi] for t in fine]
    for (a, b) in ((1, 2), (2, 4), (1, 4)):
        dv = max((abs(pa-pb)/((abs(pa)+abs(pb))/2) for pa, pb in zip(P[a], P[b]) if (pa+pb) != 0), default=0.0)
        flag = "超线" if dv > lines[name] else "通过"
        print(f"   {name} w{a}vs{b}: {dv*100:7.2f}% vs 重定线 {lines[name]*100:.2f}%  {flag}")

# ============ F3 读数降维（秩判读） ============
print()
print("="*66)
print("F3 读数降维：跨窗宽的 Spearman 秩稳定 + 峰位单调性（10 原带心）")
print("="*66)
def spearman(x, y):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0]*len(v)
        for i, j in enumerate(s): r[j] = i
        return r
    rx, ry = rank(x), rank(y)
    n = len(x); mx = sum(rx)/n; my = sum(ry)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a-mx)**2 for a in rx)); vy = math.sqrt(sum((b-my)**2 for b in ry))
    return sxy/(vx*vy) if vx and vy else None

P10 = {}
for k in (1, 2, 4):
    w = k*DG
    P10[k] = [reads_at(w, 4.0*d) for d in DS]
for name, fi in (("计数谱", 0), ("振幅谱", 1), ("禁数侧", 2)):
    for (a, b) in ((1, 2), (2, 4), (1, 4)):
        xa = [v[fi] for v in P10[a]]; xb = [v[fi] for v in P10[b]]
        rho = spearman(xa, xb)
        # 秩翻转数
        ra = sorted(range(10), key=lambda i: xa[i]); rb = sorted(range(10), key=lambda i: xb[i])
        flips = sum(1 for i in range(10) if ra[i] != rb[i])
        print(f"   {name} w{a}vs{b}: Spearman ρ={rho:.4f}  秩翻转 {flips}/10")
print("   （判读参考：ρ≥0.9 且翻转≤2 视为秩稳定——此线为本试探建议值，非冻结判据）")
