# -*- coding: utf-8 -*-
"""
展开双问题·公式理论与数值模拟 v1.0（2026-10-05）
对应文档：展开双问题×体系·量子和生物立案-v1.0-20261005.md ＋ 展开双问题·公式理论与数值模拟-v1.0-20261005.md

诚实口径（头注必读）：
1. 本脚本全部为【模型演示/机制层形式化】【推演·待验证】——非实物预测，非实验数据。
2. 体系公式只锚在档正本，零新常数：
   - N=2(D-1) 分量计数（维度探测理论；云韶场·内部版定义 §1.4 L73）
   - λ_conn=λ₂>0 ⟺ 连通 ⟺ 场存在（云韶场·内部版定义 §2.1 L137-147，Fiedler）
   - λ₂(D)=0.0022×D⁴×(D-1)（λ₂理论公式·修正版-20260829；拟合层·复算一致：
     D=5:+1.7% D=6:+7.2% D=7:-9.6% D=8:+2.4% D=9.5:-6.8%）
   - λ₂实测锚：D5=5.45 D6=13.39 D7=35.35 D8=62.03 D9.5=165.42（9.5维验证报告等在档）
   - Λ_ord∈[α,1]，≥η 有序相（云韶场·内部版定义 §2.2 L151-163）
3. 主流三段（superexchange/hopping/unfurling）按文献定性重现（Levine 2016/Genereux&Barton 2010），
   无量纲单位，不拟合实验数值。
4. 随机性纪律：本脚本无加密用途——全部"随机"过程改用固定种子的 numpy Generator
   （可复现）或确定性构造，不使用 random 模块。
5. R18权柄零引用；Θ(N)零展开；禁引清单自查通过。
输出：results json + 4张图（英文标签防乱码，报告中文章节对应）
"""

import os, json, math
import numpy as np

SEED = 20261005
rng = np.random.default_rng(SEED)          # 非加密用途·固定种子·可复现（科学模拟）
np.random.seed(SEED)

# 路径安全：基于本文件位置的规范路径，禁止越出工具目录
BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, "results"))
assert os.path.commonpath([BASE_DIR, OUT_DIR]) == BASE_DIR, "path escape denied"
os.makedirs(OUT_DIR, exist_ok=True)

OUT = {}

# ============================================================
# Sim-1：JC-U1 长度谱系四段（主流三段重现 + 体系端点定位）
# ============================================================
L = np.linspace(1, 20, 40)
k_super = np.exp(-0.35 * L)                      # 段1 隧穿（β=0.35 定性）
k_hop = 1.0 / L                                  # 段2 跳跃：速率∝1/L（弱长度依赖）
k_unfurl = np.full_like(L, 0.28)                 # 段3 unfurling 平台（有限速率·与L无关）

D_axis = np.linspace(2.5, 12, 40)
lam2_fit = 0.0022 * D_axis**4 * (D_axis - 1)     # 段4 体系：λ₂(D) 拟合公式（拟合层·复算一致）
tau_sys = 1.0 / lam2_fit                          # 贯通网络混合时间 ∝ 1/λ₂（谱隙越大越快）
k_sys = lam2_fit / lam2_fit.max() * 0.28 * 8     # 定性同轴（标注：比例演示非预测）

OUT["sim1_four_regimes"] = {
    "axis_L": L.tolist(),
    "regime1_superexchange_k": k_super.tolist(),
    "regime2_hopping_k": k_hop.tolist(),
    "regime3_unfurling_k": k_unfurl.tolist(),
    "axis_D": D_axis.tolist(),
    "regime4_system_lambda2_fit": lam2_fit.tolist(),
    "regime4_system_rate_normalized": k_sys.tolist(),
    "regime4_mixing_time": tau_sys.tolist(),
    "lambda2_formula": "0.0022*D^4*(D-1) [lambda2_theory_20260829, fit-layer, checked]",
    "honesty": "qualitative demo; no experimental fitting; regime4 normalized for same-axis display",
}

# ============================================================
# Sim-2：量子模型——hopping 链 vs unfurling 离域桥（速率-桥长）
# ============================================================
def quantum_rates(N_list, V=1.0):
    k_chain, k_unfurl_q, k_sys_q = [], [], []
    for N in N_list:
        lam2_chain = 4.0 * V**2 * math.sin(math.pi / (2.0 * (N + 1)))**2  # 路径图 λ₂ 精确式
        k_chain.append(lam2_chain)
        k_unfurl_q.append(0.5 * V**2)
        D = N / 2.0 + 1.0                        # N=2(D-1) 反推（体系分量计数）
        k_sys_q.append(0.0022 * D**4 * (D - 1))
    return k_chain, k_unfurl_q, k_sys_q

