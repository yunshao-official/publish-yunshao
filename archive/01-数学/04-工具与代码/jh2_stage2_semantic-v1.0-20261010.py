# -*- coding: utf-8 -*-
"""J-H2 语义检验（读已落盘的 stitched_path.txt + embedding）——纯计算零写盘"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
WALK = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\stitched_path.txt"
EDGES = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt"

def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx = (rx - rx.mean()) / (rx.std() + 1e-12)
    ry = (ry - ry.mean()) / (ry.std() + 1e-12)
    return float((rx * ry).mean())

def main():
    t0 = time.time()
    sw = [int(x) for x in open(WALK) if x.strip()]
    adjset = {}
    for l in open(EDGES):
        u, v = map(int, l.split())
        adjset.setdefault(u, set()).add(v)
        adjset.setdefault(v, set()).add(u)
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N = En.shape[0]

    sim_adj = [float(En[sw[i]] @ En[sw[i + 1]]) for i in range(len(sw) - 1)]
    rng = np.random.default_rng(42)
    ii = rng.integers(0, N, 100000)
    jj = rng.integers(0, N, 100000)
    allmean = float(np.mean([float(En[a] @ En[b]) for a, b in zip(ii, jj)]))

    pos = {}
    for i, v in enumerate(sw):
        if v not in pos:
            pos[v] = i
    pdist, sdist = [], []
    for _ in range(80000):
        a, b = rng.integers(0, N, 2)
        if a == b:
            continue
        pa, pb = pos.get(int(a), -1), pos.get(int(b), -1)
        if pa < 0 or pb < 0:
            continue
        pdist.append(abs(pa - pb))
        sdist.append(float(En[a] @ En[b]))
    rho = spearman(pdist, sdist)

    true_edges = sum(1 for i in range(len(sw) - 1) if sw[i + 1] in adjset.get(sw[i], ()))
    true_rate = true_edges / max(len(sw) - 1, 1)

    out = {
        "walk_len": len(sw), "true_edge_rate": round(true_rate, 4),
        "semA": {"adjacent_mean_sim": round(float(np.mean(sim_adj)), 4),
                 "random_mean_sim": round(allmean, 4),
                 "lift": round(float(np.mean(sim_adj)) - allmean, 4)},
        "semB": {"spearman_pos_vs_sim": round(rho, 4),
                 "note": "负值=路径位置远的词对相似度低（预期方向）"},
        "elapsed_s": round(time.time() - t0, 1),
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
