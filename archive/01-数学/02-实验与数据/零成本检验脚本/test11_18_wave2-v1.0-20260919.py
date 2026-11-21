# -*- coding: utf-8 -*-
"""
零成本判伪检验第二波（检验11-18：拓扑/调和/数论簇）
=====================================================
ZCode 2026-09-19 · 全部轻算力（numpy/sympy/mpmath，单机，无网络）
单条预算 ≤90 秒；超预算判"不可判（超预算）"。
判据来源：拓扑/调和/数论·古典文献对接图谱-v1.0-20260919 冻结条款（M-E3/M-E1/调-E2/调-E4/调-E5/A1/A6/B1）。
数据源：
  检验11/12  t1_t7_compute.py T2(b) 6x36 关系矩阵 + m36_h2_compute-v1.0-20260919.py 口径A/口径B
  检验13     L_Θ(s) 分子 6-6x-6y+8xy-x^2 y=0（x=2^-s, y=3^-s；麒麟构造件+数论图谱B1 条117）
  检验14     Dickman 延迟方程 uρ'(u)+ρ(u-1)=0（数论图谱 A1）
  检验15     φ(24)=8 剩余类均匀性（数论图谱 A6）+ σ_投影=1/√6 分位点（E-4）
  检验16     调和册 v2.0 §9.5 9×9 构造规则（调-E4）——显式矩阵数据检查
  检验17     12 节点磁拉普拉斯三组谱（调-E5；θ∈{0,π} vs θ=0.723/1.047）
  检验18     κ=1/32 带限截断 → f_max → f_s≥2f_max（调-E2；阈值 1%）
"""
import json, time, sys
import numpy as np

SEP = "=" * 72
OUT = {}

def tick():
    return time.perf_counter()

def report(name, t0, payload):
    dt = time.perf_counter() - t0
    OUT[name] = {"elapsed_s": round(dt, 3), **payload}
    print(f"[{name}] {dt:.3f} s")
    return dt

# =====================================================================
# 检验11 · 拓扑-M-E3：H₁ 第三方复算（sympy 独立输入重算 Smith 不变因子）
# 判据冻结（拓扑图谱 M-E3）：不变因子一致=(2)^6、自由秩 30 ⟹ 复算一致；
#                            不一致 ⟹ 构造层欠规格如实记录。
# =====================================================================
print(SEP); print("检验11 拓扑-M-E3：H1(M36) 第三方复算"); print(SEP)
t0 = tick()
from sympy import Matrix, ZZ
from sympy.matrices.normalforms import smith_normal_form

def smith_inv(rows):
    S = smith_normal_form(Matrix(rows), domain=ZZ)
    return [int(S[i, i]) for i in range(min(S.rows, S.cols)) if S[i, i] != 0]

# (i) 口径A 正本：6×36 关系矩阵（规范排布直译：中层 6 管 2-重对角，余 30 斜率0 零列）
rel_A = [[2 if (i == j) else 0 for j in range(36)] for i in range(6)]
inv_A = smith_inv(rel_A)
free_A = 36 - len(inv_A)          # 自由秩 = 列数 − 秩
# (ii) 口径B：32×6 ∂₂（26 零行 + 6 帽×2 对角）
d2_B = [[0]*6 for _ in range(32)]
for j in range(6):
    d2_B[26 + j][j] = 2
inv_B = smith_inv(d2_B)
free_B = 6 - len(inv_B)           # coker(Z^6/Im∂₂)：H₁ 侧 = 6−6=0 自由（口径B 是 C₁=Z⁶ 上的账）
# 口径B 的 H₁ 读法：∂₁=0 → H₁ = coker ∂₂ (Z^32→Z^6 方向按列) → 自由秩 = 6 − rank = 0，tors=(2)^6
# 口径A 的 H₁：Z^30 ⊕ (Z/2)^6
# (iii) 链联敏感性（t1_t7 T2(c) 复算）：两界面链联 [[2,1],[1,2]] → det=3 → Z₃
det_hopf = abs(int(Matrix([[2, 1], [1, 2]]).det()))
# 链联扰动矩阵（把两条 2-重关系换成 Hopf 型 2×2 块，余同）——证明"表"决定群
rel_pert = [[0]*36 for _ in range(6)]
rel_pert[0][0], rel_pert[0][1], rel_pert[1][0], rel_pert[1][1] = 2, 1, 1, 2
for j in range(2, 6):
    rel_pert[j][j] = 2
