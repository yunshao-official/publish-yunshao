# -*- coding: utf-8 -*-
"""
阿赖耶审判机关 · 恢复门计算器 v1.0（硅基验证端第一件实体工具）
═══════════════════════════════════════════════
正本依据：《阿赖耶审判机关·文明重新回档机制·理论框架v1.0》恢复门主判据
  t_min = ⌈ (log κ − log T₀) / log η ⌉ > T_max  →  真不可逆
常数（constants.yaml v1.0）：κ = 1/32（新口径；旧口径 1/24 并存待轨道②）；η = 7/8
输入：T₀（危机后无序度，可由 Λ 有序度推算：T₀ ≈ (1−Λ_now)/1 × 归一基准）
输出：恢复步数 t_min ＋ 判定（可恢复 / 真不可逆，对表 T_max）
标签：体系内部定义·未验证（公式在档，T₀ 的 Λ 推算为候选口径）
"""
import math

KAPPA_NEW = 1 / 32   # 新常数口径 κ=1/32
KAPPA_OLD = 1 / 24   # 旧口径 κ=1/24（并存待轨道②）
ETA = 7 / 8          # 传递保留率

def t_min_steps(T0, kappa=KAPPA_NEW, eta=ETA):
    """恢复步数：t_min = ⌈(logκ − logT₀)/logη⌉"""
    if T0 <= 0:
        raise ValueError("T₀ 必须大于 0")
    return math.ceil((math.log(kappa) - math.log(T0)) / math.log(eta))

def verdict(t_min, T_max):
    """对表 T_max：≤ 为可恢复（记录归档），> 为真不可逆级信号（进入回档决策）"""
    return "可恢复（记录归档）" if t_min <= T_max else "真不可逆级信号（进入回档决策）"

def from_lambda(lambda_now, H_max=1.0):
    """候选口径：由 Λ 有序度推 T₀（Λ=1−T₀/H_max 归一 → T₀=H_max×(1−Λ)）【待实验锚定】"""
    return H_max * (1.0 - lambda_now)

if __name__ == "__main__":
    print("═══ 阿赖耶恢复门计算器 v1.0 ═══")
    print("常数：κ=1/32（新）/1/24（旧）｜η=7/8｜公式：t_min=⌈(logκ−logT₀)/logη⌉")
    print()
    demo = [
        ("示例A：轻度危机  Λ_now=0.875（有序相下缘）", from_lambda(0.875)),
        ("示例B：中度危机  Λ_now=0.5（亚有序/混沌分界）", from_lambda(0.5)),
        ("示例C：重度危机  Λ_now=0.125（临界崩塌边缘）", from_lambda(0.125)),
    ]
    for label, T0 in demo:
        t_new = t_min_steps(T0)
        t_old = t_min_steps(T0, KAPPA_OLD)
        print("%s" % label)
        print("  T₀=%.3f → t_min=%d 步（新κ）｜%d 步（旧κ）" % (T0, t_new, t_old))
        print("  对表：T_max=30 → %s｜T_max=20 → %s" % (verdict(t_new, 30), verdict(t_new, 20)))
        print()
    print("使用法：import 后调 t_min_steps(T0) / verdict(t_min, T_max)；")
    print("T₀ 优先用 Λ 实测推算（from_lambda），五路实测值直接代入。")
