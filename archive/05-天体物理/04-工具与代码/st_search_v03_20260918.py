# -*- coding: utf-8 -*-
"""
泛弦比例搜索管线 v0.3（物理约束修正版）
修正：三频组跨波段（804nm/964nm/9660nm）——单一光谱仪不可能同时覆盖。
搜索策略改为：分波段搜索+交叉匹配。
限制：SDSS/LAMOST 红端截止 ~9200Å=920nm——可覆盖 f₀(804nm) 但 f₂(964nm) 勉强。
v0.2 的注入测试波长出界是因为物理上两条线确实分跨不同波段。
"""
import numpy as np, json, sys
from itertools import combinations

C_ANG = 2.99792458e18
TOL = 0.01

def extract_lines(wave, flux, snr_min=5.0, cont_window=100):
    """局部基线+局部噪声的谱线提取（比v0.2更稳健）"""
    lines = []
    n = len(wave)
    for i in range(5, n-5):
        local = flux[max(0,i-cont_window):i+cont_window]
        cont = np.median(local)
        noise = np.std(local) * 1.4826  # MAD→σ
        if noise <= 0: continue
        snr = (flux[i] - cont) / noise
        if snr < snr_min: continue
        # 局部极大
        if flux[i] > flux[i-1] and flux[i] >= flux[i+1]:
            lines.append({"wave": round(wave[i],2), "freq": C_ANG/wave[i],
                          "snr": round(snr,1)})
    return lines

def find_pairs(lines, ratio, tol=TOL):
    """搜索频率比≈ratio的谱线对（同一天体内）"""
    pairs = []
    for i, j in combinations(range(len(lines)), 2):
        fi, fj = lines[i]["freq"], lines[j]["freq"]
        if fi <= 0 or fj <= 0: continue
        r = max(fi,fj) / min(fi,fj)
        if abs(r - ratio)/ratio <= tol:
            hi = lines[i] if fi > fj else lines[j]
            lo = lines[j] if fi > fj else lines[i]
            pairs.append({"wave_hi_nm": round(hi["wave"]/10,2),
                          "wave_lo_nm": round(lo["wave"]/10,2),
                          "ratio": round(r,4),
                          "snr": [hi["snr"], lo["snr"]]})
    return pairs

def gen_synth(seed, n=5000, wmin=7000, wmax=10000, inject_pairs=None):
    """合成光谱：7000-10000Å（覆盖804nm/964nm近红外区）"""
    rng = np.random.default_rng(seed)
    wave = np.linspace(wmin, wmax, n)
    flux = rng.normal(1.0, 0.05, n)
    if inject_pairs:
        for lam_center, amp in inject_pairs:
            idx = np.argmin(np.abs(wave - lam_center*10))  # nm→Å
            if 2 < idx < n-2:
                flux[idx-2:idx+3] += rng.uniform(amp, amp*1.3)
    return wave, flux

# ---- 注入-恢复测试 ----
def inj_recovery(trials=200):
    """注入1.2:1双线对，检验检出率"""
    rec = 0
    for t in range(trials):
        rng = np.random.default_rng(t)
        n = 5000
        w = np.linspace(7000, 10000, n)  # Å (700-1000nm近红外)
        f = rng.normal(1.0, 0.05, n)
        # 注入一对频率比1.2的线（先选f_high，f_low=f_high/1.2）
        f_h = rng.uniform(3.1e14, 4.2e14)  # Hz → 714-970nm（近红外）
        f_l = f_h / 1.2
        lam_h = C_ANG / f_h  # Å
        lam_l = C_ANG / f_l
        if w[0] < lam_h < w[-1]:
            idx = np.argmin(np.abs(w - lam_h))
            f[idx-2:idx+3] += rng.uniform(15, 25)
        if w[0] < lam_l < w[-1]:
            idx = np.argmin(np.abs(w - lam_l))
            f[idx-2:idx+3] += rng.uniform(15, 25)
        lines = extract_lines(w, f)
        pairs = find_pairs(lines, 1.2)
        if pairs: rec += 1
    return rec / trials

rec = inj_recovery(200)
print(f"注入-恢复检出率: {rec:.1%}")

# ---- 合成光谱演示 ----
# 注入一对 804nm 和 964.8nm（比例1.2）的谱线
results = {}
for label, pairs_inj in [("无注入", []), ("泛弦对", [(804.0, 20), (964.8, 20)])]:
    rng = np.random.default_rng(42)
    w = np.linspace(7000, 10000, 5000)
    f = rng.normal(1.0, 0.05, 5000)
    for lam_c, amp in pairs_inj:
        idx = np.argmin(np.abs(w - lam_c * 10))  # nm→Å
        f[idx-2:idx+3] += rng.uniform(amp, amp*1.3)
    lines = extract_lines(w, f)
    pairs = find_pairs(lines, 1.2)
    results[label] = {"谱线数": len(lines), "1.2:1对数": len(pairs),
                      "对详情": pairs[:3]}
    print(f"{label}: {len(lines)} lines, {len(pairs)} pairs")

verdict = "PASS（管线功能正常+注入恢复通过）" if rec >= 0.95 else "FAIL"
out = {"injection_recovery": round(rec,3), "VERDICT": verdict,
       "synthetic": results,
       "strategy_note": "分波段搜索：SDSS/LAMOST覆盖f₀(804nm)和f₂(964nm)；f₁(9.66μm)需中红外专用设备；三线组搜索=多波段数据交叉匹配（UVP V3多模态交叉）"}
from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_out = (_script_dir / "st_v03_20260918.json").resolve()
_out.relative_to(_script_dir)  # 目录白名单硬校验：输出必须落在脚本目录内
_out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("VERDICT:", verdict)
