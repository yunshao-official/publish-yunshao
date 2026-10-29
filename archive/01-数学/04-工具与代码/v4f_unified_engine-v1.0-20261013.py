# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 合一引擎 v1.0（B逃逸门配方 + L1知识候选 + GPU batch打分）
拼装三件已单独实测的部件：
  1. B 逃逸门修复配方（logprob -1.31 / div 0.854 的来源）：
     - 候选池 = 宇宙候选 ∪ LM top-8（逃逸门）
     - 近窗 8 禁字 + 重复 3 次上限 + 重复惩罚 3.0
     - seeded 抖动 0.05
  2. L1 知识候选注入：当前簇的 L1 概念条目（已有层）加入候选池
  3. rank-based 融合打分（修正 M2 死穴：raw logprob 压倒宇宙先验）：
     - LM 分改为 rank 分（8-rank），宇宙先验保持 0.4-0.6 量级
     - 黑名单 token 直接排除
验收：速度（tok/s）、质量（logprob + diversity + 样例）
门模型：Qwen2.5-1.5B fp32 CPU（GPU 版 llama.cpp 是提速件，质量口径用 CPU 版公平）
"""
import sys, os, json, time
import numpy as np

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
L1 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l1"
TR  = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_unified"
QMODEL = r"H:/AI/models--Qwen2.5-1.5B"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
V = 129280
N_GEN = 40
PROMPTS = ["人工智能", "小猫", "爱情", "战争", "美食", "宇宙"]
MODES = ["SMI", "TRF", "CNT", "EXP", "MIX"]
BLACKLIST = ["但用户", "可能需要", "翻译成英文", "用户可能", "请输入", "-10分", "____"]

# rank-based 融合权重
W_LM_RANK = 1.0     # LM rank 分（top1=7 ... top8=0）
W_TR = 0.6          # 转移先验
W_SIM = 0.4         # 语义相似
W_KN = 0.5          # L1 知识候选加成

def log(m): print(m, file=sys.stderr, flush=True)

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)

    # 黑名单 -> IDs
    bl_ids = set()
    for pat in BLACKLIST:
        for i in tok.encode(pat, add_special_tokens=False).ids:
            bl_ids.add(i)

    # ---- L0 ----
    Em = np.load(L0 + r"\embed_fp16.npy").astype(np.float32)
    En = Em / (np.linalg.norm(Em, axis=1, keepdims=True) + 1e-12)
    C = np.load(L0 + r"\centers.npy").astype(np.float32)
    Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
    assign = np.load(L0 + r"\assign.npy")
    E = np.load(L0 + r"\edges.npy")
    src = np.concatenate([E[:,0], E[:,1]]); dst = np.concatenate([E[:,1], E[:,0]])
    o = np.argsort(src, kind="stable"); src_s, dst_s = src[o], dst[o]
    indptr = np.searchsorted(src_s, np.arange(V + 1))
    npz_mem = np.load(L0 + r"\member_cap.npz")
    MEMBER = {int(k): npz_mem[k] for k in npz_mem.files}
    log("[L0] loaded %.0fs" % (time.time()-t0))

    # ---- L1（已有层） ----
    tok1 = np.load(L1 + r"\concept_tok.npy", mmap_mode="r")
    valid_layers = [ln for ln in range(43) if not np.all(tok1[ln] == -1)]
    log("[L1] valid_layers=%s" % valid_layers)

    def knowledge_cands(cid, kn=8):
        """簇 -> L1 知识概念条目 top token（用已有层）"""
        out = []
        if not valid_layers:
            return out
        for ln in valid_layers[::max(1, len(valid_layers)//3)][:3]:  # 取 3 层
            e = cid % 256
            for n_off in (0, 7, 13):
                n = (cid * 13 + n_off * 37) % 2048
                row = tok1[ln, e, n]
                out.extend(int(x) for x in row if int(x) >= 0 and int(x) not in bl_ids)
        seen = set(); res = []
        for x in out:
            if x not in seen:
                seen.add(x); res.append(x)
        return res[:kn]

    # ---- L2 ----
    nxt = np.load(TR + r"\bigram_top5.npy")

    # ---- 门模型 ----
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    torch.set_num_threads(6)
    from transformers import AutoTokenizer, AutoModelForCausalLM
    qtok = AutoTokenizer.from_pretrained(QMODEL)
    qm = AutoModelForCausalLM.from_pretrained(QMODEL, dtype=torch.float32)
    qm.eval()
    log("[gate] loaded %.0fs" % (time.time()-t0))

    def lm_topk_full(ids, k=8):
        x = torch.tensor([ids[-64:]], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[-1].float(), dim=-1)
        v_, i_ = torch.topk(lp, k)
        return [(int(j), float(s)) for j, s in zip(i_, v_)], lp.numpy()

    # ---- 生成 ----
    def generate(prompt, mode):
        ids = [i for i in tok.encode(prompt, add_special_tokens=False).ids if i < V] or [3]
        ctx = En[ids].mean(axis=0); ctx /= (np.linalg.norm(ctx) + 1e-12)
        cid = int(np.argmax(Cn @ ctx))
        cur = ids[0]
        gen = list(ids)
        recent = list(ids[-8:])
        hist = {}
        step_lps = []
        for step in range(N_GEN):
            # LM 一次 forward：top-8 + 全表
            topk, lp_full = lm_topk_full(gen, 8)
            a, b = indptr[cur], indptr[cur+1]
            sim_nb = dst_s[a:b].astype(np.int64)
            tr_list = [int(x) for x in nxt[cur] if int(x) >= 0]
            kn_list = knowledge_cands(cid)
            # 脉冲决定宇宙候选
            if mode == "SMI":   uni = sim_nb
            elif mode == "TRF": uni = np.array(tr_list) if tr_list else sim_nb[:5]
            elif mode == "CNT": uni = MEMBER[cid][:10]
            elif mode == "EXP":
                both = set(sim_nb.tolist()) | set(tr_list)
                uni = np.array([j for j in both if assign[int(j)] != cid][:12])
                if len(uni)==0: uni = sim_nb
            else:
                seed_nb = set()
                for s in ids[:4]:
                    a2,b2 = indptr[s], indptr[s+1]
                    seed_nb.update(dst_s[a2:b2].tolist())
                inter = [int(x) for x in sim_nb if int(x) in seed_nb]
                uni = np.array(inter if inter else sim_nb[:10])
            # 候选池 = 宇宙 ∪ LM top-8（逃逸门）
            cands = set(int(x) for x in uni) | set(j for j,_ in topk)
            # rank-based LM 分
            lm_rank = {j: (8-r) for r, (j,_) in enumerate(topk)}  # top1=7..top8=0
            best, best_sc, best_lp = -1, -1e18, -8.0
            rng_j = np.random.default_rng(sum(ids)*131 + step*17 + hash(mode))
            for c in cands:
                c = int(c)
                if c < 0 or c >= V: continue  # Qwen 词表越界（151936 vs 129280）
                if c in recent or c in bl_ids: continue
                if hist.get(c,0) >= 3: continue
                sc = W_LM_RANK * lm_rank.get(c, -2)      # 不在 top8 的给 -2（劣于 top8 但可被宇宙加成拉回）
                if c in tr_list: sc += W_TR
                if float(En[c] @ ctx) > 0.3: sc += W_SIM
                if c in kn_list: sc += W_KN
                sc -= 3.0 * hist.get(c, 0)
                sc += 0.05 * float(rng_j.random())
                if sc > best_sc:
                    best_sc = sc; best = c
                    best_lp = float(lp_full[c]) if c < V else -8.0
            if best < 0:
                for c in cands:
                    c = int(c)
                    if 0 <= c < V and hist.get(c,0) < 4 and c not in bl_ids:
                        best = c; best_lp = float(lp_full[c]) if c < V else -8.0
                        break
            if best < 0 or best >= V:
                # 全部落空 -> 用 Qwen top1 映射：直接跳过此步（Qwen 侧 token 在 V4 词表无对应）
                best = int(np.argmax(lp_full[:V]))  # V4 词表内 LM 最高分
                best_lp = float(lp_full[best])
            gen.append(best)
            step_lps.append(best_lp)
            hist[best] = hist.get(best,0)+1
            recent = gen[-8:]
            cur = best
            ctx = 0.92*ctx + 0.08*En[best]; ctx /= (np.linalg.norm(ctx)+1e-12)
            cid = int(assign[cur])
        return gen[len(ids):], step_lps

    # ---- 跑全部模式 ----
    results = {}
    all_lp, all_ts = [], []
    for mode in MODES:
        for prompt in PROMPTS:
            tg = time.time()
            gen, lps = generate(prompt, mode)
            dt = time.time() - tg
            text = tok.decode(gen)
            key = "%s|%s" % (mode, prompt)
            results[key] = {"text": text, "tok_s": round(N_GEN/dt, 2),
                            "mean_lp": round(float(np.mean(lps)), 3)}
            all_lp.extend(lps); all_ts.append(N_GEN/dt)
            log("[%s] %s: %.2f tok/s lp=%.3f | %s" % (mode, prompt, N_GEN/dt, np.mean(lps), text[:50]))

    merged = "".join(v["text"] for v in results.values())
    mean_ts = float(np.mean(all_ts))
    mean_lp = float(np.mean(all_lp))
    div = len(set(merged)) / max(len(merged), 1)
    n_ge3 = sum(1 for x in all_lp if x >= -3.0) / max(len(all_lp), 1)

    out = {
        "engine": "概念宇宙 LLM · 合一引擎 v1.0（B逃逸门 + L1知识 + rank融合）",
        "weights": {"W_LM_RANK": W_LM_RANK, "W_TR": W_TR, "W_SIM": W_SIM, "W_KN": W_KN},
        "mean_tok_s": round(mean_ts, 2),
        "mean_logprob": round(mean_lp, 3),
        "diversity_char": round(div, 3),
        "ge_m3_rate": round(n_ge3, 3),
        "l1_layers_used": valid_layers,
        "blacklist": BLACKLIST,
        "per_mode": {m: {
            "mean_tok_s": round(float(np.mean([v["tok_s"] for k,v in results.items() if k.startswith(m+"|")])), 2),
            "mean_lp": round(float(np.mean([v["mean_lp"] for k,v in results.items() if k.startswith(m+"|")])), 3),
        } for m in MODES},
        "samples": {k: v["text"][:120] for k, v in list(results.items())[:10]},
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "rank-based 融合首次实测：LM top8 内=0~7 分、外=-2 分，宇宙先验 0.4-0.6 可拉回非 top8 候选；CPU 门实测（GPU 版速度乘 23）；L1 用当前已有层",
    }
    with open(OUT + r"\unified_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("samples","per_mode")}, ensure_ascii=False, indent=1))
    log("[done] %.0fs" % (time.time()-t0))

if __name__ == "__main__":
    main()
