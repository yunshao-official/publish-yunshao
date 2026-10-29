# hp_stitcher v1.0 (2026-09-27) — 碎片插链缝合器（格十二·m=4@1e5攻墙PoC）
# 输入: 引擎walk(--out, 带少量断口) + 引擎口径边表(dump_ba_edges) + 缺口碎片(G[U]分量)
# 移动: ①断口插入(断口(a,b)找u使a-u,u-b真边→消断口) ②真边打断插入(碎片C内部HP端点u,v,
#       找路径真边(w1,w2)使(w1,u),(v,w2)真边→打断插入, 零断口增量)
# 验收: 独立三关甲(verify_hp.py)——长度=N ∧ 无重复 ∧ 每步真边
# 用法: python hp_stitcher.py --edges ba.edges --walk walk.txt [--tl 60]
import argparse, random, sys, time
import networkx as nx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--walk", required=True)
    ap.add_argument("--tl", type=int, default=60, help="单片内部HP的CP-SAT时限秒")
    a = ap.parse_args()
    N = max(int(l.split()[0]) for l in open(a.edges) for l in [l]) if False else None
    g = nx.Graph()
    maxn = 0
    for l in open(a.edges):
        u, v = map(int, l.split()); g.add_edge(u, v); maxn = max(maxn, u, v)
    N = maxn + 1
    walk = [int(x) for x in open(a.walk) if x.strip()]
    print(f"图 {g.number_of_nodes()}点/{g.number_of_edges()}边 | walk {len(walk)}", flush=True)
    t0 = time.time()
    # 双向链表
    nxt = {}; prv = {}
    for i in range(len(walk)-1):
        nxt[walk[i]] = walk[i+1]; prv[walk[i+1]] = walk[i]
    head, tail = walk[0], walk[-1]
    path_edges = set((walk[i], walk[i+1]) for i in range(len(walk)-1))  # 有向真边(当前路径用)
    covered = set(walk)
    U = [v for v in range(N) if v not in covered]
    # 缺口碎片
    Gu = nx.Graph(); Gu.add_nodes_from(U)
    for v in U:
        for w in g.neighbors(v):
            if w not in covered:
                Gu.add_edge(v, w)
    comps = [set(c) for c in nx.connected_components(Gu)]
    print(f"缺口 {len(U)} 节点 / {len(comps)} 碎片", flush=True)
    stats = {"stitch_broken": 0, "stitch_gap": 0, "fail_frag": []}

    def frag_hp_path(gsub, tl):
        """碎片内部HP: 小图穷举(端点序), 大图CP-SAT — 返回节点序或None"""
        k = gsub.number_of_nodes()
        nodes = list(gsub.nodes())
        if k == 1:
            return nodes
        if k <= 8:
            from itertools import permutations
            for perm in permutations(nodes):
                if all(gsub.has_edge(perm[i], perm[i+1]) for i in range(k-1)):
                    return list(perm)
            return None
        # CP-SAT (工作包 AddCircuit 思路, 小模型)
        try:
            from ortools.sat.python import cp_model
            m = cp_model.CpModel()
            lits = {}
            for u, v in gsub.edges():
                lits[(u, v)] = m.NewBoolVar(f"a{u}_{v}"); lits[(v, u)] = m.NewBoolVar(f"a{v}_{u}")
            for v in nodes:
                lits[(v, v)] = m.NewBoolVar(f"self{v}")  # 自环=单点碎片占位
            # AddCircuit 允许自环跳过: 需要全走→禁自环
            for v in nodes:
                m.Add(lits[(v, v)] == 0)
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
            print(f"  CP-SAT err: {e}", flush=True)
        return None

    def insert_at(w1, frag_path, w2):
        """打断路径真边(w1->w2), 插入frag_path(首w尾w2已由调用方保证真边)"""
        global_next = nxt.get(w1)
        # 链表: w1 -> frag[0] -> ... -> frag[-1] -> w2
        nxt[w1] = frag_path[0]; prv[frag_path[0]] = w1
        for i in range(len(frag_path)-1):
            nxt[frag_path[i]] = frag_path[i+1]; prv[frag_path[i+1]] = frag_path[i]
        nxt[frag_path[-1]] = w2; prv[w2] = frag_path[-1]
        covered.update(frag_path)

    def frag_endpoints_feasible(c, gfrag):
        """枚举碎片内部HP与插入位: 返回(frag_path, w1, w2)或None"""
        nodes = list(c)
        # 接口边: 碎片节点->路径节点
        iface = {}
        for v in c:
            for w in g.neighbors(v):
                if w in covered:
                    iface.setdefault(w, []).append(v)
        # 试每条路径真边 (w1->w2): w1的接口碎片端点u + w2的接口碎片端点v, u..v为碎片内HP
        for w1, w2 in list(path_edges):
            if w1 not in iface or w2 not in iface:
                continue
            for u in iface.get(w1, []):
                for v in iface.get(w2, []):
                    if u == v and len(c) > 1:
                        continue
                    # u..v 碎片内HP: 对小碎片, 求以u为起v为终的HP
                    sub = gfrag.subgraph(c) if gfrag else None
                    fp = frag_hp_between(sub, u, v) if len(c) > 1 else [u]
                    if fp:
                        return fp, w1, w2
        return None

    def frag_hp_between(sub, u, v):
        """碎片内指定端点HP (小图DFS)"""
        k = sub.number_of_nodes()
        if k == 1:
            return [u] if u == v else None
        stack = [(u, [u], {u})]
        while stack:
            cur, p, vis = stack.pop()
            if len(p) == k:
                if cur == v:
                    return p
                continue
            for w in sub.neighbors(cur):
                if w not in vis:
                    stack.append((w, p+[w], vis | {w}))
        return None

    # 主循环: 逐碎片缝合
    frag_i = 0
    for c in sorted(comps, key=len):
        frag_i += 1
        sub = Gu.subgraph(c)
        # 端点可行的插入: 枚举接口对
        done = False
        iface = {}
        for v in c:
            for w in g.neighbors(v):
                if w in covered:
                    iface.setdefault(w, []).append(v)
        cand_edges = [(w1, w2) for (w1, w2) in path_edges if w1 in iface and w2 in iface]
        random.shuffle(cand_edges)
        for w1, w2 in cand_edges[:200]:
            for u in iface.get(w1, []):
                for v in iface.get(w2, []):
                    if len(c) == 1:
                        fp = [u] if u == v else None
                    else:
                        if u == v: continue
                        fp = frag_hp_between(sub, u, v)
                    if fp:
                        insert_at(w1, fp, w2)
                        stats["stitch_broken"] += 1
                        done = True
                        break
                if done: break
            if done: break
        if not done:
            stats["fail_frag"].append(len(c))
        if frag_i % 300 == 0:
            print(f"  进度 {frag_i}/{len(comps)} 已缝合{stats['stitch_broken']}", flush=True)
    # 重建路径并验算
    p = [head]
    seen = {head}
    while head in nxt:
        head = nxt[head]
        if head in seen: break
        seen.add(head); p.append(head)
    print(f"\n缝合结果: 路径长 {len(p)}/{N} | 断口(非真边步) {sum(1 for i in range(len(p)-1) if not g.has_edge(p[i], p[i+1]))} | 重复 {len(p)-len(set(p))} | 未缝合碎片 {stats['fail_frag']}")
    print(f"用时 {time.time()-t0:.0f}s")
    ok = len(p) == N and len(set(p)) == N and all(g.has_edge(p[i], p[i+1]) for i in range(len(p)-1))
    print(f"独立三关甲: {'PASS' if ok else 'FAIL'}")
    with open("stitched_path.txt", "w") as f:
        for v in p: f.write(f"{v}\n")
    print("路径已存 stitched_path.txt")

if __name__ == "__main__":
    main()
