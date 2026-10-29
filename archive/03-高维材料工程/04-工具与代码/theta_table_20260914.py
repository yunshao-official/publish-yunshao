# -*- coding: utf-8 -*-
"""
Θ(N) 体系全维度材料参数表（2026-09-14）
纯体系内计算：Θ(N)框架 → α(N) → η(N) → 材料参数
N = 4 到 144（v₂≥2 的所有合数 + 含3因子的合数）
全部数值从体系公式直接计算，无外部物理输入
"""
import json, math

def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def theta_full(N):
    fac = factorize(N)
    v2 = fac.get(2, 0)
    v3 = fac.get(3, 0)
    if v2 < 2:
        return None
    s = 1 if v3 >= 1 else 0
    alpha = 2**(-v2) + (1/6 - 2**(-v2)) * s
    eta = 1 - alpha
    D = 3 * N
    beams = 2 * (D - 1)
    theta_deg = 360.0 / N
    kappa = alpha / 4
    epsilon = alpha ** 2
    d_nm = alpha
    M = int(round(1 / alpha)) if alpha > 0 else 0
    
    # 群结构
    if s == 0:
        group = f'(Z2)^{v2}' if v2 > 1 else 'Z2'
    else:
        rem = v2 - 2
        group = f'A4⋊(Z2)^{rem}' if rem > 0 else 'A4'
    # 特殊群
    if N == 12: group = 'A4'
    if N == 24: group = 'S4'
    if N == 48: group = 'O_h'
    if N == 60: group = 'A5'
    if N == 8: group = '(Z2)^3'
    
    # 材料性质预测（体系内公式）
    # 压缩比 = 2^(16(D-3)/7)
    compression = 2 ** (16 * (D - 3) / 7) if D > 3 else 1
    # 干涉束数
    # 储存容量(9升基底)
    storage_m3 = 0.009 * compression
    
    return {
        'N': N, 'v2': v2, 'v3': v3, 's': s,
        'alpha': round(alpha, 8), 'eta': round(eta, 8),
        'group': group, 'D': D,
        'theta_deg': round(theta_deg, 2),
        'kappa': round(kappa, 8), 'epsilon': round(epsilon, 10),
        'd_nm': round(d_nm, 6), 'M': M,
        'beams': beams,
        'compression_ratio': f'{compression:.4e}',
        'storage_9L': f'{storage_m3:.4e} m³',
    }

def main():
    results = []
    for N in range(4, 145):
        r = theta_full(N)
        if r is not None:
            results.append(r)
    
    # 打印完整参数表
    print('N    α(N)        η(N)        G(N)           D     束数  κ         ε            d(nm)   M   压缩比', flush=True)
    print('-' * 130, flush=True)
    for r in results:
        print('%-4d %-11.8f %-11.8f %-14s %-5d %-5d %-9.8f %-12.8e %-7.4f %-3d %s' % (
            r['N'], r['alpha'], r['eta'], r['group'], r['D'],
            r['beams'], r['kappa'], r['epsilon'], r['d_nm'], r['M'],
            r['compression_ratio']), flush=True)
    
    # 关键分析
    print('\n=== 体系分析 ===', flush=True)
    
    # α 最小的 N
    best = min(results, key=lambda r: r['alpha'])
    print('α最小: N=%d, α=%.8f, 群=%s' % (best['N'], best['alpha'], best['group']), flush=True)
    
    # α=1/8 的 N（当前体系）
    a8 = [r['N'] for r in results if abs(r['alpha'] - 0.125) < 1e-6]
    print('α=1/8 的 N: %s' % a8, flush=True)
    
    # 各 N 的材料名称（按文档§3.2）
    materials = {36: '记忆石(36维)', 72: '变色龙(72维)', 108: '回声壁(108维)', 144: '完美镜子(144维)'}
    for r in results:
        if r['N'] in materials:
            print('  N=%d: %s (α=%.6f, 压缩比=%s)' % (
                r['N'], materials[r['N']], r['alpha'], r['compression_ratio']), flush=True)
    
    # N 与干涉束数关系
    print('\n干涉束数阶梯:', flush=True)
    for r in results:
        print('  N=%d → %d 束' % (r['N'], r['beams']), flush=True)
    
    # 常数阶梯
    print('\n常数阶梯 (当前体系 N=8 → 更高 N):', flush=True)
    for N_target in (8, 16, 32, 64):
        r = next((r for r in results if r['N'] == N_target), None)
        if r:
            print('  N=%d: α=%.8f κ=%.8f ε=%.8e d=%.4fnm M=%d' % (
                N_target, r['alpha'], r['kappa'], r['epsilon'], r['d_nm'], r['M']), flush=True)

    with open(r'C:\Users\Administrator\.zcode\workspace\default\theta_table_20260914.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1, default=str)
    print('\nSAVED theta_table_20260914.json (%d entries)' % len(results), flush=True)

if __name__ == '__main__':
    main()
