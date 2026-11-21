# -*- coding: utf-8 -*-
"""
概念宇宙 LLM v2 · 纯 kNN 模式（λ=1 无原模型前向）+ store 扩容 2000 条
速度目标：≥100 tok/s 实测（J-U5）
质量目标：store 扩容后的生成多样性/连贯性样例
纯计算零写盘版。stdout JSON。
"""
import os, sys, json, time, random
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
KNN_K = 8
N_GEN = 500
STORE_TARGET = 2000
TEMPLATES = ["请谈谈{w}。", "{w}是什么？", "关于{w}的事实。", "{w}的特点。", "介绍{w}。", "{w}的相关知识。"]

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N, dim = Emb.shape
    print(f"[load] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- store 词选择：2000 词（含中文的完整词优先+均匀补充）----
    rng = np.random.default_rng(42)
    vocab_ids = list(range(N))
    rng.shuffle(vocab_ids)
    store_ids = []
    seen_txt = set()
    for tid in vocab_ids:
        t = tok.decode([tid])
        if len(t) >= 1 and t.strip() and t not in seen_txt and ('是' in t or any('\u4e00' <= ch <= '\u9fff' for ch in t)):
            seen_txt.add(t); store_ids.append(tid)
        if len(store_ids) >= STORE_TARGET:
            break
    # 补足
    for tid in vocab_ids:
        if len(store_ids) >= STORE_TARGET: break
        if tid not in store_ids:
            t = tok.decode([tid])
            if t.strip() and t not in seen_txt:
                seen_txt.add(t); store_ids.append(tid)
    print(f"[store_words] {len(store_ids)}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- store 构建：每词×1 模板（轮换）→（语境向量，next-token 分布）----
    S_list, Ds_list, word_of = [], [], []
    t1 = time.time()
    with torch.no_grad():
        for si, tid in enumerate(store_ids):
            w = tok.decode([tid])
            tpl = TEMPLATES[si % len(TEMPLATES)]
            sent = tpl.replace("{w}", w)
            x = tok.encode(sent, add_special_tokens=True)
            out = model(torch.tensor([x]))
            lg = torch.softmax(out.logits[0, len(x)-1].float(), dim=-1).numpy()
            cv = En[x[1:len(x)-1]].mean(axis=0) if len(x) > 2 else En[x[0]]
            cv = cv / (np.linalg.norm(cv) + 1e-12)
            S_list.append(cv); Ds_list.append(lg); word_of.append(w)
    S = np.stack(S_list); Ds = np.stack(Ds_list)
    M = len(store_ids)
    print(f"[store] {M} entries  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # ---- 纯 kNN 生成函数（无原模型前向！）----
    def generate_pure_knn(prompt, n_tokens):
        ids = tok.encode(prompt, add_special_tokens=True)
        gen = []
        ctx = En[ids].mean(axis=0)
        with torch.no_grad():
            for _ in range(n_tokens):
                cv = En[ids[-64:]].mean(axis=0)
                cv = cv / (np.linalg.norm(cv) + 1e-12)
                sims = S @ cv
                top = np.argsort(-sims)[:KNN_K]
                p_knn = np.zeros(N)
                for ti in top:
                    w_sim = max(float(S[ti] @ cv), 0.0)
                    p_knn += w_sim * Ds[ti]
                if p_knn.sum() <= 0:
                    nid = int(rng.integers(0, N))
                else:
                    p = p_knn / p_knn.sum()
                    nid = int(rng.choice(N, p=p))
                gen.append(nid); ids.append(nid)
        return gen

    # ---- 速度实测：500 token 纯 kNN ----
    t_gen = time.time()
    gen1 = generate_pure_knn("人工智能的发展", N_GEN)
    sp = N_GEN / (time.time() - t_gen)

    # ---- 质量样例（3 prompt×40 token）----
    samples = {}
    for pr in ("人工智能", "猫", "人生的意义"):
        g = generate_pure_knn(pr, 40)
        samples[pr] = tok.decode(g)

    # 多样性
    alltxt = "".join(samples.values())
    uniq_ratio = len(set(alltxt)) / max(len(alltxt), 1)

    out = {
        "engine": "概念宇宙 LLM v2 · 纯 kNN 模式（λ=1）",
        "store_size": M, "knn_k": KNN_K,
        "speed": {"tokens": N_GEN, "tok_per_sec": round(sp, 1),
                  "J-U5": ("PASS（纯 kNN ≥100 tok/s 实测）" if sp >= 100 else f"FAIL（{sp:.1f}）")},
        "diversity_ratio": round(uniq_ratio, 3),
        "samples": samples,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "store=词表抽样 2000 词（非人工筛选）；质量为 v2 初值",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
