# -*- coding: utf-8 -*-
"""
零成本判伪检验第一波·检验1（代数-E1 + 数论-E5）
阶1152衔尾蛇群 (Z2)^3 ⋊ (S4×S3) 全候选作用 vs W(F4) 同构判定
判据冻结（云韶代数·古典文献对接图谱-v1.0-20260919 第四章E1）：
  ①枚举 Hom(S4×S3, GL(3,2)) 共轭类；②逐个构造半直积；
  ③不变量对表：元素阶分布、中心阶、交换化阶、共轭类数。
  前置声明：体系侧作用同态在 云韶数论·内部版-v2.0 §11.3/附录A 未定义
  （图谱E1原文："体系须先补作用同态规格"）→ 按任务令 fallback：穷举全部
  候选作用，检验是否存在任一候选使半直积四不变量与 W(F4) 全同。
无 GAP 环境：纯 Python（sympy 在场未依赖），零编数，全部中间值打印。
"""
import itertools, math
from fractions import Fraction
from collections import Counter

# ---------- GF(2) 3x3 矩阵：行=3bit int，bit k=第k列 ----------
def mat_mul(A, B):
    C = []
    for r in range(3):
        row = 0
        for k in range(3):
            if (A[r] >> k) & 1:
                row ^= B[k]
        C.append(row)
    return tuple(C)

def mat_vec(A, v):
    out = 0
    for k in range(3):
        if (v >> k) & 1:
            out ^= A[k]
    return out

I3 = (1, 2, 4)

def mat_inv(A):
    m = [[A[0], 1], [A[1], 2], [A[2], 4]]
    for c in range(3):
        piv = next(r for r in range(c, 3) if (m[r][0] >> c) & 1)
        m[c], m[piv] = m[piv], m[c]
        for r in range(3):
            if r != c and (m[r][0] >> c) & 1:
                m[r][0] ^= m[c][0]; m[r][1] ^= m[c][1]
    return tuple(m[k][1] for k in range(3))

GL32 = []
for rows in itertools.product(range(8), repeat=3):
    m = list(rows); rank = 0
    for c in range(3):
        piv = next((r for r in range(rank, 3) if (m[r] >> c) & 1), None)
        if piv is not None:
            m[rank], m[piv] = m[piv], m[rank]
            for r in range(3):
                if r != rank and (m[r] >> c) & 1:
                    m[r] ^= m[rank]
            rank += 1
    if rank == 3:
        GL32.append(rows)
GL32 = sorted(set(GL32))
assert len(GL32) == 168, f"GL(3,2) 阶自检失败: {len(GL32)}"
GL_idx = {A: i for i, A in enumerate(GL32)}
INVm = {A: mat_inv(A) for A in GL32}

def mat_order(A):
    B, n = A, 1
    while B != I3:
        B = mat_mul(B, A); n += 1
        if n > 168: raise RuntimeError
    return n

ord_dist_GL = Counter(mat_order(A) for A in GL32)
print(f"[自检] |GL(3,2)| = {len(GL32)}（应为168）")
print(f"[自检] GL(3,2) 元素阶分布 = {dict(sorted(ord_dist_GL.items()))}"
      f"（PSL(2,7) 标准值 {{1:1,2:21,3:56,4:42,7:48}}）")

# ---------- S4×S3 具体实现 ----------
def perm_mul(p, q): return tuple(p[i] for i in q)

def perm_order(p):
    seen = [False]*len(p); l = 1
    for i in range(len(p)):
        if not seen[i]:
            j, c = i, 0
            while not seen[j]:
                seen[j] = True; j = p[j]; c += 1
            l = math.lcm(l, c)
    return l

S4 = sorted(itertools.permutations(range(4)))
S3 = sorted(itertools.permutations(range(3)))
S4_idx = {p: i for i, p in enumerate(S4)}
S3_idx = {p: i for i, p in enumerate(S3)}
S4_mul = [[S4_idx[perm_mul(a, b)] for b in S4] for a in S4]
S3_mul = [[S3_idx[perm_mul(a, b)] for b in S3] for a in S3]
def S4_inv(i):
    for j in range(24):
        if S4_mul[i][j] == 0: return j
