# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 合一引擎 v1.1
v1.0 的词表错位修复：
  问题：Qwen LM 输出 Qwen token ID（0-151935），直接用 V4 tokenizer 解码 -> 乱码
  修复：双向映射层
    - q2v: Qwen ID -> text -> V4 ID（离线建表，一次）
    - 生成时 LM topk 后全部转 V4 ID 再融合
    - 解码统一用 V4 tokenizer
  另修：门模型改成 Qwen 只做打分器，输出候选永远在 V4 词表空间
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

W_LM_RANK = 1.0
W_TR = 0.6
W_SIM = 0.4
W_KN = 0.5

def log(m): print(m, file=sys.stderr, flush=True)

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from tokenizers import Tokenizer
    vt = Tokenizer.from_file(TOKJSON)  # V4 tokenizer

    bl_ids = set()
    for pat in BLACKLIST:
        for i in vt.encode(pat, add_special_tokens=False).ids:
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

    # ---- L1 ----
    tok1 = np.load(L1 + r"\concept_tok.npy", mmap_mode="r")
    valid_layers = [ln for ln in range(43) if not np.all(tok1[ln] == -1)]
    log("[L1] valid_layers=%s (%d/43)" % (valid_layers, len(valid_layers)))

    def knowledge_cands(cid, kn=8):
        out = []
        if not valid_layers: return out
        step = max(1, len(valid_layers)//3)
        for ln in valid_layers[::step][:3]:
            e = cid % 256
            for n_off in (0, 7, 13):
                n = (cid * 13 + n_off * 37) % 2048
                row = tok1[ln, e, n]
                out.extend(int(x) for x in row if 0 <= int(x) < V and int(x) not in bl_ids)
        seen = set(); res = []
        for x in out:
            if x not in seen: seen.add(x); res.append(x)
        return res[:kn]

    nxt = np.load(TR + r"\bigram_top5.npy")

    # ---- 门模型 + 双 tokenizer 映射 ----
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    torch.set_num_threads(6)
    from transformers import AutoTokenizer, AutoModelForCausalLM
    qt = AutoTokenizer.from_pretrained(QMODEL)
    qm = AutoModelForCausalLM.from_pretrained(QMODEL, dtype=torch.float32)
    qm.eval()
    log("[gate] loaded %.0fs" % (time.time()-t0))

    # 建 Qwen->V4 映射表（逐 token：Qwen ID -> text -> V4 IDs）
    # 只有单射部分可用（一对多时取第一个）
    map_path = OUT + r"\q2v_map.npy"
    if os.path.exists(map_path):
        q2v = np.load(map_path)
        log("[map] loaded existing")
    else:
        log("[map] building Qwen->V4 mapping...")
        q2v = np.full(151936, -1, dtype=np.int32)
        qt_vocab = qt.get_vocab()
        for qid in range(min(151936, len(qt_vocab))):
            try:
                text = qt.decode([qid])
                if not text or text.startswith("<") or "<|" in text:
                    continue
                vids = vt.encode(text, add_special_tokens=False).ids
                if len(vids) == 1:
                    q2v[qid] = vids[0]
            except:
                pass
        np.save(map_path, q2v)
        log("[map] built: %d mapped / 151936" % int((q2v >= 0).sum()))
    q2v_ok = q2v >= 0

    # 门调用：输入是 V4 ID -> decode 成 text -> Qwen encode -> forward -> top-k -> 映射回 V4
    def gate_topk(v4_ids, k=8):
        """返回 (v4_cands, v4_lp_scores, qwen_lp_full_truncated)"""
        text = vt.decode(v4_ids[-64:])
        qenc = qt.encode(text, add_special_tokens=False)
        qids = (qenc.ids if hasattr(qenc, "ids") else qenc)[-64:]
        if not qids:
            return [], [], None
        x = torch.tensor([qids], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[-1].float(), dim=-1)
        v_, i_ = torch.topk(lp, 32)  # 取 top-32 以留出映射损失余量
        cands = []
        for rank, (j, s) in enumerate(zip(i_, v_)):
            j = int(j)
            if q2v_ok[j]:
                cands.append((int(q2v[j]), float(s), 8 - min(rank, 8)))
            if len(cands) >= k:
                break
        return cands

    # ---- 生成 ----
    def generate(prompt, mode):
        ids = [i for i in vt.encode(prompt, add_special_tokens=False).ids if i < V] or [3]
        ctx = En[ids].mean(axis=0); ctx /= (np.linalg.norm(ctx) + 1e-12)
        cid = int(np.argmax(Cn @ ctx))
        cur = ids[0]
        gen = list(ids)
        recent = list(ids[-8:])
        hist = {}
        step_lps = []
        for step in range(N_GEN):
            gate_cands = gate_topk(gen, 8)  # [(v4_id, lp_score, rank_score)]
            a, b = indptr[cur], indptr[cur+1]
            sim_nb = dst_s[a:b].astype(np.int64)
            tr_list = [int(x) for x in nxt[cur] if 0 <= int(x) < V]
            kn_list = knowledge_cands(cid)
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
            # 候选池
            cands = set(int(x) for x in uni if 0 <= int(x) < V)
            lm_rank = {}
            lm_lp = {}
            for vid, s, r in gate_cands:
                cands.add(vid)
                lm_rank[vid] = r
                lm_lp[vid] = s
            # rank-based 融合
            best, best_sc, best_lp = -1, -1e18, -8.0
            rng_j = np.random.default_rng(sum(ids)*131 + step*17 + len(mode)*7)
            for c in cands:
                c = int(c)
                if c < 0 or c >= V: continue
                if c in recent or c in bl_ids: continue
                if hist.get(c,0) >= 3: continue
                sc = W_LM_RANK * lm_rank.get(c, -2)
                if c in tr_list: sc += W_TR
                if float(En[c] @ ctx) > 0.3: sc += W_SIM
                if c in kn_list: sc += W_KN
                sc -= 3.0 * hist.get(c, 0)
                sc += 0.05 * float(rng_j.random())
                if sc > best_sc:
                    best_sc = sc; best = c
                    best_lp = lm_lp.get(c, -8.0)
            if best < 0:
                for c in cands:
                    c = int(c)
                    if 0 <= c < V and hist.get(c,0) < 4 and c not in bl_ids:
                        best = c; best_lp = lm_lp.get(c, -8.0)
                        break
            if best < 0 or best >= V:
                best = int(sim_nb[0]) if len(sim_nb) else cur
                best_lp = -8.0
            gen.append(best)
            step_lps.append(best_lp)
            hist[best] = hist.get(best,0)+1
            recent = gen[-8:]
            cur = best
            ctx = 0.92*ctx + 0.08*En[best]; ctx /= (np.linalg.norm(ctx)+1e-12)
            cid = int(assign[cur])
        return gen[len(ids):], step_lps

    # ---- 跑 ----
    results = {}
    all_lp, all_ts = [], []
    for mode in MODES:
        for prompt in PROMPTS:
            tg = time.time()
            gen, lps = generate(prompt, mode)
            dt = time.time() - tg
            text = vt.decode(gen)  # 统一 V4 tokenizer 解码
            key = "%s|%s" % (mode, prompt)
            results[key] = {"text": text, "tok_s": round(N_GEN/dt, 2),
                            "mean_lp": round(float(np.mean(lps)), 3)}
            all_lp.extend(lps); all_ts.append(N_GEN/dt)
            log("[%s] %s: %.2f tok/s lp=%.3f | %s" % (mode, prompt, N_GEN/dt, np.mean(lps), text[:50]))

    merged = "".join(v["text"] for v in results.values())
    out = {
        "engine": "概念宇宙 LLM · 合一引擎 v1.1（词表映射修复 + rank融合 + B逃逸门 + L1知识）",
        "mean_tok_s": round(float(np.mean(all_ts)), 2),
        "mean_logprob": round(float(np.mean(all_lp)), 3),
        "diversity_char": round(len(set(merged))/max(len(merged),1), 3),
        "ge_m3_rate": round(sum(1 for x in all_lp if x >= -3.0)/max(len(all_lp),1), 3),
        "l1_layers_used": valid_layers,
        "l1_layer_count": len(valid_layers),
        "per_mode": {m: {
            "mean_tok_s": round(float(np.mean([v["tok_s"] for k,v in results.items() if k.startswith(m+"|")])), 2),
            "mean_lp": round(float(np.mean([v["mean_lp"] for k,v in results.items() if k.startswith(m+"|")])), 3),
        } for m in MODES},
        "samples": {k: v["text"][:120] for k, v in list(results.items())[:10]},
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "v1.1：Qwen top-32 经 q2v 映射表（单射部分）转 V4 ID；top-8 内 rank=0-7、外=-2；L1 用当下已有层（%d/43）" % len(valid_layers),
    }
    with open(OUT + r"\unified_result_v11.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("samples","per_mode","l1_layers_used")}, ensure_ascii=False, indent=1))
    log("[done] %.0fs" % (time.time()-t0))

if __name__ == "__main__":
    main()
