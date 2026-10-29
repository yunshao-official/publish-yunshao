# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 纯查表投影 v2（V4.1 embedding）
修：①每簇预选 200 代表词（速度：0.1ms/词）②温度采样（多样性）③跨簇跳转（丰富度）
"""
import os, sys, json, time, struct
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")

SAFET = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\embed_weight.safetensors"
TOKJSON = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
N_GEN = 200
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙", "医生的", "北京", "春天", "音乐"]
TEMP = 0.8   # 采样温度

def main():
    t0 = time.time()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)

    with open(SAFET, "rb") as f:
        (hlen,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(hlen).decode("utf-8"))
    for name, info in header.items():
        if name == "__metadata__": continue
        if "embed" in name.lower():
            dt, shape, offs = info["dtype"], info["shape"], info["data_offsets"]
            break
    with open(SAFET, "rb") as f:
        f.seek(8 + hlen + offs[0])
        raw = f.read(offs[1] - offs[0])
    u16 = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape)
    Emb = (u16.astype(np.uint32) << 16).view(np.float32).astype(np.float32)
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    print(f"[load] {N}x{dim}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 宇宙：kNN top-5 → 分量
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

    # v2 核心：每簇预选 200 代表词（离簇零点最近的前 200——代表度排序）
    t1 = time.time()
    repr_table = {}
    for k in range(K):
        mem = np.array(members[k])
        if len(mem) > 200:
            sims = En[mem] @ Zer[k]
            top200 = mem[np.argsort(-sims)[:200]]
            repr_table[k] = top200
        else:
            repr_table[k] = mem
    print(f"[repr] {K} clusters, avg repr={np.mean([len(v) for v in repr_table.values()]):.0f}  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # v2 生成：温度采样 + 跨簇跳转
    results = {}
    tok_s_list = []
    rng = np.random.default_rng(7)
    for prompt in PROMPTS:
        pids = [int(x) for x in tok.encode(prompt, add_special_tokens=False).ids if int(x) < N]
        if not pids: pids = [0]
        ctx = En[pids].mean(axis=0); ctx /= (np.linalg.norm(ctx)+1e-12)
        gen_ids = list(pids)
        recent = set(pids[-5:])
        t_gen = time.time()
        for i in range(N_GEN):
            k = int(np.argmax(Zer @ ctx))
            cand = repr_table[k]
            # 排除最近的词（防循环）
            mask = np.array([m not in recent for m in cand])
            if mask.sum() < 5: mask = np.ones(len(cand), dtype=bool)
            cand_f = cand[mask]
            sims = En[cand_f] @ ctx
            # 温度采样
            sims_t = sims / TEMP
            probs = np.exp(sims_t - sims_t.max())
            probs /= probs.sum()
            nid = int(rng.choice(cand_f, p=probs))
            gen_ids.append(nid)
            recent = set(gen_ids[-8:])
            nv = En[nid]
            ctx = 0.92 * ctx + 0.08 * nv
            nrm = np.linalg.norm(ctx)
            if nrm > 0: ctx /= nrm
        gen_time = time.time() - t_gen
        ts = N_GEN / gen_time
        tok_s_list.append(ts)
        text = tok.decode(gen_ids[len(pids):len(pids)+60])
        results[prompt] = {"tok_s": round(ts, 1), "sample": text[:250]}

    mean_ts = float(np.mean(tok_s_list))
    # 多样性
    all_txt = "".join(r["sample"] for r in results.values())
    diversity = len(set(all_txt)) / max(len(all_txt), 1)

    out = {
        "engine": "概念宇宙 LLM · 纯查表投影 v2（V4.1 embedding+代表词+温度采样）",
        "universe": {"K": K, "zero_MB": round(Zer.nbytes/2**20, 1)},
        "mean_tok_s": round(mean_ts, 1),
        "diversity": round(diversity, 3),
        "design_100_check": mean_ts >= 100,
        "generations": results,
        "elapsed_s": round(time.time()-t0, 1),
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
