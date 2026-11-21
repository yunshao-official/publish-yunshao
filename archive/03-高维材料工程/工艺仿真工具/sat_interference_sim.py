# -*- coding: utf-8 -*-
"""
W-SAT-1 · 干涉场 3-SAT 求解预注册实验（天工开物 第四批 · 盘点#5 多维互干涉计算机）
=====================================================================================
[判据冻结] 以下判据与参数在任一实验运行前冻结，运行后不得修改：
  - 实例：n=6 变量、m=24 子句（密度 α=4.0）、N=40 个可满足实例（拒绝采样）。
  - 装置模型（线性相干光学口径）：赋值 a∈{0,1}^6 → 平面波通道，波矢取 8×8 栅格；
    每子句一个振幅掩模：满足该子句 → 透射 1，违反 → r_amp；
    通道振幅 w_a = Π_c T_c(a)（振幅乘积编码）。
    探测面 E(x,y)=Σ_a w_a·exp(2πi(f_ax·x+f_ay·y))，I=|E|²，
    有限孔径 L 傅里叶读出每通道功率 P_a=|<E·e^{-2πi f_a·u}>|²。
  - 孔径：L ∈ {16, 256} 个条纹周期（16=相邻通道不可分辨，256=可分辨）。
  - 判正（PASS）：实例级 top-1 命中率 ≥ 80% 且 P_top1/P_2nd 中位数 ≥ 2.0。
  - 判负（FAIL）：命中率 ≤ 随机基线（平均解密度）的 95% Clopper-Pearson 置信上限。
  - 其间：INDETERMINATE。
  - 双臂：G 臂 r_amp=0.5（宽容消光）／R 臂 r_amp=0.9（现实消光）。
诚实口径：只模拟线性相干光学（单一无反馈通道）。逻辑 AND/OR 在线性光学中不可
实现，本实验检验"干涉并行探索"作为求解机制的声称。通道数=2^n，硬件规模指数
增长照记。非线性反馈光学若为体系文档本意，另行注册，不在本件范围。
"""
import itertools
import json
import numpy as np
from scipy.stats import beta

# ---------- 冻结参数 ----------
N_VAR, N_CLAUSE, N_INST = 6, 24, 40
R_AMP_ARMS = {"G": 0.5, "R": 0.9}
APERTURES = [16, 256]
N_GRID = 512
PASS_HITRATE = 0.80
PASS_MARGIN = 2.0
SEED = 42

def random_3sat(rng, n, m):
    clauses = []
    for _ in range(m):
        vs = rng.choice(n, size=3, replace=False)
        cls = tuple((int(v), int(rng.random() < 0.5)) for v in vs)
        clauses.append(cls)
    return clauses

def sat_assignments(clauses, n):
    sols = []
    for a in itertools.product([0, 1], repeat=n):
        if all(any(a[v] == p for v, p in cls) for cls in clauses):
            sols.append(a)
    return sols

def channel_weights(clauses, r_amp):
    """w_a = Π_c T_c(a)：满足子句透射 1，违反透射 r_amp（振幅）。索引 a=0..63。"""
    w = np.ones(64)
    for a, asg in enumerate(itertools.product([0, 1], repeat=N_VAR)):
        for cls in clauses:
            if not any(asg[v] == p for v, p in cls):
                w[a] *= r_amp
    return w

def clopper_pearson_upper(k, n, conf=0.95):
    if k >= n:
        return 1.0
    return float(beta.ppf(conf, k + 1, n - k))

