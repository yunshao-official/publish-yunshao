# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 投影构造器 v2 = Mini MLP Memory（按 arXiv:2508.01832 论文配方缩放）
教师：今天的 kNN store（2000 条 (语境向量, next-token 分布) 对——J-CC/J-H 线已建）
学生：mini MLP（1536→1024→8192 词输出空间，~1000 万参数——CPU 可训）
损失：ℒ = 0.4·KL(p_kNN ∥ p_MLP) + 0.6·CE(w_t)（论文配方 α=0.4）
优化：AdamW lr 4e-4, 5 epochs（论文配方）
对比：MLP Memory vs 直接查表（v1 构造器）的分布质量
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
STORE_SIZE = 2000
HID = 1024
OUT_WORDS = 8192
EPOCHS = 5
LR = 4e-4
ALPHA = 0.4
BATCH = 32

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N, dim = Emb.shape
    print(f"[load] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ① Store 构建（2000 词×6 模板轮换——同 v2 pureknn）----
    rng = np.random.default_rng(42)
    vocab_ids = list(range(N)); rng.shuffle(vocab_ids)
    store_ids, seen = [], set()
    TEMPLATES = ["请谈谈{w}。", "{w}是什么？", "关于{w}的事实。", "{w}的特点。", "介绍{w}。", "{w}的相关知识。"]
    for tid in vocab_ids:
        t = tok.decode([tid])
        if t.strip() and t not in seen and len(t) <= 12:
            seen.add(t); store_ids.append(tid)
        if len(store_ids) >= STORE_SIZE: break
    S, Ds_full = [], []
    t1 = time.time()
    with torch.no_grad():
        for si, tid in enumerate(store_ids):
            w = tok.decode([tid])
            sent = TEMPLATES[si % len(TEMPLATES)].replace("{w}", w)
            x = tok.encode(sent, add_special_tokens=True)
            out = model(torch.tensor([x]))
            lg = torch.softmax(out.logits[0, len(x)-1].float(), dim=-1).numpy()
            cv = En[x[1:len(x)-1]].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
            S.append(cv); Ds_full.append(lg)
    S = np.stack(S); Ds_full = np.stack(Ds_full)
    print(f"[store] {len(store_ids)}  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # 输出空间：全语料 top-OUT_WORDS 词
    mask_union = Ds_full.sum(axis=0).argsort()[::-1][:OUT_WORDS]
    Ds = Ds_full[:, mask_union]
    Ds = Ds / np.maximum(Ds.sum(axis=1, keepdims=True), 1e-12)
    gt_tok = np.argmax(Ds, axis=1)   # CE target=局部索引（mask_union 子空间内）

    # ---- ② Mini MLP Memory（论文架构：纯 MLP 栈）----
    torch.manual_seed(42)
    mlp = nn.Sequential(
        nn.Linear(dim, HID), nn.GELU(),
        nn.Linear(HID, HID), nn.GELU(),
        nn.Linear(HID, OUT_WORDS),
    )
    n_params = sum(p.numel() for p in mlp.parameters())
    print(f"[mlp] params={n_params/1e6:.1f}M  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    opt = torch.optim.AdamW(mlp.parameters(), lr=LR, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda e: min(1.0, 0.03/ max(e,1)) if e < 33 else max(0.0, 1 - (e-33)/(5*313/5 - 33)))
    Xall = torch.tensor(S)
    Dall = torch.tensor(Ds)
    tgt = torch.tensor(gt_tok)

    # 教师分布（kNN：同 store 内 top-8 邻居的分布加权——论文的教师= retriever）
    Sm = torch.tensor(S)
    t2 = time.time()
    teacher = torch.zeros(len(store_ids), OUT_WORDS)
    with torch.no_grad():
        for i in range(len(store_ids)):
            sims = Sm @ S[i]
            sims[i] = -2.0
            top = sims.argsort(descending=True)[:8]
            w = torch.clamp(sims[top], min=0)
            if w.sum() > 0:
                teacher[i] = (w[:, None] * Dall[top]).sum(0) / w.sum()
    print(f"[teacher] kNN dists  {time.time()-t2:.1f}s", file=sys.stderr, flush=True)

    # ---- ③ 训练（论文配方：KL 0.4 + CE 0.6，AdamW 4e-4，5 epochs）----
    t3 = time.time()
    mlp.train()
    steps_per_epoch = (len(store_ids) + BATCH - 1) // BATCH
    for ep in range(EPOCHS):
        perm = torch.randperm(len(store_ids))
        tot = 0.0
        for s in range(0, len(store_ids), BATCH):
            idx = perm[s:s+BATCH]
            logits = mlp(Xall[idx])
            logp = torch.log_softmax(logits, dim=-1)
            # KL(teacher || student)
            tq = teacher[idx] / torch.clamp(teacher[idx].sum(dim=1, keepdim=True), min=1e-12)
            kl = (tq * (torch.log(torch.clamp(tq, min=1e-12)) - logp)).sum(dim=1).mean()
            ce = nn.functional.cross_entropy(logits, tgt[idx])
            loss = ALPHA * kl + (1-ALPHA) * ce
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss)
        sched.step()
        print(f"[train] ep{ep+1}/{EPOCHS} loss={tot/steps_per_epoch:.4f}  {time.time()-t3:.1f}s", file=sys.stderr, flush=True)
    mlp.eval()

    # ---- ④ 推理对比：MLP Memory vs 查表（v1）vs 教师 kNN ----
    test_prompts = ["人工智能的", "猫在", "医生说", "北京是", "水的沸点"]
    evals = []
    with torch.no_grad():
        for pr in test_prompts:
            ids = tok.encode(pr, add_special_tokens=True)
            cv = En[ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
            # 原版基线（next-token top-50）
            out = model(torch.tensor([ids]))
            base_top50 = set(np.argsort(-out.logits[0, -1].float().numpy())[:50].tolist())
            # MLP Memory
            logits_m = mlp(torch.tensor(cv[None, :]))[0].numpy()
            mlp_top30 = set(mask_union[np.argsort(-logits_m)[:30]].tolist())
            # 查表（v1：最近零点簇……此处等价：store 最近条目的分布 top30）
            sims = S @ cv
            near = int(np.argmax(sims))
            tbl_top30 = set(mask_union[np.argsort(-Ds[near])[:30]].tolist())
            e_mlp = len(mlp_top30 & base_top50) / 30
            e_tbl = len(tbl_top30 & base_top50) / 30
            evals.append({"prompt": pr, "mlp_overlap": round(e_mlp, 3), "lookup_overlap": round(e_tbl, 3)})
            print(f"[eval] {pr} mlp={e_mlp:.2f} tbl={e_tbl:.2f}", file=sys.stderr, flush=True)
    mean_mlp = float(np.mean([e["mlp_overlap"] for e in evals]))
    mean_tbl = float(np.mean([e["lookup_overlap"] for e in evals]))

    # 推理速度（MLP 单次前向）
    t4 = time.time()
    with torch.no_grad():
        for _ in range(200):
            _ = mlp(torch.tensor(cv[None, :]))
    mlp_ms = (time.time() - t4) / 200 * 1000
    tok_s = 1000.0 / mlp_ms

    out = {
        "paper": "arXiv:2508.01832 (MLP Memory) 配方缩放版",
        "mlp_params_M": round(n_params/1e6, 1),
        "J-U6": {"mean_mlp_overlap": round(mean_mlp, 4), "mean_lookup_overlap": round(mean_tbl, 4),
                  "improvement": round(mean_mlp - mean_tbl, 4),
                  "note": "MLP Memory（蒸馏）vs 查表（v1）——正改进=蒸馏有效"},
        "speed": {"mlp_forward_ms": round(mlp_ms, 3), "tok_s_equivalent": round(tok_s, 0)},
        "evals": evals,
        "elapsed_s": round(time.time()-t0, 1),
        "frozen_doc": "J-CC系列判据纪律沿用；论文配方=arXiv:2508.01832（α=0.4/AdamW 4e-4/5ep）",
        "honest_note": "mini 版（10M 参数 vs 论文 1B；store 2000 vs 论文 5B token）——缩放验证版；速度为 MLP 前向不含采样",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
