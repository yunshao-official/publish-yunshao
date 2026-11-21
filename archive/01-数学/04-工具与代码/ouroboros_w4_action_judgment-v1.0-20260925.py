# -*- coding: utf-8 -*-
"""
衔尾蛇群候选作用构造 + W(F4) 同构判定（ZCode 代拟候选作用，非体系原文）
=====================================================================
任务：数论内部版 v2.1 §14.5/§14.9 立案（G=(Z2)^3⋊(S4×S3) 阶 1152 无作用定义，
     W(F4) 阶亦 1152）的代拟执行收口。
口径：
  1) 穷举一切同态 φ: S4×S3 → GL(3,2)（生成元关系式全解，按 GL(3,2) 共轭去重）；
  2) 每个共轭类构造半直积 G_φ = F2^3 ⋊_φ (S4×S3)，算不变量：
     阶/元素阶分布/中心阶/交换化(|Ab|+类型)/共轭类大小谱/对合数；
  3) 构造 W(F4)（按任务令简单根 α1=e1-e2, α2=e2-e3, α3=e3, α4=-(e1+e2+e3+e4)/2），
     BFS 闭包自检阶=1152，48 根集不变自检，算同一组不变量；
  4) 判定：不变量全同→再查 W(F4) 是否有正规初等交换 2^3（半直积构造必含之，
     是同构必要条件）；任何不一致→判"该候选作用下不同构"。
自检：GL(3,2) 阶=168；S4×S3 阶=144；G_φ 阶=1152；W(F4) 阶=1152；|Ab| 用 |G|/|[G,G]| 双算。
运行：python ouroboros_w4_action_judgment-v1.0-20260925.py  （预算 ≤120s）
输出：同目录 results\ouroboros_w4_action_judgment-v1.0-20260925.json
"""
import itertools, json, time
from collections import deque, Counter
from fractions import Fraction

T0 = time.time()
OUT = {}

# ---------------- 通用置换群工具 ----------------
def pmul(p, q):        # 合成 (p*q)(x) = p(q(x))
    return tuple(p[q[i]] for i in range(len(p)))

def pinv(p):
    r = [0] * len(p)
    for i, j in enumerate(p):
        r[j] = i
    return tuple(r)

def porder(p):
    ident = tuple(range(len(p)))
    q, n = p, 1
    while q != ident:
        q = pmul(p, q)
        n += 1
    return n

def closure(gens, n):
    """生成集（含逆）BFS 闭包 -> 集合"""
    ident = tuple(range(n))
    grp = {ident}
    dq = deque([ident])
    gs = gens + [pinv(g) for g in gens]
    while dq:
        x = dq.popleft()
        for g in gs:
            h = pmul(x, g)
            if h not in grp:
                grp.add(h)
                dq.append(h)
    return grp

def order_profile(grp):
    return dict(sorted(Counter(porder(g) for g in grp).items()))

def center_of(grp, gens):
    return [g for g in grp if all(pmul(g, h) == pmul(h, g) for h in gens)]

def commutator_subgroup(grp_size_hint, gens, n):
    """换位子子群 = 换位子集的正规闭包（对有限群，闭包即子群）"""
    comms = []
    for a in gens:
        ai = pinv(a)
        for b in gens:
            bi = pinv(b)
            comms.append(pmul(pmul(pmul(ai, bi), a), b))
    return closure(comms, n)

def conj_class_sizes(grp, gens):
    classes, seen = [], set()
    for g in sorted(grp):
        if g in seen:
            continue
        orb = {g}
        dq = deque([g])
        while dq:
            x = dq.popleft()
            for h in gens:
                c = pmul(pmul(h, x), pinv(h))
                if c not in orb:
                    orb.add(c)
                    dq.append(c)
        classes.append(len(orb))
        seen |= orb
    return sorted(classes, reverse=True)