class InterferenceStage:
    """8×8 平面波通道的探测面场与傅里叶读出（可分离实现）。"""

    def __init__(self, n_grid, aperture_L):
        self.n = n_grid
        self.L = aperture_L
        g = np.arange(8) - 3.5
        self.fx = g / 64.0   # 通道频率：最小间隔 1/64 /周期
        xs = np.arange(n_grid) / n_grid * self.L
        self.xs = xs
        self.EX = np.exp(2j * np.pi * np.outer(self.fx, xs))      # (8,n)
        self.EY = np.exp(2j * np.pi * np.outer(self.fx, xs))      # 同栅格
        self.EXc = np.conj(self.EX)                                # 读出共轭

    def field(self, W):
        """W: 8×8 通道振幅。返回 E(x,y) (n,n)。"""
        return (self.EX.T @ W) @ self.EY                            # (n,8)@(8,8)@(8,n)

    def readout(self, E):
        """P_a=|<E e^{-2πi f_a·u}>|²，返回 64 通道功率（a = iy*8+ix）。"""
        G = self.EXc @ E @ self.EY.T.conj()                         # (8,8) 复读出
        return np.abs(G.reshape(-1))**2

def main():
    rng = np.random.default_rng(SEED)
    stages = {(arm, L): InterferenceStage(N_GRID, L) for arm in R_AMP_ARMS for L in APERTURES}
    insts = []
    while len(insts) < N_INST:
        cls = random_3sat(rng, N_VAR, N_CLAUSE)
        sols = sat_assignments(cls, N_VAR)
        if sols:
            insts.append((cls, sols))

    results = {}
    for arm, r_amp in R_AMP_ARMS.items():
        for L in APERTURES:
            stage = stages[(arm, L)]
            hits = 0
            margins, ratio_list, sol_frac_all = [], [], []
            for cls, sols in insts:
                w = channel_weights(cls, r_amp)
                W = w.reshape(8, 8)
                E = stage.field(W)
                Pch = stage.readout(E)
                sol_idx = [a for a, asg in enumerate(itertools.product([0, 1], repeat=N_VAR))
                           if asg in set(map(tuple, sols))]
                order = np.argsort(Pch)[::-1]
                hits += int(order[0] in sol_idx)
                p1, p2 = Pch[order[0]], Pch[order[1]]
                margins.append(p1 / p2 if p2 > 0 else np.inf)
                nonsol = [i for i in range(64) if i not in sol_idx]
                ratio_list.append(float(np.median(Pch[sol_idx]) /
                                        max(np.median(Pch[nonsol]), 1e-300)))
                sol_frac_all.append(len(sol_idx) / 64.0)
            base = float(np.mean(sol_frac_all))
            cp95 = clopper_pearson_upper(int(round(base * N_INST)), N_INST)
            hr, med_margin = hits / N_INST, float(np.median(margins))
            if hr >= PASS_HITRATE and med_margin >= PASS_MARGIN:
                verdict = "PASS"
            elif hr <= cp95:
                verdict = "FAIL"
            else:
                verdict = "INDETERMINATE"
            results[f"{arm}_r{r_amp}_L{L}"] = {
                "hit_rate_top1": hr, "hits": hits, "N": N_INST,
                "median_P1_over_P2": med_margin,
                "median_sol_vs_nonsol_power_ratio": float(np.median(ratio_list)),
                "random_baseline_mean_solution_fraction": base,
                "cp95_upper_of_baseline": cp95,
                "verdict": verdict,
            }
    return {
        "experiment": "W-SAT-1 干涉场3-SAT预注册（盘点#5）",
        "frozen": {"n": N_VAR, "m": N_CLAUSE, "N_inst": N_INST,
                   "pass_rule": f"hit>={PASS_HITRATE} 且 P1/P2中位数>={PASS_MARGIN}",
                   "fail_rule": "hit<=CP95(基线)", "seed": SEED,
                   "grid": N_GRID},
        "arms": results,
        "honest_note": ("线性相干光学单通道无反馈；通道数=2^n（n=6→64；n=50→1.1e15）。"
                        "任何命中都来自掩模内已完成的逐子句乘积评估（硬件穷举），"
                        "不构成计算复杂度降低；消光比与孔径分辨是物理瓶颈。"),
    }

if __name__ == "__main__":
    out = main()
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/wsat1_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for k, v in out["arms"].items():
        print(f"{k:14s} hit={v['hit_rate_top1']:.3f} P1/P2={v['median_P1_over_P2']:.4g} "
              f"sol/nonsol={v['median_sol_vs_nonsol_power_ratio']:.4g} -> {v['verdict']}")
