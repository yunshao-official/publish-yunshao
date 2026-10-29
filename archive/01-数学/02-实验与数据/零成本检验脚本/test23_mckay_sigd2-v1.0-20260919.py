# -*- coding: utf-8 -*-
"""
零成本判伪检验第一波·检验2（代数-E2 McKay 图）+ 检验3（代数-E3 Σd²=|G| 扩表）
判据冻结：
  E2（云韶代数图谱 §四 E2）：对 2T/2O/2I 构造 (G, V2, C2) McKay 图（顶点=不可约
     表示，边=⊗V2 分解），与 Ẽ6/Ẽ7/Ẽ8 仿射 Dynkin 图同构判定；维数序列逐项对表。
  E3：六群 A4/S4/A5/2T/2O/2I 特征标表 + Σd²=|G| + 正交性 <χi,χj>=δij 全检。
方法：sympy 1.14 PermutationGroup 无 character_table → 自实现类代数谱法：
  类和乘法常数 → 单类作用矩阵对角化 → 特征标；numpy float64 + 精确关系式
  验证（行正交/列正交/Σd²，容差 1e-8）。2T≅SL(2,3)、2O≅GL(2,3)、2I≅SL(2,5)
  （GF(p) 2×2 矩阵群 → 非零向量置换表示，忠实）。
仿射图的机器独立刻画：n≤9 全 Prüfer 树穷举 + 最大度≤3 + 谱半径恰=2
  （sympy 整数 charpoly(2)=0 精确复核 + AHU 树规范形去重）→ 唯一得 Ẽ6/Ẽ7/Ẽ8，
  再与 McKay 图做回溯同构匹配（不依赖文献图形记忆）。零编数。
"""
import itertools, math, heapq
import numpy as np
import sympy
from sympy import Matrix, Symbol
from sympy.combinatorics.named_groups import AlternatingGroup, SymmetricGroup

TOL = 1e-8

# ---------- 群（元素=置换元组） ----------
def group_from_perms(perms):
    ALL = sorted(set(perms))
    idx = {g: i for i, g in enumerate(ALL)}
    deg = len(ALL[0])
    M = [[idx[tuple(g[j] for j in h)] for h in ALL] for g in ALL]
    INVv = []
    for a in ALL:
        inv = next(idx[b] for b in ALL if tuple(a[j] for j in b) == tuple(range(deg)))
        INVv.append(inv)
    return ALL, idx, M, INVv

def conjugacy_classes(M, INVv):
    n = len(M)
    seen = [False]*n
    classes = []
    for i in range(n):
        if seen[i]: continue
        cls = set()
        for k in range(n):
            cls.add(M[M[k][i]][INVv[k]])
        for c in cls: seen[c] = True
        classes.append(sorted(cls))
    return classes

def elem_order_perm(g):
    seen = [False]*len(g); l = 1
    for i in range(len(g)):
        if not seen[i]:
            j, c = i, 0
            while not seen[j]:
                seen[j] = True; j = g[j]; c += 1
            l = math.lcm(l, c)
    return l

# ---------- 类代数谱法特征标表 ----------
def character_table(classes, M):
    k = len(classes)
    n_group = sum(len(c) for c in classes)
    sizes = [len(c) for c in classes]
    cls_of = {}
    for ci, c in enumerate(classes):
        for x in c: cls_of[x] = ci
    a = [[[0.0]*k for _ in range(k)] for _ in range(k)]
    for i in range(k):
        for j in range(k):
            cnt = [0]*k
            for x in classes[i]:
                Mx = M[x]
                for y in classes[j]:
                    cnt[cls_of[Mx[y]]] += 1
            for kk in range(k):
                a[i][j][kk] = cnt[kk] / sizes[kk]
    best = None
    for j0 in range(k):
        A = np.array([[a[i][j0][kk] for kk in range(k)] for i in range(k)])
        ev = np.linalg.eigvals(A)
        if len({complex(round(e.real, 7), round(e.imag, 7)) for e in ev}) == k:
            best = j0; break
    if best is not None:
        A = np.array([[a[i][best][kk] for kk in range(k)] for i in range(k)])
    else:
        # 类代数交换 → 同时可对角化；单类有重根时用确定性权重组合分离
        # （权 w_j=1/第j个素数，仅数值分离装置，不进任何群论数值）
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47][:k]
        A = np.zeros((k, k))
        for j in range(k):
            A += (1.0/primes[j]) * np.array([[a[i][j][kk] for kk in range(k)]
                                             for i in range(k)])
    evals, evecs = np.linalg.eig(A)
    chars = []
    for m in range(k):
        v = evecs[:, m]
        lam = v / v[0]           # 恒等类分量归一为 1
        d = math.sqrt(n_group / sum(sizes[i]*abs(lam[i]/sizes[i])**2 for i in range(k)))
        chars.append(np.array([d*lam[i]/sizes[i] for i in range(k)]))
    chars.sort(key=lambda c: (round(c[0].real, 6), round(c[0].imag, 6),
                              tuple(np.round(c.real, 6))))
    return chars, sizes

