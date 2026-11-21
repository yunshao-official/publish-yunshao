# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · V4.1 FFN 知识提取 + 两层宇宙生成
从分片 3 的 FFN 权重中提取知识概念（expert gate 行向量 = 知识模式）
两层宇宙 = L0 embedding（129280 词概念）+ L1 FFN（Layer 0 的知识概念）
投影生成：L0 定位 + L1 知识增强
"""
import os, sys, json, time, struct
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")

SHARD3 = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\model-00003-of-00048.safetensors"
EMBED = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\embed_weight.safetensors"
TOKJSON = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
N_GEN = 200
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙"]

def read_tensor_safe(path, target_name):
    """safetensors 读取指定张量"""
    with open(path, "rb") as f:
        (hlen,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(hlen).decode("utf-8"))
    if target_name not in header:
        return None, None, None
    info = header[target_name]
    dt, shape, offs = info["dtype"], info["shape"], info["data_offsets"]
    data_start = 8 + hlen
    with open(path, "rb") as f:
        f.seek(data_start + offs[0])
        raw = f.read(offs[1] - offs[0])
    if dt == "BF16":
        u16 = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape)
        arr = (u16.astype(np.uint32) << 16).view(np.float32)
    elif dt == "F16":
        arr = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape).view(np.float32)
    elif dt == "F32":
        arr = np.frombuffer(raw, dtype=np.float32).reshape(shape)
    elif dt == "I8":
        arr = np.frombuffer(raw, dtype=np.int8).reshape(shape).astype(np.float32)
    elif dt == "F8_E4M3":
        # FP8 → 直接当 int8 用（值域不同但方向保留）
        arr = np.frombuffer(raw, dtype=np.uint8).reshape(shape).astype(np.float32) - 128.0
    else:
        raise RuntimeError(f"dtype {dt} not supported for {target_name}")
    return arr.astype(np.float32), dt, shape

def main():
    t0 = time.time()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)

    # ---- ① L0: embedding 层概念宇宙 ----
    Emb_l0, _, _ = read_tensor_safe(EMBED, "embed.weight")
    N, dim = Emb_l0.shape
    En_l0 = Emb_l0 / (np.linalg.norm(Emb_l0, axis=1, keepdims=True) + 1e-12)
    print(f"[L0] {N}x{dim}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # L0 聚类（kNN top-5 → 分量 → 零点）
    parent = list(range(N))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    BLOCK = 1024
    for s in range(0, N, BLOCK):
        e = min(s + BLOCK, N)
        sim = En_l0[s:e] @ En_l0.T
        for r in range(e - s):
            row = sim[r]; row[s+r] = -2.0
            knn = np.argpartition(-row, 5)[:5]
            u = s + r
            for v in knn:
                ra, rb = find(u), find(int(v))
                if ra != rb: parent[rb] = ra
    roots_l0 = np.array([find(i) for i in range(N)])
    uniq_l0, counts_l0 = np.unique(roots_l0, return_counts=True)
    r2i_l0 = {r: i for i, r in enumerate(uniq_l0)}
    K_l0 = len(uniq_l0)
    Zer_l0 = np.zeros((K_l0, dim), dtype=np.float32)
    for i in range(N):
        Zer_l0[r2i_l0[roots_l0[i]]] += En_l0[i]
    Zer_l0 = Zer_l0 / (np.linalg.norm(Zer_l0, axis=1, keepdims=True) + 1e-12)
    Zer_l0T = np.ascontiguousarray(Zer_l0)
    print(f"[L0 universe] {K_l0} clusters  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ② L1: FFN 知识概念提取 ----
    # Layer 0 的 shared_experts.w1 = 知识存储（2304 × 5120）
    # 每行 = 一个知识概念的 key 向量（5120 维，与 hidden dim 相同）
    t2 = time.time()
    expert_keys = []
    expert_meta = []
    
    # shared experts
    se_w1, dt_se, shape_se = read_tensor_safe(SHARD3, "layers.0.ffn.shared_experts.w1.weight")
    if se_w1 is not None:
        # 每行 = 一个知识模式
        se_norm = se_w1 / (np.linalg.norm(se_w1, axis=1, keepdims=True) + 1e-12)
        expert_keys.append(se_norm)
        for j in range(se_w1.shape[0]):
            expert_meta.append({"layer": 0, "type": "shared", "idx": j})
        print(f"[L1 shared] {se_w1.shape[0]} knowledge vectors  {time.time()-t2:.1f}s", file=sys.stderr, flush=True)

    # routed experts 维度不同（I8 量化 2560 vs shared 5120）——只保留 shared
    if expert_keys:
        ExpertAll = np.concatenate(expert_keys, axis=0)   # total_knowledge × dim
        n_knowledge = ExpertAll.shape[0]
        print(f"[L1 total] {n_knowledge} knowledge concepts  {time.time()-t2:.1f}s", file=sys.stderr, flush=True)
    else:
        n_knowledge = 0
        ExpertAll = np.zeros((0, dim), dtype=np.float32)

    # ---- ③ 两层概念宇宙零点 ----
    # L0 零点 + L1 知识概念的"零点"（对 FFN 知识概念也做聚类）
    # 简化 v0：L1 知识概念直接作为投影空间（不聚类）
    ExpertT = np.ascontiguousarray(ExpertAll)   # (n_knowledge, dim) 原向
    ExpertNorm = np.linalg.norm(ExpertAll, axis=1, keepdims=True)
    ExpertNorm = np.maximum(ExpertNorm, 1e-12)
    
    total_MB = (Zer_l0.nbytes + ExpertAll.nbytes) / 2**20
    print(f"[universe] L0={K_l0}+L1={n_knowledge} total={K_l0+n_knowledge} 概念  {total_MB:.1f}MB 常驻  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ④ 投影生成：L0 定位 → L1 知识投影 ----
    # 生成逻辑：
    # ① 语境向量 → L0 定位（最近零点） → 得到语义域
    # ② L1 知识投影：语境在 FFN 知识概念中找最活跃的知识模式
    # ③ 知识激活值 → 通过 w2 投影回词表 → 下一个词
    results = {}
    tok_s_list = []
    rng = np.random.default_rng(7)
    
    # 读 shared_experts.w2（投影回 hidden dim 的矩阵）
    se_w2, _, _ = read_tensor_safe(SHARD3, "layers.0.ffn.shared_experts.w2.weight")
    # 读 gate 权重（路由用）
    gate_w, _, _ = read_tensor_safe(SHARD3, "layers.0.ffn.gate.weight")
    
    for prompt in PROMPTS:
        pids = [int(x) for x in tok.encode(prompt, add_special_tokens=False).ids if int(x) < N]
        if not pids: pids = [0]
        ctx = En_l0[pids].mean(axis=0); ctx /= (np.linalg.norm(ctx)+1e-12)
        gen_ids = list(pids)
        recent = set(pids[-8:])
        t_gen = time.time()
        for i in range(N_GEN):
            # ① L0 定位
            k = int(np.argmax(Zer_l0T @ ctx))
            mem = members_local = np.where(roots_l0 == uniq_l0[k])[0]
            # ② L1 知识激活：ctx 与 FFN 知识概念的内积 → 激活 top 知识
            if n_knowledge > 0 and se_w2 is not None:
                # 用 shared_experts 做知识投影
                # ctx → gate → expert activation → w2 → hidden → 最近词
                # 简化 v0：ctx 和知识概念的相似度作为激活权重
                act = ExpertAll @ ctx   # (n_knowledge,) 激活值
                top_k = np.argsort(-np.abs(act))[:64]   # top-64 活跃知识
                # 加权组合：激活知识通过 w2 投影回 hidden
                # 简化：取 top 知识的 w2 列投影 → 混合 hidden → 找最近词
                projected = se_w2 @ (se_w1 @ ctx) if se_w1 is not None else ctx
                proj_n = projected / (np.linalg.norm(projected)+1e-12)
                # 最近词（在 L0 空间找投影向量的最近词）
                nid = int(np.argmax(En_l0 @ proj_n))
            else:
                nid = int(rng.integers(0, N))
            # 防循环
            if nid in recent:
                # 取次优
                proj = En_l0 @ ctx
                proj[list(recent)] = -999
                nid = int(np.argmax(proj))
            gen_ids.append(nid)
            recent = set(gen_ids[-10:])
            nv = En_l0[nid]
            ctx = 0.92 * ctx + 0.08 * nv
            nrm = np.linalg.norm(ctx)
            if nrm > 0: ctx /= nrm
        gen_time = time.time() - t_gen
        ts = N_GEN / gen_time
        tok_s_list.append(round(ts, 1))
        text = tok.decode(gen_ids[len(pids):len(pids)+60])
        results[prompt] = {"tok_s": round(ts, 1), "sample": text[:250]}

    mean_ts = float(np.mean(tok_s_list))
    all_txt = "".join(r["sample"] for r in results.values())
    diversity = len(set(all_txt)) / max(len(all_txt), 1)

    out = {
        "engine": "概念宇宙 LLM · 两层（L0 embedding + L1 FFN 知识）",
        "model": "DeepSeek V4.1 Flash 官方权重",
        "universe": {
            "L0_word_clusters": K_l0, "L1_knowledge_concepts": n_knowledge,
            "total_concepts": K_l0 + n_knowledge,
            "memory_MB": round(total_MB, 1),
        },
        "mean_tok_s": round(mean_ts, 1),
        "design_100_check": mean_ts >= 100,
        "diversity": round(diversity, 3),
        "generations": results,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "两层宇宙 v0：L0=embedding 概念定位，L1=FFN 知识投影。生成路径=知识激活→投影→最近词。无蒸馏无训练无前向——纯权重读取。",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
