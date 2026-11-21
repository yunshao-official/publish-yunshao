# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · L0 词面宇宙构建（V4-Flash GGUF 自洽线 v1）
来源：H:/AI/DeepSeek-V4.1-Flash-IQ2XXS/ 的 GGUF 分片2/3（token_embd Q4_K [4096,129280]）
产出（results/v4f_l0/）：
  embed_fp16.npy    (129280,4096) fp16 —— 词面坐标（解包后原样）
  edges.npy         (E,2) int32 —— kNN top-3 无向边表（相似脉冲游走图）
  centers.npy       (2048,4096) fp16 —— 概念簇中心（定位/阶段一索引）
  assign.npy        (129280,) int32 —— 词 → 概念簇归属
  member_cap.npy    dict 序列化 npz —— 每簇按中心相似度截断的 top-300 成员（阶段二候选池）
  meta.json         —— 构建参数与诚实注记
纪律：先冻结后实算沿用；纯权重读取零训练；路径全字面量。
"""
import sys, os, json, time, struct
import numpy as np

sys.path.insert(0, r"H:\llama.cpp\repo\gguf-py")
import gguf
from gguf.quants import quant_shape_to_byte_shape

GGUF_DIR = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS"
SHARD2 = GGUF_DIR + r"\DeepSeek-V4-Flash-UD-IQ2_XXS-00002-of-00003.gguf"
OUT_DIR = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
KNN = 3
BLOCK = 1024
K_CLU = 2048
MB_ITERS = 12
CAP_PER_CLU = 300

def log(msg):
    print(msg, file=sys.stderr, flush=True)

def dequant_tensor(t):
    ne = [int(x) for x in t.shape]
    oshape = tuple(reversed(ne))
    raw = np.asarray(t.data)
    if raw.ndim == 1:
        raw = raw.reshape(quant_shape_to_byte_shape(oshape, t.tensor_type))
    return gguf.quants.dequantize(raw, t.tensor_type)

def main():
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- ① token_embd 解包（Q4_K，4.6s 实测） ----
    r = gguf.GGUFReader(SHARD2)
    tb = {t.name: t for t in r.tensors}
    Emb = dequant_tensor(tb["token_embd.weight"]).astype(np.float32)
    N, D = Emb.shape
    assert (N, D) == (129280, 4096), (N, D)
    log("[embed] %dx%d  %.1fs" % (N, D, time.time() - t0))
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)

    # ---- ② kNN top-3 边表（相似脉冲图） ----
    edges = []
    for s in range(0, N, BLOCK):
        e = min(s + BLOCK, N)
        sim = En[s:e] @ En.T
        for r_i in range(e - s):
            row = sim[r_i]
            row[s + r_i] = -2.0
            knn = np.argpartition(-row, KNN)[:KNN]
            u = s + r_i
            for v in knn:
                if u < int(v):
                    edges.append((u, int(v)))
                else:
                    edges.append((int(v), u))
        if (s // BLOCK) % 25 == 0:
            log("  kNN %d/%d  %.0fs" % (e, N, time.time() - t0))
    E = np.array(edges, dtype=np.int32).reshape(-1, 2)
    np.save(OUT_DIR + r"\edges.npy", E)
    log("[edges] %d  %.1fs" % (len(E), time.time() - t0))

    # 连通分量统计（多图/路径森林的自由副产品）
    parent = np.arange(N, dtype=np.int32)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in E:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[rb] = ra
    roots = np.array([find(i) for i in range(N)], dtype=np.int32)
    uniq, counts = np.unique(roots, return_counts=True)
    log("[components] %d 个（最大 %d 词）" % (len(uniq), counts.max()))
    np.save(OUT_DIR + r"\roots.npy", roots)

    # ---- ③ mini-batch kmeans K=2048（概念簇） ----
    rng = np.random.default_rng(7)
    C = En[rng.choice(N, K_CLU, replace=False)].copy()
    for it in range(MB_ITERS):
        # mini-batch：每轮抽 30000 行
        idx = rng.choice(N, 30000, replace=False)
        X = En[idx]
        # assign in chunks to limit memory
        lab = np.empty(len(idx), dtype=np.int32)
        for s in range(0, len(idx), 8192):
            ch = X[s:s + 8192]
            lab[s:s + 8192] = np.argmax(ch @ C.T, axis=1)
        # update
        cnt = np.bincount(lab, minlength=K_CLU).astype(np.float64)
        sums = np.zeros((K_CLU, D), dtype=np.float64)
        np.add.at(sums, lab, X)
        nz = cnt > 0
        C[nz] = (sums[nz] / cnt[nz, None]).astype(np.float32)
        log("  kmeans iter %d/%d  empty=%d  %.0fs" % (it + 1, MB_ITERS, (~nz).sum(), time.time() - t0))
    Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)

    # full assign
    assign = np.empty(N, dtype=np.int32)
    for s in range(0, N, 8192):
        assign[s:s + 8192] = np.argmax(En[s:s + 8192] @ Cn.T, axis=1)
    sizes = np.bincount(assign, minlength=K_CLU)
    log("[clusters] K=%d 最大=%d 中位=%d 单点=%d  %.0fs" % (K_CLU, sizes.max(), int(np.median(sizes)), int((sizes == 1).sum()), time.time() - t0))
    np.save(OUT_DIR + r"\centers.npy", Cn.astype(np.float16))
    np.save(OUT_DIR + r"\assign.npy", assign)
    np.save(OUT_DIR + r"\cluster_sizes.npy", sizes)

    # 每簇成员按中心相似度排序取 top-300（阶段二候选池）
    # （原全量 argsort-(E@C.T) 方案内存 4GB+ 已废除——逐簇做）
    members = {}
    for c in range(K_CLU):
        m = np.nonzero(assign == c)[0]
        if len(m) == 0:
            members[c] = np.zeros(0, dtype=np.int32)
            continue
        if len(m) > CAP_PER_CLU:
            s = En[m] @ Cn[c]
            m = m[np.argsort(-s)[:CAP_PER_CLU]]
        members[c] = m.astype(np.int32)
    np.savez_compressed(OUT_DIR + r"\member_cap.npz", **{str(k): v for k, v in members.items()})
    log("[member_cap] done  %.0fs" % (time.time() - t0))

    np.save(OUT_DIR + r"\embed_fp16.npy", Emb.astype(np.float16))

    meta = {
        "engine": "概念宇宙 LLM · L0 词面宇宙（V4-Flash GGUF 自洽线）",
        "source": "DeepSeek-V4-Flash UD-IQ2_XXS GGUF 分片2 token_embd（Q4_K 解包）",
        "note_on_naming": "目录名为 V4.1-Flash-IQ2XXS，但 GGUF 自述 base_model=DeepSeek-V4-Flash（arch=deepseek4，hidden=4096）；本宇宙按 GGUF 自述命名 V4-Flash，与 V4.1 的 embed_weight(5120) 不同源不可混用",
        "embed": [N, D],
        "knn": KNN,
        "edges": int(len(E)),
        "components": int(len(uniq)),
        "largest_component": int(counts.max()),
        "clusters": K_CLU,
        "cluster_max": int(sizes.max()),
        "cluster_median": int(np.median(sizes)),
        "cluster_singletons": int((sizes == 1).sum()),
        "member_cap_per_cluster": CAP_PER_CLU,
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "词面宇宙 v1：解包=gguf-py 官方 dequantize；图=top-3 kNN（未做多图路径森林——J-H2v3 方法可后续套用）；分簇=mini-batch kmeans（IVF 索引用，非语义等价类判据）；Q4_K 解包有量化损失（原量化本身有损）",
    }
    with open(OUT_DIR + r"\meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))
    log("[done] %.1fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
