# hp_cpsat_judge v1.0 (2026-09-27) — HP存在性判定·CP-SAT AddCircuit标准工具
# 工作包-HP工具链 v1.0 成件 | 判定语义：OPTIMAL=有解(附路径) / INFEASIBLE=结构无哈密顿路(证书级) / UNKNOWN=超时未决
# 用法: python hp_cpsat_judge.py --N 100 --m 4 --seed 58 [--edges file] [--tl 300] [--workers 8]
# 口径: --edges 缺省=gen_ba_rebuild重建口径(白化42,与引擎内置同族不同序列,禁与档案互比)
import argparse, random, sys, time
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

def load_edges(path, N):
    g = nx.Graph()
    g.add_nodes_from(range(N))
    for l in open(path):
        a, b = l.split()
        g.add_edge(int(a), int(b))
    return g

def hp_cpsat(g, tl, workers):
    n = g.number_of_nodes()
    D = n
    mdl = cp_model.CpModel()
    lits = {}
    for u, v in g.edges():
        lits[(u, v)] = mdl.NewBoolVar(f"x{u}_{v}")
        lits[(v, u)] = mdl.NewBoolVar(f"x{v}_{u}")
    for i in range(n):
        lits[(i, D)] = mdl.NewBoolVar(f"d{i}e")
        lits[(D, i)] = mdl.NewBoolVar(f"d{i}s")
    mdl.AddCircuit([(u, v, lit) for (u, v), lit in lits.items()])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_search_workers = workers
    t1 = time.time()
    st = solver.Solve(mdl)
    dt = time.time() - t1
    name = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}.get(st, str(st))
    path = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {u: v for (u, v), lit in lits.items() if u != D and v != D and solver.Value(lit)}
        starts = [i for i in range(n) if solver.Value(lits[(D, i)])]
        p = [starts[0]]
        while p[-1] in succ and len(p) <= n:
            p.append(succ[p[-1]])
        ok = len(p) == n and len(set(p)) == n and all(g.has_edge(p[i], p[i+1]) for i in range(n-1))
        path = (len(p), ok)
    return name, dt, path

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--edges", default=None, help="外部边表(每行 'u v')；缺省=gen_ba_rebuild重建口径")
    ap.add_argument("--tl", type=int, default=300, help="时限秒")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    g = load_edges(a.edges, a.N) if a.edges else gen_ba_rebuild(a.N, a.m, a.seed)
    name, dt, path = hp_cpsat(g, a.tl, a.workers)
    print(f"CP-SAT判定: {name} | t={dt:.1f}s | N={g.number_of_nodes()} | path={path}")