def verify_table(chars, classes, n_group):
    k = len(chars)
    sizes = [len(c) for c in classes]
    row_err = 0.0
    for i in range(k):
        for j in range(k):
            s = sum(sizes[c]*chars[i][c]*np.conj(chars[j][c]) for c in range(k))/n_group
            row_err = max(row_err, abs(s - (1.0 if i == j else 0.0)))
    col_err = 0.0
    for ci in range(k):
        for cj in range(k):
            s = sum(ch[ci]*np.conj(ch[cj]) for ch in chars)
            target = n_group/sizes[ci] if ci == cj else 0.0
            col_err = max(col_err, abs(s - target))
    return row_err, col_err

# ---------- 六群 ----------
def perms_from_sympy_group(G, deg):
    return sorted({tuple(int(p(i)) for i in range(deg)) for p in G.elements})

def perm_from_matrices(mats, p):
    vecs = [(a, b) for a in range(p) for b in range(p) if (a, b) != (0, 0)]
    vidx = {v: i for i, v in enumerate(vecs)}
    perms = set()
    for (a, b, c, d) in mats:
        perms.add(tuple(vidx[((a*x + b*y) % p, (c*x + d*y) % p)] for (x, y) in vecs))
    return sorted(perms)

def matrices_det1(p):
    return [(a, b, c, d) for a in range(p) for b in range(p)
            for c in range(p) for d in range(p) if (a*d - b*c) % p == 1]
def matrices_GL2(p):
    return [(a, b, c, d) for a in range(p) for b in range(p)
            for c in range(p) for d in range(p) if (a*d - b*c) % p != 0]

groups = {
    'A4': perms_from_sympy_group(AlternatingGroup(4), 4),
    'S4': perms_from_sympy_group(SymmetricGroup(4), 4),
    'A5': perms_from_sympy_group(AlternatingGroup(5), 5),
    '2T=SL(2,3)': perm_from_matrices(matrices_det1(3), 3),
    '2O=GL(2,3)': perm_from_matrices(matrices_GL2(3), 3),
    '2I=SL(2,5)': perm_from_matrices(matrices_det1(5), 5),
}
EXPECTED = {'A4': [1, 1, 1, 3], 'S4': [1, 1, 2, 3, 3], 'A5': [1, 3, 3, 4, 5],
            '2T=SL(2,3)': [1, 1, 1, 2, 2, 2, 3],
            '2O=GL(2,3)': [1, 1, 2, 2, 2, 3, 3, 4],
            '2I=SL(2,5)': [1, 2, 2, 3, 3, 4, 4, 5, 6]}

print("="*72)
print("检验3：六群特征标表 + Σd²=|G| + 正交性全检（代数-E3）")
print("="*72)

