# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 投影构造器 v1 + J-U3 质量基线
宇宙：1.5B embedding 576 簇（MVP 已建）
构造器 v1：语境向量 → 最近零点簇 → 簇成员 embedding 相似度 softmax → 影子分布
基线：原模型同语境 next-token 分布
指标：top-20 词重合率（构造 vs 原版）——J-U3 质量基线（首数字，非成败判定）
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
EDGES = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt"
PROMPTS = ["人工智能的", "猫在", "今天天气", "他的心情", "宇宙的起源", "做一道数学", "音乐会的", "医生说",
           "北京是", "水的沸点", "爱情是", "战争的", "学习方法", "太阳从", "经济的", "孩子在学习",
           "这首歌的", "厨师正在", "森林里的", "未来的世界"]

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)

    # 重建宇宙（同 MVP：union-find 分量→零点）
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for l in open(EDGES):
        u, v = map(int, l.split())
        ra, rb = find(u), find(v)
        if ra != rb: parent[rb] = ra
    roots = np.array([find(i) for i in range(N)])
    uniq, counts = np.unique(roots, return_counts=True)
    r2i = {r: i for i, r in enumerate(uniq)}
    K = len(uniq)
    Zer = np.zeros((K, dim), dtype=np.float32)
    members = {i: [] for i in range(K)}
    for i in range(N):
        k = r2i[roots[i]]; Zer[k] += En[i]; members[k].append(i)
    Zer = Zer / (np.linalg.norm(Zer, axis=1, keepdims=True) + 1e-12)
    print(f"[universe] K={K}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 投影构造器 v1 + 基线对比
    results = []
    overlap20s = []
    for pr in PROMPTS:
        ids = tok.encode(pr, add_special_tokens=True)
        cv = En[ids].mean(axis=0)
        cv = cv / (np.linalg.norm(cv) + 1e-12)
        # 构造器：最近零点簇 → 簇成员相似度 softmax
        k = int(np.argmax(Zer @ cv))
        mem = members[k]
        sims = np.array([float(En[m] @ cv) for m in mem])
        sims = np.exp((sims - sims.max()) * 8)   # 温度缩放
        shadow = sims / sims.sum()
        top_mem = np.argsort(-shadow)[:20]
        cons_words = set()
        for ti in top_mem:
            cons_words.update(tok.encode(tok.decode([mem[ti]]), add_special_tokens=False))
        # 原版基线：next-token 分布 top-50
        with torch.no_grad():
            out = model(torch.tensor([ids]))
        base_top50 = set(np.argsort(-out.logits[0, -1].float().numpy())[:50].tolist())
        # 重合：构造 top20 词的 token id 与基线 top50 的交集
        hit = len(cons_words & base_top50)
        overlap20s.append(hit / 20)
        results.append({"prompt": pr, "cluster": k, "cluster_size": len(mem),
                        "cons_top_words": [tok.decode([mem[ti]]) for ti in top_mem[:5]],
                        "overlap_in_base50": round(hit/20, 2)})
    j_u3 = float(np.mean(overlap20s))
    out = {"model": MODEL, "K": K, "prompts_n": len(PROMPTS),
           "J-U3_baseline_overlap": round(j_u3, 4),
           "per_prompt": results,
           "honest_note": "构造器 v1=零点查表级（最粗糙）；J-U3=质量长跑起点数字，非成败判定",
           "elapsed_s": round(time.time()-t0, 1)}
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
