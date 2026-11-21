# -*- coding: utf-8 -*-
"""泛弦比例搜索管线 v0.4 正式版（频率已修正至近红外）
修正：v0.3 注入频率 3.1e15→3.1e14 Hz（极紫外→近红外，数量级修正）
数据：合成光谱（真实 FITS 管线另制）
判据：注入-恢复检出率 ≥90% PASS
"""
import numpy as np, json
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
            lines.append({"wave": round(wave[i],1), "freq": C_ANG/wave[i], "snr": round(snr,1)})
    return lines

def find_pairs(lines, ratio, tol=0.01):
    pairs = []
    for i, j in combinations(range(len(lines)), 2):
        fi, fj = lines[i]["freq"], lines[j]["freq"]
        r = max(fi,fj)/min(fi,fj)
        if abs(r-ratio)/ratio <= tol:
            pairs.append({"r": round(r,3), "w_hi": round(min(lines[i]["wave"],lines[j]["wave"]),1),
                          "w_lo": round(max(lines[i]["wave"],lines[j]["wave"]),1)})
    return pairs

def gen_spectrum(seed, n=5000, wmin=6000, wmax=12000):
    rng = np.random.default_rng(seed)
    wave = np.linspace(wmin, wmax, n)
    flux = rng.normal(1.0, 0.05, n)
    return wave, flux

def inject_pair(wave, flux, f_base, rng):
    """注入泛弦比例对：f_high 和 f_high/1.2"""
    for mult in [1.0, 1/1.2]:
        lam = C_ANG / (f_base * mult)
        idx = np.argmin(np.abs(wave - lam))
        if 2 < idx < len(wave)-2:
            flux[idx-2:idx+3] += rng.uniform(15, 25)

# ---- 注入-恢复测试 ----
print("=== 注入-恢复测试（频率修正后） ===")
rec = 0; N_TRIALS = 300
for t in range(N_TRIALS):
    rng = np.random.default_rng(t)
    wave, flux = gen_spectrum(t)
    f_h = rng.uniform(3.5e14, 4.2e14)  # Hz
    inject_pair(wave, flux, f_h, rng)
    lines = extract_mad(wave, flux)
    pairs = find_pairs(lines, 1.2)
    if pairs: rec += 1
rate = rec / N_TRIALS
print(f"检出率: {rate:.1%} ({rec}/{N_TRIALS})")
print("VERDICT:", "PASS" if rate >= 0.9 else "FAIL")

# ---- 真实搜索演示（合成，无注入基线） ----
print("\n=== 基线（无注入） ===")
wave, flux = gen_spectrum(42)
lines = extract_mad(wave, flux)
pairs = find_pairs(lines, 1.2)
print(f"谱线: {len(lines)}, 比例对: {len(pairs)}")

# ---- 有注入演示 ----
print("\n=== 有注入 ===")
wave, flux = gen_spectrum(42)
rng2 = np.random.default_rng(999)
f_base = rng2.uniform(3.5e14, 4.0e14)
inject_pair(wave, flux, f_base, rng2)
lines = extract_mad(wave, flux)
pairs = find_pairs(lines, 1.2)
print(f"谱线: {len(lines)}, 比例对: {len(pairs)}")
for p in pairs[:3]: print(f"  {p}")

# ---- 结果入库 ----
result = {"injection_recovery_rate": round(rate,3), "trials": N_TRIALS,
          "verdict": "PASS" if rate >= 0.9 else "FAIL",
          "baseline_pairs": len(pairs) if 'pairs' in dir() else 0,
          "note": "频率修正后首版验证。v0.3 频率在极紫外导致 0% 检出，已修正至近红外。"}
with open("st_v04_result_20260918.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("入库OK")
