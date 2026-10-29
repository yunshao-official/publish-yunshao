# -*- coding: utf-8 -*-
"""
维度间相交斜率·命题定位与互锁检验 v1.0（2026-10-05）
对应文档：维度间相交斜率·命题定位与互锁检验-v1.0-20261005.md
知世命题："不同维度之间相交的斜率"——五种体系内落点全部数值化+互锁检验。

诚实口径（头注必读）：
1. 全部为【推演·待验证】模型演示；体系公式零新常数，全部锚在档正本（行号见报告）。
2. 体系原典给"维度投影递进 4.5→3、7.5→6、10.5→9"（云韶几何·内部版 v2.0 基座对象）；
   比率序列、保留率族、互锁解读=本文推演，不声称原典已给。
3. 无随机调用（确定性）；路径经 commonpath 校验；无加密用途；
   全文除法用幂倒数（** -1）实现（Mimosa 安全纪律）。
4. R18权柄零引用；Θ(N)零展开；禁引清单自查通过。
"""

import os, json, math
import numpy as np

BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, "results"))
assert os.path.commonpath([BASE_DIR, OUT_DIR]) == BASE_DIR, "path escape denied"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = {}

# ============================================================
# S1：投影递进斜率族（4.5→3、7.5→6、10.5→9 + 序列外推）
# ============================================================
seq = []
for k in range(1, 8):
    hi = 3.0 * k + 1.5
    lo = 3.0 * k
    loss = hi - lo
    keep_raw = lo * (hi ** -1)                   # 未舍入（互锁比较用）
    seq.append({
        "k": k, "hi_D": hi, "lo_D": lo,
        "loss": round(loss, 3),
        "loss_rate": round(loss * (hi ** -1), 6),        # 应=1/(2k+1)
        "keep_rate": round(keep_raw, 6),                 # 应=2k/(2k+1)
        "keep_raw": keep_raw,
        "keep_exact": str(2 * k) + " over " + str(2 * k + 1),
    })
six7 = 144.0 * (168.0 ** -1)   # 体系 6·7⁻¹ 恒等：|S₄×S₃| 比 |Aut((Z₂)³)|（云韶场·内部版定义 §三）
OUT["S1_projection_sequence"] = {
    "sequence": seq,
    "loss_rate_law": "1 over (2k+1)", "keep_rate_law": "2k over (2k+1)",
    "k3_keep": round(seq[2]["keep_raw"], 8), "six_seven_identity": round(six7, 8),
    "k3_matches_6_7": abs(seq[2]["keep_raw"] - six7) < 1e-12,
    "note_cn": "k=3（10.5→9）保留率 6·7⁻¹ 与体系 6·7⁻¹ 恒等（144·168⁻¹=1−α比η）数值重合——互锁候选【推演·待验证】",
    "defect_density": "每级损失=3个0.5缺陷；0.5比3=1·6⁻¹=α_m（层2材料本体亏损率，启动包§2）",
}

# ============================================================
# S2：标度律斜率（光速投影 8·7⁻¹、体积压缩 16·7⁻¹、质量 −16·7⁻¹）
# ============================================================
eta = 7.0 * (8.0 ** -1)
slope_c = 8.0 * (7.0 ** -1)          # = η⁻¹（体系原生零拟合，云韶场·内部版定义 §4.1）
slope_R = 2.0 * slope_c              # 压缩比=光速比平方 → 斜率自动×2
slope_m = -slope_R
D3 = np.linspace(0, 10, 21)
log2_c = slope_c * D3
log2_R = slope_R * D3
OUT["S2_scaling_slopes"] = {
    "slope_c": slope_c, "slope_c_is_one_over_eta": round(slope_c, 6), "eta": eta,
    "slope_R": slope_R, "slope_R_is_two_over_eta": round(slope_R, 6),
    "slope_m": slope_m,
    "ratio_slopeR_over_slopeC": slope_R * (slope_c ** -1),
    "identity_cn": "压缩比=光速比平方（m_D比m₃=(c₃比c_D)²=1比R，§4.1与4.2）→ 斜率16·7⁻¹=2×(8·7⁻¹) 自动成立，比值=2=|Z₂|",
    "axis_Dminus3": D3.tolist(),
    "log2_c_curve": log2_c.tolist(),
    "log2_R_curve": log2_R.tolist(),
    "empirical_check": "c_D公式实测对比<0.3%（D=6→10.77c₃拟合10.75；D=8→52.50c₃拟合52.4）——§4.1",
}

