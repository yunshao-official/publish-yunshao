# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 合一引擎 v1.2（图导航为主 + 逃逸门降级 + 转移宇宙 v3）
知世方向修正版：
  - 生成主决策 = 宇宙图遍历（rank 融合内部决策，速度优先）
  - LM 只做逃逸门：连续 2 次图候选全被否（重复/黑名单/越界）才调 LM
  - 转移边 = 模型自身 output head 分布（v3），不是语料 bigram
  - 质量验收 = 独立打分（事后 Qwen teacher-forcing，不参与生成）
"""
import sys, os, json, time
import numpy as np

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0_v2"  # 语言分区版（修复语种沙拉）
L0_FALLBACK = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
if not os.path.exists(L0 + r"\centers.npy"):
    L0 = L0_FALLBACK
L1 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l1"
TR3 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer_v3"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_unified"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
QMODEL = r"H:/AI/models--Qwen2.5-1.5B"
V = 129280
N_GEN = 40
PROMPTS = ["人工智能", "小猫", "爱情", "战争", "美食", "宇宙"]
MODES = ["SMI", "TRF", "CNT", "EXP", "MIX"]
BLACKLIST = ["但用户", "可能需要", "翻译成英文", "用户可能", "请输入", "-10分", "____"]
ESCRIPT = 2  # 连续 2 次图决策失败才调 LM

# 宇宙内部决策权重（无 LM）
W_TR3 = 1.0   # 模型转移分布（output head）
W_SIM = 0.5   # 语义相似
W_KN = 0.4    # L1 知识
W_CO = 0.3    # attention 关联

def log(m): print(m, file=sys.stderr, flush=True)

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from tokenizers import Tokenizer
    vt = Tokenizer.from_file(TOKJSON)

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
    labels_p = L0 + r"\labels.npy"
    if os.path.exists(labels_p):
        _lab = np.load(labels_p)
        labels = np.array([{"CJK":0,"LAT":1,"CYR":2,"ARA":3,"NUM":4,"SYM":5}.get(str(x),5) for x in _lab], dtype=np.int32)
    else:
        labels = np.zeros(V, dtype=np.int32)
    K = C.shape[0]
    log("[L0] K=%d edges=%d island=%s" % (K, len(E), "on" if os.path.exists(labels_p) else "off"))

    # ---- L1 ----
    tok1 = np.load(L1 + r"\concept_tok.npy", mmap_mode="r")
    valid_layers = [ln for ln in range(43) if not np.all(tok1[ln] == -1)]
    log("[L1] %d/43 layers" % len(valid_layers))

    def knowledge_cands(cid, kn=6):
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

    # ---- 转移宇宙 v3：模型自身分布 ----
    tr3_path = TR3 + r"\model_transfer.npy"
    if os.path.exists(tr3_path):
        tr3 = np.load(tr3_path)          # (K, 8) 簇->簇
        tr3_sc = np.load(TR3 + r"\model_transfer_sc.npy")  # (K, 8) fp16
        log("[TR3] loaded shape=%s" % (tr3.shape,))
        # 簇->该簇后继簇的所有成员 token = 转移候选
        tr3_cand = {}
        for k in range(K):
            toks = []
            for cj in tr3[k]:
                cj = int(cj)
                if 0 <= cj < K:
                    toks.extend(MEMBER.get(cj, [])[:6].tolist())
            tr3_cand[k] = [t for t in toks if t not in bl_ids][:20]
        log("[TR3] built candidate pools for %d clusters" % len(tr3_cand))
    else:
        log("[TR3] NOT FOUND - falling back to bigram v1")
        tr3_cand = None

    # attention 关联
    assoc_path = TR3 + r"\attn_assoc.npz"
    cooc_w = {}
    if os.path.exists(assoc_path):
        az = np.load(assoc_path)
        for i, j, s in zip(az["i"], az["j"], az["s"]):
            cooc_w[(int(i), int(j))] = float(s)

    # ---- 逃逸门（LM）——只挂载不常调 ----
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    torch.set_num_threads(6)
    from transformers import AutoTokenizer, AutoModelForCausalLM
    qt = AutoTokenizer.from_pretrained(QMODEL)
    qm = AutoModelForCausalLM.from_pretrained(QMODEL, dtype=torch.float32)
    qm.eval()

    # q2v 映射（v1.1 已建）
    map_path = OUT + r"\q2v_map.npy"
    if os.path.exists(map_path):
        q2v = np.load(map_path)
    else:
        q2v = np.full(151936, -1, dtype=np.int32)
        for qid in range(151936):
            try:
                text = qt.decode([qid])
                if not text or text.startswith("<") or "<|" in text: continue
                vids = vt.encode(text, add_special_tokens=False).ids
                if len(vids) == 1: q2v[qid] = vids[0]
            except: pass
        np.save(map_path, q2v)
    q2v_ok = q2v >= 0
    log("[gate] loaded+mapped %.0fs" % (time.time()-t0))

    gate_calls = [0]  # 计数器
    def escape_gate(gen_ids):
        """逃逸门：LM 出 top-8，映射到 V4 词表"""
        gate_calls[0] += 1
        text = vt.decode(gen_ids[-64:])
        qenc = qt.encode(text, add_special_tokens=False)
        qids = (qenc.ids if hasattr(qenc, "ids") else qenc)[-64:]
        if not qids: return []
        x = torch.tensor([qids], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[-1].float(), dim=-1)
        v_, i_ = torch.topk(lp, 32)
        cands = []
        for rank, (j, s) in enumerate(zip(i_, v_)):
            j = int(j)
            if j < len(q2v) and q2v_ok[j]:
                cands.append((int(q2v[j]), float(s)))
            if len(cands) >= 8: break
        return cands

    # ---- 生成（图导航为主） ----
    def generate(prompt, mode):
        ids = [i for i in vt.encode(prompt, add_special_tokens=False).ids if i < V] or [3]
        ctx = En[ids].mean(axis=0); ctx /= (np.linalg.norm(ctx) + 1e-12)
        cid = int(np.argmax(Cn @ ctx))
        cur = ids[0]
        gen = list(ids)
        recent = list(ids[-8:])
        hist = {}
        fail_streak = 0
        for step in range(N_GEN):
            # --- 图候选（主决策路径） ---
            a, b = indptr[cur], indptr[cur+1]
            sim_nb = dst_s[a:b].astype(np.int64)
            kn_list = knowledge_cands(cid)
            if tr3_cand is not None:
                tr_list = [int(t) for t in tr3_cand.get(cid, []) if int(t) not in recent and 0 <= int(t) < V]
            else:
                nxt_v1 = np.load(r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer\bigram_top5.npy")
                tr_list = [int(x) for x in nxt_v1[cur] if 0 <= int(x) < V and int(x) not in bl_ids]

            if mode == "SMI":   uni = list(int(x) for x in sim_nb)
            elif mode == "TRF": uni = list(tr_list)
            elif mode == "CNT": uni = list(int(x) for x in MEMBER[cid][:10])
            elif mode == "EXP":
                both = set(int(x) for x in sim_nb) | set(int(x) for x in tr_list)
                uni = [int(j) for j in both if assign[int(j)] != cid][:12] or list(int(x) for x in sim_nb)
            else:
                seed_nb = set()
                for s in ids[:4]:
                    a2,b2 = indptr[s], indptr[s+1]
                    seed_nb.update(int(x) for x in dst_s[a2:b2])
                inter = [int(x) for x in sim_nb if int(x) in seed_nb]
                uni = inter or list(int(x) for x in sim_nb[:10])

            cands = set(int(x) for x in list(uni) + list(kn_list) if 0 <= int(x) < V and int(x) not in bl_ids)

            # --- 宇宙内部决策（rank 融合，无 LM） ---
            best, best_sc = -1, -1e18
            rng_j = np.random.default_rng(sum(ids)*131 + step*17 + len(mode)*7)
            tr_set = set(tr_list)
            tr3_row = list(tr3[cid]) if (tr3_cand is not None and cid < tr3.shape[0]) else []
            my_island = int(labels[cur]) if cur < V else -1
            for c in cands:
                c = int(c)
                if c in recent: continue
                if hist.get(c,0) >= 3: continue
                if labels[c] != my_island: continue  # ★ 语言岛隔离：不跳岛
                sc = 0.0
                if c in tr_set:
                    sc += W_TR3  # 基础转移加成
                    if tr3_row:
                        tgt_cluster = int(assign[c])
                        if tgt_cluster in tr3_row:
                            sc += W_TR3 * float(tr3_sc[cid][tr3_row.index(tgt_cluster)])
                if float(En[c] @ ctx) > 0.3: sc += W_SIM
                if c in kn_list: sc += W_KN
                co = cooc_w.get((cid, assign[c]), 0)
                if co > 0: sc += W_CO * co
                sc -= 3.0 * hist.get(c, 0)
                sc += 0.05 * float(rng_j.random())
                if sc > best_sc:
                    best_sc, best = sc, c

            if best >= 0:
                fail_streak = 0
            else:
                fail_streak += 1
                if fail_streak >= ESCRIPT:
                    # --- 逃逸门：LM 兜底 ---
                    gate = escape_gate(gen)
                    for vid, s in gate:
                        if 0 <= vid < V and vid not in recent and vid not in bl_ids:
                            if hist.get(vid, 0) < 3:
                                best = vid
                                break
                    fail_streak = 0
            if best < 0:
                # 最终兜底：簇内 top1
                m = MEMBER.get(cid, np.array([3]))
                best = int(m[0]) if len(m) else 3

            gen.append(best)
            hist[best] = hist.get(best,0)+1
            recent = gen[-8:]
            cur = best
            ctx = 0.92*ctx + 0.08*En[best]; ctx /= (np.linalg.norm(ctx)+1e-12)
            cid = int(assign[cur])
        return gen[len(ids):]

    # ---- 跑 ----
    results = {}
    gate_total_per_mode = {}
    for mode in MODES:
        gate_calls[0] = 0
        for prompt in PROMPTS:
            tg = time.time()
            gen = generate(prompt, mode)
            dt = time.time() - tg
            text = vt.decode(gen)
            results["%s|%s" % (mode, prompt)] = {
                "text": text, "tok_s": round(N_GEN/dt, 2)}
            log("[%s] %s: %.1f tok/s | %s" % (mode, prompt, N_GEN/dt, text[:50]))
        gate_total_per_mode[mode] = gate_calls[0]

    # ---- 事后质量打分（独立，不参与生成） ----
    log("[scoring] teacher-forcing via Qwen...")
    def score_text(text):
        qenc = qt.encode(text, add_special_tokens=False)
        qids = (qenc.ids if hasattr(qenc, "ids") else qenc)[:128]
        if len(qids) < 2: return -8.0
        x = torch.tensor([qids], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[:-1].float(), dim=-1)
        tgt = x[0][1:]
        sel = lp.gather(1, tgt.unsqueeze(1)).squeeze(1)
        return float(sel.mean())

    all_ts, all_lp = [], []
    for k, v in results.items():
        all_ts.append(v["tok_s"])
        lp = score_text(v["text"])
        v["lp"] = round(lp, 3)
        all_lp.append(lp)
    merged = "".join(v["text"] for v in results.values())

    out = {
        "engine": "概念宇宙 LLM · 合一引擎 v1.2（图导航为主+逃逸门降级+转移v3）",
        "architecture": "图遍历主决策 / LM 仅连续%d次失败后逃逸 / 转移边=模型output head分布" % ESCRIPT,
        "weights": {"W_TR3": W_TR3, "W_SIM": W_SIM, "W_KN": W_KN, "W_CO": W_CO},
        "mean_tok_s": round(float(np.mean(all_ts)), 2),
        "mean_logprob_post": round(float(np.mean(all_lp)), 3),
        "diversity_char": round(len(set(merged))/max(len(merged),1), 3),
        "ge_m3_rate": round(sum(1 for x in all_lp if x >= -3.0)/max(len(all_lp),1), 3),
        "gate_calls_per_mode": gate_total_per_mode,
        "gate_call_ratio": round(sum(gate_total_per_mode.values()) / (30*6), 4),
        "l1_layers": len(valid_layers),
        "transfer_v3": tr3_cand is not None,
        "per_mode": {m: {
            "tok_s": round(float(np.mean([v["tok_s"] for k,v in results.items() if k.startswith(m+"|")])), 2),
            "lp": round(float(np.mean([v.get("lp",-8) for k,v in results.items() if k.startswith(m+"|")])), 3),
            "gate_calls": gate_total_per_mode[m],
        } for m in MODES},
        "samples": {k: v["text"][:120] for k, v in list(results.items())[:10]},
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "v1.2 方向反转版：图导航为主（速度=架构速度），LM 只在连续2次图决策失败后逃逸；转移边来自 output head（模型自身分布）；质量打分是事后独立的 teacher-forcing（与生成过程无关）",
    }
    with open(OUT + r"\unified_result_v12.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("samples","per_mode")}, ensure_ascii=False, indent=1))
    log("[done] %.0fs" % (time.time()-t0))

if __name__ == "__main__":
    main()