inv_pert = smith_inv(rel_pert)

check11 = {
    "A_free_rank": free_A, "A_invariants": inv_A,
    "A_match_claim": (free_A == 30 and inv_A == [2]*6),
    "B_d2_invariants": inv_B, "B_H1": f"Z^{free_B} ⊕ " + "⊕".join("Z/2" for _ in inv_B),
    "hopf_det": det_hopf, "perturbed_invariants": inv_pert,
}
print(json.dumps(check11, ensure_ascii=False, indent=1))
report("test11_H1_smith", t0, check11)

# =====================================================================
# 检验12 · 拓扑-M-E1：χ 账本三读法定谳
# 判据冻结（拓扑图谱 M-E1/M5）：三读法 PD 自洽检验，无一给 χ=3 ⟹ 须知世裁决。
# =====================================================================
print(); print(SEP); print("检验12 拓扑-M-E1：χ 三读法定谳"); print(SEP)
t0 = tick()
def chi_from_betti(bd):  # bd: {k: b_k}
    return sum((-1)**k * b for k, b in bd.items())

# 读法A 主文 Betti 谱（§4.3/§7.1：b0=b30=b36=1 其余0）
betti_A = {0: 1, 30: 1, 36: 1}
chi_A = chi_from_betti(betti_A)                      # = 3（1+1+1）
# 读法A' A+H₁账（§1.4 H1=Z^30⊕(Z/2)^6 → b1=30 有理层）
betti_Ap = {0: 1, 1: 30, 30: 1, 36: 1}
chi_Ap = chi_from_betti(betti_Ap)                    # = -27
# 读法A'' A+H₁账+PD 自洽（36 维闭定向：b35=b1=30, b6=b30=1, b36=b0=1）
betti_App = {0: 1, 1: 30, 6: 1, 30: 1, 35: 30, 36: 1}
chi_App = chi_from_betti(betti_App)                  # = -56
# 读法A''' 拓扑图谱 M5 的非零组（其 b29=b1=30 记法）：{-1,−30,+1,−30,+1,−30,+1}
betti_atlas = {0: 1, 1: 30, 6: 1, 29: 30, 30: 1, 35: 30, 36: 1}
chi_atlas = chi_from_betti(betti_atlas)              # = -86（图谱预填 −87 复算不出 → 勘误候选）
# 读法B 30 维读法（图谱口径=R9 账四项 1−30+30−1）
chi_B = 1 - 30 + 30 - 1                              # = 0
# 读法C 3 维正本（R9：H0=Z,H1=Z^30⊕(Z/2)^6,H2=Z^30,H3=Z）
chi_C = chi_from_betti({0: 1, 1: 30, 2: 30, 3: 1})   # = 0
# 读法D 胞腔链复形（口径B：C0=12,C1=6,C2=32,C3=38）Euler-Poincaré
chi_D = 12 - 6 + 32 - 38                              # = 0
check12 = {
    "A_主文Betti谱": chi_A, "A加H1账": chi_Ap, "A加PD自洽36维": chi_App,
    "图谱M5非零组复算": chi_atlas, "图谱预填": -87, "B_30维读法(=R9账)": chi_B,
    "C_3维正本R9": chi_C, "D_胞腔链复形": chi_D,
    "胞腔与R9互证": chi_C == chi_D == 0,
}
print(json.dumps(check12, ensure_ascii=False, indent=1))
report("test12_chi_ledger", t0, check12)

