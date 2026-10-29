# -*- coding: utf-8 -*-
"""
零成本判伪检验第一波·检验4（几何-G-E1 E6/A8 根系计数）+ 检验5（几何-G-E3 30/6 拆分穷举）
判据冻结：
  G-E1：E6 根数=72、正根=36；A8 正根=C(9,2)=36。判据：与 72/36/36 一致=计数层 T1 复算一致。
       顺带输出 E6 正根完整坐标表（供 G-E3）。
  G-E3：按自然候选规则穷举 E6 正根的 30/6 二分：存在任一自然候选给出恰 30/6 且
       6 个根构成 A2 或"2-重"结构 → G4 立案升 T2；全部候选无 → E6 走廊对 30+6 关闭（照记，不硬凑）。
方法：E6 取标准单根系（Cartan 整数阵，o-o-o 分支形 (2,1,2) 臂），在单根坐标格点内
  穷举范数平方=2 的格向量 = 全部根（根系内根的单根坐标系数有界）。零编数。
"""
import itertools
from collections import Counter

# E6 Cartan 矩阵（1-α4 为支点，臂 (2,1,2)：节点 4 连 3、2、5）
# 拓扑:  3-4-5-6 链，1-3，2-4  →  度3节点=4
IDX = {
    (1, 1): 2, (2, 2): 2, (3, 3): 2, (4, 4): 2, (5, 5): 2, (6, 6): 2,
    (3, 4): -1, (4, 3): -1, (4, 5): -1, (5, 4): -1, (5, 6): -1, (6, 5): -1,
    (1, 3): -1, (3, 1): -1, (2, 4): -1, (4, 2): -1,
}
C = [[IDX.get((i+1, j+1), 0) for j in range(6)] for i in range(6)]

# 形状自检：度序列
deg = [sum(1 for j in range(6) if C[i][j] != 0 and i != j) for i in range(6)]
assert sorted(deg) == [1, 1, 1, 2, 2, 3], f"E6 图形自检失败: {deg}"
print(f"[自检] E6 单根系 Dynkin 图度序列 = {sorted(deg)}（含唯一度3节点 ✓）")

def norm2(x):
    return sum(x[i]*C[i][j]*x[j] for i in range(6) for j in range(6))

roots = []
for x in itertools.product(range(-3, 4), repeat=6):
    if norm2(x) == 2:
        roots.append(x)
print(f"[自检] 范数²=2 的整向量数 = {len(roots)}（应为 72；系数界 ±3 覆盖 E6 最高根）")
assert len(roots) == 72

# 正根：单根坐标下第一个非零分量为正
pos = sorted(x for x in roots if next(v for v in x if v) > 0)
neg = sorted(x for x in roots if next(v for v in x if v) < 0)
assert len(pos) == 36 and len(neg) == 36
assert {tuple(-v for v in r) for r in pos} == set(neg)
print(f"[裁决-检验4] E6 根数 = {len(roots)}；正根数 = {len(pos)}；负根数 = {len(neg)}（36/36/72 ✓）")

# A8：根 e_i - e_j (i<j 正)
a8_pos = [(i, j) for i in range(9) for j in range(9) if i < j]
print(f"[裁决-检验4] A8 正根数 = C(9,2) = {len(a8_pos)}（应为 36）")
assert len(a8_pos) == 36

print("\n[E6 正根完整坐标表（单根坐标 α=Σx_i α_i，供 G-E3）]")
for h in sorted(range(1, 12), reverse=False):
    row = [x for x in pos if sum(x) == h]
    if row:
        print(f"  高度 {h:2d} ({len(row):2d}个): {row}")

heights = Counter(sum(x) for x in pos)
print(f"[中间值] 正根高度分布 = {dict(sorted(heights.items()))}，总数 {sum(heights.values())}")

def pair_mult(a, b):
    """⟨a,b⟩ = Σ a_i C_ij b_j（单根坐标内积，根长²=2 归一）"""
    return sum(a[i]*C[i][j]*b[j] for i in range(6) for j in range(6))

print("\n" + "="*70)
print("检验5：E6 正根 30/6 拆分穷举（几何-G-E3）")
print("="*70)
found = []

# ---- 规则A：高度层 ----
print("\n[规则A] 高度层二分：")
for hsel in sorted(heights):
    a = heights[hsel]; b = 36 - a
    six = [x for x in pos if sum(x) == hsel]
    if {a, b} == {6, 30}:
        # 检查 6 个根那一侧的结构：是否构成 A2（3个正根：两两夹角 120°，即 ⟨⟩=-1 对）
        side6 = six if a == 6 else [x for x in pos if sum(x) != hsel]
        pairneg = [(i, j) for i in range(len(side6)) for j in range(i+1, len(side6))
                   if pair_mult(side6[i], side6[j]) == -1]
        struct = "A2⁺(3根两两⟨⟩=−1)" if len(pairneg) == 3 else \
                 (f"含{len(pairneg)}对⟨⟩=−1" if pairneg else "无⟨⟩=−1对")
        print(f"  高度层 {hsel}: {a} 根 vs 补 {b} 根 → 30/6 数值拆分存在；6 根结构 = {struct}")
        found.append((f"高度层{hsel}", struct))
    else:
        print(f"  高度层 {hsel}: {a} vs {b} → 非 30/6")

