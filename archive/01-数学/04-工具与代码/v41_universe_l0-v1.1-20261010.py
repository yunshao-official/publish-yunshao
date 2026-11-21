# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · V4.1 Flash L0 构建+投影生成
权重：DeepSeek V4.1 Flash 官方 model-00002（embed.weight=129280×4096 bf16）
管线：safetensors→embedding→kNN top-3→连通分量→零点矩阵→投影生成 200 token
输出：结构数字+速度+token 样例。纯计算零写盘版（stdout JSON）。
"""
import os, sys, json, time, struct
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")

SAFET = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\embed_weight.safetensors"
TOKJSON = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
N_GEN = 200
BLOCK = 512

def read_embed(path):
    with open(path, "rb") as f:
        (hlen,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(hlen).decode("utf-8"))
    for name, info in header.items():
        if name == "__metadata__": continue
        if "embed" in name.lower():
            dt, shape, offs = info["dtype"], info["shape"], info["data_offsets"]
            data_start = 8 + hlen
            with open(path, "rb") as f2:
                f2.seek(data_start + offs[0])
                raw = f2.read(offs[1] - offs[0])
            if dt == "BF16":
                u16 = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape)
                arr = (u16.astype(np.uint32) << 16).view(np.float32)
            elif dt == "F16":
                arr = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape).view(np.float32)
            elif dt == "F32":
                arr = np.frombuffer(raw, dtype=np.float32).reshape(shape)
            else:
                raise RuntimeError(f"dtype {dt} not supported")
            return name, dt, arr.astype(np.float32)
    raise RuntimeError("embed not found")

def main():
    t0 = time.time()

    # tokenizer
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)
    vs = tok.get_vocab_size()
    print(f"[tokenizer] vocab={vs}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # embedding
    emb_name, dt, Emb = read_embed(SAFET)
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    print(f"[embed] {emb_name} dtype={dt} {N}x{dim}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # kNN top-3 语义图（分块）
    t1 = time.time()
    adj = {}
    for s in range(0, N, BLOCK):
        e = min(s + BLOCK, N)
        sim = En[s:e] @ En.T
        for r in range(e - s):
            row = sim[r]
            row[s + r] = -2.0
            knn = np.argpartition(-row, 3)[:3]
            u = s + r
            for v in knn:
                adj.setdefault(u, set()).add(int(v))
                adj.setdefault(int(v), set()).add(u)
    n_edges = sum(len(v) for v in adj.values()) // 2
    print(f"[knn] edges={n_edges}  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # 连通分量
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for u, nbrs in adj.items():
        for v in nbrs:
            ra, rb = find(u), find(v)
            if ra != rb: parent[rb] = ra
    roots = np.array([find(i) for i in range(N)])
    uniq, counts = np.unique(roots, return_counts=True)
    n_clusters = len(uniq)
    sizes = sorted(counts.tolist(), reverse=True)
    print(f"[components] {n_clusters} clusters top5={sizes[:5]}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 零点矩阵
    r2i = {r: i for i, r in enumerate(uniq)}
    Zer = np.zeros((n_clusters, dim), dtype=np.float32)
    for i in range(N):
        Zer[r2i[roots[i]]] += En[i]
    Zer = Zer / (np.linalg.norm(Zer, axis=1, keepdims=True) + 1e-12)
    mem_mb = Zer.nbytes / 2**20

    # 投影生成 200 token
    t_gen = time.time()
    prompt_ids = [int(x) for x in tok.encode("人工智能", add_special_tokens=False).ids if int(x) < N]
    ctx = En[prompt_ids].mean(axis=0); ctx /= (np.linalg.norm(ctx)+1e-12)
    gen_ids = []
    rng = np.random.default_rng(7)
    for i in range(N_GEN):
        k = int(np.argmax(Zer @ ctx))
        mem_ids = np.where(roots == uniq[k])[0]
        best = mem_ids[np.argmax(En[mem_ids] @ ctx)]
        gen_ids.append(int(best))
        nv = En[best]
        ctx = 0.9 * ctx + 0.1 * nv
        nrm = np.linalg.norm(ctx)
        if nrm > 0: ctx /= nrm
    gen_time = time.time() - t_gen
    tok_s = N_GEN / gen_time

    sample = tok.decode(gen_ids[:100])

    out = {
        "model": "DeepSeek V4.1 Flash（deepseek_v4·官方权重 embed 层）",
        "embedding": {"name": emb_name, "dtype": dt, "shape": [N, dim]},
        "universe": {"n_clusters": n_clusters, "zero_matrix_MB": round(mem_mb, 1),
                      "largest_clusters": sizes[:10], "median": int(np.median(counts)),
                      "singletons": int((counts == 1).sum()), "n_edges": n_edges},
        "generation": {"tokens": N_GEN, "tok_per_sec": round(tok_s, 1),
                        "sample_100": sample[:300]},
        "design_100_check": tok_s >= 100,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "L0 字级概念宇宙（V4.1 官方 embedding）；L1 FFN 知识级+L2 影子级待建；投影=零点最近成员（v0）；tokenizer=1.5B 的（跨模型 decode 会有乱码，速度数字有效）",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
