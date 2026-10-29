# cpsat_hp_judge v1.0 (2026-09-27)
# 知世质问"你确定你用了最新的哈密顿解法?而不是重复造轮子"——格九手搓MILP五版的造轮子实锤补课：
# OR-Tools CP-SAT AddCircuit（哈密顿约束一等公民）复核格九两份INFEASIBLE证书+对照组
# 建模：加 depot 节点 n；弧(i,n),(n,i) 对每个真实节点存在=路径断开标记；AddCircuit 找经全部真实节点的环=HP
import sys, random, time
import networkx as nx
from ortools.sat.python import cp_model

def gen_ba_rebuild(N, m, seed):
    rng = random.Random(seed)
    g = nx.complete_graph(m)
    for u in range(m, N):
        nodes = list(g.nodes())
        weights = [g.degree(v) + 0.5 for v in nodes]
        total = sum(weights)
        for _ in range(m):
            pick = rng.random() * total
            acc = 0.0
            for v, w in zip(nodes, weights):
                acc += w
                if acc >= pick:
                    if v != u and not g.has_edge(u, v):
                        g.add_edge(u, v)
                    break
        g.add_node(u)
    return g

def hp_cpsat(g, tl):
    n = g.number_of_nodes()
    D = n  # depot
    mdl = cp_model.CpModel()
    lits = {}
    for u, v in g.edges():
        lits[(u, v)] = mdl.NewBoolVar(f"x{u}_{v}")
        lits[(v, u)] = mdl.NewBoolVar(f"x{v}_{u}")
    for i in range(n):  # depot 弧=断开标记
        lits[(i, D)] = mdl.NewBoolVar(f"d{i}e")
        lits[(D, i)] = mdl.NewBoolVar(f"d{i}s")
    arc_list = [(u, v, lit) for (u, v), lit in lits.items()]
    mdl.AddCircuit(arc_list)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = 8
    t1 = time.time()
    st = solver.Solve(mdl)
    dt = time.time() - t1
    name = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}.get(st, str(st))
    path = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}
        for (u, v), lit in lits.items():
            if u != D and v != D and solver.Value(lit):
                succ[u] = v
        # depot 后继=路径起点；前驱=终点
        starts = [i for i in range(n) if solver.Value(lits[(D, i)])]
        p = [starts[0]]
        while p[-1] in succ and len(p) <= n:
            p.append(succ[p[-1]])
        ok = len(p) == n and len(set(p)) == n and all(g.has_edge(p[i], p[i+1]) for i in range(n-1))
        path = (len(p), ok)
    return name, dt, path

cases = [(100, 58, 60), (100, 42, 60), (100, 43, 60), (100, 49, 60), (500, 49, 300)]
for N, seed, tl in cases:
    g = gen_ba_rebuild(N, 4, seed)
    name, dt, path = hp_cpsat(g, tl)
    print(f"seed{seed}@N={N}: CP-SAT {name} t={dt:.1f}s path={path}", flush=True)
