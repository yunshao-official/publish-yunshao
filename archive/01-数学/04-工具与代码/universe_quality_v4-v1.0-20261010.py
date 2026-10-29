# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 全量质量攻坚 v4（简化版：稀疏影子 + MLP Memory）
核心改动：影子存储为 (top-1024 token_ids, probabilities) 稀疏对，不做全维度 mask。
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
BATCH = 32
SAMPLE_N = 20000
TOP_SHADOW = 512
HID_MLP = 2048
ALPHA = 0.4
EPOCHS = 3
LR = 4e-4

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    N, dim = Emb.shape
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    print(f"[load] vocab={N} dim={dim}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ① 采样 20000 词 ----
    rng = np.random.default_rng(42)
    sample_idx = np.sort(rng.choice(N, SAMPLE_N, replace=False))
    print(f"[sample] {SAMPLE_N} words  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ② 影子提取：稀疏 (top-512 indices, probs) ----
    t1 = time.time()
    # 每个 word 一个 shadow = softmax 后 top-512 (token_id, prob)
    shadow_indices = np.zeros((SAMPLE_N, TOP_SHADOW), dtype=np.int32)
    shadow_probs = np.zeros((SAMPLE_N, TOP_SHADOW), dtype=np.float32)
    store_emb = np.zeros((SAMPLE_N, dim), dtype=np.float32)

    with torch.no_grad():
        for s in range(0, SAMPLE_N, BATCH):
            e = min(s + BATCH, SAMPLE_N)
            batch_ids = sample_idx[s:e]
            texts = [tok.decode([int(i)]) + "。" for i in batch_ids]
            enc = [tok.encode(x, add_special_tokens=True) for x in texts]
            maxlen = max(len(x) for x in enc)
            pad_id = tok.pad_token_id if tok.pad_token_id is not None else 0
            mat = np.full((len(enc), maxlen), pad_id)
            for i, x in enumerate(enc):
                mat[i, :len(x)] = x
            out = model(torch.tensor(mat))
            for i, x in enumerate(enc):
                lg = torch.softmax(out.logits[i, len(x)-1].float(), dim=-1).numpy()
                top512 = lg.argsort()[::-1][:TOP_SHADOW]
                shadow_indices[s+i] = top512
                shadow_probs[s+i] = lg[top512]
                # store embedding = 该词自己的 embedding
                wid = batch_ids[i]
                store_emb[s+i] = En[wid]
            if (s // BATCH) % 100 == 0:
                print(f"  [shadow] {s}/{SAMPLE_N}  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)
    print(f"[shadow] done  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # ---- ③ 概念宇宙（kNN 分量 + 零点）----
    t2 = time.time()
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
            knn = np.argpartition(-row, 3)[:3]
            u = s + r
            for v in knn:
                ra, rb = find(u), find(int(v))
                if ra != rb: parent[rb] = ra
    roots = np.array([find(i) for i in range(N)])
    uniq, counts = np.unique(roots, return_counts=True)
    n_clusters = len(uniq)
    sizes = sorted(counts.tolist(), reverse=True)
    print(f"[universe] {n_clusters} clusters top5={sizes[:5]}  {time.time()-t2:.1f}s", file=sys.stderr, flush=True)

    # ---- ④ 构建 MLP Memory 训练集 ----
    # 输入 = store 词的 embedding（store_emb）
    # 教师 = kNN 检索分布（top-8 邻居影子均值）
    # 输出空间 = 全部 shadow_indices 的 union
    all_indices = set()
    for i in range(SAMPLE_N):
        for j in range(TOP_SHADOW):
            all_indices.add(shadow_indices[i, j])
    all_indices = sorted(all_indices)
    token_to_idx = {t: i for i, t in enumerate(all_indices)}
    OUT_DIM = len(all_indices)
    print(f"[output_space] {OUT_DIM} unique tokens  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 构建 dense 教师矩阵（SAMPLE_N × OUT_DIM）
    t3 = time.time()
    teacher = np.zeros((SAMPLE_N, OUT_DIM), dtype=np.float32)
    for i in range(SAMPLE_N):
        for j in range(TOP_SHADOW):
            tid = shadow_indices[i, j]
            if tid in token_to_idx:
                teacher[i, token_to_idx[tid]] = shadow_probs[i, j]
    # 归一化
    teacher = teacher / np.maximum(teacher.sum(axis=1, keepdims=True), 1e-12)
    print(f"[teacher] built  {time.time()-t3:.1f}s", file=sys.stderr, flush=True)

    # kNN 教师（top-8 邻居的教师均值——论文配方）
    Sm = torch.tensor(store_emb)
    Tm = torch.tensor(teacher)
    t4 = time.time()
    with torch.no_grad():
        for i in range(SAMPLE_N):
            sims = Sm @ store_emb[i]
            sims[i] = -2.0
            top = sims.argsort(descending=True)[:8]
            w = torch.clamp(sims[top], min=0)
            if w.sum() > 0:
                teacher[i] = (w[:, None] * Tm[top]).sum(0) / w.sum()
    teacher = teacher / np.maximum(teacher.sum(axis=1, keepdims=True), 1e-12)
    print(f"[knn_teacher] done  {time.time()-t4:.1f}s", file=sys.stderr, flush=True)

    # ---- ⑤ MLP Memory 训练 ----
    torch.manual_seed(42)
    mlp = nn.Sequential(
        nn.Linear(dim, HID_MLP), nn.GELU(),
        nn.Linear(HID_MLP, HID_MLP), nn.GELU(),
        nn.Linear(HID_MLP, OUT_DIM),
    )
    n_params = sum(p.numel() for p in mlp.parameters())
    print(f"[mlp] params={n_params/1e6:.1f}M", file=sys.stderr, flush=True)

    Xall = torch.tensor(store_emb)
    Tall = torch.tensor(teacher)
    tgt = torch.tensor(np.argmax(teacher, axis=1))

    opt = torch.optim.AdamW(mlp.parameters(), lr=LR, weight_decay=0.0)
    mlp.train()
    BATCH_TRAIN = 64
    t5 = time.time()
    for ep in range(EPOCHS):
        perm = torch.randperm(SAMPLE_N)
        tot = 0.0
        n_batches = 0
        for s in range(0, SAMPLE_N, BATCH_TRAIN):
            idx = perm[s:s+BATCH_TRAIN]
            logits = mlp(Xall[idx])
            logp = torch.log_softmax(logits, dim=-1)
            tq = Tall[idx]
            kl = (tq * (torch.log(torch.clamp(tq, min=1e-12)) - logp)).sum(dim=1).mean()
            ce = nn.functional.cross_entropy(logits, tgt[idx])
            loss = ALPHA * kl + (1-ALPHA) * ce
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss); n_batches += 1
        print(f"[train] ep{ep+1}/{EPOCHS} loss={tot/max(n_batches,1):.4f}  {time.time()-t5:.1f}s", file=sys.stderr, flush=True)
    mlp.eval()

    # ---- ⑥ 质量开票 ----
    test_prompts = ["人工智能的", "猫在", "医生说", "北京是", "水的沸点",
                    "爱情是", "战争的", "学习的", "宇宙的", "美食的"]
    mlp_ovs, tbl_ovs = [], []
    eval_detail = []
    with torch.no_grad():
        for pr in test_prompts:
            ids = tok.encode(pr, add_special_tokens=True)
            cv = En[ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
            # 原版 top-50
            out = model(torch.tensor([ids]))
            base_top50 = set(np.argsort(-out.logits[0, -1].float().numpy())[:50].tolist())
            # MLP top-30
            cv_t = torch.tensor(cv[None, :])
            logits_m = mlp(cv_t)[0].numpy()
            mlp_top30 = set(np.argsort(-logits_m)[:30].tolist())
            # 查表 top-30（最近 store 词的影子）
            sims = store_emb @ cv
            near = int(np.argmax(sims))
            near_top30 = set(shadow_indices[near][:30].tolist())
            mlp_ov = len(mlp_top30 & base_top50) / 30
            tbl_ov = len(near_top30 & base_top50) / 30
            mlp_ovs.append(mlp_ov); tbl_ovs.append(tbl_ov)
            eval_detail.append({"prompt": pr, "mlp": round(mlp_ov, 3), "tbl": round(tbl_ov, 3)})
            print(f"[eval] {pr} mlp={mlp_ov:.3f} tbl={tbl_ov:.3f}", file=sys.stderr, flush=True)

    mean_mlp = float(np.mean(mlp_ovs))
    mean_tbl = float(np.mean(tbl_ovs))
    improve = mean_mlp - mean_tbl

    # ---- 速度 ----
    t_sp = time.time()
    with torch.no_grad():
        for _ in range(200):
            _ = mlp(torch.tensor(cv[None, :]))
    mlp_ms = (time.time() - t_sp) / 200 * 1000
    tok_s = 1000.0 / mlp_ms

    out = {
        "model": MODEL,
        "universe": {"n_clusters": n_clusters, "top5": sizes[:5], "zero_MB": 0},
        "store": {"n": SAMPLE_N, "shadow_dim": TOP_SHADOW, "output_dim": OUT_DIM},
        "mlp_params_M": round(n_params/1e6, 1),
        "quality": {"mean_mlp_overlap": round(mean_mlp, 4),
                     "mean_tbl_overlap": round(mean_tbl, 4),
                     "improvement": round(improve, 4),
                     "detail": eval_detail},
        "speed": {"mlp_forward_ms": round(mlp_ms, 3), "tok_s_equivalent": round(tok_s, 0)},
        "verdict": ("MLP Memory 蒸馏有效（改进>0）" if improve > 0 else "蒸馏无效（查表更好）"),
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "全量=20000 采样词；影子=稀疏 top-512；输出空间=union of all shadows；EPOCHS=3；单模型 1.5B",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
