# hp_compressed v1.0 (2026-09-27) — 压缩图HP：碎片+切段→超级节点→CP-SAT AddCircuit→展开
# 格十三·头格实现 | 判据书: 格十三·压缩图HP判据书-v1.0-20260927.md
# Mimosa 注: random.Random 为实验可复现种子（预注册要求，非加密用途）；输出仅写脚本所在目录的 final_100k_hp.txt
import argparse, random, sys, time
import networkx as nx
from itertools import permutations
from ortools.sat.python import cp_model

def frag_hp(sub, tl=15):
    k = sub.number_of_nodes(); nodes = list(sub.nodes())
    if k == 1: return nodes
    if k <= 8:
        for perm in permutations(nodes):
            if all(sub.has_edge(perm[i], perm[i+1]) for i in range(k-1)):
                return list(perm)
        return None
    try:
        m = cp_model.CpModel(); lits = {}
        for u, v in sub.edges():
            lits[(u, v)] = m.NewBoolVar(f"a{u}_{v}"); lits[(v, u)] = m.NewBoolVar(f"a{v}_{u}")
        for v in nodes: lits[(v, v)] = m.NewBoolVar(f"s{v}")
        for v in nodes: m.Add(lits[(v, v)] == 0)
        m.AddCircuit([(u, v, l) for (u, v), l in lits.items()])
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl
        st = s.Solve(m)
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            succ = {u: v for (u, v), l in lits.items() if v != u and s.Value(l)}
            start = [v for v in nodes if v not in succ]
            p = [start[0]]
            while p[-1] in succ and len(p) <= k: p.append(succ[p[-1]])
            return p if len(p) == k else None
    except Exception as e:
        print(f"CP-SAT frag err: {e}")
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--walk", required=True)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--tl", type=int, default=600)
    a = ap.parse_args()
    g = nx.Graph(); maxn = 0
    for l in open(a.edges):
        u, v = map(int, l.split()); g.add_edge(u, v); maxn = max(maxn, u, v)
    N = maxn + 1
    walk = [int(x) for x in open(a.walk) if x.strip()]
    covered = set(walk)
    U = [v for v in range(N) if v not in covered]
    Gu = nx.Graph(); Gu.add_nodes_from(U)
    for v in U:
        for w in g.neighbors(v):
            if w not in covered: Gu.add_edge(v, w)
    comps = [set(c) for c in nx.connected_components(Gu)]
    print(f"碎片 {len(comps)}", flush=True)
    t0 = time.time()
    frag_paths = {}
    for ci, c in enumerate(comps):
        hp = frag_hp(Gu.subgraph(c))
        if hp is None:
            print(f"碎片{ci} 无内部HP (规模{len(c)})——剔除记账"); continue
        frag_paths[ci] = hp
    print(f"内部HP就绪 {len(frag_paths)}/{len(comps)} 用时{time.time()-t0:.0f}s", flush=True)

    for rnd in range(a.rounds):
        rng = random.Random(1000 + rnd)
        t1 = time.time()
        cuts = set()
        occupied = set()  # 节点级切口占用（每 walk 节点至多一切口，防单节点段断联）
        skipped = 0
        for ci, hp in frag_paths.items():
            ends = (hp[0], hp[-1])  # 切口必须绑定碎片HP端点（port），中部节点不可作接口
            iface = [(w, v) for v in ends for w in g.neighbors(v) if w in covered]
            rng.shuffle(iface)
            chosen = None
            for i in range(len(iface)):
                for j in range(len(iface)):
                    if i == j: continue
                    w1, u = iface[i]; w2, v = iface[j]
                    if w1 == w2: continue
                    if ("out", w1) in occupied or ("in", w2) in occupied: continue
                    if ("out", w2) in occupied or ("in", w1) in occupied: continue  # 防双切交叉成单节点段
                    chosen = (w1, u, v, w2); break
                if chosen: break
            if chosen is None:
                skipped += 1; continue  # 该碎片保持 walk 内原位（不切口不入环）
            w1, u, v, w2 = chosen
            occupied.add(("out", w1)); occupied.add(("in", w2))
            cuts.add(("out", w1)); cuts.add(("in", w2))
        if skipped:
            print(f"[轮{rnd}] 切口碰撞剔除碎片 {skipped}（不切口不入环，缺口留待收尾）", flush=True)
        segments = []; cur = [walk[0]]
        for i in range(len(walk)-1):
            x, y = walk[i], walk[i+1]
            cur.append(y)
            if ("out", x) in cuts or ("in", y) in cuts:
                segments.append(cur); cur = []
        if cur: segments.append(cur)
        print(f"[轮{rnd}] 段数 {len(segments)} 切口 {len(cuts)}", flush=True)
        nodes_meta = []
        for si, seg in enumerate(segments):
            nodes_meta.append(("seg", si, seg[0], seg[-1]))
        for ci, hp in frag_paths.items():
            nodes_meta.append(("frag", ci, hp[0], hp[-1]))
        owner = {}
        for si, seg in enumerate(segments):
            for v in seg: owner[v] = ("seg", si)
        for ci, hp in frag_paths.items():
            for v in hp: owner[v] = ("frag", ci)
        idx = {nm[0]+str(nm[1]): i for i, nm in enumerate(nodes_meta)}
        arcs = set()
        for i, (kind, sid, inp, outp) in enumerate(nodes_meta):
            for w in g.neighbors(outp):
                tgt = owner.get(w)
                if tgt is None: continue
                tk, tid = tgt
                j = idx[tk+str(tid)]
                if j == i: continue
                if g.has_edge(outp, nodes_meta[j][2]):
                    arcs.add((i, j))
        arcs = sorted(arcs)
        print(f"[轮{rnd}] 压缩图 {len(nodes_meta)}节点 {len(arcs)}弧", flush=True)
        m = cp_model.CpModel(); lits = {}
        for (i, j) in arcs:
            lits[(i, j)] = m.NewBoolVar(f"a{i}_{j}")
        for i in range(len(nodes_meta)):
            lits[(i, i)] = m.NewBoolVar(f"self{i}")
        m.AddCircuit([(i, j, l) for (i, j), l in lits.items()])
        for i in range(len(nodes_meta)): m.Add(lits[(i, i)] == 0)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = a.tl
        solver.parameters.num_search_workers = 8
        st = solver.Solve(m)
        name = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE",
                cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN"}.get(st, str(st))
        print(f"[轮{rnd}] CP-SAT: {name} t={time.time()-t1:.0f}s", flush=True)
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            succ = {}
            for (i, j), l in lits.items():
                if i != j and solver.Value(l): succ[i] = j
            starts = [i for i in range(len(nodes_meta)) if all(solver.Value(lits[(k, i)]) == 0 for k in range(len(nodes_meta)) if k != i and (k, i) in lits)]
            cur = starts[0] if starts else 0
            order = []
            for _ in range(len(nodes_meta)):
                order.append(cur); cur = succ.get(cur)
                if cur is None: break
            full = []
            for oi in order:
                kind, sid, inp, outp = nodes_meta[oi]
                if kind == "seg":
                    full.extend(segments[sid])
                else:
                    full.extend(frag_paths[sid])
            ok = len(full) == N and len(set(full)) == N and all(g.has_edge(full[i], full[i+1]) for i in range(N-1))
            print(f"展开长 {len(full)}/{N} 三关甲: {'PASS' if ok else 'FAIL'}")
            if ok:
                with open("final_100k_hp.txt", "w") as f:
                    for v in full: f.write(f"{v}\n")
                print("m=4@1e5 首破! 严格HP已存 final_100k_hp.txt")
                return
    print("全部轮次未出可行解（Z-2/Z-3 如实记账）")

if __name__ == "__main__":
    main()
