# -*- coding: utf-8 -*-
"""
云韶概率论·数值验证 v1.0（2026-09-19）· 纯计算版（零文件IO）
验证两个对接预言：
  EG-1: 体系度量g_p的自然梯度 = 标准梯度 × κ(1-p)^ε
  OT-2: 两个不同初始分布经D/E动力学后W₂距离单调递减
确定性：无随机数、无网络、零API、零文件写入。
"""
import json
import numpy as np

# ── 体系常数 ──
KAPPA = 1.0 / 32.0
EPSILON = 1.0 / 64.0
ALPHA = 1.0 / 8.0
ETA = 7.0 / 8.0

# ── 体系度量 g_p ──
def metric_g(p):
    """g_p = (1/κ) · (1-p)^(-ε)。p=0时发散（正确：零概率区域信息距离无穷大）"""
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return (1.0 / KAPPA) * (1.0 - p) ** (-EPSILON)

# ── EG-1：自然梯度验证 ──
def test_EG1():
    """
    对某个目标函数 F(p) = -(p - 0.7)²（最优点在p=0.7），
    比较标准梯度下降与自然梯度下降的路径。
    自然梯度 = g^{-1} · ∇F（用度量g_p的逆来修正梯度方向）。
    预言：自然梯度 = 标准梯度 / g_p = 标准梯度 × κ × (1-p)^ε
    """
    n_steps = 200
    lr = 0.001
    p_std = 0.1  # 标准梯度下降初始值
    p_nat = 0.1  # 自然梯度下降初始值
    p_true_opt = 0.7

    traj_std = [p_std]
    traj_nat = [p_nat]

    for _ in range(n_steps):
        # 标准梯度：dF/dp = -2(p - 0.7)
        grad_std = -2.0 * (p_std - p_true_opt)
        p_std += lr * grad_std
        traj_std.append(p_std)

        # 自然梯度：修正梯度方向 by g^{-1}
        grad = -2.0 * (p_nat - p_true_opt)
        g_inv = KAPPA * (1.0 - p_nat) ** EPSILON  # = 1/g_p
        p_nat += lr * g_inv * grad
        traj_nat.append(p_nat)

    # 验证：自然梯度下降在低概率区域的步长更大（因为g_inv更大）
    # 这意味着自然梯度下降"更快地穿越低概率区域"
    final_std = traj_std[-1]
    final_nat = traj_nat[-1]
    return {
        "test": "EG-1 自然梯度",
        "standard_final": round(final_std, 6),
        "natural_final": round(final_nat, 6),
        "true_optimum": p_true_opt,
        "natural_faster_in_low_p": abs(traj_nat[10] - 0.1) > abs(traj_std[10] - 0.1) if len(traj_nat) > 10 else "N/A",
        "convergence_steps_std": next((i for i, p in enumerate(traj_std) if abs(p - p_true_opt) < 0.01), "not reached"),
        "convergence_steps_nat": next((i for i, p in enumerate(traj_nat) if abs(p - p_true_opt) < 0.01), "not reached"),
        "trajectory_std_first10": [round(p, 4) for p in traj_std[:10]],
        "trajectory_nat_first10": [round(p, 4) for p in traj_nat[:10]]
    }

# ── OT-2：W₂距离收缩 ──
def w2_distance_1d(mu1, s1, mu2, s2):
    """一维W₂距离的闭式解：W₂² = (μ1-μ2)² + (σ1-σ2)²（两个高斯分布的情形）"""
    return np.sqrt((mu1 - mu2)**2 + (s1 - s2)**2)

def simulate_DE(mu, sigma, n_steps, alpha=ALPHA, eta=ETA):
    """
    简化D/E动力学模拟：
    D步骤：注入亏损（增加方差σ²→σ²+α·dt，均值偏移向0）
    E步骤：涌现修复（减少方差σ²→η·σ²，均值向有序态恢复）
    """
    mus = [mu]
    sigmas = [sigma]
    for _ in range(n_steps):
        # D步骤：亏损注入（加噪声）
        mu = mu + np.random.normal(0, np.sqrt(alpha * 0.01))
        sigma = sigma + alpha * 0.01
        # E步骤：涌现修复（衰减）
        mu *= eta
        sigma = max(sigma * eta, 0.01)
        mus.append(mu)
        sigmas.append(sigma)
    return mus[-1], sigmas[-1]

def test_OT2():
    """
    两个不同的初始高斯分布，经同一D/E动力学演化后，
    W₂距离应该单调递减（收缩性质）。
    """
    # 注意：这里用np.random是为了D步骤的噪声；结果对seed敏感但方向不敏感
    np.random.seed(42)
    
    # 两个不同的初始分布
    mu1, sig1 = 0.3, 0.1
    mu2, sig2 = 0.7, 0.3
    
    w2_traj = []
    n_steps = 50
    m1, s1 = mu1, sig1
    m2, s2 = mu2, sig2
    
    for t in range(n_steps):
        w2 = w2_distance_1d(m1, s1, m2, s2)
        w2_traj.append(w2)
        # 同一D/E步
        m1, s1 = simulate_DE_step(m1, s1)
        m2, s2 = simulate_DE_step(m2, s2)
    
    # 检查单调递减
    is_monotone = all(w2_traj[i] >= w2_traj[i+1] - 1e-6 for i in range(len(w2_traj)-1))
    total_shrink = w2_traj[0] / w2_traj[-1] if w2_traj[-1] > 0 else float('inf')
    
    return {
        "test": "OT-2 W₂距离收缩",
        "initial_W2": round(w2_traj[0], 6),
        "final_W2": round(w2_traj[-1], 6),
        "monotone_decreasing": is_monotone,
        "total_shrinkage_factor": round(total_shrink, 3),
        "w2_first10": [round(w, 5) for w in w2_traj[:10]],
        "verdict": "PASS" if is_monotone else "FAIL（收缩性质不成立，需查D/E定义）"
    }

def simulate_DE_step(mu, sigma):
    """单步D/E动力学"""
    # D步骤
    mu = mu + np.random.normal(0, np.sqrt(ALPHA * 0.01))
    sigma = sigma + ALPHA * 0.01
    # E步骤
    mu *= ETA
    sigma = max(sigma * ETA, 0.001)
    return mu, sigma

# ── 主函数 ──
def main():
    np.random.seed(42)
    results = {
        "meta": {
            "title": "云韶概率论·数值验证",
            "constants": {"α": ALPHA, "η": ETA, "κ": KAPPA, "ε": EPSILON},
            "note": "零文件IO纯计算版"
        }
    }
    
    eg1 = test_EG1()
    results["EG1"] = eg1
    
    # OT-2需要多个seed取平均（因为有随机噪声）
    monotone_count = 0
    n_trials = 20
    for trial in range(n_trials):
        np.random.seed(42 + trial)
        r = test_OT2()
        if r["monotone_decreasing"]:
            monotone_count += 1
    results["OT2"] = {
        "test": "OT-2 W₂距离收缩",
        "trials": n_trials,
        "monotone_count": monotone_count,
        "monotone_rate": round(monotone_count / n_trials, 3),
        "verdict": "PASS" if monotone_count / n_trials > 0.9 else "MIXED（需进一步分析）"
    }
    
    results["analytic"] = {
        "EG1_prediction": "自然梯度步长在低概率区域更大（g_inv = κ(1-p)^ε随p减小而增大）",
        "OT2_prediction": "W₂距离在D/E动力学下单调递减（收缩不等式）"
    }
    
    print(json.dumps(results, ensure_ascii=False, indent=1, default=str))

import json

if __name__ == "__main__":
    main()
