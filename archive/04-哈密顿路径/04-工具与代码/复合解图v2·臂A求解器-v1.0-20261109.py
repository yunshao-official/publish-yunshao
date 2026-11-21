# -*- coding: utf-8 -*-
# 复合解图v2·臂A求解器（知世方法论复合：拼接法+胶囊法SAT片内核+反转边等价交换）
# 打法=概念宇宙五脉冲对应：Pósa扩张=扩展脉冲 | 分片胶囊=收缩脉冲 | 缝合桥=转移脉冲 | 多种子重启=干涉脉冲
# 判据：解出=长度N+无重复+全真边（双verify：内建+对外包verify_path.py现货）
import sys, random, time
import networkx as nx
from ortools.sat.python import cp_model

def load_edges(path, n=None):
    g = nx.Graph()
    if n:
        g.add_nodes_from(range(n))
    for l in open(path):
        p = l.split()
        if len(p) >= 2:
            g.add_edge(int(p[0]), int(p[1]))
    return g

def verify(g, P):
    """三关甲：长度=N / 无重复 / 全真边。"""
    n = g.number_of_nodes()
    if len(P) != n:
        return False, "长度%d≠%d" % (len(P), n)
    if len(set(P)) != n:
        return False, "重复顶点"
    for i in range(n - 1):
        if not g.has_edge(P[i], P[i + 1]):
            return False, "第%d步非真边" % (i + 1)
    return True, "STRICT-PASS"

def capsule_exact(sub, tl=20, workers=8):
    """胶囊片内核：片内 CP-SAT AddCircuit 精确解，返回片内 HP 或 None（v8.5定案'胶囊+SAT片内核'正路）。"""
    nodes = sorted(sub.nodes())
    idx = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)
    if n <= 1:
        return nodes
    if n == 2:
        return nodes if sub.has_edge(*nodes) else None
    mdl = cp_model.CpModel()
    lits = {}
    for u, v in sub.edges():
        lits[(idx[u], idx[v])] = mdl.NewBoolVar("")
        lits[(idx[v], idx[u])] = mdl.NewBoolVar("")
    mdl.AddCircuit([(u, v, lit) for (u, v), lit in lits.items()])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    st = solver.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    succ = {}
    for (u, v), lit in lits.items():
        if solver.Value(lit):
            succ[u] = v
    ring = [0]
    while len(ring) <= n:
        nxt = succ.get(ring[-1])
        if nxt is None or nxt == 0:
            break
        ring.append(nxt)
    if len(ring) != n:
        return None  # 多环=片内无HP（胶囊判死，本片跳过）
    return [nodes[i] for i in ring]

def posa(g, rng, rounds=300):
    """扩展脉冲：Pósa 扩张+旋转闭包，返回主路径（可能不满覆盖）。"""
    nodes = list(g.nodes())
    rng.shuffle(nodes)
    P = [nodes[0]]
    inP = {nodes[0]}
    for _ in range(rounds):
        grew = False
        for end, side in ((P[-1], 1), (P[0], 0)):
            cands = [v for v in g[end] if v not in inP]
            if cands:
                v = rng.choice(cands)
                if side:
                    P.append(v)
                else:
                    P.insert(0, v)
                inP.add(v)
                grew = True
                break
        if grew:
            continue
        end = P[-1]
        idxs = [i for i in range(1, len(P) - 1) if g.has_edge(P[i], end)]
        if idxs:
            i = rng.choice(idxs)
            P = P[:i + 1] + [end] + P[i + 1:-1][::-1]
            continue
        start = P[0]
        idxs = [i for i in range(1, len(P) - 1) if g.has_edge(P[i], start)]
        if idxs:
            i = rng.choice(idxs)
            P = [start] + P[1:i][::-1] + P[i:]
            continue
        break  # 压不动
    return P

def endpoints_family(P, g):
    """端点族=P两端+旋转可达端（邻接端点的路径内点，旋转一步即成端）。"""
    fam = [P[0], P[-1]]
    for end in (P[0], P[-1]):
        for x in g[end]:
            if x in P:
                i = P.index(x)
                if 0 < i < len(P) - 1:
                    fam.append(x)
    return fam