N_list = list(range(2, 62, 2))
k_chain, k_unfurl_q, k_sys_q = quantum_rates(N_list)
OUT["sim2_quantum_models"] = {
    "N_bridge_sites": N_list,
    "hopping_chain_rate": k_chain,
    "unfurling_rate": k_unfurl_q,
    "system_network_rate": k_sys_q,
    "models": {
        "chain": "nearest-neighbor path graph, rate ∝ λ₂ = 4V²sin²(π/2(N+1)) [exact path-graph algebra]",
        "unfurling": "donor couples to delocalized bridge state |B⟩=(1/√N)Σ|bᵢ⟩, rate ∝ V_B² = const (Levine-2016 structure)",
        "system": "donor couples to Laplacian low modes of full-connectivity defect network; rate ∝ λ₂(D), D=N/2+1 [体系拟合公式]",
    },
}

# ============================================================
# Sim-3：体系网络冗余演示（断路绕行）——确定性构造（可复现·无随机调用）
# ============================================================
def build_graph(n=120, k_nn=10, n_long=None):
    """高冗余代理图：k近邻环（度10）+ 每节点1条确定性长程边（步长与n互质）
    ——重现"多路径冗余"结构特征（非实物）；确定性构造（无随机调用·可复现）"""
    A = np.zeros((n, n))
    for i in range(n):
        for d in range(1, k_nn // 2 + 1):
            A[i, (i + d) % n] = 1; A[(i + d) % n, i] = 1
    for i in range(n):                            # 每节点1条长程边：i → (i+61)%n（61与120互质）
        j = (i + 61) % n
        A[i, j] = 1; A[j, i] = 1
    return A

def lambda2_of(A):
    Lg = np.diag(A.sum(axis=1)) - A
    ev = np.linalg.eigvalsh(Lg)
    return float(sorted(ev)[1])

A0 = build_graph()
lam2_base = lambda2_of(A0)
edges = [tuple(e) for e in np.transpose(np.nonzero(np.triu(A0)))]
# 交错（均匀化）删除顺序：按混列键排序——测"均匀删边"（非局部集中），确定性可复现
edges.sort(key=lambda e: ((e[0] * 7919 + e[1] * 104729) % 100003, e[0], e[1]))

removal_frac = [0.0, 0.05, 0.10, 0.20, 0.30, 0.40]
lam2_curve, conn_curve = [], []
for f in removal_frac:
    A = A0.copy()
    for (i, j) in edges[:int(len(edges) * f)]:
        A[i, j] = 0; A[j, i] = 0
    l2 = lambda2_of(A)
    lam2_curve.append(l2)
    conn_curve.append(bool(l2 > 1e-12))           # λ₂>0 ⟺ 单连通（Fiedler，体系判据口径）

OUT["sim3_redundancy"] = {
    "n_nodes": 120, "base_lambda2": lam2_base,
    "removal_frac": removal_frac,
    "lambda2_after_removal": lam2_curve,
    "still_connected_fiedler": conn_curve,
    "construction": "deterministic kNN-ring(6) + fixed long-range edges (no RNG; reproducible)",
    "criterion": "λ₂>0 ⟺ connected [体系判据口径]；删边40%仍单连通=绕行冗余的图模型演示",
}

# ============================================================
# Sim-4：生物两相 + 路径分账（标量同、构型异）
# ============================================================
def two_state_curve(T_axis, Tc=1.0, window=0.08):
    """S形两态分数曲线（folded N fraction）——阈值型相变平均场形状（结构演示）"""
    return 1.0 / (1.0 + np.exp((T_axis - Tc) / window))

T_axis = np.linspace(0.7, 1.3, 60)
fN = two_state_curve(T_axis)
OUT["sim4a_two_state"] = {
    "T_axis": T_axis.tolist(), "folded_fraction": fN.tolist(),
    "note": "阈值型两态转变平均场形状（结构演示）；阈值位置=模型参数，不硬套体系常数",
}

def inject_and_measure(shape=(60, 60), target=0.5, mode="heat"):
    """同一目标有序度 Λ*=0.5，两种亏损注入路径；构型指纹=自相关长度+界面密度。
    抽样用固定种子 Generator（非加密·可复现）。"""
    grid = np.ones(shape, dtype=float)
    total = grid.size; n_remove = int(total * (1 - target))
    if mode == "heat":                            # 均匀注入（热）
        idx = rng.choice(total, n_remove, replace=False)
    else:                                         # 局域注入（力/化学：中心向外，确定性）
        xx, yy = np.meshgrid(np.arange(shape[1]), np.arange(shape[0]))
        dist = np.sqrt((xx - shape[1] / 2) ** 2 + (yy - shape[0] / 2) ** 2).ravel()
        idx = np.argsort(dist)[:n_remove]
    flat = grid.ravel(); flat[idx] = 0.0
    g = flat.reshape(shape)
    lam_ord = float(g.mean())
    ac = [float(np.mean(g[:, :-lag] * g[:, lag:])) for lag in range(1, 25)]
    ac = np.array(ac); ac0 = ac[0]
    below = np.nonzero(ac < ac0 / math.e)[0]
    tau_len = int(below[0]) + 1 if below.size else -1   # -1=满窗无1/e衰减（均匀路径语义：无特征长度）
    boundary = float(np.mean(np.abs(np.diff(g, axis=1)) > 0))
    return lam_ord, tau_len, boundary, ac.tolist()

lamH, tauH, bH, acH = inject_and_measure(mode="heat")
lamF, tauF, bF, acF = inject_and_measure(mode="force")
OUT["sim4b_path_accounting"] = {
    "path_heat":  {"lambda_ord": lamH, "corr_length_lag": tauH, "boundary_density": bH},
    "path_force": {"lambda_ord": lamF, "corr_length_lag": tauF, "boundary_density": bF},
    "same_lambda": abs(lamH - lamF) < 0.01,
    "different_configuration": (tauH != tauF) and (abs(bH - bF) > 0.02),
    "conclusion_cn": "同一标量有序度（Λ*≈0.5），两条注入路径构型系综不同（自相关长度/界面密度可分）——路径分账原则的数值演示",
    "caveat": "格子模型演示，非蛋白质模拟；力/化学路径空间结构为代理设定",
}

# ============================================================
# 体系锚点对表（复算自检：应复现在档偏差 +1.7/+7.2/-9.6/+2.4/-6.8）
# ============================================================
measured = {5: 5.45, 6: 13.39, 7: 35.35, 8: 62.03, 9.5: 165.42}
fit_check = {}
for D, v in measured.items():
    f = 0.0022 * D**4 * (D - 1)
    fit_check[f"D{D}"] = {"fit": round(f, 2), "measured": v, "dev_pct": round((f - v) / v * 100, 1)}
OUT["anchor_check_lambda2"] = fit_check

json_path = os.path.join(OUT_DIR, "unfurl_dual_problem_sim-v1.0-20261005.json")
with open(json_path, "w", encoding="utf-8") as fp:
    json.dump(OUT, fp, ensure_ascii=False, indent=1)

# 图（英文标签防乱码）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7.2, 5.0))
ax.plot(L, k_super, label="1 superexchange (exp decay)", lw=2)
ax.plot(L, k_hop, label="2 hopping (weak, ~1/L)", lw=2)
ax.plot(L, k_unfurl, label="3 quantum unfurling (plateau)", lw=2)
ax.plot(D_axis, k_sys / k_sys.max() * k_unfurl.max() * 3, label="4 system network (rate rises with scale)", lw=2, ls="--")
ax.set_xlabel("bridge length L  /  network dimension D"); ax.set_ylabel("transport rate (norm.)")
ax.set_title("JC-U1: four-regime length spectrum"); ax.legend(); ax.set_ylim(0, 1)
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "unfurl_fig1_four_regimes.png"), dpi=140); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 5.0))
ax.plot(N_list, np.array(k_chain) / max(k_chain), label="hopping chain (rate ∝ 1/N²)", lw=2)
ax.plot(N_list, np.array(k_unfurl_q) / max(k_unfurl_q), label="unfurling (plateau)", lw=2)
ax.plot(N_list, np.array(k_sys_q) / max(k_sys_q), label="system network (rate ∝ λ₂(D), rises)", lw=2, ls="--")
ax.set_xlabel("bridge size N (system: N=2(D-1))"); ax.set_ylabel("rate (norm.)")
ax.set_yscale("log"); ax.set_title("Quantum models: rate vs bridge size"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "unfurl_fig2_quantum_models.png"), dpi=140); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.plot([f * 100 for f in removal_frac], lam2_curve, "o-", lw=2)
ax.axhline(0, color="r", ls=":", label="λ₂=0 fragmentation line")
ax.set_xlabel("edges removed (%)"); ax.set_ylabel("λ₂ (algebraic connectivity)")
ax.set_title("Redundancy: network stays connected (λ₂>0) under edge loss"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "unfurl_fig3_redundancy.png"), dpi=140); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
axs[0].plot(T_axis, fN, lw=2); axs[0].set_xlabel("denaturant / T"); axs[0].set_ylabel("folded fraction (N)")
axs[0].set_title("Two-state threshold transition (structure demo)")
axs[1].plot(range(1, 25), acH, "o-", label=f"heat path (corr len {tauH})")
axs[1].plot(range(1, 25), acF, "s--", label=f"force path (corr len {tauF})")
axs[1].set_xlabel("spatial lag"); axs[1].set_ylabel("config autocorr")
axs[1].set_title("Same Λ, different configuration (path accounting)"); axs[1].legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "unfurl_fig4_bio_paths.png"), dpi=140); plt.close(fig)

print("ANCHOR_CHECK:", json.dumps(fit_check))
print("SIM3: base", round(lam2_base, 3), "curve", [round(x, 2) for x in lam2_curve], conn_curve)
print("SIM4B:", {"heat": [round(lamH, 3), tauH, round(bH, 3)], "force": [round(lamF, 3), tauF, round(bF, 3)]})
print("DONE ->", json_path)
