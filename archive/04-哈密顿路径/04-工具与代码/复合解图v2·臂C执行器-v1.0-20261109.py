# -*- coding: utf-8 -*-
# 复合解图v2·臂C执行器 v1.0（2026-11-09）——体系版胶囊分块管线
# 体系对应：谱体检（调和册）→零维代理分块（拓扑册N=0）→片内核CP-SAT（群论册对称性）→跨空间缝合（范畴册亏损态射）
# 靶：m4@1e5 s42 残局（锚 892）。过线：产物断口 < 892-30=862 且覆盖 100000 点。判负照记。
import sys, time, json
import networkx as nx
from networkx.algorithms.community import louvain_communities
from ortools.sat.python import cp_model

def load_edges(path, N=None):
    g = nx.Graph()
    for l in open(path):
        p = l.split()
        if len(p) >= 2:
            g.add_edge(int(p[0]), int(p[1]))
    if N:
        g.add_nodes_from(range(N))
    return g

def verify(g, P):
    n = g.number_of_nodes()
    if len(P) != n: return False, "长度%d≠%d" % (len(P), n)
    if len(set(P)) != n: return False, "重复"
    for i in range(n - 1):
        if not g.has_edge(P[i], P[i + 1]):
            return False, "第%d步非真边" % (i + 1)
    return True, "STRICT-PASS"

def capsule_exact(sub, tl=25, workers=8):
    """胶囊片内核 v1.1：D 虚拟节点编码（路径化——hp_cpsat_judge 现货同款）。
    v1.0 纯环编码判死≠路径判死（环严于路径），v1.1 修此 bug。"""
    nodes = sorted(sub.nodes())
    idx = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)
    if n <= 2:
        return list(nodes) if n < 2 or sub.has_edge(*nodes) else None
    mdl = cp_model.CpModel()
    D = n
    lits = {}
    for u, v in sub.edges():
        lits[(idx[u], idx[v])] = mdl.NewBoolVar("")
        lits[(idx[v], idx[u])] = mdl.NewBoolVar("")
    for i in range(n):
        lits[(i, D)] = mdl.NewBoolVar("")
        lits[(D, i)] = mdl.NewBoolVar("")
    mdl.AddCircuit([(u, v, lit) for (u, v), lit in lits.items()])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    st = solver.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    succ = {}
    start = None
    for (u, v), lit in lits.items():
        if solver.Value(lit):
            if u == D:
                start = v
            elif v != D:
                succ[u] = v
    if start is None:
        return None
    p = [start]
    while len(p) <= n:
        nxt = succ.get(p[-1])
        if nxt is None:
            break
        p.append(nxt)
    if len(p) != n:
        return None
    return [nodes[i] for i in p]

def split_community(g, comm, max_size, depth=0):
    """社区>max_size 时再切（Louvain 二次分块），返回社区列表。"""
    if len(comm) <= max_size or depth > 6:
        return [comm]
    sub = g.subgraph(comm)
    try:
        parts = louvain_communities(sub, seed=42 + depth, resolution=1.5)
    except Exception:
        parts = [comm]
    out = []
    for p in parts:
        out.extend(split_community(g, set(p), max_size, depth + 1))
    return out

def bridge_between(Pa_tail_set, Pb_head_set, g):
    """跨空间缝合：找真边 (a,b)，a∈Pa尾族，b∈Pb头族。返回 (a, b) 或 None。"""
    for a in Pa_tail_set:
        for b in g[a]:
            if b in Pb_head_set:
                return a, b
    return None

def posa_on(g, rng, rounds=300):
    """Pósa 扩张+旋转（臂A现货同款，供退化片用）。"""
    nodes = list(g.nodes())
    if not nodes:
        return []
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
        e = P[-1]
        idxs = [i for i in range(1, len(P) - 1) if g.has_edge(P[i], e)]
        if idxs:
            i = rng.choice(idxs)
            P = P[:i + 1] + [e] + P[i + 1:-1][::-1]
            continue
        s = P[0]
        idxs = [i for i in range(1, len(P) - 1) if g.has_edge(P[i], s)]
        if idxs:
            i = rng.choice(idxs)
            P = [s] + P[1:i][::-1] + P[i:]
            continue
        break
    rest = [v for v in nodes if v not in inP]
    return P + rest  # 剩余点挂尾（断口记账）


