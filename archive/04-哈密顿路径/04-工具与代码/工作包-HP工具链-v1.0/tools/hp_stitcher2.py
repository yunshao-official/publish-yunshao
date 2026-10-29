# hp_stitcher2 v1.0 (2026-09-27) — 双碎片交换移动缝合器（格十二 v2）
# 核心移动: 拆两条路径真边 (a,b),(c,d) → 交叉重连 a-C1-d 与 c-C2-b（C1/C2 碎片内部HP桥接）→ 零断口消2碎片
# 单数尾巴: 三明治收尾（碎片+断口耦合）或留尾记账
# 验收: 独立三关甲
# 用法: python hp_stitcher2.py --edges ba.edges --walk walk.txt
import argparse, random, sys, time
import networkx as nx
from itertools import permutations

def frag_hp(sub, tl=10):
    k = sub.number_of_nodes()
    nodes = list(sub.nodes())
    if k == 1: return nodes
    if k <= 8:
        for perm in permutations(nodes):
            if all(sub.has_edge(perm[i], perm[i+1]) for i in range(k-1)):
                return list(perm)
        return None
    try:
        from ortools.sat.python import cp_model
        m = cp_model.CpModel(); lits = {}
        for u, v in sub.edges():
            lits[(u, v)] = m.NewBoolVar(f"x{u}_{v}"); lits[(v, u)] = m.NewBoolVar(f"x{v}_{u}")
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
        print(f"CP-SAT err: {e}")
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--walk", required=True)
    a = ap.parse_args()
    g = nx.Graph(); maxn = 0
    for l in open(a.edges):
        u, v = map(int, l.split()); g.add_edge(u, v); maxn = max(maxn, u, v)
    N = maxn + 1
    walk = [int(x) for x in open(a.walk) if x.strip()]
    t0 = time.time()
    nxt = {}; prv = {}
    for i in range(len(walk)-1):
        nxt[walk[i]] = walk[i+1]; prv[walk[i+1]] = walk[i]
    head, tail = walk[0], walk[-1]
    covered = set(walk)
    U = [v for v in range(N) if v not in covered]
    Gu = nx.Graph(); Gu.add_nodes_from(U)
    for v in U:
        for w in g.neighbors(v):
            if w not in covered: Gu.add_edge(v, w)
    comps = [set(c) for c in nx.connected_components(Gu)]
    print(f"walk {len(walk)} 缺口 {len(U)} 碎片 {len(comps)}", flush=True)
    # 预计算碎片内部HP（一次，端点自由——双碎片交换需要指定端点，故存：任意HP+端点置换尝试）
    frag_hp_cache = {}
    frag_iface = {}
    for ci, c in enumerate(comps):
        sub = Gu.subgraph(c)
        hp = frag_hp(sub)
        frag_hp_cache[ci] = hp
        iface = {}
        for v in c:
            for w in g.neighbors(v):
                if w in covered: iface.setdefault(w, set()).add(v)
        frag_iface[ci] = iface
    # 双碎片交换主循环
    def try_pair(ci, cj):
        """拆两条真边 (a,b),(c,d): a-Ci-d 桥接 + c-Cj-b 桥接"""
        hpi, hpj = frag_hp_cache[ci], frag_hp_cache[cj]
        if not hpi or not hpj: return False
        ii, ij = frag_iface[ci], frag_iface[cj]
        # Ci: 接口边 (a,u)∈E 且 (v,d)∈E, u..v 为 hpi 的某定向（HP可正反向）
        used_edges = set()
        # 枚举 Ci 的接口边对
        iedges = [(w, u) for w, us in ii.items() for u in us]
        jedges = [(w, u) for w, us in ij.items() for u in us]
        random.shuffle(iedges); random.shuffle(jedges)
        for (a, u), (d, v) in [(ie, je) for ie in iedges for je in jedges]:
            if a == d: continue
            b = nxt.get(a); c_ = nxt.get(d) if False else None
            # 需要两条路径真边: (a,b) 与 (c,d)——b=a的后继, d取jedges里的w(需有后继)
            if b is None: continue
            # (v,d) 需真边且 (c,d) 为路径真边——c 为 d 的前驱
            if not g.has_edge(v, d): continue
            c_ = prv.get(d)
            if c_ is None: continue
            if (a, b) in used_edges or (c_, d) in used_edges: continue
            if (a, b) == (c_, d): continue
            # Cj: (c,u2),(v2,b)∈E, u2..v2 为 hpj 某定向
            hpr = hpj[::-1]
            okj = False; fpi = None; fpj = None
            for fp1, s1, t1 in [(hpi, hpi[0], hpi[-1]), (hpi[::-1], hpi[-1], hpi[0])]:
                for fp2, s2, t2 in [(hpj, hpj[0], hpj[-1]), (hpj[::-1], hpj[-1], hpj[0])]:
                    if g.has_edge(a, fp1[0]) and g.has_edge(fp1[-1], d) and g.has_edge(c_, fp2[0]) and g.has_edge(fp2[-1], b):
                        fpi, fpj = fp1, fp2; okj = True; break
                if okj: break
            if not okj: continue
            # 执行: 拆 (a,b),(c_,d); 接 a-fpi-d 与 c_-fpj-b
            del nxt[a]; del prv[b]
            del nxt[c_]; del prv[d]
            cur = a
            for x in fpi: nxt[cur] = x; prv[x] = cur; cur = x
            nxt[cur] = d; prv[d] = cur
            cur = c_
            for x in fpj: nxt[cur] = x; prv[x] = cur; cur = x
            nxt[cur] = b; prv[b] = cur
            covered.update(fpi); covered.update(fpj)
            used_edges.add((a, b)); used_edges.add((c_, d))
            return True
        return False

    ci_list = list(range(len(comps)))
    random.shuffle(ci_list)
    remaining = set(ci_list)
    pairs = 0
    while len(remaining) >= 2:
        ci = remaining.pop()
        cj = None
        for cj_cand in list(remaining):
            if try_pair(ci, cj_cand):
                cj = cj_cand; break
        if cj is not None:
            remaining.discard(cj); pairs += 1
        else:
            remaining.add(ci)
            break  # 单飞失败, 简单退出（PoC不求全）
        if pairs % 200 == 0:
            print(f"  已配对 {pairs} 剩余 {len(remaining)}", flush=True)
    # 重建路径
    p = [head]; seen = {head}
    cur = head
    while cur in nxt:
        cur = nxt[cur]
        if cur in seen: break
        seen.add(cur); p.append(cur)
    brk = sum(1 for i in range(len(p)-1) if not g.has_edge(p[i], p[i+1]))
    ok = len(p) == N and len(set(p)) == N and brk == 0
    print(f"\n缝合结果: 路径 {len(p)}/{N} | 断口 {brk} | 配对消碎片 {pairs*2} | 剩余碎片 {len(remaining)}")
    print(f"独立三关甲: {'PASS' if ok else 'FAIL'} | 用时 {time.time()-t0:.0f}s")
    if ok:
        with open("stitched_final.txt", "w") as f:
            for v in p: f.write(f"{v}\n")
        print("严格HP已存 stitched_final.txt —— m=4@1e5 首破")

if __name__ == "__main__":
    main()
