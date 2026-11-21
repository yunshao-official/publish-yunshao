# -*- coding: utf-8 -*-
"""
JC-H3 云韶拉普拉斯谱独立重算 v1.0（2026-09-19，ZCode）
判据来源：数论线账本 JC-H3（对象：调和分析册 H2/R20）
算子（调和分析册§4.1-4.4 原文定义）：
  12 节点三层 K₄ 链环图：层内完全图（度3），层间垂直对应连接（相邻层单位阵）
  L_Γ = D - A（图拉普拉斯）
  云韶算子：λ = (η/α)·μ + (1/κ)·V，η/α=7，1/κ=32，V=V_single·I
方法：纯 Python 对称 Jacobi 特征分解（不依赖 numpy）。
检验项：
  V1 册内声称 μ₁≈0.76、μ₂≈1.27 是否复现（§4.4 原文）
  V2 常数项两套并存（§4.3: 32×4/3=42.67 vs §4.4/§5: 128=32×4）——两口径都算
  V3 比例失败复现：λ₀/λ₁ 与 λ₀/λ₂（册内承认 ≈0.858/0.783 ≠ 144/1.44，图拉普拉斯近似失败）
  V4 新谱登记：精确 μ 谱 + 两口径 λ 谱（供轨道②/R20 修复取用）
诚实标签：执行层独立重算；不构成对修正框架（第六-七章）的检验。
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')

N = 12; LAYERS = 3; PER = 4
def idx(layer, i): return layer*PER + i

# 邻接矩阵
A = [[0.0]*N for _ in range(N)]
for l in range(LAYERS):
    for i in range(PER):
        for j in range(PER):
            if i != j:
                A[idx(l,i)][idx(l,j)] = 1.0
for l in range(LAYERS-1):
    for i in range(PER):
        A[idx(l,i)][idx(l+1,i)] = 1.0
        A[idx(l+1,i)][idx(l,i)] = 1.0
deg = [sum(A[i]) for i in range(N)]
Lap = [[(deg[i] if i==j else 0.0) - A[i][j] for j in range(N)] for i in range(N)]

def jacobi_eig(M, iters=200):
    n = len(M)
    a = [row[:] for row in M]
    for _ in range(iters):
        off = math.sqrt(sum(a[i][j]**2 for i in range(n) for j in range(n) if i!=j))
        if off < 1e-12: break
        for p in range(n-1):
            for q in range(p+1, n):
                if abs(a[p][q]) < 1e-15: continue
                theta = (a[q][q]-a[p][p])/(2*a[p][q])
                t = (1 if theta>=0 else -1)/(abs(theta)+math.sqrt(theta*theta+1))
                c = 1/math.sqrt(t*t+1); s = t*c
                for k in range(n):
                    akp = a[k][p]; akq = a[k][q]
                    a[k][p] = c*akp - s*akq; a[k][q] = s*akp + c*akq
                for k in range(n):
                    apk = a[p][k]; aqk = a[q][k]
                    a[p][k] = c*apk - s*aqk; a[q][k] = s*apk + c*aqk
    return sorted(a[i][i] for i in range(n))

mu = jacobi_eig(Lap)
print("="*66)
print("JC-H3 云韶拉普拉斯谱独立重算 v1.0 ｜ 2026-09-19")
print("="*66)
print(f"图：12节点三层K₄链环（层内K₄，层间垂直对应）；度序列={sorted(set(deg))}（层1/3:{deg[0]}，层2:{deg[4]}）")
print(f"\nμ 谱（图拉普拉斯，升序）：")
print("  " + "  ".join(f"{v:.6f}" for v in mu))
mu1, mu2 = mu[1], mu[2]
print(f"\nV1 册内声称复现检验（§4.4：μ₁≈0.76、μ₂≈1.27）：")
print(f"  重算 μ₁={mu1:.4f}（声称0.76，偏差 {abs(mu1-0.76):.4f}）")
print(f"  重算 μ₂={mu2:.4f}（声称1.27，偏差 {abs(mu2-1.27):.4f})")
print(f"  判定：{'μ 声称复现' if abs(mu1-0.76)<0.05 and abs(mu2-1.27)<0.05 else 'μ 声称与重算不符（偏差超容差）'}")

V_a = 4/3   # §4.2/§4.3 口径：V_single=64/48=4/3
V_b = 4.0   # §4.4 行文"V=V_single≈4"口径 → 常数项 128
for name, V in (("口径a：V=4/3（常数项 32×4/3=42.67）", V_a), ("口径b：V=4（常数项 32×4=128）", V_b)):
    lam = [7*m + 32*V for m in mu]
    r1 = lam[0]/lam[1]; r2 = lam[0]/lam[2]
    print(f"\nV2/V3 {name}：")
    print(f"  λ 谱前六：{'  '.join(f'{v:.3f}' for v in lam[:6])}")
    print(f"  λ₀/λ₁={r1:.4f}  λ₀/λ₂={r2:.4f}")
    print(f"  对照泛弦比例 144 与 1.44：偏离 {abs(144-r1)/144*100:.1f}% / {abs(1.44-r2)/1.44*100:.1f}%")
    print(f"  → 图拉普拉斯近似下比例失败{'复现' if r1<1 and r2<1 else '异常'}（册内§5.1 自承认结论一致）")

print("\nV4 判定汇总（JC-H3 部分执行）：")
print("  └ 图结构 μ 谱已精确重算并入档（轨道②/R20 修复的起点数据）")
print("  └ 册内 μ₁/μ₂ 声称值待与上行 V1 对照——偏差即记录")
print("  └ 常数项 42.67 vs 128 两套并存=新发现精确对表差异（V_single=4/3 vs ≈4），入轨道②提案补遗")
print("  └ 修正框架（第六-七章）不含于此重算范围——诚实边界")