def stitch(P, Q, g):
    """转移脉冲：反转等价交换+一跳真桥+二跳曲桥。返回缝合后新路径或 None。"""
    for Ps in (P, P[::-1]):
        for Qs in (Q, Q[::-1]):
            pfa, qfa = endpoints_family(Ps, g), endpoints_family(Qs, g)
            # 一跳：真边 p-q
            for p in (Ps[-1],) + tuple(pfa):
                for q in (Qs[0],) + tuple(qfa):
                    if g.has_edge(p, q):
                        # 旋转 Ps 使 p 成尾（p=邻端点一步旋转）
                        Pp = rotate_to_end(Ps, p, g)
                        Qq = rotate_to_front(Qs, q, g)
                        if Pp is not None and Qq is not None:
                            cand = Pp + Qq
                            if len(cand) == len(set(cand)):
                                return cand
            # 二跳：p-c-q（c∈Q 内部，插入中间）
            for p in (Ps[-1],) + tuple(pfa):
                for c in g[p]:
                    if c in Qs:
                        ci = Qs.index(c)
                        # Q 分两段：c 前段反向接 p，c 后段直连
                        left, right = Qs[:ci], Qs[ci:]
                        if left and g.has_edge(p, left[-1]):
                            cand = (rotate_to_end(Ps, p, g) or Ps) + left[::-1] + right
                        elif right and g.has_edge(p, right[0]):
                            cand = (rotate_to_end(Ps, p, g) or Ps) + left + right
                        else:
                            continue
                        if len(cand) == len(set(cand)) and len(cand) > len(P):
                            ok = all(g.has_edge(cand[i], cand[i + 1]) for i in range(len(cand) - 1))
                            if ok:
                                return cand
    return None

def rotate_to_end(P, p, g):
    """旋转使 p 成为路径尾（p 为端点族成员：p=P尾 或 p 邻接 P尾）。"""
    if P[-1] == p:
        return P[:]
    if g.has_edge(P[-1], p):
        i = P.index(p)
        return P[:i + 1] + [P[-1]] + P[i + 1:-1][::-1]
    return None

def rotate_to_front(P, p, g):
    """旋转使 p 成为路径头 = 对反向路径 rotate_to_end 后再反转（Pósa 旋转对称操作）。"""
    if P[0] == p:
        return P[:]
    r = rotate_to_end(P[::-1], p, g)
    return r[::-1] if r else None

def solve(g, budget_sec=60, seed=42):
    """复合主循环：主路径→剩余图片内精确解（胶囊）→缝合→verify。压到底无中间态。"""
    t0 = time.time()
    rng = random.Random(seed)
    best = None
    restart = 0
    while time.time() - t0 < budget_sec:
        restart += 1
        P = posa(g, rng)
        used = set(P)
        progress = True
        while progress and len(P) < g.number_of_nodes() and time.time() - t0 < budget_sec:
            progress = False
            rest = [v for v in g.nodes() if v not in used]
            sub = g.subgraph(rest)
            for C in sorted(nx.connected_components(sub), key=len, reverse=True):
                Qh = capsule_exact(g.subgraph(C).copy(), tl=15)
                if Qh is None:
                    Qh = posa(g.subgraph(C).copy(), rng)  # 胶囊判死→片内 Pósa 退化
                S = stitch(P, Qh, g)
                if S is not None and len(S) > len(P):
                    ok, why = verify(g, S)
                    if ok:
                        P = S
                        used = set(P)
                        progress = True
                        break
        if len(P) == g.number_of_nodes():
            ok, why = verify(g, P)
            if ok:
                return P, restart, time.time() - t0
        if best is None or len(P) > len(best):
            best = P[:]
    return None, restart, time.time() - t0

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    edges = sys.argv[2] if len(sys.argv) > 2 else None
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    g = load_edges(edges, N)
    P, restart, dt = solve(g, budget, seed)
    if P:
        ok, why = verify(g, P)
        print("SOLVED restart=%d t=%.1fs len=%d %s" % (restart, dt, len(P), why))
        print(",".join(map(str, P)))
    else:
        print("UNsolved（压不动） restart=%d t=%.1fs 覆盖=%d/%d" % (restart, dt, len(best) if best else 0, N))
