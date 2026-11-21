# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 五脉冲图遍历生成引擎 + 验收实测（V4-Flash 自洽线 v1）
脉冲分量（知世："用不同的分量，不同的脉冲分量"）：
  sim     相似脉冲 —— 沿 kNN 边游走（联想）
  tr      转移脉冲 —— 沿 bigram 转移边走（续写）
  mix     干涉脉冲 —— 多路种子邻居交并（并行思考）
  conc    收缩脉冲 —— 向概念簇中心/hub 收敛（归纳）
  expand  扩展脉冲 —— 跨簇前沿向外扩散（创造展开）
生成循环（无 LM 内联——速度真测）：定位→选脉冲→遍历→线性化
  候选融合分 = w_tr·rank_tr + w_sim·rank_sim + w_kn·知识(L1) + w_cooc·关联 − 重复惩罚
  重复惩罚（B 修复配方继承）：近窗 6 禁字 = -inf；重复次数×1.5 惩罚
验收（提示词 §6）：速度≥100 tok/s；logprob≥-3.0（Qwen1.5B 离线 teacher-forcing）；
  多样性≥0.6（字符 distinct）；语法正确率代理=6 提示中 logprob≥-3 的比例；知识覆盖=L1 meta
"""
import sys, os, json, time, hashlib
import numpy as np

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
L1 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l1"
TR = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_engine-20261012.json"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
QMODEL = r"H:/AI/models--Qwen2.5-1.5B"
V, K_CLU, N_GEN = 129280, 2048, 60
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙"]
PULSES = ["sim", "tr", "mix", "conc", "expand"]

def log(m): print(m, file=sys.stderr, flush=True)

def main():
    t0 = time.time()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)

    # ---- L0 ----
    Em = np.load(L0 + r"\embed_fp16.npy").astype(np.float32)
    En = Em / (np.linalg.norm(Em, axis=1, keepdims=True) + 1e-12)
    C = np.load(L0 + r"\centers.npy").astype(np.float32)
    Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
    assign = np.load(L0 + r"\assign.npy")
    E = np.load(L0 + r"\edges.npy")
    # CSR 邻接（相似脉冲图）
    src = np.concatenate([E[:, 0], E[:, 1]])
    dst = np.concatenate([E[:, 1], E[:, 0]])
    o = np.argsort(src, kind="stable")
    src_s, dst_s = src[o], dst[o]
    indptr = np.searchsorted(src_s, np.arange(V + 1))
    log("[L0] edges=%d  %.0fs" % (len(E), time.time() - t0))

    # ---- L2 ----
    nxt = np.load(TR + r"\bigram_top5.npy")
    coc = np.load(TR + r"\cooc_cluster.npz")
    cooc_i, cooc_j, cooc_c = coc["i"], coc["j"], coc["c"]
    cooc_w = {}
    for a, b, c in zip(cooc_i, cooc_j, cooc_c):
        cooc_w[(int(a), int(b))] = float(c)

    # ---- L1 知识候选（占位映射照记）----
    tok1 = np.load(L1 + r"\concept_tok.npy", mmap_mode="r")
    def knowledge_tokens(cluster, topn=12):
        """簇 → 知识候选：层{0,21,42} × 专家 (c%256) × 神经元派生 —— v0 确定性占位映射（未接 router，照记）"""
        out = []
        for ln in (0, 21, 42):
            e = cluster % 256
            for n_off in (0, 7, 13):
                n = (cluster * 13 + n_off * 37) % 2048
                row = tok1[ln, e, n]
                out.extend(int(x) for x in row if int(x) >= 0)
        # dedup preserve order
        seen = set(); res = []
        for x in out:
            if x not in seen:
                seen.add(x); res.append(x)
        return res[:topn]

    # ---- 定位 ----
    def locate(ids):
        ctx = En[ids].mean(axis=0)
        ctx /= (np.linalg.norm(ctx) + 1e-12)
        c = int(np.argmax(Cn @ ctx))
        tokv = int(np.argmax(En[ids[0]]))  # seed for graph walk: 最相似词
        return ctx, c, tokv

    # ---- 候选与打分 ----
    W_TR, W_SIM, W_KN, W_CO = 1.0, 0.7, 0.6, 0.4
    def generate(prompt, pulse, seed_cluster):
        ids = [i for i in tok.encode(prompt, add_special_tokens=False).ids if i < V]
        if not ids:
            ids = [3]
        ctx, cluster, cur = locate(ids)
        gen = []
        recent = list(ids[-6:])
        hist_count = {}
        for step in range(N_GEN):
            a, b = indptr[cur], indptr[cur + 1]
            sim_nb = dst_s[a:b]
            tr_cand = nxt[cur]
            kn_cand = np.array(knowledge_tokens(cluster), dtype=np.int64)
            # 脉冲决定候选集（v1.1 逃逸门：tr top5 ∪ sim top8 始终在池——B修复配方继承）
            tr_valid = np.array([int(x) for x in tr_cand if int(x) >= 0], dtype=np.int64)
            if pulse == "sim":
                cand = np.unique(np.concatenate([sim_nb, tr_valid]))
            elif pulse == "tr":
                cand = np.unique(np.concatenate([tr_valid, sim_nb[:8]]))
            elif pulse == "mix":
                # 多路：prompt 种子的邻居并集 ∩ 语义合理（sim 邻居 ∪ tr）——简化：交集
                seed_nb = set()
                for s in ids[:4]:
                    a2, b2 = indptr[s], indptr[s + 1]
                    seed_nb.update(int(x) for x in dst_s[a2:b2])
                inter = [int(x) for x in sim_nb if int(x) in seed_nb]
                cand = np.unique(np.concatenate([
                    np.array(inter if inter else sim_nb, dtype=np.int64), tr_valid]))
            elif pulse == "conc":
                # 收缩：簇内按 ctx 相似度取 top —— 用成员表
                m = MEMBER[cluster]
                s = En[m] @ ctx
                cand = np.unique(np.concatenate([m[np.argsort(-s)[:30]], tr_valid]))
            else:  # expand
                other = np.array([int(x) for x in sim_nb if assign[int(x)] != cluster], dtype=np.int64)
                if len(other) == 0:
                    m = MEMBER[cluster]
                    s = En[m] @ ctx
                    other = m[np.argsort(s)[:30]]   # 簇边缘（最不像中心）= 向外
                cand = np.unique(np.concatenate([other, tr_valid]))
            if len(cand) == 0:
                cand = sim_nb if len(sim_nb) else np.array([3])
            # 融合打分
            best, best_sc = -1, -1e18
            tr_rank = {int(t): k for k, t in enumerate(tr_cand) if int(t) >= 0}
            kn_set = set(int(x) for x in kn_cand)
            seed_rng = (sum(ids) * 131 + step * 17 + sum(ord(c) for c in prompt) * 7 + len(pulse)) & 0x7FFFFFFF
            jit = np.random.default_rng(seed_rng)
            for tok_ in cand:
                tok_ = int(tok_)
                if tok_ in recent:                    # 近窗 8 禁字
                    continue
                if hist_count.get(tok_, 0) >= 3:      # v1.1 全局三次上限（防死循环）
                    continue
                sc = 0.0
                if tok_ in tr_rank:
                    sc += W_TR * (5 - tr_rank[tok_])
                # sim rank
                rank_s = np.where(sim_nb == tok_)[0]
                if len(rank_s):
                    sc += W_SIM * (len(sim_nb) - int(rank_s[0]))
                if tok_ in kn_set:
                    sc += W_KN
                co = cooc_w.get((cluster, assign[tok_]), 0)
                if co > 0:
                    sc += W_CO * min(np.log1p(co), 3.0)
                sc -= 3.0 * hist_count.get(tok_, 0)   # v1.1 重复惩罚 1.5→3.0
                sc += 1e-4 * float(En[tok_] @ ctx)    # 微弱语义 tiebreak
                sc += 0.05 * float(jit.random())      # v1.1 平局抖动（seeded）
                if sc > best_sc:
                    best_sc, best = sc, tok_
            if best < 0:                              # 全被禁：放宽近窗（全局上限仍卡）
                for tok_ in cand:
                    tok_ = int(tok_)
                    if hist_count.get(tok_, 0) >= 4:
                        continue
                    sc = (1.0 if tok_ in tr_rank else 0.0) - 3.0 * hist_count.get(tok_, 0)
                    sc += 0.05 * float(jit.random())
                    if sc > best_sc:
                        best_sc, best = sc, tok_
            if best < 0:
                best = int(sim_nb[0]) if len(sim_nb) else 3
            # 状态更新
            gen.append(best)
            hist_count[best] = hist_count.get(best, 0) + 1
            recent = (recent + [best])[-8:]           # v1.1 近窗 6→8
            nv = En[best]
            ctx = 0.92 * ctx + 0.08 * nv
            ctx /= (np.linalg.norm(ctx) + 1e-12)
            cur = best
            # 概念簇随游走更新（收缩/扩展会移动 cluster）
            cluster = int(assign[cur])
        return gen, ids

    # ---- 主循环：5 脉冲 × 6 提示 ----
    results = {}
    all_text = []
    tok_s_list = []
    npz_members = np.load(L0 + r"\member_cap.npz")
    global MEMBER
    MEMBER = {int(k): npz_members[k] for k in npz_members.files}
    texts_store = {}
    for pulse in PULSES:
        for prompt in PROMPTS:
            tg = time.time()
            gen, ids = generate(prompt, pulse, None)
            dt = time.time() - tg
            text = tok.decode(gen)
            key = "%s|%s" % (pulse, prompt)
            texts_store[key] = text
            tok_s_list.append(N_GEN / dt)
    mean_ts = float(np.mean(tok_s_list))
    concat = "".join(texts_store.values())
    diversity = len(set(concat)) / max(len(concat), 1)
    log("[gen] mean=%.1f tok/s diversity=%.3f  %.0fs" % (mean_ts, diversity, time.time() - t0))

    # ---- 离线 logprob（Qwen1.5B teacher-forcing）----
    lp = {}
    try:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        qtok = AutoTokenizer.from_pretrained(QMODEL)
        qm = AutoModelForCausalLM.from_pretrained(QMODEL, torch_dtype=torch.float32)
        with torch.no_grad():
            for key, text in texts_store.items():
                enc = qtok(text, return_tensors="pt")
                out = qm(**enc).logits[0]
                logp = torch.log_softmax(out[:-1].float(), dim=-1)
                tgt = enc["input_ids"][0][1:]
                sel = logp.gather(1, tgt.unsqueeze(1)).squeeze(1)
                lp[key] = float(sel.mean())
        del qm
        log("[qwen] logprob done  %.0fs" % (time.time() - t0))
    except Exception as ex:
        log("[qwen] FAIL: %r" % ex)
        lp = {k: None for k in texts_store}

    lpm = np.mean([v for v in lp.values() if v is not None]) if lp else None
    n_pass = sum(1 for v in lp.values() if v is not None and v >= -3.0)
    grammar_rate = n_pass / max(len(lp), 1)

    l1meta = json.load(open(L1 + r"\meta.json", encoding="utf-8")) if os.path.exists(L1 + r"\meta.json") else {}
    l1_cov = l1meta.get("coverage", 0)

    out = {
        "engine": "概念宇宙 LLM · 五脉冲图遍历生成（V4-Flash 自洽线 v1）",
        "pulses": PULSES,
        "prompts": PROMPTS,
        "n_gen_per_case": N_GEN,
        "mean_gen_tok_s": round(mean_ts, 1),
        "speed_ge_100": mean_ts >= 100,
        "diversity_char": round(diversity, 3),
        "diversity_ge_0_6": diversity >= 0.6,
        "mean_logprob_qwen15b": None if lpm is None else round(lpm, 3),
        "logprob_ge_m3_rate": round(grammar_rate, 3),
        "grammar_ge_80pct": grammar_rate >= 0.8,
        "knowledge_coverage_l1": l1_cov,
        "knowledge_ge_80pct": l1_cov >= 0.8,
        "logprobs": {k: (None if v is None else round(v, 3)) for k, v in lp.items()},
        "samples": {k: v[:160] for k, v in texts_store.items()},
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "速度=纯图遍历+查表（无 LM 内联）；logprob=Qwen1.5B 离线 teacher-forcing 代理；语法正确率代理=logprob≥-3 的样本比例（非人工文法判定）；L1 知识映射=簇号确定性占位（未接 router，照记）；语料转移表历史判负角色（bigram 天花板）已按知识候选源定位",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "samples"}, ensure_ascii=False))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
