# -*- coding: utf-8 -*-
"""
概念宇宙 v2 过夜管线：50 概念扩集 → 影子提取（batch）→ 真·语义等价类 → 构造器 v2 质量对比
修正 v1 两大根因：①聚类空间=影子 JSD（语义）而非 embedding（字面）；②扩集=embedding top-20 相关词
纯计算零写盘版（stdout JSON）。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
TOPK_REL = 15   # 每概念扩集：embedding top-15 相关词
BATCH = 32

CONCEPTS = {
    "猫": "猫", "死亡": "死亡", "愤怒": "愤怒", "快乐": "快乐", "勇敢": "勇敢",
    "海洋": "大海", "花": "花朵", "朋友": "朋友", "时间": "时间", "自由": "自由",
    "太阳": "太阳", "书": "书", "医生": "医生", "音乐": "音乐", "和平": "和平",
}
NEUTRAL = "请谈谈{w}。"

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N, dim = Emb.shape
    print(f"[load] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ① 扩集：每概念 = 种子词 + embedding top-15 相关词（去碎片：只留含中文或纯字母≥3 的）----
    def ok_word(t):
        return len(t) >= 2 and (" " not in t) and ("\n" not in t)
    universe = {}   # concept -> [token ids]
    seed_words = []
    for c, seed in CONCEPTS.items():
        sid = tok.encode(seed, add_special_tokens=False)
        cv = En[sid].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
        sims = En @ cv
        top = np.argsort(-sims)[:TOPK_REL+8]
        picked = [seed]
        for ti in top:
            t = tok.decode([int(ti)])
            if ok_word(t) and t not in picked:
                picked.append(t)
            if len(picked) >= TOPK_REL:
                break
        universe[c] = picked   # 修：按词字符串存成员（v1.1 bug=存 token id 查字符串）
        seed_words.extend(picked)
    all_words = sorted(set(seed_words))
    print(f"[expand] {len(CONCEPTS)} concepts, {len(all_words)} unique words  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ② 影子提取（batch=32，中性语境）----
    Sents = [NEUTRAL.replace("{w}", w) for w in all_words]
    idx_of = {w: i for i, w in enumerate(all_words)}
    shadows = np.zeros((len(all_words), N), dtype=np.float32)   # 全 logits 暂存（~60MB）
    mask_union = np.zeros(N, dtype=bool)
    t1 = time.time()
    with torch.no_grad():
        for s in range(0, len(Sents), BATCH):
            batch = Sents[s:s+BATCH]
            enc = [tok.encode(x, add_special_tokens=True) for x in batch]
            maxlen = max(len(x) for x in enc)
            pad = tok.pad_token_id if tok.pad_token_id is not None else 0
            mat = np.full((len(enc), maxlen), pad)
            for i, x in enumerate(enc):
                mat[i, :len(x)] = x
            out = model(torch.tensor(mat))
            for i, x in enumerate(enc):
                shadows[s+i] = torch.softmax(out.logits[i, len(x)-1].float(), dim=-1).numpy()
            top = shadows[s:s+len(enc)].sum(axis=0).argsort()[::-1][:512]
            mask_union[top] = True
    print(f"[shadow] {len(Sents)} done  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)
    sub = np.nan_to_num(shadows[:, mask_union], nan=0.0, posinf=0.0, neginf=0.0)
    Q = sub / np.maximum(sub.sum(axis=1, keepdims=True), 1e-12)

    # ---- ③ 真·语义等价类（影子空间的类内/类间）----
    def jsd(p, q):
        m = 0.5 * (p + q)
        def kl(x):
            mask = x > 1e-12
            return float(np.sum(x[mask] * np.log2(x[mask] / m[mask])))
        return float(np.sqrt(max(0.5 * kl(p) + 0.5 * kl(q), 0.0)))
    print("[debug] Q nan:", int(np.isnan(Q).sum()), " Q行零和:", int((Q.sum(axis=1)==0).sum()), " 行数:", Q.shape[0], file=sys.stderr, flush=True)
    word_concept = {}
    for c, ws in universe.items():
        for w in ws:
            word_concept[w] = c
    words_in_universe = [w for w in all_words if w in word_concept]
    M = len(words_in_universe)
    idx_list = [idx_of[w] for w in words_in_universe]
    Qm = Q[idx_list]
    # 预计算 M×M JSD 矩阵（向量化分块——一次算完，置换只查表）
    Dm = np.zeros((M, M))
    for i in range(M):
        m = 0.5 * (Qm[i][None, :] + Qm[i+1:])
        kl_i = np.where(Qm[i][None, :] > 1e-12, Qm[i][None, :] * np.log2(np.maximum(Qm[i][None, :] / m, 1e-12)), 0).sum(axis=1)
        mj = Qm[i+1:] > 1e-12
        kl_j = np.where(mj, Qm[i+1:] * np.log2(np.maximum(Qm[i+1:] / m, 1e-12)), 0).sum(axis=1)
        dd = np.sqrt(np.maximum(0.5 * kl_i + 0.5 * kl_j, 0))
        Dm[i, i+1:] = dd; Dm[i+1:, i] = dd
    intra, inter = [], []
    for i in range(M):
        for j in range(i+1, M):
            (intra if word_concept[words_in_universe[i]] == word_concept[words_in_universe[j]] else inter).append(Dm[i, j])
    obs = float(np.mean(inter) - np.mean(intra))
    rng = np.random.default_rng(42)
    lab = [word_concept[w] for w in words_in_universe]
    cnt = 0
    for _ in range(5000):
        sh = rng.permutation(lab)
        ia, ie = [], []
        for a in range(M):
            for b in range(a+1, M):
                (ia if sh[a] == sh[b] else ie).append(Dm[a, b])
        if float(np.mean(ie) - np.mean(ia)) >= obs:
            cnt += 1
    p_perm = float((cnt + 1) / 5001)
    # 注意：全对 JSD 重算量大（15词×15概念≈100 词→4950 对×2 次）——可控
    verdict_A = ("PASS（影子空间等价类成立·语义聚类修正版）" if obs > 0 and p_perm < 0.05 else "FAIL（判负照记）")

    # ---- ④ 构造器 v2 质量对比（影子均值分布 vs 原版 next-token）----
    overlaps = []
    detail = []
    for c, seed in CONCEPTS.items():
        ids_c = universe[c]
        # 概念影子 = 成员影子均值（语义等价类的构造形态）
        member_rows = [idx_of[w] for w in all_words if w in word_concept and word_concept[w] == c]
        if not member_rows: continue
        concept_shadow = Q[member_rows].mean(axis=0)
        concept_shadow = concept_shadow / concept_shadow.sum()
        top_c = set(np.argsort(-concept_shadow)[:30].tolist())
        # 原版：seed 语境 next-token top-50
        ids = tok.encode(f"请谈谈{seed}。", add_special_tokens=True)
        with torch.no_grad():
            out = model(torch.tensor([ids]))
        base_top50 = set(np.argsort(-out.logits[0, -1].float().numpy())[:50].tolist())
        ov = len(top_c & base_top50) / 30
        overlaps.append(ov)
        detail.append({"concept": c, "overlap": round(ov, 2)})
    j_u3_v2 = float(np.mean(overlaps))

    out = {
        "model": MODEL,
        "expA_semantic_equiv": {"intra": round(float(np.mean(intra)),4), "inter": round(float(np.mean(inter)),4),
                                 "diff": round(obs,4), "p_perm": p_perm, "verdict": verdict_A},
        "expB_constructor_v2": {"mean_overlap_top30_in_base50": round(j_u3_v2, 4), "detail": detail},
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "语义空间=影子 JSD（修正 v1 的 embedding 字面空间）；构造器 v2=概念影子均值分布 vs 原版 next-token",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
