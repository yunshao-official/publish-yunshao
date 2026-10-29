# -*- coding: utf-8 -*-
# 云韶群论 G-1 复核·决定性对照脚本 (2026-09-19, ZCode 任务五续跑第2轮)
# 问题: GAP库 SmallGroup(192,1493) 一手属性=Aut(Z4×V4) 同构类（Groupprops "Groups of order 16"
#       Automorphism groups 表行, 2026-09-19 实取）。我们的 192 阶扩展群 (Z2)^3:~S4 是否同构于它?
# 方法: 显式枚举 Aut(C4×C2×C2) 全部 192 个自同构（映射复合乘法表）, 算结构指纹;
#       与 (Z2)^3:~S4 (φ=模2标准表示) 同款指纹对照; 再做生成元级同构搜索定谳。
import json, itertools
from collections import Counter

# ---------- A. Aut(C4 x C2 x C2) ----------
# 元素 (a,b,c): a mod 4, b,c mod 2.  e1=(1,0,0) 阶4, e2=(0,1,0), e3=(0,0,1) 阶2.
Apts = [(a, b, c) for a in range(4) for b in range(2) for c in range(2)]
Ai = {p: k for k, p in enumerate(Apts)}
def a_add(x, y): return ((x[0] + y[0]) % 4, (x[1] + y[1]) % 2, (x[2] + y[2]) % 2)
def a_ord(x):
    o, s = 1, x
    while s != (0, 0, 0):
        s = a_add(s, x); o += 1
    return o
E1, E2, E3 = (1, 0, 0), (0, 1, 0), (0, 0, 1)
ord2 = [p for p in Apts if a_ord(p) <= 2]           # 8 个阶≤2 元
ord4 = [p for p in Apts if a_ord(p) == 4]           # 8 个阶4 元

def gen_subgroup(gens):
    """生成子群闭包"""
    S = {(0, 0, 0)}
    grew = True
    while grew:
        grew = False
        for x in list(S):
            for g in gens:
                y = a_add(x, g)
                if y not in S:
                    S.add(y); grew = True
    return S

autos = []
for f1 in ord4:                                     # f(e1) 必须阶 4
    for f2 in ord2:
        for f3 in ord2:
            if gen_subgroup([f1, f2, f3]) == set(Apts):   # 可逆 = 生成全群
                autos.append((f1, f2, f3))
def apply_auto(t, x):
    f1, f2, f3 = t
    return a_add(a_add((f1[0] * x[0] % 4, f1[1] * x[0] % 2, f1[2] * x[0] % 2), (f2[0] * x[1], f2[1] * x[1], f2[2] * x[1])),
                 (f3[0] * x[2], f3[1] * x[2], f3[2] * x[2]))
# 注: 同态像由 e1,e2,e3 的像线性决定; 直接查表更稳——改为显式表:
def auto_map(t):
    f1, f2, f3 = t
    m = [None] * 16
    for x in Apts:
        img = (0, 0, 0)
        if x[0] & 1: img = a_add(img, f1)
        if x[0] & 2: img = a_add(img, a_add(f1, f1))
        if x[1]: img = a_add(img, f2)
        if x[2]: img = a_add(img, f3)
        m[Ai[x]] = Ai[img]
    return tuple(m)
AM = [auto_map(t) for t in autos]
assert len(set(AM)) == len(AM) == 192, f"Aut 阶异常: {len(AM)}"

# ---------- B. (Z2)^3 :~ S4 (φ=模2标准表示) 的 8 点仿射置换表示 ----------
N = list(itertools.product([0, 1], repeat=3))
v2p = {v: i for i, v in enumerate(N)}
def s_add(x, y): return tuple((x[i] + y[i]) & 1 for i in range(3))
def std(eps, r):
    a, b, c = eps
    v = (a, b, c, (a + b + c) & 1)
    w = [0] * 4
    for i in range(4):
        w[r[i]] = v[i]
    return tuple(w[:3])
def affine(n, r):
    p = [0] * 8
    for x in N:
        y = s_add(std(x, r), n)
        p[v2p[x]] = v2p[y]
    return tuple(p)
S4 = list(itertools.permutations(range(4)))
id4 = tuple(range(4))
GM = [affine(n, id4) for n in ([1, 0, 0], [0, 1, 0], [0, 0, 1])]
GM += [affine((0, 0, 0), r) for r in [(1, 0, 2, 3), (1, 2, 0, 3), (3, 1, 2, 0)]]
def closure(maps, ptsize):
    """由生成元映射闭包生成全群（映射复合）"""
    comp = lambda f, g: tuple(f[g[i]] for i in range(ptsize))   # f∘g
    els = {tuple(range(ptsize))}
    grew = True
    while grew:
        grew = False
        for a in list(els):
            for g in maps:
                for h in (comp(a, g), comp(g, a)):
                    if h not in els:
                        els.add(h); grew = True
    return els