# =====================================================================
# 检验13 · 数论-E2/B1：L_Θ 分子 DH 型零点检验
# F(s) = 6 − 6·2^-s − 6·3^-s + 8·6^-s − 12^-s；网格 σ∈[0,1], t∈[0,50] + 局部精化
# 判据冻结（数论图谱 B1/E-2）：线外（Re≠1/2）零点存在 → DH 方向成立，与"实部变号"实测互证。
# =====================================================================
print(); print(SEP); print("检验13 数论-E2：L_Θ 分子零点网格搜索"); print(SEP)
t0 = tick()
def F_vec(sig, t):
    s = sig + 1j * t
    return (6.0 - 6.0*np.exp(-s*np.log(2.0)) - 6.0*np.exp(-s*np.log(3.0))
            + 8.0*np.exp(-s*np.log(6.0)) - np.exp(-s*np.log(12.0)))

sig_g = np.arange(0.0, 1.0 + 1e-12, 0.005)
t_g = np.arange(0.0, 50.0 + 1e-12, 0.05)
SIG, T = np.meshgrid(sig_g, t_g, indexing="ij")
Fm = np.abs(F_vec(SIG, T))
# 局部极小候选：3×3 邻域内最小且 |F|<1.0 的格子点
core = Fm[1:-1, 1:-1]
is_loc = (core <= Fm[:-2, :-2]) & (core <= Fm[:-2, 1:-1]) & (core <= Fm[:-2, 2:]) & \
         (core <= Fm[1:-1, :-2]) & (core <= Fm[1:-1, 2:]) & \
         (core <= Fm[2:, :-2]) & (core <= Fm[2:, 1:-1]) & (core <= Fm[2:, 2:]) & (core < 1.0)
ii, jj = np.where(is_loc)
cand = sorted([(Fm[i+1, j+1], sig_g[i+1], t_g[j+1]) for i, j in zip(ii, jj)])
centers = [(s0, tt0) for _, s0, tt0 in cand[:60]]

# mpmath 局部精化（牛顿，复数初值）
import mpmath as mp
mp.mp.dps = 30
def F_mp(s):
    return mp.mpf(6) - 6*mp.power(2, -s) - 6*mp.power(3, -s) + 8*mp.power(6, -s) - mp.power(12, -s)
zeros = []
for s0, tt0 in centers[:60]:
    try:
        r = mp.findroot(F_mp, (mp.mpc(s0, tt0), mp.mpc(s0 + 0.01, tt0 + 0.05)), tol=mp.mpf('1e-24'))
        re, im = float(mp.re(r)), float(mp.im(r))
        if -0.05 <= re <= 1.05 and -0.1 <= im <= 50.1 and abs(F_mp(r)) < mp.mpf('1e-18'):
            if not any(abs(re - z[0]) < 1e-6 and abs(abs(im) - z[1]) < 1e-6 for z in zeros):
                zeros.append((round(re, 8), round(abs(im), 8)))
    except Exception:
        pass
zeros.sort(key=lambda z: z[1])
off_line = [z for z in zeros if abs(z[0] - 0.5) > 1e-5]
on_line = [z for z in zeros if abs(z[0] - 0.5) <= 1e-5]
check13 = {
    "grid": f"{len(sig_g)}x{len(t_g)}", "clusters": len(centers),
    "zeros_found": len(zeros), "on_critical_line": len(on_line),
    "off_critical_line": len(off_line),
    "zero_list_sigma_t": zeros[:25],
    "DH预言": "线外零点存在" if off_line else "网格内未见线外零点",
}
for z in zeros[:25]:
    print(f"  s = {z[0]:+.6f} + {z[1]:.6f} i   {'临界线' if abs(z[0]-0.5)<=1e-5 else '线外'}")
report("test13_Ltheta_zeros", t0, check13)