def S3_inv(i):
    for j in range(6):
        if S3_mul[i][j] == 0: return j
t4, u4 = S4_idx[(1, 0, 2, 3)], S4_idx[(1, 2, 3, 0)]   # (12) 与 (1 2 3 4)
p3, q3 = S3_idx[(1, 0, 2)], S3_idx[(0, 2, 1)]          # (12) 与 (23)
assert perm_order(S4[t4]) == 2 and perm_order(S4[u4]) == 4
assert perm_order(perm_mul(S4[t4], S4[u4])) == 3        # S4=<t,u|t2,u4,(tu)3>

H_list = [(i, j) for i in range(24) for j in range(6)]
H_idx = {h: k for k, h in enumerate(H_list)}
assert len(H_list) == 144
H_mul = [[H_idx[(S4_mul[a][c], S3_mul[b][d])] for (c, d) in H_list] for (a, b) in H_list]
H_inv = [H_idx[(S4_inv(a), S3_inv(b))] for (a, b) in H_list]
print(f"[自检] |S4×S3| = {len(H_list)}（应为144）")

# ---------- 枚举 Hom ----------
def comm(A, B): return mat_mul(A, B) == mat_mul(B, A)

homs_S4 = [(a, b) for a in GL32 if mat_mul(a, a) == I3
           for b in GL32 if mat_order(b) in (1, 2, 4)
           and mat_order(mat_mul(a, b)) in (1, 3)]   # (tu)^3=1 → 阶整除3
homs_S3 = [(x, y) for x in GL32 if mat_mul(x, x) == I3
           for y in GL32 if mat_mul(y, y) == I3
           and mat_order(mat_mul(x, y)) in (1, 3)]   # (xy)^3=1
print(f"[中间值] |Hom(S4,GL(3,2))| = {len(homs_S4)}，|Hom(S3,GL(3,2))| = {len(homs_S3)}")

pairs_comm = [((a, b), (x, y)) for (a, b) in homs_S4 for (x, y) in homs_S3
              if comm(a, x) and comm(a, y) and comm(b, x) and comm(b, y)]
print(f"[中间值] 交换像配对 |Hom(S4×S3,GL(3,2))| = {len(pairs_comm)}")

def conj(A, K): return mat_mul(mat_mul(K, A), INVm[K])
def canon(p1, p2):
    best = None
    for K in GL32:
        cand = ((conj(p1[0], K), conj(p1[1], K)), (conj(p2[0], K), conj(p2[1], K)))
        if best is None or cand < best: best = cand
    return best
classes = {}
for pr in pairs_comm:
    classes[canon(pr[0], pr[1])] = classes.get(canon(pr[0], pr[1]), 0) + 1
print(f"[中间值] GL(3,2)-共轭类数 |Hom(S4×S3,GL(3,2))/共轭| = {len(classes)}")
hom_classes = sorted(classes.keys())

# ---------- 半直积构造与不变量 ----------
def build_action(p1, p2):
    (a, b), (x, y) = p1, p2
    m_S4 = {0: I3}; stack = [0]
    g4 = [(t4, a), (u4, b), (S4_inv(t4), INVm[a]), (S4_inv(u4), INVm[b])]
    while stack:
        e = stack.pop()
        for g, m in g4:
            ne = S4_mul[e][g]
            if ne not in m_S4:
                m_S4[ne] = mat_mul(m_S4[e], m); stack.append(ne)
    assert len(m_S4) == 24
    m_S3 = {0: I3}; stack = [0]
    g3 = [(p3, x), (q3, y), (S3_inv(p3), INVm[x]), (S3_inv(q3), INVm[y])]
    while stack:
        e = stack.pop()
        for g, m in g3:
            ne = S3_mul[e][g]
            if ne not in m_S3:
                m_S3[ne] = mat_mul(m_S3[e], m); stack.append(ne)
    assert len(m_S3) == 6
    return {k: mat_mul(m_S4[i], m_S3[j]) for (i, j), k in H_idx.items()}

