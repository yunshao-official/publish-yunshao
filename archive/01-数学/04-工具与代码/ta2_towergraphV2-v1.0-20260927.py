# -*- coding: utf-8 -*-
"""
第二轮·实验B：塔图连接规则 v2——元素阶谱共享
规则（冻结）：顶点=前8座塔(q=7..31)；连边 iff 两塔元素阶谱交集含≥3个非平凡阶（敏感档2/4）
阶谱来源：orbit 实算 q=7,11,13,17,19,23（验证）+ 闭式 {p,2,整除(q±1)/2}（q=29,31）
检验序列：连通→定理A容量→λ2→哈密顿回溯；对照=同8塔 gcd≥12 图
预注册：《黎曼猜想·通俗图解-v4.0-20260927》§十二（NTFS 时间戳在先）
"""
import numpy as np, sympy as sp, networkx as nx, json, platform, datetime
from networkx.algorithms.flow import maximum_flow

def psl_elements(q):
    E = []
    for a in range(1, q):
        ia = pow(a, -1, q)
        for b in range(q):
            for c in range(q):
                d = ((1 + b * c) * ia) % q
                E.append((a, b, c, d))
    for b in range(1, q):
        c = (-pow(b, -1, q)) % q
        for d in range(q):
            E.append((0, b, c, d))
    S = set()
    for (a, b, c, d) in E:
        neg = ((-a) % q, (-b) % q, (-c) % q, (-d) % q)
        S.add(min((a, b, c, d), neg))
    return list(S)

def mul(x, y, q):
    (a, b, c, d), (e, f, g, h) = x, y
    A, B, C, D = a*e+b*g, a*f+b*h, c*e+d*g, c*f+d*h
    neg = ((-A) % q, (-B) % q, (-C) % q, (-D) % q)
    return min((A % q, B % q, C % q, D % q), neg)

def inv(x, q):
    a, b, c, d = x
    return (d % q, (-b) % q, (-c) % q, a % q)

def element_order_spectrum(q):
    """orbit 共轭类 → 每类代表元求阶 → 阶谱集合"""
    E = psl_elements(q)
    I = ((1 % q, 0, 0, 1 % q))
    seen, spec = set(), set()
    for x in E:
        if x in seen: continue
        orb = {mul(g, mul(x, inv(g, q), q), q) for g in E}
        seen |= orb
        g, k = x, 1
        while g != I:
            g = mul(g, x, q); k += 1
            if k > 4 * q * q: break
        if k > 1: spec.add(k)
    return spec

def closed_form_spectrum(q):
    spec = {2, q}
    for d in sp.divisors((q - 1) // 2): spec.add(int(d))
    for d in sp.divisors((q + 1) // 2): spec.add(int(d))
    spec.discard(1)
    return spec

print("===== 实验 B：元素阶谱实算 vs 闭式 =====")
specs, ok = {}, True
for q in [7, 11, 13, 17, 19, 23]:
    real = element_order_spectrum(q)
    cf = closed_form_spectrum(q)
    match = real == cf
    ok &= match
    specs[q] = sorted(real)
    print(f"PSL(2,{q}): 实算{sorted(real)} 闭式{sorted(cf)} {'✓' if match else '✗'}")
for q in [29, 31]:
    specs[q] = sorted(closed_form_spectrum(q))
    print(f"PSL(2,{q}): 闭式档（实算超预算）{specs[q]}")
print(f"闭式验证：q≤23 六塔{'全中' if ok else '有MISMATCH——29/31 档失效需实算'}")

def build_graph(th, rule="v2"):
    qs = [7, 11, 13, 17, 19, 23, 29, 31]
    G = nx.Graph(); G.add_nodes_from(qs)
    for i in range(len(qs)):
        for j in range(i+1, len(qs)):
            if rule == "v2":
                inter = set(specs[qs[i]]) & set(specs[qs[j]])
                if len(inter) >= th: G.add_edge(qs[i], qs[j])
            else:
                o = lambda x: x * (x*x - 1) // 2
                if sp.gcd(o(qs[i]), o(qs[j])) >= th: G.add_edge(qs[i], qs[j])
    return G

def capacity_kill(G):
    degs = dict(G.degree()); d_min = min(degs.values())
    L = [v for v in G if degs[v] == d_min]
    indep = (len(L) < 2) or (G.subgraph(L).number_of_edges() == 0)
    if not indep:
        keep, blocked = [], set()
        for v in sorted(L, key=lambda v: degs[v]):
            if v not in blocked: keep.append(v); blocked |= set(G.neighbors(v)) | {v}
        L = keep
    if len(L) < 2: return False, {"L_size": len(L), "note": "无靶"}
    D = nx.DiGraph(); nbrs = sorted({u for l in L for u in G.neighbors(l)})
    D.add_edges_from([("S", l, {"capacity": 2}) for l in L])
    for l in L:
        for u in G.neighbors(l): D.add_edge(l, u, capacity=1)
    for u in nbrs: D.add_edge(u, "T", capacity=2)
    R = maximum_flow(D, "S", "T"); fv = R[0] if isinstance(R, tuple) else R.flow_value
    return fv < 2*len(L) - 2, {"L_size": len(L), "flow": int(fv), "need": 2*len(L)-2, "indep": indep}

def hamilton(G, cap=100000):
    nodes = sorted(G.nodes, key=lambda v: G.degree(v), reverse=True)
    adj = {v: sorted(G.neighbors(v), key=lambda u: G.degree(u)) for v in G.nodes}
    cnt = 0
    def bt(path, used):
        nonlocal cnt
        if cnt >= cap: return True
        if len(path) == len(G.nodes): cnt += 1; return cnt >= cap
        for u in adj[path[-1]]:
            if u not in used:
                used.add(u); path.append(u)
                stop = bt(path, used); path.pop(); used.remove(u)
                if stop: return True
        return False
    for s in nodes[:4]:
        bt([s], {s})
    return cnt > 0, cnt

print("\n===== v2 塔图（8塔）三档阈值 + gcd 对照 =====")
results = {}
for rule, ths in [("v2", [3, 2, 4]), ("gcd", [12])]:
    for th in ths:
        G = build_graph(th, rule)
        tag = f"{rule}_th{th}"
        ent = {"n_edges": G.number_of_edges(), "complete": G.number_of_edges() == 28,
               "connected": nx.is_connected(G) if G.number_of_nodes() else False}
        if ent["connected"]:
            k, info = capacity_kill(G)
            ent["capacity"] = {**info, "KILL": bool(k)}
            lam = np.linalg.eigvalsh(nx.laplacian_matrix(G).toarray().astype(float))
            ent["lambda2"] = round(float(np.sort(lam)[1]), 4)
            ent["hamilton"] = {"KILL": True} if k else dict(zip(["exists", "count"], hamilton(G)))
        results[tag] = ent
        print(f"[{tag}] 边{ent['n_edges']}/28 完全图{ent['complete']} 连通{ent['connected']} "
              f"容量{ent.get('capacity')} λ2={ent.get('lambda2')} 哈密顿{ent.get('hamilton')}")

out = {"script": "ta2_towergraphV2-v1.0-20260927.py",
       "prereg": "黎曼猜想·通俗图解-v4.0-20260927 §十二（NTFS冻结在先）",
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "platform": platform.platform(),
       "spectra": {str(k): v for k, v in specs.items()}, "closed_form_verified": ok,
       "results": results}
with open("results/ta2_B_towergraphV2_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n结果已写 results/ta2_B_towergraphV2_result-v1.0-20260927.json")