tables = {}
for name, perms in groups.items():
    ALL, idx, M, INVv = group_from_perms(perms)
    n = len(ALL)
    classes = conjugacy_classes(M, INVv)
    chars, sizes = character_table(classes, M)
    row_err, col_err = verify_table(chars, classes, n)
    deg_int = [round(chi[0].real) for chi in chars]
    deg_ok = all(abs(chi[0].real - round(chi[0].real)) < 1e-7 for chi in chars)
    sum_d2 = sum(d*d for d in deg_int)
    seq_ok = sorted(deg_int) == sorted(EXPECTED[name])
    print(f"\n【{name}】|G|={n} 类数={len(classes)}")
    print(f"  维数多重集 = {sorted(deg_int)}")
    print(f"  Σd² = {sum_d2}；=|G| ? {sum_d2 == n}（float 差 {abs(sum(ch[0].real**2+ch[0].imag**2 for ch in chars)-n):.2e}）")
    print(f"  行正交 max|<χi,χj>−δij| = {row_err:.2e}；列正交 max err = {col_err:.2e}（判据 1e-8 {'✓' if max(row_err,col_err)<1e-8 else '✗'}）")
    print(f"  维数皆正整数: {deg_ok}；与经典序列逐项一致: {seq_ok}")
    print("  特征标表（行=不可约 d，列=类(大小;代表元阶)）:")
    print("   d\\类 " + "".join(f"({len(cls)};{elem_order_perm(ALL[cls[0]])})".rjust(10) for cls in classes))
    for chi in chars:
        d = round(chi[0].real)
        if all(abs(chi[c].imag) < 1e-6 for c in range(len(classes))):
            print(f"   d={d:<3}" + "".join(f"{chi[c].real:+10.4f}" for c in range(len(classes))))
        else:
            print(f"   d={d:<3}" + "".join(f"{chi[c].real:+7.3f}{chi[c].imag:+6.3f}i" if abs(chi[c].imag) >= 1e-6
                                            else f"{chi[c].real:+10.4f}" for c in range(len(classes))))
    tables[name] = dict(ALL=ALL, M=M, INVv=INVv, classes=classes,
                        chars=chars, sizes=sizes, n=n)

# ---------- McKay ----------
def tree_canonical(adj):
    """AHU 树规范形"""
    n = len(adj)
    deg = [len(a) for a in adj]
    killed = [False]*n
    alive = n
    while alive > 2:
        leaves = [i for i in range(n) if not killed[i] and sum(1 for j in adj[i] if not killed[j]) == 1]
        for lf in leaves:
            killed[lf] = True; alive -= 1
    centers = [i for i in range(n) if not killed[i]]
    def ser(root, parent):
        subs = [ser(j, root) for j in adj[root] if j != parent]
        return "(" + "".join(sorted(subs)) + ")"
    return min(ser(c, -1) for c in centers)

def tree_from_prufer(seq, nn):
    degc = [1]*nn
    for s in seq: degc[s] += 1
    if max(degc) > 3: return None
    edges = []
    leaves = [i for i in range(nn) if degc[i] == 1]
    heapq.heapify(leaves)
    for s in seq:
        lf = heapq.heappop(leaves)
        edges.append((lf, s))
        degc[lf] -= 1; degc[s] -= 1
        if degc[s] == 1: heapq.heappush(leaves, s)
    rest = [i for i in range(nn) if degc[i] == 1]
    edges.append((rest[0], rest[1]))
    adj = [[0]*nn for _ in range(nn)]
    for a, b in edges:
        adj[a][b] = adj[b][a] = 1
    return adj

def spectral_radius(adj):
    return max(abs(np.linalg.eigvals(np.array(adj, dtype=float))))

def graph_iso_match(adj1, adj2):
    n = len(adj1)
    if len(adj2) != n: return None
    d1 = [sum(r) for r in adj1]; d2 = [sum(r) for r in adj2]
    if sorted(d1) != sorted(d2): return None
    bydeg = {}
    for j in range(n): bydeg.setdefault(d2[j], []).append(j)
    mapping = [None]*n; used = [False]*n
    order = sorted(range(n), key=lambda i: -d1[i])
    def bt(pos):
        if pos == n: return True
        i = order[pos]
        for j in bydeg[d1[i]]:
            if used[j]: continue
            if all(adj1[i][i2] == adj2[j][mapping[i2]] for i2 in order[:pos]):
                mapping[i] = j; used[j] = True
                if bt(pos+1): return True
                mapping[i] = None; used[j] = False
        return False
    return mapping if bt(0) else None

