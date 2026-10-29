# -*- coding: utf-8 -*-
"""
永动反读实验：从塔数值侧独立提取边界奇点峰位→反解零点地址→与已知零点表对账
协议（冻结于本文件落盘，NTFS 锚在先）：
  R-1 峰提取：Re(w)=0.08 纵线，t∈[25,60]（投影稀疏区，避免低区密度饱和），
      |Re logL| 局部极大 > 1.5×中位数 记峰位
  R-2 对账：峰位 y 与正读谱 {t_ρ/n : ρ=ζ 第 1..80 零点（mpmath.zetazero），n=1..20}
      距离 < 0.1 记命中（正读谱即"零点→边界"正向投影）
  R-3 匹配率 = 命中数/峰数
  R-4 随机基线：等量均匀随机点同容差对账，1000 次取分布（密度校正的零假设）
  R-5 判定：R-3 > R-4 的 95 分位 ⟹ 「塔数值侧独立重现 ζ 零点编码」确认；
      否则判负照记
  R-6 诚实边界：延拓层精度 ~1e-2；峰位提取分辨率 0.15；容差 0.1 = 谱位置级对账（非精度级）
"""
import numpy as np, sympy as sp, json, datetime, mpmath
from mpmath import mp, loggamma, exp as mexp, zetazero
mp.dps = 20
PALL = np.array(list(sp.primerange(7, 10**6)), dtype=float)
logs = np.array([float(sp.log(q*(q*q-1)//2)) for q in sp.primerange(7, 294)])
MUS = [(m, int(sp.mobius(m))) for m in range(1, 26) if sp.mobius(m) != 0]

def P7(s):
    if s.real > 1.45: return complex(np.sum(PALL ** (-s)))
    if s.real > 1.0:
        part = complex(np.sum(PALL ** (-s))); x = PALL[-1]; ss = complex(s)
        return part + complex(x**(1-ss)/((ss-1)*mp.log(x))*(1+1/((ss-1)*mp.log(x))))
    tot = 0j
    for m, mu in MUS: tot += mu/m * complex(mpmath.log(mpmath.zeta(m*s)))
    return tot - 2.0**(-s) - 3.0**(-s) - 5.0**(-s)

def log_L(w, k_max=6, j_max=80):
    tot = 0j
    for k in range(1, k_max+1):
        lgkw = loggamma(k*w); inner = 0j
        for j in range(0, j_max+1):
            inner += complex(mexp(loggamma(k*w+j)-loggamma(j+1)-lgkw)) * P7(3*k*w+2*j)
        tot += (2**(k*w))/k * inner
    return tot

# 正读谱：零点表 zetazero(1..80) × n=1..20
ZT = [float(mpmath.im(zetazero(i))) for i in range(1, 81)]
ROSTER = sorted(t/n for t in ZT for n in range(1, 21))
print(f"正读谱（80 零点×n≤20）：{len(ROSTER)} 点，[25,60] 窗内 {sum(1 for y in ROSTER if 25<=y<=60)} 点", flush=True)

# R-1 峰提取
ts = np.arange(25, 60.001, 0.15)
vals = []
for i, t in enumerate(ts):
    v = log_L(0.08+1j*t).real
    vals.append(v)
    if (i+1) % 50 == 0: print(f"  ...t={t:.1f}", flush=True)
vals = np.array(vals)
med = np.median(np.abs(vals))
peaks = []
for i in range(1, len(ts)-1):
    if abs(vals[i]) > 1.5*med and abs(vals[i]) >= abs(vals[i-1]) and abs(vals[i]) >= abs(vals[i+1]):
        peaks.append(float(ts[i]))
print(f"\nR-1 峰提取：{len(peaks)} 峰（中位 |Re|={med:.3f}）")
print("峰位：", [round(p, 2) for p in peaks], flush=True)

# R-2/R-3 对账
def match_rate(points):
    hit = sum(1 for y in points if min(abs(np.array(ROSTER) - y)) < 0.1)
    return hit/len(points) if points else 0.0
rate = match_rate(peaks)
print(f"\nR-3 塔峰位匹配率：{rate:.4f}（{sum(1 for y in peaks if min(abs(np.array(ROSTER)-y))<0.1)}/{len(peaks)}）")

# R-4 随机基线
rng = np.random.default_rng(42)
base = [match_rate(rng.uniform(25, 60, len(peaks))) for _ in range(1000)]
q95 = float(np.quantile(base, 0.95)); mean_b = float(np.mean(base))
print(f"R-4 随机基线：mean={mean_b:.4f} 95分位={q95:.4f}")

verdict = "CONFIRMED（塔数值侧独立重现ζ零点编码）" if rate > q95 else "NEGATIVE（判负照记：匹配率未超随机基线95分位）"
print(f"\nR-5 判定：{verdict}")

out = {"script": "ta11_backread-v1.0-20260927.py", "frozen": "R-1..R-6 协议冻结在先",
       "peaks": peaks, "rate": rate, "baseline_mean": mean_b, "baseline_q95": q95,
       "verdict": verdict, "ran_at": datetime.datetime.now().isoformat(timespec="seconds")}
json.dump(out, open("results/ta11_backread-v1.0-20260927.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写 results/ta11_backread-v1.0-20260927.json")