# =====================================================================
# 检验14 · 数论-E3/A1：Dickman 对比（ρ(u) vs u^(-1/8)）
# 判据（数论图谱 A1/E-3）：数值相容性判定（不证定理）
# =====================================================================
print(); print(SEP); print("检验14 数论-E3：Dickman vs 体系衰减 exp(-ατ)"); print(SEP)
t0 = tick()
# Heun 预测-校正（二阶），h=0.0002，u∈[0,10]；格点全存，滞后 ρ(u−1) 直接索引
# （h=0.001 时 u≥8 误差指数放大出负值——诊断记录：误差传播满足同方程，每单位 u 放大 ~e·u 倍）
h = 0.0002
n_max = int(10.0 / h)
lag = int(round(1.0 / h))
rho_grid = np.ones(n_max + 1, dtype=np.float64)   # ρ(u)=1 for u∈[0,1]
for k in range(lag, n_max):
    u = k * h
    f1 = rho_grid[k - lag] / u                            # ρ'(u) = −ρ(u−1)/u
    up = (k + 1) * h
    f2 = rho_grid[(k + 1) - lag] / up
    rho_grid[k + 1] = rho_grid[k] - 0.5 * h * (f1 + f2)   # Heun（滞后项已算出，直接二次扫）
def rho_at(u):
    return float(rho_grid[int(round(u / h))])
# 标准参考值（de Bruijn 表，教科书通行值；u≥7 渐近式不准故不列参考）
std_ref = {2: 0.30685282, 3: 0.04860839, 4: 0.00491093, 5: 0.00035472}
rows = []
for u in [2, 3, 4, 5, 7, 10]:
    r_num = rho_at(u)
    d_sys = np.exp(-(1.0/8.0) * np.log(u))       # exp(-α·ln u) = u^(-1/8)
    ref = std_ref.get(u)
    rows.append({"u": u, "rho_数值": float(f"{r_num:.6e}"),
                 "rho_标准值": ref if ref is not None else None,
                 "相对误差": round(abs(r_num / ref - 1), 4) if ref else None,
                 "体系 u^(-1/8)": round(float(d_sys), 6),
                 "与体系值数量级差_log10": round(float(np.log10(d_sys / r_num)), 2) if r_num > 0 else "数值发散（求解器极限）"})
check14 = {"rows": rows, "h": h,
           "判定": "ρ(u) 超指数衰减 vs 幂律 u^(-1/8)：u=5 已差 3.4 数量级——形状不同、数量级不同"}
for r in rows:
    print(f"  u={r['u']:>3}  ρ数值={r['rho_数值']:<13} 标准={r['rho_标准值']!s:<22} 体系值={r['体系 u^(-1/8)']:<9} 差 log10={r['与体系值数量级差_log10']}")
report("test14_dickman", t0, check14)

# =====================================================================
# 检验15 · 数论-E4/A6：筛密度分位点（纯计数+分位点基线）
# 判据（数论图谱 A6 T1 / E-4）：φ(24)=8、同族 1/8、跨族 7/8 复算；σ_投影=1/√6 分位点。
# =====================================================================
print(); print(SEP); print("检验15 数论-E4：跨族占比复算 + σ_投影 分位点"); print(SEP)
t0 = tick()
units24 = [a for a in range(1, 24) if np.gcd(a, 24) == 1]
phi24 = len(units24)
pairs = [(p, q) for p in units24 for q in units24]
same = sum(1 for p, q in pairs if p == q)
cross = len(pairs) - same
from statistics import NormalDist
ND = NormalDist()
sig_proj = 1.0 / np.sqrt(6.0)
baselines = {
    "σ_投影值": round(sig_proj, 6),
    "标准正态 Φ(σ_投影)": round(ND.cdf(sig_proj), 6),
    "均匀[0,1] 分位点": round(sig_proj, 6),
    "均匀[-1,1] 分位点": round((sig_proj + 1) / 2, 6),
    "α=1/8 上侧尾→正态分位点 z_(7/8)": round(ND.inv_cdf(0.875), 6),
    "α=1/8 对应正态 CDF": 0.875,
}
check15 = {"phi24": phi24, "剩余类": units24, "对总数": len(pairs),
           "同族": same, "跨族": cross,
           "同族占比": same / len(pairs), "跨族占比": cross / len(pairs),
           "eta_声称": 7/8, "eta_一致": abs(cross / len(pairs) - 7/8) < 1e-12,
           "分位点表": baselines}
