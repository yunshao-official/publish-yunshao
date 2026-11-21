# -*- coding: utf-8 -*-
"""
J-H2 stage1（纯计算零写盘）：概念宇宙 10⁵ 级——embedding 权重 kNN 语义边表 + 贪心引擎 walk
stdout 分两段输出（===EDGES=== / ===WALK===），文件落盘由 Bash 重定向完成。
模型：Qwen2.5-1.5B embedding 权重矩阵（151936×1536）——"概念宇宙=权重本身"
"""
import os, sys, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
TOPK_NN = 3

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    N, dim = Emb.shape
    print(f"[load] vocab={N} dim={dim}", file=sys.stderr, flush=True)

    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)

    # ---- kNN top-3 边表（分块暴力余弦，BA-m3 同构）----
    NN = N
    BLOCK = 2048
    t1 = time.time()
    print("===EDGES===")
    out = []
    for s in range(0, NN, BLOCK):
        e = min(s + BLOCK, NN)
        sim = En[s:e] @ En.T
        for r in range(e - s):
            row = sim[r]
            row[s + r] = -2.0
            knn = np.argpartition(-row, TOPK_NN)[:TOPK_NN]
            u = s + r
            for v in knn:
                out.append(f"{u} {int(v)}")
        if len(out) > 200000:
            sys.stdout.write("\n".join(out) + "\n")
            out = []
    if out:
        sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()
    print(f"[knn] {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # ---- 贪心引擎 walk（语义图上，允许断口；枢纽优先）----
    adj = {}
    with open(r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt", encoding="utf-8") as f:
        for l in f:
            u, v = map(int, l.split())
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
    visited = np.zeros(NN, dtype=bool)
    walk = []
    order = np.argsort([-len(adj.get(i, ())) for i in range(NN)])
    for s in order:
        if visited[s]:
            continue
        cur = int(s)
        visited[s] = True
        walk.append(cur)
        while True:
            nbrs = [v for v in adj.get(cur, ()) if not visited[v]]
            if not nbrs:
                break
            best = max(nbrs, key=lambda v: float(En[cur] @ En[v]))
            visited[best] = True
            walk.append(best)
            cur = best
    print("===WALK===")
    sys.stdout.write("\n".join(map(str, walk)) + "\n")
    sys.stdout.flush()
    print(f"[engine] walk={len(walk)}  total={time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