# ---- 规则B：与 A2 子系统的正交性 ----
print("\n[规则B] 与 A2 子系统正交性：")
a2_count = 0
ortho_hits = []
for i in range(len(pos)):
    for j in range(i+1, len(pos)):
        if pair_mult(pos[i], pos[j]) == -1:   # 夹角120°，生成 A2
            a2_count += 1
            S = [pos[i], pos[j]]
            orth = [x for x in pos if all(pair_mult(x, s) == 0 for s in S)]
            if len(orth) == 30:
                comp = [x for x in pos if x not in orth]
                pairneg = [(ii, jj) for ii in range(len(comp)) for jj in range(ii+1, len(comp))
                           if pair_mult(comp[ii], comp[jj]) == -1]
                # 检查 comp 是否 = A2 正根(3) + 3 或两个 A2
                struct = f"补6根={comp}，内含{len(pairneg)}对⟨⟩=−1"
                ortho_hits.append((pos[i], pos[j], struct))
if a2_count:
    print(f"  E6⁺ 内 A2 子系统（⟨⟩=−1 对）总数 = {a2_count}")
print(f"  正交补恰=30 的 A2 子系统数 = {len(ortho_hits)}")
for s in ortho_hits[:10]:
    print(f"    A2={s[0]}×{s[1]} → {s[2]}")
    found.append(("A2正交补", s[2]))

# ---- 规则C：单节点删除（抛物子根系） ----
print("\n[规则C] 抛物型：支撑避开某单节点：")
for node in range(6):
    avoid = [x for x in pos if x[node] == 0]
    print(f"  避开节点 α{node+1}: {len(avoid)} 根 vs 含该节点 {36-len(avoid)} 根"
          + ("  → 30/6！" if {len(avoid), 36-len(avoid)} == {30, 6} else ""))
    if {len(avoid), 36 - len(avoid)} == {30, 6}:
        comp = [x for x in pos if x[node] != 0]
        pairneg = sum(1 for ii in range(len(comp)) for jj in range(ii+1, len(comp))
                      if pair_mult(comp[ii], comp[jj]) == -1)
        print(f"    6 根 = {comp}，含 {pairneg} 对⟨⟩=−1")
        found.append((f"避开节点α{node+1}", f"{pairneg}对⟨⟩=−1"))

# ---- 规则D：与单根正交 ----
print("\n[规则D] 与某单根 α_i 正交的正根数：")
for node in range(6):
    orth = [x for x in pos if pair_mult(x, tuple(1 if k == node else 0 for k in range(6))) == 0
            and x[node] == 0]
    print(f"  与 α{node+1} 正交: {len(orth)} 根" + ("  → 补 6 根！" if 36-len(orth) == 6 else ""))

# ---- 规则E：系数类型二分（整型格点型 / 其他） ----
print("\n[规则E] 单根系数结构自然二分候选：")
even = [x for x in pos if all(v % 2 == 0 for v in x)]
print(f"  全偶系数: {len(even)} 根（应 0——偶系数范数≥8）")
ones = [x for x in pos if all(abs(v) <= 1 for v in x)]
print(f"  系数∈{{0,±1}}: {len(ones)} 根 vs 系数含±2: {36-len(ones)} 根"
      + ("  → 30/6！" if {len(ones), 36-len(ones)} == {30, 6} else ""))

print("\n[裁决-检验5汇总]")
thirty_six = [f for f in found]
if not thirty_six:
    print("  未找到任何自然规则给出恰 30/6 拆分 → E6 走廊对 30+6 关闭（照记，不硬凑）")
else:
    for name, struct in thirty_six:
        okstruct = ("A2" in struct) or ("2-重" in struct)
        print(f"  {name}: 30/6 存在；6 根结构 = {struct}；构成 A2 或 2-重: {okstruct}")
    strict = [f for f in thirty_six if ("A2⁺" in f[1] or "2-重" in f[1])]
    if not strict:
        print("  → 有 30/6 数值拆分但无一满足『6 根构成 A2 或 2-重结构』的冻结条件 → G4 升 T2 通道关闭（照记）")
    else:
        print(f"  → 满足冻结条件的候选 {strict} → G4 立案升 T2 材料（须另过体系排布翻译）")