def abelianization(grp, comm, n):
    """商 G/[G,G]：返回 (阶, 元素阶分布)"""
    cid = {}
    cosets = []
    for g in sorted(grp):
        if g in cid:
            continue
        k = len(cosets)
        coset = set()
        dq = deque([g])
        while dq:
            x = dq.popleft()
            if x in cid:
                continue
        cid[x] = k
        coset.add(x)
        for c in comm:
            dq.append(pmul(x, c))
        cosets.append(g)
    ident = tuple(range(n))
    rep = {i: cosets[i] for i in range(len(cosets))}
    def op(i, j):
        return cid[pmul(rep[i], rep[j])]
    prof = {}
    for i in range(len(cosets)):
        x, m = i, 1
        while True:
            x = op(x, i)
            if x == 0:
                break
            m += 1
        prof[i] = m
    # 商群元素阶
    qprof = Counter()
    for i in range(len(cosets)):
        x, m = i, 1
        while x != 0:
            x = op(x, i)
            m += 1
        qprof[m] += 1
    return len(cosets), dict(sorted(qprof.items()))

# ---------------- S4 × S3 ----------------
S4 = list(itertools.permutations(range(4)))           # 24
S3 = list(itertools.permutations(range(3)))           # 6
assert len(S4) == 24 and len(S3) == 6
Gamma = [(a, b) for a in S4 for b in S3]              # 144
gidx = {g: i for i, g in enumerate(Gamma)}
def gmul_idx(i, j):
    a1, b1 = Gamma[i]
    a2, b2 = Gamma[j]
    return gidx[(tuple(a1[a2[k]] for k in range(4)),
                 tuple(b1[b2[k]] for k in range(3)))]
GM = [[gmul_idx(i, j) for j in range(144)] for i in range(144)]
assert len(Gamma) == 144

# Γ 生成元：S4 = <(1234),(12)>，S3 = <(123)',(12)'>
a4 = (1, 2, 3, 0)     # (1234)
b4 = (1, 0, 2, 3)     # (12)
c3 = (1, 2, 0)        # (123)
d3 = (1, 0, 2)        # (12)
GENS_G = [gidx[(a4, tuple(range(3)))], gidx[(b4, tuple(range(3)))],
          gidx[(tuple(range(4)), c3)], gidx[(tuple(range(4)), d3)]]

# ---------------- GL(3,2)（列掩码矩阵）----------------
def popcount(x):
    return bin(x).count("1")

GL = []
for c0 in range(1, 8):
    for c1 in range(1, 8):
        if c1 == c0:
            continue
        for c2 in range(1, 8):
            if c2 in (c0, c1) or (c0 ^ c1 ^ c2) == 0:
                continue
            GL.append((c0, c1, c2))   # 列向量；矩阵作用 v: wj = parity(cj & v)
assert len(GL) == 168, len(GL)
glidx = {m: i for i, m in enumerate(GL)}

def mat_apply(m, v):
    return (popcount(m[0] & v) & 1) | ((popcount(m[1] & v) & 1) << 1) | ((popcount(m[2] & v) & 1) << 2)

def mat_mul(m, n):
    # (m*n)：n 先作用。结果列 j 的分量 i = Σ_k m[k]行i 分量 × n[j]列k 分量
    cols = []
    for j in range(3):
        w = 0
        for i in range(3):
            bit = 0
            for k in range(3):
                bit ^= ((m[k] >> i) & 1) & ((n[j] >> k) & 1)
            w |= bit << i
        cols.append(w)
    return tuple(cols)

# ---------------- 穷举同态 φ: S4×S3 → GL(3,2) ----------------
# S4: <A,B | A^4=B^2=(AB)^3=1>；S3: <C,D | C^3=D^2=(CD)^2=1>
homs_S4 = []
I = (1 << 0, 1 << 1, 1 << 2)   # 单位矩阵（列 = 单位向量）
for A in GL:
    for B in GL:
        AB = mat_mul(A, B)
        x = A
        for _ in range(3):
            x = mat_mul(x, A)
        ok4 = (x == I)
        ok2 = (mat_mul(B, B) == I)
        z = mat_mul(AB, mat_mul(AB, AB))
        ok3 = (z == I)
        if ok4 and ok2 and ok3:
            homs_S4.append((A, B))
