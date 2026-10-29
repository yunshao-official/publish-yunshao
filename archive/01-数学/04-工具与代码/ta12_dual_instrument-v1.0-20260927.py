# -*- coding: utf-8 -*-
"""
双仪器交叉实验（知世 0927「做」令）：
  仪器甲=塔侧探测器：log L_塔 延拓层峰位（本实验加码：k_max=10/j_max=150/m_max=35，峰心二分细化）
  仪器乙=珠子侧探测器：Landau 权重 E(t)=Σ_{n≤X} Λ(n)/√n·(1−n/X)·n^{−it}，|E(t)| 强峰（独立方法：显式和）
交叉判据（冻结于落盘，NTFS 锚在先）：
  X-1：甲乙峰位的近邻距离分布 vs 随机基线（2000 次均匀随机）——双侧独立方法是否看向同一批位置
  X-2：共同命中=同一零点地址（虚部 t_ρ）±0.15 内甲乙同时有信号的重合率 vs 随机
  X-3：精度加码曲线：加码前后塔侧峰位-正读谱偏差中位（0.03→?）
诚实边界：珠子侧 X=1e4（档内原法 1e8 不可及）——分辨率与主项污染如实标注
"""
import numpy as np, sympy as sp, json, datetime, mpmath
from mpmath import mp, loggamma, exp as mexp, zetazero
mp.dps = 20
PALL = np.array(list(sp.primerange(7, 10**6)), dtype=float)
logs = np.array([float(sp.log(q*(q*q-1)//2)) for q in sp.primerange(7, 294)])
MUS = [(m, int(sp.mobius(m))) for m in range(1, 36) if sp.mobius(m) != 0]

def P7(s):
    if s.real > 1.45: return complex(np.sum(PALL ** (-s)))
    if s.real > 1.0:
        part = complex(np.sum(PALL ** (-s))); x = PALL[-1]; ss = complex(s)
        return part + complex(x**(1-ss)/((ss-1)*mp.log(x))*(1+1/((ss-1)*mp.log(x))))
    tot = 0j
    for m, mu in MUS: tot += mu/m * complex(mpmath.log(mpmath.zeta(m*s)))
    return tot - 2.0**(-s) - 3.0**(-s) - 5.0**(-s)

def log_L(w, k_max=10, j_max=150):
    tot = 0j
    for k in range(1, k_max+1):
        lgkw = loggamma(k*w); inner = 0j
        for j in range(0, j_max+1):
            inner += complex(mexp(loggamma(k*w+j)-loggamma(j+1)-lgkw)) * P7(3*k*w+2*j)
        tot += (2**(k*w))/k * inner
    return tot

ZT = [float(mpmath.im(zetazero(i))) for i in range(1, 81)]
ROSTER = np.array(sorted(t/n for t in ZT for n in range(1, 21)))

# ===== 仪器甲（加码）：粗扫+峰心细化 =====
ts = np.arange(25, 60.001, 0.15)
vals = np.array([log_L(0.08+1j*t).real for t in ts])
med = np.median(np.abs(vals))
coarse = [float(ts[i]) for i in range(1, len(ts)-1)
          if abs(vals[i]) > 1.5*med and abs(vals[i]) >= abs(vals[i-1]) and abs(vals[i]) >= abs(vals[i+1])]
print(f"甲粗扫：{len(coarse)} 峰（中位 {med:.3f}）", flush=True)
# 峰心细化：±0.15 内步长 0.03，取 |Re| 最大点
fine = []
for c in coarse:
    tt = np.arange(max(25, c-0.15), min(60, c+0.15)+0.001, 0.03)
    vv = [abs(log_L(0.08+1j*t).real) for t in tt]
    fine.append(float(tt[int(np.argmax(vv))]))
dev_fine = np.array([float(np.min(np.abs(ROSTER - y))) for y in fine])
med_dev = float(np.median(dev_fine))
print(f"甲加码：{len(fine)} 峰，偏差中位 {med_dev:.4f}（加码前 0.0337）", flush=True)

# ===== 仪器乙（珠子）：Landau 权重显式和 =====
X = 10**4
ns = np.arange(1, X+1)
lam = np.zeros(X)
for n in range(1, X+1):
    f = sp.factorint(n)
    if len(f) == 1: lam[n-1] = list(f.values())[0]   # Λ(n)=ln p（素数幂），否则 0
w = lam/np.sqrt(ns)*(1-ns/X)
def E(t):
    return complex(np.sum(w * np.exp(-1j*t*np.log(ns))))
tb = np.arange(25, 60.001, 0.1)
Eb = np.array([abs(E(t)) for t in tb])
Eb_med = np.median(Eb)
beads = []
for i in range(2, len(tb)-2):
    if Eb[i] > 2.0*Eb_med and Eb[i] == max(Eb[i-2:i+3]):
        beads.append(float(tb[i]))
print(f"乙珠子：{len(beads)} 强峰（阈值 2×中位）", flush=True)
print("乙峰位：", [round(b,1) for b in beads], flush=True)

# ===== 交叉 X-1/X-2 =====
def nn_dist(points, ref):
    return np.array([float(np.min(np.abs(ref - y))) for y in points])
d_cross = nn_dist(fine, np.array(beads))
rng = np.random.default_rng(11)
base_x1 = [float(np.mean(nn_dist(rng.uniform(25,60,len(fine)), np.array(beads)) < 0.3)) for _ in range(2000)]
obs_x1 = float(np.mean(d_cross < 0.3))
# X-2 共同命中（零点地址级）
zt_arr = np.array(ZT)
def addr_hit(points, tol=0.15):
    return sum(1 for y in points if float(np.min(np.abs(zt_arr - y))) < tol)
hit_a = addr_hit(fine); hit_b = addr_hit(beads)
both = sum(1 for z in zt_arr if (float(np.min(np.abs(np.array(fine)-z))) < 0.15 and float(np.min(np.abs(np.array(beads)-z))) < 0.15))
print(f"\nX-1 甲乙近邻<0.3 占比：观测 {obs_x1:.4f} vs 随机基线 mean {np.mean(base_x1):.4f} q95 {np.quantile(base_x1,0.95):.4f}")
print(f"X-2 零点地址命中：甲 {hit_a}/80 乙 {hit_b}/80 共同 {both}/80")

out = {"fine_peaks": fine, "med_dev_upgraded": med_dev, "beads": beads,
       "X1_obs": obs_x1, "X1_base_mean": float(np.mean(base_x1)), "X1_base_q95": float(np.quantile(base_x1, 0.95)),
       "X2_hit_a": hit_a, "X2_hit_b": hit_b, "X2_both": both,
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds")}
json.dump(out, open("results/ta12_dual_instrument-v1.0-20260927.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已写 results/ta12_dual_instrument-v1.0-20260927.json")
