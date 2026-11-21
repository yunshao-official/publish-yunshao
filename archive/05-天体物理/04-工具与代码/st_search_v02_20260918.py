# -*- coding: utf-8 -*-
"""
泛弦比例搜索管线 v0.2（修正版）
修正：从三线组搜索改为双线对搜索——f₀(804nm) 和 f₀/1.2(964nm) 都在近红外，
SDSS 可同时覆盖。比例 1.2:1 是泛弦比例外层关系（跨体系不变）。
"""
import numpy as np, json, sys
from itertools import combinations

TOL = 0.01  # 比例容差1%
C_ANG = 2.99792458e18

def extract_lines(wave, flux, snr_min=5.0):
    lines = []
    cont = np.median(flux)
    noise = np.std(flux - cont)
    for i in range(2, len(wave)-2):
        if flux[i] > flux[i-1] and flux[i] > flux[i+1] and flux[i] > flux[i-2] and flux[i] > flux[i+2]:
            snr = (flux[i] - cont) / noise if noise > 0 else 0
            if snr >= snr_min:
                lines.append({"wave": round(wave[i],2), "freq": C_ANG/wave[i],
                              "snr": round(snr,1)})
    return lines

def find_ratio_pairs(lines, ratio=1.2, tol=TOL):
    """搜索频率比≈ratio的谱线对"""
    pairs = []
    for i, j in combinations(range(len(lines)), 2):
        fi, fj = lines[i]["freq"], lines[j]["freq"]
        if fi <= 0 or fj <= 0: continue
        r = max(fi,fj) / min(fi,fj)
        if abs(r - ratio)/ratio <= tol:
            pairs.append({"wave_high": round(min(lines[i]["wave"],lines[j]["wave"]),1),
                          "wave_low": round(max(lines[i]["wave"],lines[j]["wave"]),1),
                          "ratio": round(r,4), "snr": [lines[i]["snr"],lines[j]["snr"]]})
    return pairs

def gen_test(seed, n=3000, inject_pair=False, inject_z=0.0):
    rng = np.random.default_rng(seed)
    wave = np.linspace(3800, 9500, n)
    flux = rng.normal(1.0, 0.05, n)
    if inject_pair:
        f_base = 373e12 / (1 + inject_z)  # Hz
        f_high = f_base
        f_low = f_base / 1.2
        lam_high = C_ANG / f_high * 1e10  # Å
        lam_low = C_ANG / f_low * 1e10
        for lam in [lam_high, lam_low]:
            idx = np.argmin(np.abs(wave - lam))
            if 2 < idx < n-2:
                flux[idx-2:idx+3] += rng.uniform(15, 25)
    return wave, flux

# ---- 注入-恢复测试 ----
def inj_recovery(trials=200):
    rec = 0
    for t in range(trials):
        rng = np.random.default_rng(t)
        w = rng.uniform(4000, 9000, 3000)
        f = rng.normal(1.0, 0.05, 3000)
        # 注入一对 1.2:1 谱线
        base_idx = rng.integers(100, 2900)
        lam_h = w[base_idx]
        lam_l = lam_h * 1.2  # 波长比=频率倒数
        for lam, amp in [(lam_h, 20), (lam_l if lam_l < w[-1] else None, 20)]:
            if lam is not None and w[0] < lam < w[-1]:
                idx = np.argmin(np.abs(w - lam))
                f[idx-2:idx+3] += amp
        lines = extract_lines(w, f)
        pairs = find_ratio_pairs(lines, ratio=1.2)
        if pairs: rec += 1
    return rec / trials

rec = inj_recovery(200)
print(f"注入-恢复检出率: {rec:.1%}")

# ---- 合成光谱演示 ----
results = {}
for inject in [False, True]:
    w, f = gen_test(42, inject_pair=inject, inject_z=0.0)
    lines = extract_lines(w, f)
    pairs = find_ratio_pairs(lines, ratio=1.2)
    results[f"inject={inject}"] = {"谱线数": len(lines), "1.2:1对数": len(pairs)}
    print(f"inject={inject}: {len(lines)} lines, {len(pairs)} pairs@1.2:1")

verdict = "PASS（管线功能正常）" if rec >= 0.95 else "FAIL"
out = {"injection_recovery_rate": round(rec,3), "VERDICT": verdict,
       "synthetic_test": results,
       "note": "v0.2: 双线对搜索（f₀ vs f₀/1.2）。三线组搜索需多波段数据，列为v1.1扩展。"}
from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_out = (_script_dir / "st_pipeline_v02_20260918.json").resolve()
_out.relative_to(_script_dir)  # 目录白名单硬校验：输出必须落在脚本目录内
_out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("VERDICT:", verdict)
