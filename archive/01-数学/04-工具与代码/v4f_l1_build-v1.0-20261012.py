# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · L1 知识宇宙构建（V4-Flash FFN 逐层概念条目）
输入：results/v4f_l0/（centers/embed_fp16/member_cap）+ GGUF ffn_down_exps（IQ3_XXS）
产出（results/v4f_l1/）：
  concept_tok.npy   (43,256,2048,10) int32 —— 每神经元 top-10 激活 token（-1=无效/层缺失）
  concept_sc.npy    (43,256,2048,10) fp16  —— 对应余弦分
  meta.json
方法（两段式，对 24 PFLOP 精确全词表 top-10 的可行替代，诚实标注为近似）：
  stage1  S = C @ W_e          （K=2048 簇中心打分，向量化）
  stage2  精排 = top1 簇成员组式 gemm + top2 簇成员逐神经元 gemv（cap 300/簇）
  完整性：43 层全在 GGUF 两分片；异常量化（blk.26 等）try/except 落 -1 并照记
"""
import sys, os, json, time, struct
import numpy as np
from multiprocessing import Process

sys.path.insert(0, r"H:\llama.cpp\repo\gguf-py")
import gguf
from gguf.quants import quant_shape_to_byte_shape

GGUF_DIR = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS"
SH2 = GGUF_DIR + r"\DeepSeek-V4-Flash-UD-IQ2_XXS-00002-of-00003.gguf"
SH3 = GGUF_DIR + r"\DeepSeek-V4-Flash-UD-IQ2_XXS-00003-of-00003.gguf"
L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l1"
N_LAY, N_EXP, N_NEU, TOPK, K_CLU = 43, 256, 2048, 10, 2048

def log(msg):
    print(msg, file=sys.stderr, flush=True)

def dequant_expert(t, e):
    ne = [int(x) for x in t.shape]
    oshape = tuple(reversed(ne))          # (256, 4096, 2048)
    raw = np.asarray(t.data)
    if raw.ndim == 1:
        raw = raw.reshape(quant_shape_to_byte_shape(oshape, t.tensor_type))
    # 单专家切片：raw[e] -> byte-shape (4096, bytes/row) -> dequant -> (4096, 2048)
    sl = raw[e]
    return gguf.quants.dequantize(sl, t.tensor_type)

def merge_group(best_ids, best_sc, cols, cand_ids, score_mat):
    """把一组神经元(cols)的候选打分并入运行 top10。
    best_*: (N_NEU, TOPK) 按行存——行=神经元，列=topk 槽位。
    score_mat: (|cand|, |cols|)；cand_ids: (|cand|,)"""
    if len(cols) == 0:
        return
    cur_sc = best_sc[cols].astype(np.float32)                  # (n, 10)
    cur_ids = best_ids[cols]                                   # (n, 10)
    M = score_mat.shape[0]
    big_sc = np.concatenate([cur_sc, score_mat.T.astype(np.float32)], axis=1)          # (n, 10+M)
    big_ids = np.concatenate([cur_ids,
                              np.broadcast_to(np.asarray(cand_ids, dtype=np.int32).reshape(1, M),
                                              (len(cols), M))], axis=1)                 # (n, 10+M)
    k = min(TOPK, big_sc.shape[1])
    idx = np.argpartition(-big_sc, k - 1, axis=1)[:, :k]        # (n, 10)
    take_sc = np.take_along_axis(big_sc, idx, axis=1)
    take_ids = np.take_along_axis(big_ids, idx, axis=1)
    order = np.argsort(-take_sc, axis=1)
    best_sc[cols] = np.take_along_axis(take_sc, order, axis=1)
    best_ids[cols] = np.take_along_axis(take_ids, order, axis=1).astype(np.int32)

def worker(wid, layers, tok_ids_path, sc_path, done_path):
    t0 = time.time()
    # L0 资产（v1.2 省内存：embed fp16 常驻 1.06GB，按候选切片转 fp32）
    Em16 = np.load(L0 + r"\embed_fp16.npy")
    C = np.load(L0 + r"\centers.npy").astype(np.float32)   # (K,4096)
    npz = np.load(L0 + r"\member_cap.npz")
    members = {int(k): npz[k] for k in npz.files}
    log("[w%d] L0 assets %.1fs" % (wid, time.time() - t0))

    r2 = gguf.GGUFReader(SH2)
    r3 = gguf.GGUFReader(SH3)
    by_name = {}
    for r in (r2, r3):
        for t in r.tensors:
            if "ffn_down_exps" in t.name:
                by_name[t.name] = t

    tok_out = np.load(tok_ids_path, mmap_mode="r+")   # full memmap, slice per layer
    sc_out = np.load(sc_path, mmap_mode="r+")

    for ln in layers:
        name = "blk.%d.ffn_down_exps.weight" % ln
        t = by_name.get(name)
        if t is None:
            log("[w%d] blk.%d MISSING -> -1" % (wid, ln))
            tok_out[ln] = -1
            continue
        try:
            best_ids = np.full((N_EXP, N_NEU, TOPK), -1, dtype=np.int32)
            best_sc = np.full((N_EXP, N_NEU, TOPK), -np.inf, dtype=np.float32)
            t_layer = time.time()
            for e in range(N_EXP):
                try:
                    W = dequant_expert(t, e)              # (4096, 2048)
                except Exception as ex:
                    log("[w%d] blk.%d expert %d dequant FAIL: %r" % (wid, ln, e, ex))
                    best_ids[e] = -1
                    continue
                # ---- stage1: centroid scores ----
                S = C @ W                                 # (K, 2048)
                top2c = np.argpartition(-S, 1, axis=0)[:2]  # (2, 2048)
                c1 = top2c[0]
                c2 = top2c[1]
                # ---- stage2a: top1 centroid grouped gemm ----
                order_c1 = np.argsort(c1)
                starts = np.flatnonzero(np.r_[True, c1[order_c1][1:] != c1[order_c1][:-1]])
                ends = np.r_[starts[1:], N_NEU]
                for s, e2 in zip(starts, ends):
                    cols = order_c1[s:e2]                  # 神经元组
                    cid = int(c1[cols[0]])
                    cand = members.get(cid, np.zeros(0, np.int32))
                    if len(cand) == 0:
                        continue
                    # 只对组内神经元列做 gemm（切列；否则成本爆炸 ×2048/组）
                    score = Em16[cand].astype(np.float32) @ W[:, cols]   # fp16→fp32 切片（省常驻内存）
                    merge_group(best_ids[e], best_sc[e], cols, cand, score)
                # ---- stage2b: top2 centroid per-neuron gemv ----
                for j in range(N_NEU):
                    cand2 = members.get(int(c2[j]), None)
                    if cand2 is None or len(cand2) == 0:
                        continue
                    sc2 = Em16[cand2].astype(np.float32) @ W[:, j]       # (|cand2|,)
                    merge_group(best_ids[e], best_sc[e], [j], cand2, sc2.reshape(-1, 1))
                if (e + 1) % 64 == 0:
                    log("[w%d] blk.%d expert %d/%d  %.0fs" % (wid, ln, e + 1, N_EXP, time.time() - t0))
            tok_out[ln] = best_ids
            sc_out[ln] = np.clip(best_sc, -32, 32).astype(np.float16)
            log("[w%d] blk.%d done in %.0fs" % (wid, ln, time.time() - t_layer))
        except Exception as ex:
            log("[w%d] blk.%d FAIL: %r" % (wid, ln, ex))
            tok_out[ln] = -1
    with open(done_path, "a") as f:
        f.write("w%d:%s\n" % (wid, ",".join(str(x) for x in layers)))
    log("[w%d] FINISHED %.0fs" % (wid, time.time() - t0))

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    tok_path = OUT + r"\concept_tok.npy"
    sc_path = OUT + r"\concept_sc.npy"
    if not os.path.exists(tok_path):
        np.lib.format.open_memmap(tok_path, mode="w+", dtype=np.int32, shape=(N_LAY, N_EXP, N_NEU, TOPK))[:] = -1
        np.lib.format.open_memmap(sc_path, mode="w+", dtype=np.float16, shape=(N_LAY, N_EXP, N_NEU, TOPK))
        log("[init] memmaps created (%.0f MB total)" % ((os.path.getsize(tok_path) + os.path.getsize(sc_path)) / 2**20))
    # 3 进程按层轮转
    # v1.1：4 worker（12 核 × 3 线程）+ 断点续跑（已完成层幂等跳过——OMG 事故恢复）
    done_layers = set()
    if os.path.exists(tok_path):
        tk_chk = np.load(tok_path, mmap_mode="r")
        for ln in range(N_LAY):
            if not np.all(tk_chk[ln] == -1):
                done_layers.add(ln)
        del tk_chk
    if done_layers:
        log("[resume] 已完成层跳过: %s" % sorted(done_layers))
    slices = [[ln for ln in list(range(w, N_LAY, 4)) if ln not in done_layers] for w in range(4)]
    procs = []
    for w in range(4):
        if not slices[w]:
            continue
        p = Process(target=worker, args=(w, slices[w], tok_path, sc_path, OUT + r"\done.txt"))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    # 验收统计
    tok = np.load(tok_path, mmap_mode="r")
    valid = int((tok >= 0).sum())
    total = N_LAY * N_EXP * N_NEU
    missing_layers = [ln for ln in range(N_LAY) if np.all(tok[ln] == -1)]
    meta = {
        "engine": "概念宇宙 LLM · L1 知识宇宙（V4-Flash FFN 逐层概念条目）",
        "shape": [N_LAY, N_EXP, N_NEU, TOPK],
        "valid_entries": valid,
        "coverage": round(valid / total, 4),
        "missing_layers": missing_layers,
        "method": "两段式：C@W_e 簇中心预选 + top1 组式 gemm/top2 逐神经元 gemv 精排（cap300/簇）",
        "approximation": "top-10 在 top-2 簇成员（≤600 词）内精排——近似全局 top-10，精确全词表版需 24 PFLOP 不可行（诚实标注）",
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "blk.26 等 UD 混合量化异常层 dequant 失败则该层落 -1 并在 stderr 照记；npz cap 300/簇截断可能漏低排名词",
    }
    with open(OUT + r"\meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
