# -*- coding: utf-8 -*-
"""gen_edges.py · 预注册 m5e5 实例生成（冻结口径：networkx barabasi_albert_graph）"""
import hashlib
import json
import sys

import networkx as nx


def main():
    seed = int(sys.argv[1])
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    m = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    out = sys.argv[4]
    G = nx.barabasi_albert_graph(N, m, seed=seed)
    assert G.number_of_nodes() == N
    with open(out, "w", newline="\n") as f:
        for u, v in G.edges():
            f.write(f"{u} {v}\n")
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    deg = dict(G.degree())
    leaves = sum(1 for v in G.nodes() if deg[v] == m)
    rec = {
        "generator": "networkx.barabasi_albert_graph",
        "networkx_version": nx.__version__,
        "N": N, "m": m, "seed": seed,
        "n_edges": G.number_of_edges(),
        "n_leaves_deg_eq_m": leaves,
        "sha256": h,
    }
    print(json.dumps(rec))
    with open(out + ".meta.json", "w") as f:
        json.dump(rec, f, indent=1)


if __name__ == "__main__":
    main()
