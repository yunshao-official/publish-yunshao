# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 纯查表投影（无蒸馏·无MLP·无训练）
V4.1 Flash embedding（129280×5120）→ kNN 分量 → 零点 → 概念定位 → 邻域投影 → 出字
速度+质量一步到位。
"""
import os, sys, json, time, struct
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")

SAFET = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\embed_weight.safetensors"
TOKJSON = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
N_GEN = 200
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙", "医生的", "北京"]

def main():
    t0 = time.time()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)

    # 读 safetensors embedding
    with open(SAFET, "rb") as f:
        (hlen,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(hlen).decode("utf-8"))
    for name, info in header.items():
        if name == "__metadata__": continue
        if "embed" in name.lower():
            dt, shape, offs = info["dtype"], info["shape"], info["data_offsets"]
            break
    data_start = 8 + hlen
    with open(SAFET, "rb") as f:
        f.seek(data_start + offs[0])
        raw = f.read(offs[1] - offs[0])
    if dt == "BF16":
        u16 = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape)
        Emb = (u16.astype(np.uint32) << 16).view(np.float32)
    else:
        Emb = np.frombuffer(raw, dtype=np.float32).reshape(shape)
    Emb = Emb.astype(np.float32)
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    print(f"[load] {N}x{dim} {dt}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 概念宇宙：kNN top-5 → 分量 → 零点
    t1 = time.time()
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    BLOCK = 1024
    for s in range(0, N, BLOCK):
        e = min(s + BLOCK, N)
        sim = En[s:e] @ En.T
        for r in range(e - s):
            row = sim[r]; row[s + r] = -2.0
            knn = np.argpartition(-row, 5)[:5]
            u = s + r
            for v in knn:
                ra, rb = find(u), find(int(v))
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
    ZerT = np.ascontiguousarray(Zer)
    mem_mb = Zer.nbytes / 2**20
    sizes = sorted(counts.tolist(), reverse=True)
    print(f"[universe] K={K} top5={sizes[:5]} zero={mem_mb:.1f}MB  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # ---- 投影生成（纯查表，无前向，无训练）----
    # 语境向量 → 概念定位 → 簇内最近成员 → 下一词 → embedding 回馈
    results = {}
    tok_s_list = []
    for prompt in PROMPTS:
        pids = [int(x) for x in tok.encode(prompt, add_special_tokens=False).ids if int(x) < N]
        if not pids: pids = [0]
        ctx = En[pids].mean(axis=0); ctx /= (np.linalg.norm(ctx)+1e-12)
        gen_ids = list(pids)
        t_gen = time.time()
        for i in range(N_GEN):
            k = int(np.argmax(ZerT @ ctx))
            mem = members[k]
            # 簇内最近成员（排除已选的尾部避免无限循环）
            tail = set(gen_ids[-5:])
            cand = [m for m in mem if m not in tail]
            if not cand: cand = mem
            best = max(cand, key=lambda m: float(En[m] @ ctx))
            gen_ids.append(best)
            nv = En[best]
            ctx = 0.9 * ctx + 0.1 * nv
            nrm = np.linalg.norm(ctx)
            if nrm > 0: ctx /= nrm
        gen_time = time.time() - t_gen
        ts = N_GEN / gen_time
        tok_s_list.append(ts)
        text = tok.decode(gen_ids[len(pids):len(pids)+50])
        results[prompt] = {"tok_s": round(ts, 1), "sample": text[:200]}

    mean_ts = float(np.mean(tok_s_list))

    out = {
        "engine": "概念宇宙 LLM · 纯查表投影 v1（无蒸馏·无MLP·无训练·无前向）",
        "model_source": "DeepSeek V4.1 Flash 官方 embedding",
        "universe": {"K": K, "zero_MB": round(mem_mb, 1), "top5": sizes[:5]},
        "mean_tok_s": round(mean_ts, 1),
        "design_100_check": mean_ts >= 100,
        "generations": results,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "纯查表投影 v1：概念定位+簇内最近成员。质量取决于 embedding 的语义丰富度（V4.1 官方 5120 维）。无注意力、无 FFN、无训练——纯几何投影。",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