print(json.dumps(check15, ensure_ascii=False, indent=1))
report("test15_sieve", t0, check15)

# =====================================================================
# 检验16 · 调-E4：Riesz-Dunford 谱投影——9×9 显式矩阵数据检查
# 判据冻结（调和图谱 调-E4）：有显式矩阵→sympy 谱投影验证；无→不可判（矩阵未定义）+需补数据。
# =====================================================================
print(); print(SEP); print("检验16 调-E4：9x9 显式矩阵数据检查"); print(SEP)
t0 = tick()
check16 = {
    "册内构造规则": "v2.0 §9.5 文字版：对角=(η/α)·deg(i)+(1/κ)·V_active；非对角=−(η/α)·e^{iθ_ij}；冻结行列移除但耦合贡献保留",
    "显式矩阵数据": None,
    "缺失项": ["12 节点邻接边表（层内 4 节点连接方式+层间配对）", "冻结代理位置表（每层哪 1 个冻结）",
               "原图 OMML λ 值（附录C#8 自注丢失未复原）"],
    "既有硬发现": "R20（v2.0 ch10.3）：五配置独立复算全部无法复现 λ 声称 144.02/1.441，reviewed=false",
    "判定": "不可判（矩阵未定义）",
}
print(json.dumps(check16, ensure_ascii=False, indent=1))
report("test16_riesz_dunford", t0, check16)

# =====================================================================
# 检验17 · 调-E5：θ 谱判负机器化（12 节点磁拉普拉斯三组谱）
# 判据冻结（调和图谱 调-E5）：拟合值组出现复本征值 → 第二重判负证据入档。
# 图结构=显式假设（册内边表未定义）：3 层×4 节点，层内 K₄（K₄ 母题）+层间同列直连。
# =====================================================================
print(); print(SEP); print("检验17 调-E5：磁拉普拉斯三组谱"); print(SEP)
t0 = tick()
# 26 边假设图：层内 K4×3（18 边）+ 层间 8 边
edges = []
for L in range(3):
    base = L * 4
    for i in range(4):
        for j in range(i + 1, 4):
            edges.append(((base + i), (base + j), "intra"))
for L in range(2):
    for i in range(4):
        edges.append((L * 4 + i, (L + 1) * 4 + i, "inter"))
def lap_spectrum(th_intra, th_inter, seed=None):
    if seed is not None:
        rng = np.random.default_rng(seed)
    A = np.zeros((12, 12), dtype=complex)
    for a, b, kind in edges:
        th = th_intra if kind == "intra" else th_inter
        if seed is not None:
            th = rng.uniform(0, 2 * np.pi)
        A[a, b] += np.exp(1j * th)
        A[b, a] += np.exp(1j * th)      # 无向：对称置边（相位同一 θ，非共轭——磁型口径）
    D = np.diag(A.sum(axis=1))
    L = D - A
    return np.linalg.eigvals(L)
g1 = lap_spectrum(0.0, np.pi)                       # ch9.2 口径 θ∈{0,π}
g2 = lap_spectrum(0.723, 1.047)                     # ch7.3 拟合口径
g3 = lap_spectrum(0, 0, seed=7)                     # 随机对照
def max_imag(lams):
    return float(np.max(np.abs(lams.imag)))