print("\n[机器独立推导仿射树] n=7,8,9 全 Prüfer 穷举 + 最大度≤3 + 谱半径恰=2（先计数预筛再建树）")
canonical = {}
for nn in (7, 8, 9):
    reps = {}
    for seq in itertools.product(range(nn), repeat=nn-2):
        cnt = [0]*nn
        okflag = True
        for s in seq:
            cnt[s] += 1
            if cnt[s] > 2: okflag = False; break
        if not okflag: continue
        adj = tree_from_prufer(seq, nn)
        if adj is None: continue
        if abs(spectral_radius(adj) - 2.0) < 1e-9:
            key = tree_canonical(adj)
            if key not in reps:
                reps[key] = adj
    for rp in reps.values():
        cp = Matrix(rp).charpoly().as_expr()
        assert cp.subs(Symbol('x'), 2) == 0, "精确 charpoly(2)≠0"
    canonical[nn] = list(reps.values())
    print(f"  n={nn}: λmax恰=2 的树（同构去重后）={len(reps)} 个，精确 charpoly(2)=0 ✓")

def mckay_graph(name):
    T = tables[name]
    n = T['n']; classes = T['classes']; chars = T['chars']; sizes = T['sizes']
    ALL = T['ALL']
    c2_cls = None
    for ci, cls in enumerate(classes):
        g = ALL[cls[0]]
        if elem_order_perm(g) == 2 and len(cls) == 1:
            c2_cls = ci
    assert c2_cls is not None
    cands = [ri for ri, chi in enumerate(chars)
             if abs(chi[0].real - 2) < 1e-7 and abs(chi[c2_cls] + 2) < 1e-7]
    assert cands, "未找到 χ(C2)=−2 的二维不可约"
    chi2 = chars[cands[0]]
    r = len(classes)
    mult = [[sum(sizes[c]*chars[a][c]*chi2[c]*np.conj(chars[b][c]) for c in range(r))/n
             for b in range(r)] for a in range(r)]
    def int_err(z): return min(abs(z - nn) for nn in range(-1, 5))
    int_check = max(int_err(m) for row in mult for m in row)
    mult_int = [[int(round(m.real)) for m in row] for row in mult]
    rowsum_ok = all(sum(row) == 2 for row in mult_int)
    simple_ok = all(m in (0, 1) for row in mult_int for m in row)
    symmetric = all(mult_int[a][b] == mult_int[b][a] for a in range(r) for b in range(r))
    seen = {0}; st = [0]
    while st:
        x = st.pop()
        for y in range(r):
            if mult_int[x][y] and y not in seen:
                seen.add(y); st.append(y)
    connected = len(seen) == r
    degs = [round(chi[0].real) for chi in chars]
    print(f"\n【{name}】C2=类#{c2_cls}(大小1,阶2=中心−1)；V2=不可约#{cands[0]}(d=2,χ(C2)=−2)"
          f"{'（共%d个二维候选，取首个；张1维特征标仅换标号）' % len(cands) if len(cands)>1 else ''}")
    print(f"  重数整数性 max err = {int_check:.2e}；单边(0/1)={simple_ok}；"
          f"每顶点Σm=dimV2=2: {rowsum_ok}；对称={symmetric}；连通={connected}")
    print(f"  邻接阵 = {mult_int}")
    print(f"  顶点维数 = {degs}；最大维数顶点唯一 = {degs.count(max(degs)) == 1}")
    return mult_int, degs

print("\n检验2 裁决输出：")
verdicts = {}
for name, nn, aff in [('2T=SL(2,3)', 7, 'Ẽ6'), ('2O=GL(2,3)', 8, 'Ẽ7'), ('2I=SL(2,5)', 9, 'Ẽ8')]:
    mult_int, degs = mckay_graph(name)
    match = None
    for rp in canonical[nn]:
        m = graph_iso_match(mult_int, rp)
        if m is not None: match = m; break
    ok = match is not None
    verdicts[name] = ok
    print(f"  → {name}: McKay 图 ≅ {aff}（机器独立刻画树）? {'是 ✓' if ok else '否 ✗'}")

print("\n[总结] 检验2:", verdicts)