homs_S3 = []
I = (1 << 0, 1 << 1, 1 << 2)
for C in GL:
    for D in GL:
        x = C
        for _ in range(2):
            x = mat_mul(x, C)
        if x != I:
            continue
        if mat_mul(D, D) != I:
            continue
        CD = mat_mul(C, D)
        z = mat_mul(CD, CD)
        if z == I:
            homs_S3.append((C, D))
OUT["hom_counts_raw"] = {"S4_to_GL32": len(homs_S4), "S3_to_GL32": len(homs_S3)}

# 交换性筛选：S4 像 × S3 像逐生成元交换
pairs = []
for (A, B) in homs_S4:
    for (C, D) in homs_S3:
        if (mat_mul(A, C) == mat_mul(C, A) and mat_mul(A, D) == mat_mul(D, A)
                and mat_mul(B, C) == mat_mul(C, B) and mat_mul(B, D) == mat_mul(D, B)):
            pairs.append(((A, B), (C, D)))
OUT["commuting_pairs_count"] = len(pairs)

# 同态扩展：由 4 生成元像扩到全 Γ 同态表（BFS）
def image_of(phigen):
    tab = {0: I}
    dq = deque([0])
    gens_img = {g: m for g, m in zip(GENS_G, phigen)}
    while dq:
        gi = dq.popleft()
        for g in GENS_G:
            gj = GM[gi][g]
            if gj not in tab:
                tab[gj] = mat_mul(tab[gi], gens_img[g])
                dq.append(gj)
    assert len(tab) == 144
    return tab

def im_order(pha):
    return len(set(pha.values()))

# 共轭去重（预算优化：预计算逆元；按（像共轭类，核）分桶，桶数少且不漏判）
INV = {}
for X in GL:
    for Y in GL:
        if mat_mul(X, Y) == I and mat_mul(Y, X) == I:
            INV[X] = Y
            break

def conj_mat(P, M):
    return mat_mul(mat_mul(P, M), INV[P])

def image_of_full(phagen):
    """同态表 + 像集合 + 核"""
    pha = image_of(phagen)
    im = frozenset(pha.values())
    ker = frozenset(gi for gi in range(144) if pha[gi] == I)
    return pha, im, ker

# 像子群的共轭规范形：min over P of 排序后的共轭像
def canon_image(im):
    best = None
    for P in GL:
        c = tuple(sorted(conj_mat(P, m) for m in im))
        if best is None or c < best:
            best = c
    return best

buckets = {}
for (s4h, s3h) in pairs:
    phagen = (s4h[0], s4h[1], s3h[0], s3h[1])
    pha, im, ker = image_of_full(phagen)
    key = (im_order(pha), canon_image(im), ker)
    if key not in buckets:
        buckets[key] = phagen
classes = [(pha_gen, key[0]) for key, pha_gen in buckets.items()]
OUT["n_dedup_buckets"] = len(classes)
OUT["hom_conj_classes"] = [
    {"im_order": k,
     "gen_images": {"S4_A": list(c[0]), "S4_B": list(c[1]),
                    "S3_C": list(c[2]), "S3_D": list(c[3])}}
    for c, k in classes]
OUT["n_hom_conj_classes"] = len(classes)

