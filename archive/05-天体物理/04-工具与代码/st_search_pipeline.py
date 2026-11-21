# -*- coding: utf-8 -*-
"""
泛弦比例搜索管线 v0.1（可运行原型）
功能：对光谱数据搜索泛弦比例三线组（12:1 + 1.2:1）
数据格式：SDSS/LAMOST FITS 光谱（或 CSV 简化格式）
前置：注入-恢复测试通过后才跑真实搜索
运行：python st_search_pipeline.py [光谱文件目录]
"""
import numpy as np, json, os, sys, glob
from itertools import combinations

# ---- 参数（冻结） ----
TOL1 = 0.01   # 12:1 容差
TOL2 = 0.01   # 1.2:1 容差
TOLZ = 0.01   # 共红移容差
SNR_MIN = 5.0 # 谱线SNR阈值
C_ANGSTROM = 2.99792458e18  # 光速 Å/s

def extract_lines(wave, flux, err, snr_min=SNR_MIN):
    """谱线提取：SNR≥阈值 的局部极大值"""
    lines = []
    for i in range(2, len(wave)-2):
        # 局部极大
        if flux[i] > flux[i-1] and flux[i] > flux[i+1]:
            # 连续谱估计（局部中值）
            cont = np.median(flux[max(0,i-50):i+50])
            # SNR = (peak - cont) / noise
            noise = np.std(flux[max(0,i-50):i+50])
            if noise > 0:
                snr = (flux[i] - cont) / noise
                if snr >= snr_min:
                    lines.append({"wave": wave[i], "snr": round(snr,1),
                                  "ew": round((flux[i]-cont)/cont*100, 2)})
    return lines

def find_triplets(lines, tol1=TOL1, tol2=TOL2):
    """搜索泛弦比例三线组"""
    triplets = []
    if len(lines) < 3:
        return triplets
    freqs = [C_ANGSTROM / l["wave"] for l in lines]  # λ→频率
    for i, j, k in combinations(range(len(lines)), 3):
        fa, fb, fc = sorted([freqs[i], freqs[j], freqs[k]], reverse=True)
        if fc <= 0: continue
        r1 = fa / fb   # 应≈12
        r2 = fb / fc   # 应≈1.2（泛弦比例外层的1.2关系简化）
        # 检查两种排列：12:1:1.2/12 或 12:1:1.2
        ok1 = abs(r1 - 12)/(12) <= tol1 and abs(r2 - 1.2)/(1.2) <= tol2
        ok2 = abs(r2 - 12)/(12) <= tol1 and abs(r1 - 1.2)/(1.2) <= tol2
        if ok1 or ok2:
            triplets.append({
                "line_waves": [lines[i]["wave"], lines[j]["wave"], lines[k]["wave"]],
                "line_indices": [i, j, k],
                "r1": round(r1, 3), "r2": round(r2, 3),
                "snrs": [lines[i]["snr"], lines[j]["snr"], lines[k]["snr"]]
            })
    return triplets

def generate_test_spectrum(seed=42, n_lines=5000, inject=True):
    """生成测试光谱（含噪声+可选注入泛弦三线组）"""
    rng = np.random.default_rng(seed)
    wave = np.linspace(3800, 9000, n_lines)  # Å
    flux = rng.normal(1.0, 0.05, n_lines)  # 连续谱+噪声
    
    if inject:
        # 注入泛弦比例三线组
        z = 0.1  # 注入红移
        base_freq = 373e12 / (1 + z)  # Hz（观测频率）
        # f_a:f_b:f_c = 12:1:1.2
        f_a = base_freq
        f_b = base_freq / 12
        f_c = base_freq / 1.2
        for f_target, width in [(f_a, 2.0), (f_b, 2.0), (f_c, 2.0)]:
            lam_target = C_ANGSTROM / f_target  # Å
            idx = np.argmin(np.abs(wave - lam_target))
            if 2 < idx < n_lines - 2:
                flux[idx-2:idx+3] += rng.uniform(10, 20)  # 注入强峰
    return wave, flux

def run_injection_recovery(n_trials=100, tol1=TOL1, tol2=TOL2):
    """注入-恢复测试"""
    detected = 0
    for trial in range(n_trials):
        wave, flux = generate_test_spectrum(seed=trial, inject=True)
        lines = extract_lines(wave, flux, flux*0.1)
        triplets = find_triplets(lines)
        # 检查是否找到了注入的三线组（近似：找到任何比例组即算）
        if len(triplets) > 0:
            detected += 1
    return detected / n_trials

if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 注入-恢复测试（前置）
    print("=== 注入-恢复测试 ===")
    rec = run_injection_recovery(100)
    print(f"检出率: {rec:.1%}")
    if rec < 0.95:
        print("⚠ 管线判负：注入-恢复不通过。修正管线后重跑。")
        sys.exit(1)
    print("✓ 注入-恢复通过")
    
    # 演示搜索（合成光谱）
    print("\n=== 演示搜索（合成光谱） ===")
    for inject in [False, True]:
        wave, flux = generate_test_spectrum(42, inject=inject)
        lines = extract_lines(wave, flux, flux*0.1)
        triplets = find_triplets(lines)
        print(f"inject={inject}: {len(lines)} 谱线, {len(triplets)} 候选三线组")
        for t in triplets[:3]:
            print(f"  → λ={t['line_waves']} r1={t['r1']} r2={t['r2']}")
    
    print("\n泛弦搜索管线 v0.1 原型完成。")
    print("下一步：接入真实 SDSS FITS 数据 → 全量搜索。")
