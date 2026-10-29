# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 转移宇宙 v3：从模型自身分布提取（知世原意版）
"知识内容和质量方向，难道不是与生俱来的吗？你都已经有权重和大语言模型本身了，
 你就不能从它里面提取出来？" —— 知世 2026-10-12 00:49

方法：不统计语料。用 V4-Flash 自身的结构：
  1. output head（norm.weight + output.weight）-> 每个概念簇的"天然后继分布"
     · 对每个概念簇中心 c，计算 output head 对 c 的投影 -> top-8 后继概念
     · 这是模型"想说什么"的分布，不是"说过什么"的统计
  2. ffn_gate_tid2eid [6, 129280] -> token->expert 的真实路由表
     · 模型自己决定每个 token 归哪个专家 -> 概念簇的"官方"归属（替代 kmeans）
  3. attention 结构 -> 关联边（wq_b/wo_b 的簇间投影）

产出：results/v4f_transfer_v3/
  model_transfer.npy  (2048, 8) int32 —— 簇->簇的模型自身转移 top-8
  model_transfer_sc.npy (2048, 8) fp16 —— 归一化分数
  tid2eid.npy         (129280,) int32 —— token->官方专家路由
  meta.json
"""
import sys, os, json, time, struct
import numpy as np

sys.path.insert(0, r"H:\llama.cpp\repo\gguf-py")
import gguf
from gguf.quants import quant_shape_to_byte_shape

L0 = r"H:\理论存档\01-数学\04-工具与_code\results\v4f_l0".replace("_code", r"_与_code").replace(r"_与_code", r"")
L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer_v3"
GGUF2 = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\DeepSeek-V4-Flash-UD-IQ2_XXS-00002-of-00003.gguf"

def log(m): print(m, file=sys.stderr, flush=True)

def deq(t):
    ne = [int(x) for x in t.shape]
    oshape = tuple(reversed(ne))
    raw = np.asarray(t.data)
    if raw.ndim == 1:
        raw = raw.reshape(quant_shape_to_byte_shape(oshape, t.tensor_type))
    return gguf.quants.dequantize(raw, t.tensor_type)

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)

    # ---- L0 资产 ----
    En = np.load(L0 + r"\embed_fp16.npy").astype(np.float32)
    En /= (np.linalg.norm(En, axis=1, keepdims=True) + 1e-12)
    C = np.load(L0 + r"\centers.npy").astype(np.float32)
    Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
    assign = np.load(L0 + r"\assign.npy")
    V, D = En.shape
    K = C.shape[0]
    log("[L0] V=%d D=%d K=%d" % (V, D, K))

    r = gguf.GGUFReader(GGUF2)
    by = {t.name: t for t in r.tensors}

    # ---- ① tid2eid：模型官方路由表 ----
    t2e_name = "blk.0.ffn_gate_tid2eid.weight"
    if t2e_name in by:
        t = by[t2e_name]
        raw = np.asarray(t.data)
        if str(t.tensor_type) == "GGMLQuantizationType.I32":
            tid2eid = np.frombuffer(raw.tobytes(), dtype=np.int32).reshape([int(x) for x in reversed(t.shape)])
            # shape [6, 129280] -> 每 token 前6个专家
            # 我们取第0个作为主专家
            tid2eid_main = tid2eid[0].copy()  # (129280,)
            np.save(OUT + r"\tid2eid.npy", tid2eid_main.astype(np.int32))
            log("[tid2eid] shape=%s unique=%s" % (tid2eid.shape, len(np.unique(tid2eid[0]))))
        else:
            log("[tid2eid] type=%s skip" % t.tensor_type)
            tid2eid_main = None
    else:
        log("[tid2eid] not found")
        tid2eid_main = None

    # ---- ② output head -> 簇的天然后继分布 ----
    # output.weight: (V, D) —— 词表->hidden 的投影矩阵
    # 用法：簇中心 c (D,) -> output.weight @ c -> (V,) = 模型在概念 c 处的输出倾向
    # top-8 -> 这些 token 的簇归属 = "这个概念之后模型天然倾向去哪些概念"
    out_name = "output.weight"
    if out_name in by:
        t = by[out_name]
        log("[output] type=%s shape=%s" % (t.tensor_type.name, [int(x) for x in t.shape]))
        OutW = deq(t)  # (V, D) 或 (D, V)——GGUF 里是 (V, D)
        log("[output] dequant done %.0fs  shape=%s" % (time.time()-t0, OutW.shape))
        # 确保方向：(V, D) @ (D,) -> (V,)
        if OutW.shape[0] != V:
            OutW = OutW.T  # 转置到 (V, D)
        OutW = OutW.astype(np.float32)
        # 批量：Cn (K, D) @ OutW.T (D, V) -> (K, V)
        log("[output] computing cluster->token scores (K=%d x V=%d)..." % (K, V))
        scores = Cn @ OutW.T  # (K, V)
        top8 = np.argsort(-scores, axis=1)[:, :8]  # (K, 8)
        # token -> 簇归属 = 转移目标
        top8_clusters = assign[top8.ravel()].reshape(K, 8)  # (K, 8)
        top8_scores = np.take_along_axis(scores, top8, axis=1)
        # 归一化
        top8_scores = top8_scores / (np.abs(top8_scores).max(axis=1, keepdims=True) + 1e-12)
        np.save(OUT + r"\model_transfer.npy", top8_clusters.astype(np.int32))
        np.save(OUT + r"\model_transfer_sc.npy", top8_scores.astype(np.float16))
        log("[transfer] K=%d -> 8 后继簇 saved" % K)
        # 样例：前5个簇的后继
        for k in range(5):
            log("  cluster %d -> %s (sc=%s)" % (k, top8_clusters[k][:4], np.round(top8_scores[k][:4], 2)))
    else:
        log("[output] not found; trying output_norm...")
        # 备用：用 attention 的 wq_b 做投影
        log("[fallback] using attention wq_b from blk.42")
        wq_name = "blk.42.attn.wq_b.weight"
        if wq_name in by:
            W = deq(by[wq_name]).astype(np.float32)  # (head*dim, rank) 或反
            log("[wq_b] shape=%s" % (W.shape,))
        else:
            log("[fallback] nothing found")

    # ---- ③ 关联宇宙：簇间 attention 关联（wo_b 簇投影） ----
    wo_name = "blk.0.attn.wo_b.weight"
    if wo_name in by:
        Wo = deq(by[wo_name]).astype(np.float32)  # (D, rank)
        log("[wo_b] shape=%s" % (Wo.shape,))
        # 簇 x 簇关联 = Cn @ Wo 的 rank 空间中相似度
        if Wo.shape[0] == D:
            proj = Cn @ Wo  # (K, rank)
        else:
            proj = Cn @ Wo.T
        proj /= (np.linalg.norm(proj, axis=1, keepdims=True) + 1e-12)
        # 簇间余弦相似 top-5（关联边）
        sim = proj @ proj.T  # (K, K)
        np.fill_diagonal(sim, -2)
        top5_j = np.argsort(-sim, axis=1)[:, :5]
        top5_s = np.take_along_axis(sim, top5_j, axis=1)
        keep = top5_s > 0.3  # 关联阈值
        np.savez_compressed(OUT + r"\attn_assoc.npz",
                            i=np.repeat(np.arange(K), 5)[keep.ravel()],
                            j=top5_j.ravel()[keep.ravel()],
                            s=top5_s.ravel()[keep.ravel()].astype(np.float16))
        log("[assoc] %d 条关联边（阈 0.3）" % int(keep.sum()))

    meta = {
        "engine": "概念宇宙 LLM · 转移宇宙 v3（模型自身分布版）",
        "principle": "知世原话：知识内容和质量方向，难道不是与生俱来的吗——不统计语料，直接从权重结构提取",
        "sources": {
            "tid2eid": "blk.0.ffn_gate_tid2eid [6,129280] I32 -> token 官方专家路由",
            "output_head": "output.weight -> 簇中心投影 -> 天然后继 top-8",
            "attn_assoc": "blk.0.attn.wo_b -> 簇投影余弦 -> 关联边（阈 0.3）",
        },
        "cluster_count": K,
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "v3 与 v1/v2 的区别：v1 从聊天记录统计（污染+天花板），v2 用 gate_inp（选型器），v3 用 output head（模型自己的'想说什么'分布）+ 官方路由表 + attention 关联——全部直接来自权重，零语料依赖",
    }
    with open(OUT + r"\meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