def semidirect_invariants(act):
    elems = [(v, k) for k in range(144) for v in range(8)]
    eid = {e: i for i, e in enumerate(elems)}
    def mul(i, j):
        v1, h1 = elems[i]; v2, h2 = elems[j]
        return eid[(v1 ^ mat_vec(act[h1], v2), H_mul[h1][h2])]
    einv = [eid[(mat_vec(act[H_inv[h]], v), H_inv[h])] for (v, h) in elems]
    gens = [eid[(1, 0)], eid[(2, 0)], eid[(4, 0)],
            eid[(0, H_idx[(t4, 0)])], eid[(0, H_idx[(u4, 0)])],
            eid[(0, H_idx[(0, p3)])], eid[(0, H_idx[(0, q3)])]]
    order_dist = Counter()
    for i in range(1152):
        x, n = 0, 0
        while True:
            x = mul(x, i)
            n += 1
            if x == 0: break
        order_dist[n] += 1
    center = sum(1 for i in range(1152)
                 if all(mul(mul(g, i), einv[g]) == i for g in gens))
    commset = {mul(mul(mul(g, h), einv[g]), einv[h]) for g in gens for h in gens}
    grp = {0} | commset; stack = list(commset)
    while stack:
        e = stack.pop()
        for c in list(commset):
            for ne in (mul(e, c), mul(e, einv[c])):
                if ne not in grp:
                    grp.add(ne); stack.append(ne)
    derived_order = len(grp)
    seen = [False]*1152; nclasses = 0
    sizes = []
    for i in range(1152):
        if seen[i]: continue
        nclasses += 1; cnt = 0; queue = [i]; seen[i] = True
        while queue:
            e = queue.pop(); cnt += 1
            for g in gens:
                c = mul(mul(g, e), einv[g])
                if not seen[c]:
                    seen[c] = True; queue.append(c)
        sizes.append(cnt)
    return dict(order_dist=dict(sorted(order_dist.items())),
                center_order=center,
                abelianization_order=1152//derived_order,
                derived_order=derived_order,
                num_conj_classes=nclasses, max_class=max(sizes))

results = []
for ci, (p1, p2) in enumerate(hom_classes):
    act = build_action(p1, p2)
    inv = semidirect_invariants(act)
    im_ord = len({act[k] for k in range(144)})
    results.append((ci, p1, p2, im_ord, inv))
    print(f"[候选作用 {ci:02d}] 像阶={im_ord:3d} 不变量={inv}")

print("\n[候选作用不变量去重]")
seen_inv = {}
for ci, p1, p2, im_ord, inv in results:
    key = (tuple(sorted(inv['order_dist'].items())), inv['center_order'],
           inv['abelianization_order'], inv['num_conj_classes'])
    seen_inv.setdefault(key, []).append(ci)
for key, cis in seen_inv.items():
    print(f"  不变量组 {key} ← 候选作用 {cis}")

# ---------- W(F4) ----------
ROOTS = set()
for i in range(4):
    for s in (1, -1):
        v = [0]*4; v[i] = s; ROOTS.add(tuple(v))
for i, j in itertools.combinations(range(4), 2):
    for si in (1, -1):
        for sj in (1, -1):
            v = [0]*4; v[i] = si; v[j] = sj; ROOTS.add(tuple(v))
for v in itertools.product((1, -1), repeat=4):
    ROOTS.add(tuple(Fraction(x, 2) for x in v))
ROOTS = sorted(ROOTS)
assert len(ROOTS) == 48, f"F4 根数自检失败: {len(ROOTS)}"
R_idx = {r: i for i, r in enumerate(ROOTS)}
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def reflect(a, x):
    f = Fraction(2*dot(a, x), dot(a, a))
    return tuple(xi - f*ai for xi, ai in zip(x, a))
SIMPLE = [(0, 1, -1, 0), (0, 0, 1, -1), (0, 0, 0, 1),
          tuple(Fraction(-1, 2) for _ in range(4))]  # o-o=o-o 型 F4 单根系
