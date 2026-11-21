# -*- coding: utf-8 -*-
"""第二步演示v2：D维网格全覆盖 —— 逐维独立全扫(玩具) vs 全局顺序(哈密顿)
逐维独立全扫：每个自由度独立做全行程往返扫描（从零开始，每条线去+回），
总步数随维度累积 -> 浪费随 D 线性爆炸
全局顺序：D维 snake 构造哈密顿路径，每步相邻，N-1 步
"""
import json, math

def toy_perdim(n, D):
    """玩具：每维独立全扫。每条线 = 沿该维从0到n-1再回来（去+回=2(n-1)步）"""
    lines_per_dim = n ** (D - 1)          # 每维有 n^(D-1) 条线
    per_line = 2 * (n - 1)                # 去+回
    steps = D * lines_per_dim * per_line  # D 个维度累积
    # 转折：每条线两端各一次大转向（到端+返回起点）
    turns = D * lines_per_dim * 2
    return steps, turns

def global_snake(n, D):
    """全局顺序：D维 snake（灰码式折叠）构造哈密顿路径，每步相邻"""
    seq = [(i,) for i in range(n)]  # 初始：一维整条线 n 个点
    for _ in range(D - 1):
        new_seq = []
        for t in range(n):
            if t % 2 == 0:
                new_seq += [pt + (t,) for pt in seq]
            else:
                new_seq += [pt + (t,) for pt in reversed(seq)]
        seq = new_seq
    # 断言：每步曼哈顿距离 = 1（真哈密顿路径）
    steps = 0
    dirs = []
    for i in range(1, len(seq)):
        d = sum(abs(x - y) for x, y in zip(seq[i-1], seq[i]))
        assert d == 1, f"not adjacent at {i}: {seq[i-1]}->{seq[i]} d={d}"
        steps += d
        dirs.append(tuple(b - a for a, b in zip(seq[i-1], seq[i])))
    turns = sum(1 for i in range(1, len(dirs)) if dirs[i] != dirs[i-1])
    return steps, turns

n = 5
rows = []
print(f"{'D':>2} {'N':>7} | {'逐维独立全扫':>14} | {'全局顺序(哈密顿)':>16} | 浪费倍数")
print("-" * 72)
for D in range(2, 7):
    N = n ** D
    toy_steps, toy_turns = toy_perdim(n, D)
    ham_steps, ham_turns = global_snake(n, D)
    waste = toy_steps / ham_steps
    rows.append({
        "D": D, "N": N,
        "toy_steps": toy_steps, "toy_turns": toy_turns,
        "ham_steps": ham_steps, "ham_turns": ham_turns,
        "waste": round(waste, 2),
        "waste_linear": round(2 * D * (n - 1) / n, 2),  # 理论 2D(n-1)/n (n=5 -> 1.6D)
    })
    print(f"{D:>2} {N:>7} | {toy_steps:>9}步/{toy_turns:>7}转折 | {ham_steps:>11}步/{ham_turns:>6}转折 | {waste:>4.1f}x (理论1.6D={2*D*(n-1)/n:.2f})")

# 模型检验：浪费倍数是否命中 2D(n-1)/n？
print("\n=== 模型检验：浪费倍数 vs 2D(n-1)/n ===")
for r in rows:
    hit = "命中" if abs(r["waste"] - r["waste_linear"]) < 0.15 else "偏离"
    print(f"D={r['D']}: 实测{r['waste']:.2f}x vs 理论1.6D={r['waste_linear']:.2f} -> {hit}")

with open(r"D:\data\scratch\grid_coverage_result.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("saved json")

# 画图
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    Ds = [r["D"] for r in rows]
    wastes = [r["waste"] for r in rows]
    plt.figure(figsize=(7, 5))
    plt.plot(Ds, wastes, "o-", label="实测浪费倍数")
    plt.plot(Ds, [2 * d * (n - 1) / n for d in Ds], "--", label="理论 2D(n-1)/n")
    plt.xlabel("维度 D"); plt.ylabel("路径浪费倍数")
    plt.title("逐维独立全扫 vs 全局哈密顿：浪费随维度线性爆炸")
    plt.legend(); plt.grid(alpha=0.3)
    plt.savefig(r"D:\data\scratch\grid_coverage.png", dpi=110, bbox_inches="tight")
    print("saved png")
except Exception as e:
    print("png fail:", e)