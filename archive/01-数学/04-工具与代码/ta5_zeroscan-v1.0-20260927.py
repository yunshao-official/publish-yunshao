# -*- coding: utf-8 -*-
"""
永动任务1：零点判据冻结+临界线大窗口重扫（t∈[0,20]）
判据（冻结于本文件落盘，NTFS 锚在先，零点判据首次冻结）：
  Z-1 辐角卷绕：Im(log L) 相邻点跳变 |Δ|>3（主分支切割≈π）记零点候选；跳变点 |L|=e^{Re}<0.5 为强候选
  Z-2 模深谷：|L|<0.1 的局部极小点
  Z-3 诚实边界：延拓层数值精度~1e-2（k_max/j_max 截断+积分尾），全部候选为"候选级"非确认
预注册：黎曼猜想·通俗图解-v9.0 §十三（判据冻结在先）
"""
import numpy as np, sympy as sp, json, datetime, mpmath
from mpmath import mp, loggamma, exp as mexp
mp.dps = 25
PALL = np.array(list(sp.primerange(7, 10**6)), dtype=float)
logs = np.array([float(sp.log(q*(q*q-1)//2)) for q in sp.primerange(7, 294)])
MUS = [(m, int(sp.mobius(m))) for m in range(1, 41) if sp.mobius(m) != 0]

def P7(s):
    if s.real > 1.45:
        return complex(np.sum(PALL ** (-s)))
    if s.real > 1.0:
        part = complex(np.sum(PALL ** (-s)))
        x = PALL[-1]; ss = complex(s)
        tail = x**(1-ss) / ((ss-1)*mp.log(x)) * (1 + 1/((ss-1)*mp.log(x)))
        return part + complex(tail)
    tot = 0j
    for m, mu in MUS:
        tot += mu/m * complex(mpmath.log(mpmath.zeta(m*s)))
    return tot - 2.0**(-s) - 3.0**(-s) - 5.0**(-s)

def log_L(w, k_max=10, j_max=200):
    tot = 0j
    for k in range(1, k_max+1):
        lgkw = loggamma(k*w)
        inner = 0j
        for j in range(0, j_max+1):
            lc = loggamma(k*w+j) - loggamma(j+1) - lgkw
            inner += complex(mexp(lc)) * P7(3*k*w+2*j)
        tot += (2**(k*w))/k * inner
    return tot

ts = np.arange(0, 20.001, 0.25)
res, prev, wraps, strong, deep = [], None, [], [], []
for t in ts:
    if t == 0.0:
        res.append(complex(np.nan)); prev = None; continue
    v = log_L(0.5+1j*t)
    res.append(v)
    if prev is not None:
        d_im = v.imag - prev[1].imag
        if abs(d_im) > 3:                      # Z-1 主分支切割
            mod = float(mexp(v.real))
            entry = {"t": float(t), "jump": round(float(d_im), 3), "|L|": round(mod, 4)}
            wraps.append(entry)
            if mod < 0.5: strong.append(entry)
    mod = float(mexp(v.real))
    if mod < 0.1: deep.append({"t": float(t), "|L|": round(mod, 5)})   # Z-2
    prev = (t, v)

print(f"扫描 {len(ts)} 点（t∈[0,20]，步长0.25）")
print(f"Z-1 辐角卷绕候选：{len(wraps)} 处")
for e in wraps[:15]: print("  ", e)
print(f"Z-1 强候选（|L|<0.5）：{len(strong)} 处")
print(f"Z-2 模深谷（|L|<0.1）：{len(deep)} 处")
for e in deep[:15]: print("  ", e)

out = {"script": "ta5_zeroscan-v1.0-20260927.py",
       "frozen_criteria": {"Z1": "Im(logL)相邻跳变|Δ|>3记候选，|L|<0.5强候选",
                            "Z2": "|L|<0.1局部极小",
                            "Z3": "延拓层精度~1e-2，候选级非确认"},
       "n_points": len(ts), "wraps": wraps, "strong": strong, "deep": deep,
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds")}
json.dump(out, open("results/ta5_zeroscan-v1.0-20260927.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已写 results/ta5_zeroscan-v1.0-20260927.json")
