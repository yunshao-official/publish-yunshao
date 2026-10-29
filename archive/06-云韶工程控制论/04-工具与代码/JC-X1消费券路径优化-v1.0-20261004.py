# -*- coding: utf-8 -*-
"""JC-X1 消费券发放路径优化·首跑（判据书 v1.0 预注册后执行）
模型：列昂惕夫投入产出传导（8行业）+ 边际乘数贪心分配 vs 均匀基线
判据：C-X1a 机制成立 / C-X1b 量级记录 / C-X1c 蒙特卡洛稳健性
"""
import io, json
import numpy as np

N = 8
SECTORS = ["餐饮食品", "文旅娱乐", "日用零售", "服装", "家居家电", "教育医疗", "交通通信", "其他服务"]
BUDGET = 100.0
SAVE = 0.30

base_A = np.array([
    [0.30, 0.10, 0.15, 0.05, 0.02, 0.06, 0.08, 0.06],
    [0.06, 0.28, 0.04, 0.03, 0.01, 0.04, 0.10, 0.05],
    [0.10, 0.05, 0.22, 0.06, 0.04, 0.05, 0.05, 0.06],
    [0.02, 0.03, 0.08, 0.18, 0.01, 0.02, 0.02, 0.03],
    [0.01, 0.01, 0.05, 0.02, 0.15, 0.02, 0.02, 0.03],
    [0.03, 0.03, 0.04, 0.02, 0.01, 0.20, 0.04, 0.04],
    [0.06, 0.08, 0.05, 0.03, 0.02, 0.04, 0.22, 0.06],
    [0.08, 0.07, 0.08, 0.05, 0.04, 0.06, 0.07, 0.24],
])
A_base = base_A * (1 - SAVE)
np.fill_diagonal(A_base, 0.0)
CAPS = np.array([0.30, 0.22, 0.16, 0.08, 0.06, 0.10, 0.12, 0.16]) * BUDGET * 4

def full_multiplier(A, inject_idx, rounds=25):
    x = np.zeros(N)
    x[inject_idx] += 1.0
    total = x.copy()
    cur = x.copy()
    for _ in range(rounds):
        cur = A.T @ cur
        total += cur
        if cur.sum() < 1e-10:
            break
    return total.sum()

# 1) 均匀基线
per = BUDGET / N
m_uniform = sum(full_multiplier(A_base, i) * per for i in range(N))

# 2) 贪心优化分配
mults = np.array([full_multiplier(A_base, i) for i in range(N)])
alloc = np.zeros(N)
remain = BUDGET
step = 0.01
while remain > 1e-9:
    best, bestm = -1, -1
    for i in range(N):
        if alloc[i] >= CAPS[i]:
            continue
        m = mults[i] * (1 - alloc[i] / CAPS[i])
        if m > bestm:
            bestm, best = m, i
    put = min(step, remain)
    alloc[best] += put
    remain -= put
m_opt = sum(full_multiplier(A_base, i) * alloc[i] for i in range(N) if alloc[i] > 0.005)
m_opt = sum(full_multiplier(A_base, np.where(alloc > 0.005)[0].tolist()) * 1.0 for _ in [1])  # 组合注入

# 更准确：组合注入的总乘数
idx_active = np.where(alloc > 0.005)[0].tolist()
x = np.zeros(N)
for i in idx_active:
    x[i] += alloc[i]
total = x.copy()
cur = x.copy()
for _ in range(25):
    cur = A_base.T @ cur
    total += cur
    if cur.sum() < 1e-10:
        break
m_opt = total.sum()

gain = (m_opt / m_uniform - 1) * 100
print("=== 均匀基线 ===")
print("总激活: {:.2f}（预算 {:.0f}）".format(m_uniform, BUDGET))
print("\n=== 优化分配 ===")
for i in np.argsort(-alloc):
    if alloc[i] > 0.005:
        print("  {:<10s} {:>7.2f} 亿元".format(SECTORS[i], alloc[i]))
print("总激活: {:.2f}".format(m_opt))

print("\n=== 判据开票 ===")
c1a = gain > 5
print("C-X1a: 增益 {:+.1f}%（>5%→成立）: {}".format(gain, "成立" if c1a else "不成立"))
print("C-X1b: 最优/均匀 = {:.3f}".format(m_opt / m_uniform))

# C-X1c 蒙特卡洛
rng = np.random.default_rng(20261004)
基准mults = np.array([full_multiplier(A_base, i) for i in range(N)])
基准top3 = set(np.argsort(-基准mults)[:3])
stable = 0
TRIALS = 300
for _ in range(TRIALS):
    A_p = A_base * (1 + rng.uniform(-0.2, 0.2, size=A_base.shape))
    np.fill_diagonal(A_p, 0.0)
    mp = np.array([full_multiplier(A_p, i) for i in range(N)])
    if set(np.argsort(-mp)[:3]) == 基准top3:
        stable += 1
rate = stable / TRIALS
print("C-X1c: top3排序稳健率 {:.0%}（≥80%→稳健）: {}".format(rate, "稳健" if rate >= 0.8 else "不稳健"))

out = r"H:/理论存档/06-云韶工程控制论/02-实验与数据/JC-X1-消费券路径优化-v1.0-20261004.json"
io.open(out, "w", encoding="utf-8").write(json.dumps({
    "uniform_multiplier": round(m_uniform, 3),
    "optimal_multiplier": round(m_opt, 3),
    "gain_pct": round(gain, 1),
    "C-X1a": "成立" if c1a else "不成立",
    "C-X1b_ratio": round(m_opt / m_uniform, 4),
    "C-X1c_stability": round(rate, 4),
    "top3_sectors": [SECTORS[i] for i in np.argsort(-基准mults)[:3]],
    "sectors": SECTORS,
    "alloc_opt": alloc.tolist(),
}, ensure_ascii=False, indent=1))
print("结果件：", out)