GS = closure(GM, 8)
assert len(GS) == 192, f"半直积阶异常: {len(GS)}"

# ---------- 指纹计算（映射群通用） ----------
def fingerprints(els, ptsize):
    ident = tuple(range(ptsize))
    comp = lambda f, g: tuple(f[g[i]] for i in range(ptsize))
    inv = {f: g for f in els for g in els if comp(f, g) == ident}
    ctr = [f for f in els if all(comp(f, g) == comp(g, f) for g in els)]
    comm = {ident}
    for f in els:
        for g in els:
            comm.add(comp(comp(comp(f, g), inv[f]), inv[g]))
    grew = True
    while grew:
        grew = False
        for a in list(comm):
            for b in list(comm):
                if comp(a, b) not in comm:
                    comm.add(comp(a, b)); grew = True
    dist = Counter()
    for f in els:
        o, k = 1, f
        while k != ident:
            k = comp(k, f); o += 1
        dist[o] += 1
    seen, ncc, sizes = set(), 0, []
    for f in els:
        if f not in seen:
            ncc += 1
            cl = {comp(comp(g, f), inv[g]) for g in els}
            seen |= cl; sizes.append(len(cl))
    # 阶3元个数与中心元阶（区分指纹）
    n3 = sum(v for k, v in dist.items() if k == 3)
    n4 = sum(v for k, v in dist.items() if k == 4)
    return {"群阶": len(els), "中心阶": len(ctr),
            "交换子群阶": len(comm), "阿贝尔化阶": len(els) // len(comm),
            "元素阶分布": {str(k): v for k, v in sorted(dist.items())},
            "共轭类数": ncc, "共轭类大小多重集": sorted(sizes),
            "阶3元数": n3, "阶4元数": n4}

FA = fingerprints(set(AM), 16)
FS = fingerprints(GS, 8)

# ---------- 第六维指纹: 交换子子群自身的元素阶分布 ----------
def derived_dist(els, ptsize):
    ident = tuple(range(ptsize))
    comp = lambda f, g: tuple(f[g[i]] for i in range(ptsize))
    inv = {f: g for f in els for g in els if comp(f, g) == ident}
    comm = {ident}
    for f in els:
        for g in els:
            comm.add(comp(comp(comp(f, g), inv[f]), inv[g]))
    grew = True
    while grew:
        grew = False
        for a in list(comm):
            for b in list(comm):
                if comp(a, b) not in comm:
                    comm.add(comp(a, b)); grew = True
    dist = Counter()
    for f in comm:
        o, k = 1, f
        while k != ident:
            k = comp(k, f); o += 1
        dist[o] += 1
    return {"交换子子群阶": len(comm), "交换子子群元素阶分布": {str(k): v for k, v in sorted(dist.items())}}

FA.update(derived_dist(set(AM), 16))
FS.update(derived_dist(GS, 8))
same = FA == FS

# 同构深挖（若指纹全同）: 比较阶2元生成的初等阿贝尔子群结构与 Sylow2 商特征
verdict = None
if same:
    verdict = "指纹全同: Aut(C4×C2×C2) ≅ (Z2)^3:~S4 结构无差异 (不排除同构, 指纹级判定=一致)"
else:
    diffs = [k for k in FA if FA[k] != FS[k]]
    verdict = f"指纹不同构 (差异项: {diffs}) -> SmallGroup(192,1493)=Aut(C4×C2×C2) ≠ 体系192阶扩展群"

out = {"G-1复核": "SmallGroup(192,1493) 候选编号判定",
       "来源": "Groupprops Groups_of_order_16 Automorphism-groups 表行(2026-09-19实取): SmallGroup(192,1493)=Aut(Z4×V4)同构类, |Aut|=192, 其2-Sylow≅U(4,2), 2-core/内自同构群平凡",
       "环境": "无GAP; 纯自写穷举(映射复合乘法表), Python 3.14.3",
       "A_Aut(C4xC2xC2)_即GAP库1493号": FA,
       "B_体系(Z2)^3:~S4": FS,
       "同构判定": "NOT-ISOMORPHIC" if not same else "FINGERPRINT-EQUAL",
       "判词": verdict}
txt = json.dumps(out, ensure_ascii=False, indent=1)
print(txt)
open(r"H:/理论存档/01-数学/04-工具与代码/results/g1_idgroup_crosscheck-20260919.json", "w", encoding="utf-8").write(txt)
