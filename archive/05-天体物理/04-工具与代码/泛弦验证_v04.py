# -*- coding: utf-8 -*-
"""泛弦管线v0.4注入-恢复验证（频率修正后）"""
import numpy as np
from itertools import combinations
C_ANG = 2.99792458e18

def extract_mad(wave, flux, snr_min=5.0, win=200):
    lines = []
    n = len(wave)
    for i in range(5, n-5):
        local = flux[max(0,i-win):i+win]
        med = np.median(local)
        mad = np.median(np.abs(local - med))
        sig = mad * 1.4826
        if sig <= 0: continue
        snr = (flux[i] - med) / sig
        if snr < snr_min: continue
        if flux[i] > flux[i-1] and flux[i] >= flux[i+1]:
            lines.append({"wave": round(wave[i],1), "freq": C_ANG/wave[i]})
    return lines

def find_pairs(lines, ratio, tol=0.01):
    pairs = []
    for i, j in combinations(range(len(lines)), 2):
        fi, fj = lines[i]["freq"], lines[j]["freq"]
        r = max(fi,fj)/min(fi,fj)
        if abs(r-ratio)/ratio <= tol:
            pairs.append(r)
    return pairs

rng = np.random.default_rng(42)
rec = 0
for t in range(300):
    r2 = np.random.default_rng(t)
    w = np.linspace(7000, 12000, 5000)
    f = r2.normal(1.0, 0.05, 5000)
    f_h = r2.uniform(3.1e14, 4.2e14)
    f_l = f_h / 1.2
    for lam in [C_ANG/f_h, C_ANG/f_l]:
        if w[0] < lam < w[-1]:
            idx = np.argmin(np.abs(w - lam))
            f[idx-2:idx+3] += r2.uniform(15, 25)
    lines = extract_mad(w, f)
    if find_pairs(lines, 1.2): rec += 1

rate = rec / 300
print(f"注入-恢复检出率: {rate:.1%} ({rec}/300)")
print("PASS" if rate >= 0.9 else "FAIL")