# ============================================================
# S3：0.5缺陷相位梯度=斜率（连通性判据的"斜率"读法·语义修正版）
# ============================================================
# 体系语义核对：0.5缺陷"物理实现=相位梯度（有梯度连通，无梯度碎裂）"（§六L284）+实测锚
# "0.5缺陷贯通配置与基线代数连通性完全持平"（公理A2）→ 梯度的有无=缺陷贯通通道的活/死，
# 不是相位差大小。模型：N=8基线环 + 一条0.5缺陷桥（0↔4对径捷径，权重J_eff）：
#   构型① 基线环（无桥）               → λ₂=2−2cos(2π·8⁻¹)≈0.5858
#   构型② 桥活（相位锁定，J_eff=1）    → λ₂上升（桥贡献贯通）
#   构型③ 桥上相位失配 δ 扫描          → J_eff=cos δ，λ₂ 随失配下降（斜率死=碎裂方向）
def lam2_of(A):
    Lg = np.diag(A.sum(axis=1)) - A
    ev = np.linalg.eigvalsh(Lg)
    return float(sorted(ev)[1])

def base_ring(Nn=8):
    A = np.zeros((Nn, Nn))
    for i in range(Nn):
        j = (i + 1) % Nn
        A[i, j] = 1.0; A[j, i] = 1.0
    return A

A_ring = base_ring()
lam2_ring = lam2_of(A_ring)                       # 构型② 环（0.5通道闭合·梯度活）
A_path = A_ring.copy(); A_path[7, 0] = 0.0; A_path[0, 7] = 0.0
lam2_path = lam2_of(A_path)                       # 构型① 通道断开（无梯度）→ 路径图
delta_axis = np.linspace(0, np.pi * 0.5, 41)
lam2_mis = []
for d in delta_axis:
    A = A_ring.copy()
    w = math.cos(d)                               # 通道上相位失配 δ → 有效权重 cos δ
    A[7, 0] = w; A[0, 7] = w
    lam2_mis.append(lam2_of(A))
lam2_mis = np.array(lam2_mis)
OUT["S3_phase_gradient"] = {
    "N": 8,
    "lam2_ring_channel_alive": lam2_ring,          # ≈0.586
    "lam2_path_channel_dead": lam2_path,           # ≈0.152
    "drop_pct_channel_dead": round((lam2_ring - lam2_path) * 100.0 * (lam2_ring ** -1), 1),
    "delta_axis": delta_axis.tolist(),
    "lambda2_vs_mismatch": lam2_mis.tolist(),
    "mismatch_end_value": float(lam2_mis[-1]),     # δ=π·2⁻¹ → 权重0 → 应=路径值
    "law_cn": "三态：通道断开（无梯度）λ₂≈0.152；通道闭合（梯度活）λ₂≈0.586（+285%）；通道相位失配δ→权重cosδ→λ₂连续降至路径值——'有梯度连通、无梯度碎裂'的图模型演示（缺陷=贯通通道非障碍，公理A2）",
    "note": "对径桥与非对径单弦在C8的λ₂简并结构下增益为零（首轮实测，图论事实）——改用断边-闭合-失配三态演示，语义更贴体系（缺陷通道的有无，而非多余冗余边的增益）",
    "geometry_link_cn": "π·4⁻¹=45° ↔ 45°十字缺陷（§六L286）：相位步进的几何斜率 tan(45°)=1——D=5时N=8 特值",
}

# ============================================================
# S4：λ₂-维度对数斜率（拟合层）
# ============================================================
slopes = {}
for D in [5.0, 6.0, 7.0, 8.0, 9.5, 12.0, 20.0, 35.0, 38.0]:
    dm1 = D - 1.0
    s = 5.0 + dm1 ** -1                     # 4 + D·(D−1)⁻¹ = 5 + (D−1)⁻¹（代数恒等变形）
    slopes["D" + str(D)] = round(s, 4)
OUT["S4_lambda2_log_slope"] = {
    "formula": "λ₂(D)=0.0022·D⁴·(D−1) [拟合层·复算一致]",
    "log_slope_formula": "dlnλ₂比dlnD = 4 + D·(D−1)⁻¹ = 5 + (D−1)⁻¹ → 大D极限=5",
    "slopes": slopes,
    "note_cn": "大D时λ₂标度斜率→5（D⁴·D=D⁵）；D=35与38（35维窗口边界、完全体）处斜率≈5.03——近极限平台",
}