# ---------------- 半直积 G_φ 与不变量 ----------------
def semidirect_invariants(phagen):
    pha = image_of(phagen)
    # 元素 (v, gi) 编号 = v*144+gi
    N = 8 * 144
    def mul(x, y):
        v, gi = divmod(x, 144)
        w, hj = divmod(y, 144)
        return ((v ^ mat_apply(pha[gi], w)) * 144) + GM[gi][hj]
    def inv_elenum(x):
        v, gi = divmod(x, 144)
        # 找 y 使 x*y=0：y=(pha[gi]^{-1} v, gi^{-1})
        # gi 逆：穷举
        for hj in range(144):
            if GM[gi][hj] == 0:
                break
        Minv = None
        for X in GL:
            if mat_mul(pha[gi], X) == I:
                Minv = X
                break
        w = 0
        for i in range(3):
            bit = 0
            for k in range(3):
                bit ^= ((Minv[k] >> i) & 1) & ((v >> k) & 1)
            w |= bit << i
        return w * 144 + hj
    ident = 0
    # 生成元：V 的三个基 + Γ 四生成元
    gens = [1 * 144 + 0, 2 * 144 + 0, 4 * 144 + 0] + [gi for gi in GENS_G]
    # 全群枚举（阶自检）
    grp = closure_generic(gens, mul, N)
    order = len(grp)
    # 元素阶
    prof = Counter()
    for x in grp:
        y, m = x, 1
        while y != ident:
            y = mul(x, y)
            m += 1
        prof[m] += 1
    # 中心
    zc = 0
    for x in grp:
        if all(mul(x, g) == mul(g, x) for g in gens):
            zc += 1
    # 换位子子群
    comms = []
    for i, x in enumerate(gens):
        xi = inv_elenum(x)
        for y in gens:
            yi = inv_elenum(y)
            # [x,y] = x^-1 y^-1 x y
            comms.append(mul(mul(mul(xi, yi), x), y))
    comm = closure_generic(comms, mul, N)
    ab_order = order // len(comm)
    # 共轭类
    cls = []
    seen = set()
    for x in sorted(grp):
        if x in seen:
            continue
        orb = {x}
        dq = deque([x])
        while dq:
            e = dq.popleft()
            for g in gens:
                gi_ = inv_elenum(g)
                c = mul(mul(g, e), gi_)
                if c not in orb:
                    orb.add(c)
                    dq.append(c)
        cls.append(len(orb))
        seen |= orb
    return {
        "order": order,
        "element_orders": dict(sorted(prof.items())),
        "center_order": zc,
        "ab_order": ab_order,
        "comm_order": len(comm),
        "n_conj_classes": len(cls),
        "class_sizes": sorted(cls, reverse=True),
        "n_involutions": prof.get(2, 0),
    }

def closure_generic(gens, mul, N):
    grp = {0}
    dq = deque([0])
    gs = list(gens)
    while dq:
        x = dq.popleft()
        for g in gs:
            h = mul(x, g)
            if h not in grp:
                grp.add(h)
                dq.append(h)
    return grp

semidirect_results = []
for phagen, k in classes:
    inv = semidirect_invariants(phagen)
    semidirect_results.append({"im_order": k, **inv})
OUT["semidirect_invariants"] = semidirect_results

# ---------------- W(F4) ----------------
# 简单根（任务令）：α1=e1-e2, α2=e2-e3, α3=e3, α4=-(e1+e2+e3+e4)/2
# 向量用 Fraction；反射 s_i(v)=v-2<v,ai>/<ai,ai> ai
alphas = [
    [Fraction(1), Fraction(-1), Fraction(0), Fraction(0)],
    [Fraction(0), Fraction(1), Fraction(-1), Fraction(0)],
    [Fraction(0), Fraction(0), Fraction(1), Fraction(0)],
    [Fraction(-1, 2)] * 4,
]
def dot(u, v):
    return sum(x * y for x, y in zip(u, v))

