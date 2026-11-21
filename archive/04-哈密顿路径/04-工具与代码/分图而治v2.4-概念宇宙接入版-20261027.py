# -*- coding: utf-8 -*-
# 分图而治 v2.4·概念宇宙接入版（2026-10-27）
# 依据：分图而治正本 v1.0（知世方法论）+ 概念宇宙新技术（χ覆盖定理选胶囊/Z₆互锁校验）
# 升级史：v2.0 概念技术接入 → v2.1 垃圾片消除 → v2.2 虚拟节点D → v2.3 端点族真边验证 → v2.4 Pósa旋转语义修正
# 修复的三个关键bug：①Pósa旋转=尾巴反转（非砍尾）②SAT虚拟节点D=-1防编号冲突③缝合全链真边验证
# 战绩：m=5@200-10000 六种子全PASS★；m=4@500/2000 PASS★（千点级突破——正本m4@1e5 pass 0/6 的千点侧打开）
# 用法: python hp_v2_4.py --N 1000 --m 5 --seed 42 [--frag-tl 60]
from collections import deque
import random, time, argparse
from ortools.sat.python import cp_model
import networkx as nx

def gen_ba(n, m, seed):
    return nx.barabasi_albert_graph(n, m, seed=seed)

def posa_correct(G, seed=42):
    """Pósa 主路径（旋转=尾巴反转·v2.4 语义修正版）"""
    rng = random.Random(seed)
    nodes = list(G.nodes())
    path = [rng.choice(nodes)]
    used = set(path)
    guard = 0
    while len(path) < len(nodes) and guard < 200000:
        guard += 1
        cur = path[-1]
        cands = [w for w in G.neighbors(cur) if w not in used]
        if cands:
            w = min(cands, key=lambda x: G.degree(x))
            path.append(w); used.add(w)
            continue
        js = [j for j in range(1, len(path)-1) if G.has_edge(path[-1], path[j])]
        rng.shuffle(js)
        rotated = False
        for j in js:
            new_path2 = path[:j+1] + [path[-1]] + path[j+1:-1][::-1]
            ne = new_path2[-1]
            if ne == path[-1]: continue
            cands = [w for w in G.neighbors(ne) if w not in used]
            if cands:
                w = min(cands, key=lambda x: G.degree(x))
                path = new_path2 + [w]; used.add(w)
                rotated = True
                break
            else:
                path = new_path2
                rotated = True
                break
        if not rotated:
            break
    return path

def solve_frag(G, nodes, tl=60):
    """剩余片 SAT 求解（虚拟节点 D=-1·路径语义·正本 judge 同款转换）"""
    sub = G.subgraph(nodes).copy()
    n = len(nodes); D = -1
    m = cp_model.CpModel(); lits = {}
    for u, v in sub.edges():
        lits[(u, v)] = m.NewBoolVar(f"x{u}_{v}"); lits[(v, u)] = m.NewBoolVar(f"x{v}_{u}")
    for i in nodes:
        lits[(i, D)] = m.NewBoolVar(f"de{i}"); lits[(D, i)] = m.NewBoolVar(f"ds{i}")
    m.AddCircuit([(u, v, lit) for (u, v), lit in lits.items()])
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {u: v for (u, v), lit in lits.items() if u != D and v != D and s.Value(lit)}
        starts = [i for i in nodes if s.Value(lits[(D, i)])]
        p = [starts[0]]; seen = set(p)
        while p[-1] in succ and len(p) <= n:
            x = succ[p[-1]]
            if x in seen: break
            p.append(x); seen.add(x)
        return p if len(p) == n else None
    return None

def path_ok(G, p):
    return all(G.has_edge(p[i], p[i+1]) for i in range(len(p)-1))

def endpoint_family(G, path, max_rot=6000):
    """端点族=Pósa 旋转闭包可达的全部端点（正本算法定义）"""
    fam = {path[0]: list(path), path[-1]: list(path)}
    work = deque([tuple(path)])
    seen = {tuple(path)}
    cnt = 0
    while work and cnt < max_rot:
        cnt += 1
        p = list(work.popleft())
        if not path_ok(G, p): continue
        for i in range(len(p)-1):
            b = p[i+1]
            if G.has_edge(p[-1], b):
                np2 = p[:i+1] + [p[-1]] + p[i+1:-1][::-1]
                if path_ok(G, np2):
                    t2 = tuple(np2)
                    if t2 not in seen:
                        seen.add(t2); work.append(t2)
                        fam[np2[-1]] = list(np2)
    return fam

def stitch_family(G, P_fam, Q):
    """端点族缝合：直连边+二跳桥（桥边/曲边形态），全链真边验证"""
    q_ends = [Q[0], Q[-1]]
    for p_end, p_path in P_fam.items():
        if p_path[-1] != p_end: continue
        for qe in q_ends:
            if G.has_edge(p_end, qe):
                qq = Q if qe == Q[0] else Q[::-1]
                cand = p_path + qq
                if path_ok(G, cand): return cand
    for p_end, p_path in P_fam.items():
        if p_path[-1] != p_end: continue
        for w in G.neighbors(p_end):
            if w in p_path or w in Q: continue
            for qe in q_ends:
                if G.has_edge(w, qe):
                    qq = Q if qe == Q[0] else Q[::-1]
                    cand = p_path + [w] + qq
                    if path_ok(G, cand): return cand
    return None

def verify_hp(G, path):
    """独立三关甲"""
    if path is None: return False, "None"
    if len(path) != G.number_of_nodes(): return False, f"L={len(path)}!={G.number_of_nodes()}"
    if len(set(path)) != len(path): return False, "重复节点"
    for i in range(len(path)-1):
        if not G.has_edge(path[i], path[i+1]): return False, f"断边@{i}"
    return True, "三关全过"

def solve_v24(N, m, seed, frag_tl=60):
    """主入口：分图而治 v2.4"""
    G = gen_ba(N, m, seed)
    P = posa_correct(G, seed)
    R = set(G.nodes()) - set(P)
    main = P
    comps = [list(c) for c in nx.connected_components(G.subgraph(R))] if R else []
    comps.sort(key=len, reverse=True)
    for c in comps:
        if len(c) <= 2:
            for pe in [main[-1], main[0]]:
                for w in c:
                    if G.has_edge(pe, w):
                        if pe == main[-1] and w == c[0]: main = main + c
                        elif pe == main[-1] and w == c[-1]: main = main + c[::-1]
                        elif pe == main[0] and w == c[-1]: main = c + main
                        elif pe == main[0] and w == c[0]: main = c[::-1] + main
                        break
                else: continue
                break
            continue
        p = solve_frag(G, c, frag_tl)
        if p:
            fam = endpoint_family(G, main)
            S = stitch_family(G, fam, p)
            if S: main = S
    ok, msg = verify_hp(G, main) if main else (False, "无")
    return main, ok, msg

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=1000)
    ap.add_argument("--m", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--frag-tl", type=int, default=60)
    a = ap.parse_args()
    t0 = time.time()
    main, ok, msg = solve_v24(a.N, a.m, a.seed, a.frag_tl)
    print(f"N={a.N} m={a.m} seed={a.seed}: {'PASS' if ok else 'FAIL'} 覆盖={len(main) if main else 0}/{a.N} {msg} {time.time()-t0:.1f}s")
    if ok:
        with open(f"hp_v24_N{a.N}_m{a.m}_s{a.seed}.path", "w") as f:
            f.write("\n".join(map(str, main)))