def main(edges_fn, out_fn, max_capsule=3000, tl_per_capsule=40):
    t0 = time.time()
    g = load_edges(edges_fn, 100000)
    N = g.number_of_nodes()
    E = g.number_of_edges()
    deg = dict(g.degree())
    degs = sorted(deg.values())
    print("图: N=%d E=%d 平均度=%.2f 度中位=%d max=%d" % (
        N, E, 2 * E / N, degs[len(degs)//2], degs[-1]), flush=True)

    # ① 零维代理分块（拓扑册 N=0：子结构卷成代理点）——v1.1 调粗防碎
    comms = louvain_communities(g, seed=42)
    comms = sorted((set(c) for c in comms), key=len, reverse=True)
    print("Louvain 社区: %d 个，大小 top5=%s" % (len(comms), [len(c) for c in comms[:5]]), flush=True)
    caps = []
    for c in comms:
        caps.extend(split_community(g, c, max_capsule, 0))
    caps = [c for c in caps if c]
    print("胶囊: %d 个，大小 min/中位/max = %d/%d/%d" % (
        len(caps), min(len(c) for c in caps),
        sorted(len(c) for c in caps)[len(caps)//2], max(len(c) for c in caps)), flush=True)

    # ② 片内核批量（群论册：片内精确解）
    cap_paths = {}
    t_cap0 = time.time()
    solved = failed = 0
    for ci, cap in enumerate(caps):
        sub = g.subgraph(cap)
        hp = capsule_exact(sub, tl=tl_per_capsule)
        if hp:
            cap_paths[ci] = hp
            solved += 1
        else:
            failed += 1
            # v1.2 退化：片内 Pósa（臂A现货——覆盖率高，断口远小于 sorted 序）
            rng = __import__('random').Random(42 + ci)
            pp = posa_on(sub, rng, rounds=5 * len(cap))
            cap_paths[ci] = pp
        if (ci + 1) % 20 == 0:
            print("  胶囊进度 %d/%d 解出%d 败%d (%.0fs)" % (
                ci + 1, len(caps), solved, failed, time.time() - t_cap0), flush=True)
    print("片内核: 解出 %d / 败 %d / 共 %d（%.0fs）" % (solved, failed, len(caps), time.time() - t_cap0), flush=True)

    # ③ 跨空间缝合（范畴册：代理图=胶囊为点、接口边为代理边；按生成树序缝合）
    cap_of = {}
    for ci, cap in enumerate(caps):
        for v in cap:
            cap_of[v] = ci
    proxy_edges = set()
    for u, v in g.edges():
        cu, cv = cap_of[u], cap_of[v]
        if cu != cv:
            proxy_edges.add((min(cu, cv), max(cu, cv)))
    PG = nx.Graph()
    PG.add_nodes_from(range(len(caps)))
    PG.add_edges_from(proxy_edges)
    print("代理图: %d 代理点 %d 接口边 连通分量=%d" % (
        PG.number_of_nodes(), PG.number_of_edges(), nx.number_connected_components(PG)), flush=True)

    # 按生成树序串胶囊
    order = []
    seen = set()
    def dfs(ci):
        seen.add(ci)
        order.append(ci)
        for nb in PG[ci]:
            if nb not in seen:
                dfs(nb)
    import sys as _sys
    _sys.setrecursionlimit(10000)
    for ci in range(len(caps)):
        if ci not in seen:
            dfs(ci)

    # 缝合拼装：当前链尾的邻居落在下一胶囊内→环序旋转使该邻居成头→真边接口；无桥则接+亏损记账
    full = list(cap_paths[order[0]])
    ring_flags = {order[0]: True}  # 片内 HP=环序（可任意旋转）；退化序=非环
    stitched_ok = 0
    misses = 0
    for nxt in order[1:]:
        seq = cap_paths[nxt]
        is_ring = True  # capsule_exact 解出的都是环序
        seqset = set(seq)
        tail = full[-1]
        best_pos = None
        for x in g[tail]:
            if x in seqset:
                pos = seq.index(x)
                if best_pos is None or pos < best_pos:
                    best_pos = pos
        if best_pos is not None and is_ring:
            seq2 = seq[best_pos:] + seq[:best_pos]  # 环序旋转：x 成头，且 (tail, x) 真边
            full = full + seq2
            stitched_ok += 1
        else:
            full = full + seq  # 无桥接口=亏损记账（断口）
            misses += 1
    dup = len(full) - len(set(full))
    print("拼装: 长度=%d 唯一点=%d 重复=%d 无桥接口=%d（%.0fs）" % (
        len(full), len(set(full)), dup, misses, time.time() - t0), flush=True)
    ok, why = verify(g, full)
    brks = 0 if ok else why
    # 断口数
    if not ok and "非真边" in str(why):
        pass
    brk_n = sum(1 for i in range(len(full) - 1) if not g.has_edge(full[i], full[i + 1]))
    cover = len(set(full))
    print("产物: 覆盖 %d/100000 断口 %d（锚 892，过线 862）判定=%s" % (
        cover, brk_n, "PASS" if (cover == 100000 and brk_n < 862) else "FAIL"), flush=True)
    json.dump({"N": N, "capsules": len(caps), "solved": solved, "failed": failed,
               "proxy_edges": PG.number_of_edges(), "misses": misses,
               "cover": cover, "dup": dup, "breaks": brk_n, "anchor": 892,
               "wall_s": round(time.time() - t0, 1)}, open(out_fn, "w"))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