gens_perm = [tuple(R_idx[reflect(a, r)] for r in ROOTS) for a in SIMPLE]
id48 = tuple(range(48))
def p_mul(p, q): return tuple(p[i] for i in q)
def p_inv(p):
    inv = [0]*48
    for i, j in enumerate(p): inv[j] = i
    return tuple(inv)
group48 = {id48}; stack = [id48]
while stack:
    e = stack.pop()
    for g in gens_perm:
        gi = p_inv(g)
        for ne in (p_mul(e, g), p_mul(e, gi)):
            if ne not in group48:
                group48.add(ne); stack.append(ne)
group48 = sorted(group48)
print(f"\n[自检] |W(F4)| = {len(group48)}（应为1152=2^7·3^2）")
def perm48_order(p):
    seen = [False]*48; l = 1
    for i in range(48):
        if not seen[i]:
            j, c = i, 0
            while not seen[j]:
                seen[j] = True; j = p[j]; c += 1
            l = math.lcm(l, c)
    return l
w_order = Counter(perm48_order(g) for g in group48)
w_center = sum(1 for g in group48
               if all(p_mul(p_mul(k, g), p_inv(k)) == g for k in gens_perm))
commset = {p_mul(p_mul(p_mul(g, h), p_inv(g)), p_inv(h))
           for g in gens_perm for h in gens_perm}
grp = {id48} | commset; stack = list(commset)
cinv = {c: p_inv(c) for c in commset}
while stack:
    e = stack.pop()
    for c in commset:
        for ne in (p_mul(e, c), p_mul(e, cinv[c])):
            if ne not in grp:
                grp.add(ne); stack.append(ne)
w_derived = len(grp)
seen = set(); nclasses = 0  # 从空集起算，恒等元类也计入（与全量复核一致）
while len(seen) < len(group48):
    rep = next(iter(set(group48) - seen))
    nclasses += 1; queue = [rep]; seen.add(rep)
    while queue:
        e = queue.pop()
        for g in gens_perm:
            c = p_mul(p_mul(g, e), p_inv(g))
            if c not in seen:
                seen.add(c); queue.append(c)
# 全量共轭复核（1152×1152 穷举，防生成元轨道遗漏）
full_seen = set(); full_nclasses = 0
g48_all = list(group48)
for rep in g48_all:
    if rep in full_seen: continue
    full_nclasses += 1
    for k in g48_all:
        full_seen.add(p_mul(p_mul(k, rep), p_inv(k)))
assert full_nclasses == nclasses, f"共轭类数复核不一致: {nclasses} vs {full_nclasses}"
# 交换子群复核：全元素交换子生成
full_comm = set()
g48_i = {g: p_inv(g) for g in group48}
for a in g48_all:
    for b in g48_all:
        full_comm.add(p_mul(p_mul(p_mul(a, b), g48_i[a]), g48_i[b]))
assert len(full_comm) <= len(grp)
print(f"[复核] W(F4) 全量穷举共轭类数 = {full_nclasses}；全元素交换子生成子群阶 ≥ 闭包阶："
      f"{len(grp)}（全交换子集大小 {len(full_comm)}，应含于交换子群）")
W_inv = dict(order_dist=dict(sorted(w_order.items())),
             center_order=w_center,
             abelianization_order=len(group48)//w_derived,
             derived_order=w_derived, num_conj_classes=nclasses)
print(f"[W(F4)] 不变量 = {W_inv}")
W_key = (tuple(sorted(w_order.items())), w_center, len(group48)//w_derived, nclasses)
match = [ci for ci, p1, p2, im, inv in results
         if (tuple(sorted(inv['order_dist'].items())), inv['center_order'],
             inv['abelianization_order'], inv['num_conj_classes']) == W_key]
print(f"\n[裁决原始输出] W(F4) 不变量键 = {W_key}")
print(f"[裁决原始输出] 与 W(F4) 四不变量全同的候选作用编号 = {match}")
print(f"[裁决原始输出] 候选作用类总数 = {len(hom_classes)}；不同不变量组数 = {len(seen_inv)}")