refl = []
for al in alphas:
    naa = dot(al, al)
    S = [[Fraction(int(i == j)) for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            S[i][j] -= Fraction(2) * al[i] * al[j] / naa
    refl.append(S)

def mat4_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

I4 = [[Fraction(int(i == j)) for j in range(4)] for i in range(4)]

def mat_key(A):
    return tuple(tuple(str(x) for x in row) for row in A)

# 根系 48 根：±e_i（8 短）+ ±e_i±e_j（24 长）+ (±½,±½,±½,±½)（16 短）
roots = set()
for i in range(4):
    v = [Fraction(0)] * 4
    v[i] = Fraction(1)
    roots.add(tuple(v))
    v2 = [Fraction(0)] * 4
    v2[i] = Fraction(-1)
    roots.add(tuple(v2))
    for j in range(i + 1, 4):
        for si, sj in [(1, -1), (-1, 1), (1, 1), (-1, -1)]:
            v = [Fraction(0)] * 4
            v[i], v[j] = Fraction(si), Fraction(sj)
            roots.add(tuple(v))
for sign in itertools.product([Fraction(-1, 2), Fraction(1, 2)], repeat=4):
    roots.add(sign)
roots = sorted(roots)
assert len(roots) == 48, len(roots)

# BFS 闭包
def apply_mat(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(4)) for i in range(4))

Wset = {mat_key(I4): I4}
dq = deque([I4])
gens4 = refl
while dq:
    X = dq.popleft()
    for G in gens4:
        Y = mat4_mul(X, G)
        k = mat_key(Y)
        if k not in Wset:
            Wset[k] = Y
            dq.append(Y)
W_order = len(Wset)
OUT["W_F4_order"] = W_order
rootset = set(roots)
OUT["W_F4_preserves_roots"] = all(
    apply_mat(A, r) in rootset for A in Wset.values() for r in roots)

# 根置换表示 -> 群工具
ridx = {r: i for i, r in enumerate(roots)}
Wperms = {}
for k, A in Wset.items():
    Wperms[k] = tuple(ridx[apply_mat(A, r)] for r in roots)
Wgen_perms = [tuple(ridx[apply_mat(G, r)] for r in roots) for G in gens4]
Wgrp = set(Wperms.values())
assert len(Wgrp) == W_order

Winv = {}
prof = Counter()
for p in Wgrp:
    prof[porder(p)] += 1
Winv["order"] = W_order
Winv["element_orders"] = dict(sorted(prof.items()))
zc = sum(1 for p in Wgrp if all(pmul(p, g) == pmul(g, p) for g in Wgen_perms))
Winv["center_order"] = zc
comm = commutator_subgroup(W_order, Wgen_perms, 48)
Winv["comm_order"] = len(comm)
Winv["ab_order"] = W_order // len(comm)
ab_o, ab_prof = abelianization(Wgrp, comm, 48)
Winv["ab_profile"] = ab_prof
Winv["n_conj_classes"] = len(conj_class_sizes(Wgrp, Wgen_perms))
Winv["class_sizes"] = conj_class_sizes(Wgrp, Wgen_perms)
Winv["n_involutions"] = prof.get(2, 0)

# W(F4) 是否有正规初等交换 2^3（半直积构造的必要条件）
inv_classes = []   # 对合所在共轭类（按代表元）
cls_repr = []
seen = set()
for g in sorted(Wgrp):
    if g in seen:
        continue
    orb = {g}
    dq = deque([g])
    while dq:
        x = dq.popleft()
        for h in Wgen_perms:
            c = pmul(pmul(h, x), pinv(h))
            if c not in orb:
                orb.add(c)
                dq.append(c)
    cls_repr.append((g, frozenset(orb)))
    seen |= orb
normal_cand = []
# 正规子群 = 若干完整共轭类的并；阶 8 且全部元素阶<=2 且交换
subsets = []
ident = tuple(range(48))
nonid_classes = [orb for (g, orb) in cls_repr if g != ident]
for r in range(1, 5):
    for combo in itertools.combinations(range(len(nonid_classes)), r):
        tot = 1 + sum(len(nonid_classes[i]) for i in combo)
        if tot == 8:
            subsets.append(combo)
checked = 0
for combo in subsets:
    elems = {ident}
    for i in combo:
        elems |= set(nonid_classes[i])
    if any(porder(e) > 2 for e in elems):
        continue
    checked += 1
    # 子群+交换判定：闭包
    gs = list(elems - {ident})
    cl = closure(gs, 48)
    if len(cl) == 8 and cl == elems:
        # 交换性
        if all(pmul(a, b) == pmul(b, a) for a in elems for b in elems):
            normal_cand.append(sorted(elems))
OUT["W_F4_normal_E8_count"] = len(normal_cand)
# S4×S3 自身元素阶分布（商群比对基准）
def gmul_idx_(g, h):
    a1, b1 = g
    a2, b2 = h
    return (tuple(a1[a2[k]] for k in range(4)), tuple(b1[b2[k]] for k in range(3)))

S4S3_orders = Counter()
ig = (tuple(range(4)), tuple(range(3)))
for gg in Gamma:
    o, x = 1, gg
    while x != ig:
        x = gmul_idx_(x, gg)
        o += 1
    S4S3_orders[o] += 1
OUT["S4xS3_order_profile"] = dict(sorted(S4S3_orders.items()))
OUT["W_F4_invariants"] = Winv

# 商群检查（若有正规 2^3）
quot_checks = []
for E in normal_cand[:4]:
    Es = set(E)
    # 陪集空间
    cs = {}
    reps = []
    for g in sorted(Wgrp):
        if g in cs:
            continue
        k = len(reps)
        for e in Es:
            cs[pmul(g, e)] = k
        reps.append(g)
    qord = len(reps)
    # 商元素阶：rep 的幂落回单位陪集
    profq = Counter()
    for i in range(len(reps)):
        x, m = reps[i], 1
        while cs[x] != 0:
            x = pmul(x, reps[i])
            m += 1
        profq[m] += 1
    quot_checks.append({"quotient_order": qord,
                        "quotient_order_profile": dict(sorted(profq.items())),
                        "matches_S4xS3": dict(sorted(profq.items())) == dict(sorted(S4S3_orders.items()))})
OUT["W_F4_normal_E8_quotients"] = quot_checks

# ---------------- 判定 ----------------
Wvec = (Winv["element_orders"], Winv["center_order"], Winv["ab_order"],
        Winv["class_sizes"])
verdicts = []
for c in OUT["semidirect_invariants"]:
    gvec = (c["element_orders"], c["center_order"], c["ab_order"], c["class_sizes"])
    same = (gvec == Wvec)
    diffs = [nm for nm, a, b in
             [("element_orders", c["element_orders"], Winv["element_orders"]),
              ("center_order", c["center_order"], Winv["center_order"]),
              ("ab_order", c["ab_order"], Winv["ab_order"]),
              ("class_sizes", c["class_sizes"], Winv["class_sizes"])]
             if a != b]
    verdicts.append({"im_order": c["im_order"],
                     "isomorphic_candidate": same,
                     "differing_invariants": diffs})
OUT["verdicts_per_class"] = verdicts
OUT["structural_note"] = {
    "W_has_normal_E8": len(normal_cand) > 0,
    "lagrange_constraint": "144 不整除 168： faithful S4 像(24) 与 faithful S3 像(6) 交换配对必不存在",
    "im_orders_found": sorted({c["im_order"] for c in OUT["semidirect_invariants"]}),
}
OUT["runtime_sec"] = round(time.time() - T0, 1)

with open(r"H:\理论存档\01-数学\02-实验与数据\results\ouroboros_w4_action_judgment-v1.0-20260925.json",
          "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1, default=str)

print("=== 判定摘要 ===")
print("GL(3,2) 阶:", len(GL), "| Γ 阶:", len(Gamma))
print("S4 同态原始数:", OUT["hom_counts_raw"]["S4_to_GL32"],
      "| S3:", OUT["hom_counts_raw"]["S3_to_GL32"],
      "| 交换配对:", OUT["commuting_pairs_count"],
      "| 共轭类:", OUT["n_hom_conj_classes"])
for c in OUT["semidirect_invariants"]:
    print("— im φ 阶 =", c["im_order"], "| 阶", c["order"],
          "| 中心", c["center_order"], "| Ab 阶", c["ab_order"],
          "| 类数", c["n_conj_classes"])
print("W(F4) 阶:", Winv["order"], "自检(应=1152) | 中心", Winv["center_order"],
      "| Ab 阶", Winv["ab_order"], "| 类数", Winv["n_conj_classes"])
print("W(F4) 正规 2^3 个数:", OUT["W_F4_normal_E8_count"])
print("逐类判定:", json.dumps(OUT["verdicts_per_class"], ensure_ascii=False))
print("运行秒:", OUT["runtime_sec"])
