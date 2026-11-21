# -*- coding: utf-8 -*-
"""
Θ(2) 因果维度直算（天工开物 第十七批 · 知世令"不要近似自己算" 2026-09-15）
生成公式原样外延（theta_table_20260914.py 同源，不设合法性门槛）：
  α = 2^(-v2) + (1/6 − 2^(-v2))·s；η=1−α；κ=α/4；ε=α²；d=α nm；M=round(1/α)
  D=3N；束数=2(D−1)；压缩比=2^(16(D−3)/7)；λ₂=0.0022·D⁴(D−1)；n_D=3/D；c_D/c₃=2^(8(D−3)/7)
因果维度 D=6 → 扇区 N=2（v₂=1）：公式直算有效，扇区合法性（v₂≥2 条款外）待知世裁决。
"""
import json, math

def theta_full(N):
    fac = {}; n = N; d = 2
    while d * d <= n:
        while n % d == 0:
            fac[d] = fac.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: fac[n] = fac.get(n, 0) + 1
    v2 = fac.get(2, 0); v3 = fac.get(3, 0); s = 1 if v3 >= 1 else 0
    alpha = 2**(-v2) + (1/6 - 2**(-v2)) * s
    D = 3 * N
    return dict(N=N, v2=v2, v3=v3, s=s, alpha=alpha, eta=1-alpha,
                group=('Z2' if v2 == 1 else f'(Z2)^{v2}') if s == 0 else 'A4族',
                D=D, beams=2*(D-1), theta_deg=360.0/N, kappa=alpha/4,
                epsilon=alpha**2, d_nm=alpha, M=int(round(1/alpha)),
                compression=2**(16*(D-3)/7) if D > 3 else 1, legal=(v2 >= 2))

if __name__ == "__main__":
    t2 = theta_full(2)
    t2.update({
        "lambda2": 0.0022 * t2["D"]**4 * (t2["D"]-1),
        "n_D": 3/t2["D"], "resistance": abs(1 - 3/t2["D"]),
        "c_D_over_c3": 2**(8*(t2["D"]-3)/7),
        "Tc_at_Lambda_alpha_K": 350/math.sqrt(t2["alpha"]+0.01),
        "E_Free": 1.5*(t2["D"]-1),
        "legality_flag": "v₂=1<2 → 表外延拓：公式计算有效，合法性待知世裁决（非近似）",
        "feasibility_note": "d=0.5nm>原子间距0.254nm——因果维度缺陷周期几何可行",
        "consistency": "束数10=分量数2(D−1)=10，两读法自洽合流"})
    t12 = theta_full(12)
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/ys_theta2_causal.json", "w", encoding="utf-8") as f:
        json.dump({"因果维度D6_Θ2直算": t2,
                   "对照_被否决N12近似": {"alpha": t12["alpha"], "d_nm": t12["d_nm"], "M": t12["M"]},
                   "honest_note": "生成公式原样外延直算，无近似；全部【未验证】待实测"},
                  f, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in t2.items()},
                     ensure_ascii=False, indent=1, default=float))