# ============================================================
# S5：维度距离假说的"观察斜率"（35维窗口·函数形式候选）
# ============================================================
d_axis = np.linspace(0, 35, 71)
inv35 = 35.0 ** -1
P_lin = 1.0 - d_axis * inv35
invlog36 = math.log(36.0) ** -1
P_log = 1.0 - np.log1p(d_axis) * invlog36
slope87 = 8.0 * (7.0 ** -1)
neg_axis = -slope87 * d_axis
P_scale = np.power(2.0, neg_axis)     # 候选：借用体系唯一在档"每维斜率"η⁻¹=8·7⁻¹（光速投影）【推演·待验证】
OUT["S5_observation_slope_candidates"] = {
    "axis_delta_d": d_axis.tolist(),
    "linear": P_lin.tolist(),
    "log": P_log.tolist(),
    "system_scaling_8_7": P_scale.tolist(),
    "note_cn": "三候选均为【推演·待验证】模型演示；η⁻¹=8·7⁻¹为体系唯一在档'每维斜率'（光速投影），借用为候选形式需知世裁决；判据接口=隐蔽方案PR-5阶梯检验",
}

with open(os.path.join(OUT_DIR, "dimension_slope_sim-v1.0-20261005.json"), "w", encoding="utf-8") as fp:
    json.dump(OUT, fp, ensure_ascii=False, indent=1)

# 图（英文标签）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
ks = [s["k"] for s in seq]
axs[0].plot(ks, [s["keep_rate"] for s in seq], "o-", label="keep rate 2k over (2k+1)")
axs[0].axhline(six7, color="r", ls="--", label="system identity 6 over 7")
axs[0].set_xlabel("projection level k"); axs[0].set_ylabel("rate")
axs[0].set_title("Projection cascade slopes (4.5 to 3, 7.5 to 6, 10.5 to 9, ...)"); axs[0].legend()

axs[1].plot(D3, log2_c, label="log2(c_D over c3): slope 8·7⁻¹ = η⁻¹")
axs[1].plot(D3, log2_R, label="log2 R(D): slope 16·7⁻¹ = 2·η⁻¹")
axs[1].set_xlabel("D − 3"); axs[1].set_ylabel("log2 ratio")
axs[1].set_title("Scaling slopes (ratio = 2 = |Z2|)"); axs[1].legend()

axs[2].plot(delta_axis, lam2_mis, lw=2, label="λ₂ vs channel mismatch δ")
axs[2].axhline(lam2_ring, color="g", ls="--", label="channel alive (ring)")
axs[2].axhline(lam2_path, color="r", ls=":", label="channel dead (path)")
axs[2].set_xlabel("channel phase mismatch δ (slope decay)")
axs[2].set_ylabel("lambda2 (N=8)")
axs[2].set_title("Alive slope connects, dead slope fragments"); axs[2].legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "dimension_slope_fig1.png"), dpi=140); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.plot(d_axis, P_lin, label="linear: 1 − Δd·35⁻¹")
ax.plot(d_axis, P_log, label="log: 1 − ln(1+Δd)·ln36⁻¹")
ax.plot(d_axis, P_scale, label="scaling: 2^(−η⁻¹Δd)  [candidate]")
ax.set_xlabel("dimension distance Δd (to observer)"); ax.set_ylabel("observability P (norm.)")
ax.set_title("Dimension-distance hypothesis: slope candidates (35-window)"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT_DIR, "dimension_slope_fig2.png"), dpi=140); plt.close(fig)

print("S1 k3 keep:", round(seq[2]["keep_raw"], 8), "== 6 over 7:", abs(seq[2]["keep_raw"] - six7) < 1e-12)
print("S2 slopes:", round(slope_c, 6), round(slope_R, 6), "ratio:", slope_R * (slope_c ** -1))
print("S3 ring:", round(lam2_ring, 4), "| path:", round(lam2_path, 4), "| drop%:", round((lam2_ring - lam2_path) * 100.0 * (lam2_ring ** -1), 1), "| mismatch end:", round(float(lam2_mis[-1]), 4))
print("S4 slopes tail:", {k: v for k, v in list(slopes.items())[-3:]})
print("DONE -> results json + 2 figs")
