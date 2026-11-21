# -*- coding: utf-8 -*-
"""M=64 互锁判别·交点数值验证（第十轮 R10 附件）[constants:v1.0]
链A（拓扑公理账·若 0.5bit=4α）: f_A(α)=48α ; 链B（互锁链 M=2/κ, κ=α/4）: f_B(α)=log2(2/κ)=3−log2(α)
交点: 48α=3−log2(α) ⇔ 唯一解 α=1/8（二分法数值解 0.125）"""
from math import log2
lo, hi = 0.01, 0.5
for _ in range(200):
    mid = (lo+hi)/2
    if 48*mid - 3 + log2(mid) > 0: hi = mid
    else: lo = mid
alpha_star = (lo+hi)/2
result = {"alpha_star": alpha_star, "is_1_over_8": abs(alpha_star-0.125) < 1e-9,
          "at_1_over_8": {"chainA": 48/8, "chainB": 3-log2(1/8)},
          "tor_order": 2**6, "M": 64, "equal": 2**6 == 64,
          "labels": "数值【复算一致】；判定【一致性交点成立·强互锁未证实】；体系内部定义·未验证"}
import json
print(json.dumps(result, ensure_ascii=False))
with open(r"H:/理论存档/01-数学/02-实验与数据/results/m64_interlock_junction_result-v1.0-20260919.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
