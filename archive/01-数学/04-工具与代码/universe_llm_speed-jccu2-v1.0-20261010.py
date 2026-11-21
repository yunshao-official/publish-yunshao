# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 完整生成循环速度实测（J-U2）
自回归生成：语境向量→概念定位→查预计算影子表→采样→新词 embedding 回馈语境→下一词
对比项：定位+查表通路（J-U1 已测 9518 tok/s）——本轮加采样+回馈的全循环
含 200 token 生成样例（质量粗看）。纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
EDGES = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt"
N_GEN = 2000
PROMPT = "人工智能"

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    print(f"[load] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 宇宙构建（同 MVP）
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
    members = {i: [] for i in range(K)}
    for i in range(N):
        members[r2i[roots[i]]].append(i)
    print(f"[universe] K={K}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 概念影子预计算（启动时一次性：每簇=成员 embedding 均值→簇内相似度 softmax→簇代表词分布）
    # v1 简化：影子=簇内成员的 embedding 相似度排序（top-512 成员 id 缓存）
    shadow_table = {}
    for k in range(K):
        mem = members[k]
        if len(mem) == 0: continue
        center = En[mem].mean(axis=0)
        center /= (np.linalg.norm(center) + 1e-12)
        sims = En[mem] @ center
        order = np.argsort(-sims)[:512]
        shadow_table[k] = np.array([mem[i] for i in order])   # top-512 成员 token id（按代表度排序）
    print(f"[shadow_table] {K} clusters precomputed  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 自回归生成 N_GEN tokens（概念宇宙引擎）
    pids = tok.encode(PROMPT, add_special_tokens=False)
    ctx_vec = En[pids].mean(axis=0)
    ctx_vec /= (np.linalg.norm(ctx_vec) + 1e-12)
    Zer = np.zeros((K, dim), dtype=np.float32)
    for k in range(K):
        m = members[k]
        Zer[k] = En[m].mean(axis=0)
    Zer /= (np.linalg.norm(Zer, axis=1, keepdims=True) + 1e-12)
    ZerT = np.ascontiguousarray(Zer)   # 修：保留 (K,dim) 原向

    rng = np.random.default_rng(7)
    gen_tokens = []
    t_gen = time.time()
    for i in range(N_GEN):
        # ① 概念定位
        k = int(np.argmax(ZerT @ ctx_vec))
        # ② 查影子表（预计算缓存——零计算）
        cand = shadow_table.get(k)
        if cand is None or len(cand) == 0:
            nid = int(rng.integers(0, N))
        else:
            # ③ 按影子序采样（前列概率高：指数衰减采样模拟分布）
            pick = min(len(cand)-1, int(rng.exponential(30)))
            nid = int(cand[pick])
        gen_tokens.append(nid)
        # ④ 自回归回馈：新词 embedding 混入语境
        nv = En[nid]
        ctx_vec = 0.9 * ctx_vec + 0.1 * nv
        nrm = np.linalg.norm(ctx_vec)
        if nrm > 0: ctx_vec /= nrm
    gen_time = time.time() - t_gen
    tok_s = N_GEN / gen_time

    # 生成样例文本（前 120 token 解码粗看）
    sample_text = tok.decode(gen_tokens[:120])

    out = {
        "model": MODEL, "engine": "概念宇宙 LLM v0（定位+影子表查表+自回归回馈）",
        "speed": {"tokens": N_GEN, "gen_time_s": round(gen_time, 3),
                  "tokens_per_sec": round(tok_s, 1),
                  "per_token_ms": round(1000*gen_time/N_GEN, 3)},
        "J-U2": ("PASS（完整生成循环 ≥100 tok/s·含采样+回馈全流程）" if tok_s >= 100
                 else f"未达 100（{tok_s:.1f}）"),
        "design_check": {"J-U1_9518_通路": "定位+查表", "J-U2_本轮": "全循环含采样回馈"},
        "sample_text_120tok": sample_text,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "影子表=启动时预计算（构造开销在启动不在运行）；采样为指数衰减近似（非训练分布）；质量粗看非判定",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