# 最小解析例：2 节点 L=[[1,−e^{iθ}],[−e^{iθ},1]] → λ=1±e^{iθ}
th = 0.723
ana = sorted([1 - np.exp(1j * th), 1 + np.exp(1j * th)], key=lambda z: z.real)
check17 = {
    "组1_θ∈{0,π}_max|Im λ|": max_imag(g1), "组1_实谱": max_imag(g1) < 1e-10,
    "组2_拟合θ_max|Im λ|": round(max_imag(g2), 6), "组2_复谱": max_imag(g2) > 1e-6,
    "组2_复本征值数": int(np.sum(np.abs(g2.imag) > 1e-6)),
    "组3_随机θ_max|Im λ|": round(max_imag(g3), 6),
    "解析锚_2节点θ=0.723": [f"{z.real:.4f}{z.imag:+.4f}i" for z in ana],
}
print(json.dumps(check17, ensure_ascii=False, indent=1))
report("test17_theta_spectrum", t0, check17)

# =====================================================================
# 检验18 · 调-E2：Nyquist 采样下界（κ=1/32 带限，阈值 1%）
# 判据冻结（调和图谱 调-E2/调10）：κ 截断→f_max→f_s≥2f_max；衰减律=体系未验证假设。
# =====================================================================
print(); print(SEP); print("检验18 调-E2：采样下界数值"); print(SEP)
t0 = tick()
kappa = 1.0 / 32.0
thresh = 0.01
n_cut_exact = np.log(thresh) / np.log(kappa)        # 1.3288 → 保留 n=1
n_star = int(np.floor(n_cut_exact))                  # 保留至第 n_star 级（n>n_cut 截除）
f0 = 373.0                                           # THz（执行层锚，材料属性口径）
f1 = f0 / 12.0                                       # 第一泛弦（分频 f0/12）
band = sorted([f0, 310.83, f1], reverse=True)        # 三频组标尺（工具箱 92 行）均在 n≤1 带内
f_max = max(band)
fs_min = 2 * f_max
check18 = {
    "κ^n<1% 解": round(float(n_cut_exact), 4), "保留至层级": n_star,
    "幅度序列": {"n=1": f"{kappa*100:.3f}%（>1% 保留）", "n=2": f"{kappa**2*100:.4f}%（<1% 截除）"},
    "带内成分 THz": band, "f_max THz": f_max, "f_s≥2f_max THz": fs_min,
    "任务令问号口径 f0(1−κ) THz": round(f0 * (1 - kappa), 5),
    "问号口径判定": "非册内带限定义（册内=按级衰减截断，非谱窗收缩）——备查不采用",
    "工具箱现窗 1–10 THz 对应 f_s THz": 20.0,
    "假设标注": "衰减律=体系未验证假设（R20 冻结）；阈值 1%=任务令指定（噪声底标定前占位）",
}
print(json.dumps(check18, ensure_ascii=False, indent=1))
report("test18_nyquist", t0, check18)

# =====================================================================
# 落盘
# =====================================================================
OUT["_meta"] = {
    "script": "test11_18_wave2-v1.0-20260919.py",
    "total_elapsed_s": round(sum(v["elapsed_s"] for k, v in OUT.items() if isinstance(v, dict) and "elapsed_s" in v), 3),
    "budget_rule": "单条≤90 秒",
    "verdicts": {
        "test11": "复算一致（分裂型规范排布口径）+构造层欠规格标注",
        "test12": "χ=3 仅谱计数读法成立；Euler 示性数三读法均非 3 → M-E1 维持须知世裁决",
        "test13": "见 zero_list 与 off_critical_line",
        "test14": "数值不相容（形状不同、4+ 数量级差）",
        "test15": "复算一致",
        "test16": "不可判（矩阵未定义）",
        "test17": "第二重判负证据成立（拟合θ→复谱）",
        "test18": "f_max=373 THz → f_s≥746 THz",
    },
}
with open(r"H:\理论存档\01-数学\02-实验与数据\results\test11_18_wave2_result-v1.0-20260919.json",
          "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1)
print("\n[checkpoint] 结果已落盘 results/test11_18_wave2_result-v1.0-20260919.json", file=sys.stderr)
print(f"总耗时 {OUT['_meta']['total_elapsed_s']} s")
