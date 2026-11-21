# -*- coding: utf-8 -*-
"""
RD-4 局部窗修复试探（T-5·知世"都试试"2026-09-25 批准执行）
状态：试探性修复（非正式读数）——按《磨光读数归一化与RD首跑执行口径v1.0》冻结核口径，
仅窗单位按 T-5 修复方向换"带位局地零点间距"，其余逐字照口径 v1.0。
对照：全局窗（复现首跑判负）vs 局部窗（修复试探）。
诚实标签：本试探为协助执行（数论对接线），判读留账本（R-N16），正式读数归任务二线 RD 口径。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')

# 数据：任务二线存档零点表（前 100,000 零点）
ZPATH = r"H:\理论存档\01-数学\02-实验与数据\results\odlyzko_zeros1-100k-20260921.txt"
gammas = [float(l) for l in open(ZPATH) if l.strip()]
gammas300 = [g for g in gammas if g <= 300]

# R-N10 十档直方图（JC-N3 v2 修正版，240,163 对）——口径 v1.0 §三.2 复算锚
H = {2: 29555, 4: 34288, 6: 52977, 8: 19819, 10: 23379,
     12: 34223, 14: 10932, 16: 14544, 18: 15704, 22: 4742}
DS = sorted(H)

KAPPA = 1/32; ALPHA = 1/8
def gen_exp(d):
    T = d/24
    return 1 if T <= ALPHA else (2 if T <= 1/math.sqrt(6) else 3)

# 冻结口径 §2.1：全局窗单位
gbar = sum(gammas300)/len(gammas300)
DG_global = 2*math.pi/math.log(gbar)

# T-5 修复：带位局地零点间距（经验版——取带中心 ±30 内相邻零点平均间隙；空窗回退全局）
def local_dg(t_c):
    near = [g for g in gammas if abs(g - t_c) <= 30]
    if len(near) < 3:
        return DG_global
    gaps = [near[i+1]-near[i] for i in range(len(near)-1)]
    return sum(gaps)/len(gaps)

# 冻结口径 §2.2：两侧读数（核不逐点归一；截断 6w）
def Z_read(w, centers, amp=False):
    out = []
    for t_c in centers:
        s = 0.0; R = 6*w
        for g in gammas:
            if abs(g - t_c) > R: continue
            wt = (1.0/(0.5 if not amp else 1.0))
            m = 1.0
            fac = math.exp(-(g-t_c)**2/(2*w*w))
            s += m*(1.0/math.hypot(0.5, g) if amp else 1.0)*fac
        out.append(s)
    return out

def F_read(w, centers):
    out = []
    for t_c in centers:
        s = 0.0; R = 6*w
        for d in DS:
            t_j = 4.0*d
            if abs(t_j - t_c) > R: continue
            s += H[d]*math.exp(-(t_j-t_c)**2/(2*w*w))
        out.append(s)
    return out

def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(x, y))
    vx = math.sqrt(sum((a-mx)**2 for a in x)); vy = math.sqrt(sum((b-my)**2 for b in y))
    return sxy/(vx*vy) if vx > 0 and vy > 0 else None

def dev_max(P1, P2):
    ds = []
    for a, b in zip(P1, P2):
        m = (abs(a)+abs(b))/2
        if m > 0: ds.append(abs(a-b)/m)
    return max(ds) if ds else 0.0

centers = [4.0*d for d in DS]
print("="*66)
print("RD-4 局部窗修复试探（T-5）｜ 2026-09-25 ｜ 试探性·判读留账本")
print("="*66)
print(f"冻结复现：全局 γ̄={gbar:.1f} → Δγ̄={DG_global:.3f}（口径 v1.0 首跑值 1.216 的复算）")
print("带位局地零点间距（±30 经验平均间隙）：")
loc = {t_c: local_dg(t_c) for t_c in centers}
for t_c in centers:
    print(f"   t_c={t_c:>5.1f} (d={int(t_c/4):>2}): Δγ_loc={loc[t_c]:.3f}")

def run_mode(mode):
    """mode='global'|'local'；返回三读数的 (w 键, 读数) 与 RD-4 计量"""
    res = {}
    for k in (1, 2, 4):
        if mode == "global":
            w = k*DG_global
        else:
            w = None  # 逐带局地：读数时逐带取 w
        if mode == "global":
            Z  = Z_read(w, centers)
            Za = Z_read(w, centers, amp=True)
            F  = F_read(w, centers)
            res[k] = (Z, Za, F, {c: w for c in centers})
        else:
            Z  = []; Za = []; F = []
            for t_c in centers:
                wk = k*loc[t_c]
                Z.append(Z_read(wk, [t_c])[0])
                Za.append(Z_read(wk, [t_c], amp=True)[0])
                F.append(F_read(wk, [t_c])[0])
            res[k] = (Z, Za, F, {c: k*loc[c] for c in centers})
    return res

for mode in ("global", "local"):
    res = run_mode(mode)
    print(f"\n── {mode} 窗（{'首跑口径复现' if mode=='global' else 'T-5 修复试探'}）──")
    viol = 0; items = 0
    for name, idx in (("计数谱", 0), ("振幅谱", 1), ("禁数侧", 2)):
        d12 = dev_max(res[1][idx], res[2][idx])
        d24 = dev_max(res[2][idx], res[4][idx])
        d14 = dev_max(res[1][idx], res[4][idx])
        for tag, dv in (("1vs2", d12), ("2vs4", d24), ("1vs4", d14)):
            items += 1
            flag = "超5%线" if dv > 0.05 else "通过"
            if dv > 0.05: viol += 1
            print(f"   {name} w{tag}: 相对偏差 {dv*100:8.2f}%  {flag}")
    r1 = pearson(res[1][0], res[1][2]); r2_ = pearson(res[2][0], res[2][2]); r4 = pearson(res[4][0], res[4][2])
    fmt = lambda r: f"{r:.4f}" if r is not None else "无定义(零方差)"
    print(f"   RD-1 主形态 r_w（计数谱×禁数侧）：r1={fmt(r1)} r2={fmt(r2_)} r4={fmt(r4)}")
    dr = [abs(r1-r2_), abs(r2_-r4), abs(r1-r4)]
    for tag, dv in zip(("1vs2","2vs4","1vs4"), dr):
        items += 1
        if dv is not None and dv > 0.05: viol += 1
    print(f"   相关漂移 Δr：{['%.4f' % d for d in dr]}")
    print(f"   → {mode} 窗 RD-4 计量：{viol}/{items} 项超 5% 冻结线")

print("\n判读（试探性，留账本 R-N16）：")
print("  └ 若局部窗超线项显著少于全局窗 → T-5 方向（局地零点间距定窗）对 RD-4 修复有效，")
print("    建议任务二线按其口径程序将'窗单位=带位局地间距'立为 v1.1 修正案（预注册后正式重跑）")
print("  └ 本试探不代任务二线判读；读数禁止入结论（口径 §2.4 纪律沿用）")
