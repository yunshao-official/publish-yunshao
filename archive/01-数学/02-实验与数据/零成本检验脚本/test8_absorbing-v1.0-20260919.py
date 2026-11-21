# -*- coding: utf-8 -*-
"""零成本判伪检验第一波·检验8（概率册 P5/P-E2 吸收链寿命）+ 检验9 对照组
显式假设构造（全部标注）：
  状态（活跃,浅,深）暂态 + 冻结=吸收态；每步以 α=1/8 下沉一层、η=7/8 留守；无回跃（η=0 纯吸收极限）。
  Q 列随机（与册内 D 列随机口径一致）：Q[i][j] = 从 j 转到 i 的概率
输出：N=(I-Q)^-1 暂态期望访问数、各暂态出发期望吸收时间 t；与 1/α=8 量级比对。
"""
import numpy as np

a = 1/8          # α=1/8 [constants:v1.0]
e = 1 - a        # η=7/8 留守
# 列随机 Q：列 j 是状态 j 的去向分布（j=0 活跃, 1 浅, 2 深）
Q = np.array([
    [e, 0, 0],   # 活跃->活跃, 浅->活跃(无回跃=0), 深->活跃(0)
    [a, e, 0],   # 活跃->浅=α, 浅->浅, 深->浅=0
    [0, a, e],   # 浅->深=α, 深->深
])               # 每列和 = e+a = 1 ✓ 列随机
# 规范形 P=[[Q,R],[0,I]]：活跃/浅列和=1（去向全在暂态块），深列和=η（剩 α=1/8 流向冻结吸收态，在 R 块）
col_sums = Q.sum(axis=0)
assert np.allclose(col_sums[:2], 1) and np.isclose(col_sums[2], e) and (col_sums <= 1).all(), "规范形列检查失败"
print(f"规范形检查：Q 列和 = {col_sums}（活跃/浅=1，深=η={e}，α=1/8 入吸收块 ✓）")

N = np.linalg.inv(np.eye(3) - Q)
t = N.sum(axis=0)   # 各暂态列出发的期望吸收时间
names = ["活跃", "浅", "深"]
print("N=(I-Q)^-1 =")
print(np.array_str(N, precision=4, suppress_small=True))
for n, tv in zip(names, t):
    print(f"  从[{n}]出发期望吸收时间 t = {tv:.6f} 步")
print(f"[裁决-检验8] t(活跃)={t[0]:.0f} 步 = 3×(1/α)=3×8；与 1/α=8 同量级（×层数因子 3）")

# 检验9 对照组：该稀疏 Q 下 D=(1-α)I+αQ 是否一步全正
D = (1-a)*np.eye(3) + a*Q
print(f"[检验9-对照] D 最小元 = {D.min():.6f}；零元个数 = {int((D==0).sum())} → {('全正' if D.min()>0 else '非全正（活跃→深=0）')}（册内 softmax Q 恒正则为全正，见报告正文）")
