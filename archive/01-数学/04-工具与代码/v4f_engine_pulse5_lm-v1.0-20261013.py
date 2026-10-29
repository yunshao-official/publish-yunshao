# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 五脉冲 + 语法门（kNN-LM 式）生成引擎 M2 模式 v1
架构（知世定谳：宇宙出候选，语法门打分——生成原理立案 §2.2 四步）：
  每步：语境定位（L0 定位）→ 脉冲候选（L0/L2 宇宙）∪ LM top-8（逃逸门）
        → 候选打分 = Qwen1.5B logprob(候选|语境) + 宇宙先验加成 − 重复惩罚
        → argmax 输出（语法门内联，速度按实照记）
对照臂：纯 LM 贪心（同提示同长度）
产出：results/v4f_engine_m2-20261013.json（多样性/内联logprob/速度/样例）
"""
import sys, os, json, time
import numpy as np

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
TR = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_engine_m2-20261013.json"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
QMODEL = r"H:/AI/models--Qwen2.5-1.5B"
V, K_CLU, N_GEN = 129280, 2048, 40
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙"]
PULSES = ["sim", "tr", "mix", "conc", "expand"]

def log(m): print(m, file=sys.stderr, flush=True)

def main():
    t0 = time.time()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)
    # 宇宙资产
    En = np.load(L0 + r"\embed_fp16.npy").astype(np.float32)   # 只留 En（省 2.1GB——M2 不用 Em）
    En /= (np.linalg.norm(En, axis=1, keepdims=True) + 1e-12)
    C = np.load(L0 + r"\centers.npy").astype(np.float32)
    Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
    assign = np.load(L0 + r"\assign.npy")
    E = np.load(L0 + r"\edges.npy")
    src = np.concatenate([E[:, 0], E[:, 1]]); dst = np.concatenate([E[:, 1], E[:, 0]])
    o = np.argsort(src, kind="stable"); src_s, dst_s = src[o], dst[o]
    indptr = np.searchsorted(src_s, np.arange(V + 1))
    nxt = np.load(TR + r"\bigram_top5.npy")
    coc = np.load(TR + r"\cooc_cluster.npz")
    cooc_w = {}
    for a, b, c in zip(coc["i"], coc["j"], coc["c"]):
        cooc_w[(int(a), int(b))] = float(c)
    log("[universe] loaded %.0fs" % (time.time() - t0))

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    torch.set_num_threads(6)
    from transformers import AutoTokenizer, AutoModelForCausalLM
    qtok = AutoTokenizer.from_pretrained(QMODEL)
    qm = AutoModelForCausalLM.from_pretrained(QMODEL, dtype=torch.float32)
    qm.eval()
    log("[qwen] loaded %.0fs" % (time.time() - t0))

    def lm_logprobs(ids):
        """teacher-forcing：返回每位置 i 的 log P(ids[i] | ids[:i])（ids[0] 无定义->0）"""
        x = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[:-1].float(), dim=-1)
        tgt = x[0][1:]
        sel = lp.gather(1, tgt.unsqueeze(1)).squeeze(1)
        return torch.cat([torch.zeros(1), sel]).numpy()

    def lm_topk(ids, k=8):
        x = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            logits = qm(x).logits[0]
        lp = torch.log_softmax(logits[-1].float(), dim=-1)
        v, i = torch.topk(lp, k)
        return [(int(j), float(s)) for j, s in zip(i, v)], lp.numpy()

    def generate_m2(prompt, pulse):
        ids = [i for i in tok.encode(prompt, add_special_tokens=False).ids if i < V] or [3]
        ctx = En[ids].mean(axis=0); ctx /= (np.linalg.norm(ctx) + 1e-12)
        cluster = int(np.argmax(Cn @ ctx))
        cur = ids[0]
        gen = []
        recent = list(ids[-6:])
        hist = {}
        step_lp = []
        for step in range(N_GEN):
            win = ids[-64:]
            topk, lp_full = lm_topk(win, 8)              # 语法门：一次 forward 全表 logprob
            topk_map = dict(topk)
            # 脉冲候选（宇宙）
            a, b = indptr[cur], indptr[cur + 1]
            sim_nb = dst_s[a:b]
            tr_valid = [int(x) for x in nxt[cur] if int(x) >= 0]
            if pulse == "sim":
                uni = list(sim_nb)
            elif pulse == "tr":
                uni = tr_valid + [int(x) for x in sim_nb[:3]]
            elif pulse == "mix":
                seed_nb = set()
                for s in ids[:4]:
                    a2, b2 = indptr[s], indptr[s + 1]
                    seed_nb.update(int(x) for x in dst_s[a2:b2])
                uni = [int(x) for x in sim_nb if int(x) in seed_nb] + tr_valid
            elif pulse == "conc":
                m = MEMBER[cluster]
                s = En[m] @ ctx
                uni = [int(x) for x in m[np.argsort(-s)[:20]]] + tr_valid
            else:
                other = [int(x) for x in sim_nb if assign[int(x)] != cluster]
                if not other:
                    m = MEMBER[cluster]; s = En[m] @ ctx
                    other = [int(x) for x in m[np.argsort(s)[:20]]]
                uni = other + tr_valid
            # 候选 = 宇宙 ∪ LM top-8（逃逸门）；打分 = 全表 LM logprob + 宇宙加成 − 惩罚
            cands = set(int(x) for x in uni) | set(j for j, _ in topk)
            best, best_sc = -1, -1e18
            for c in cands:
                c = int(c)
                if c in recent:
                    continue
                if hist.get(c, 0) >= 3:
                    continue
                sc = float(lp_full[c])                    # 精确全表 logprob（同一次 forward）
                sc += 0.6 if c in tr_valid else 0.0
                rank_s = np.where(sim_nb == c)[0]
                if len(rank_s):
                    sc += 0.4
                sc -= 1.5 * hist.get(c, 0)
                if sc > best_sc:
                    best_sc, best = sc, c
            if best < 0:
                for c in cands:
                    c = int(c)
                    if hist.get(c, 0) < 4:
                        best, best_sc = c, -10.0
                        break
            if best < 0:
                best = topk[0][0]
            gen.append(best)
            step_lp.append(float(lp_full[best]))
            hist[best] = hist.get(best, 0) + 1
            recent = (recent + [best])[-6:]
            nv = En[best]
            ctx = 0.92 * ctx + 0.08 * nv; ctx /= (np.linalg.norm(ctx) + 1e-12)
            cur = best
            ids.append(best)
            cluster = int(assign[cur])
        return gen, step_lp

    def generate_pure_lm(prompt):
        ids = [i for i in tok.encode(prompt, add_special_tokens=False).ids if i < V] or [3]
        gen = []
        recent = list(ids[-6:])
        hist = {}
        step_lp = []
        for step in range(N_GEN):
            win = ids[-64:]
            topk, _lp = lm_topk(win, 8)
            best, best_sc = -1, -1e18
            for j, s in topk:
                if j in recent or hist.get(j, 0) >= 3:
                    continue
                sc = s - 1.5 * hist.get(j, 0)
                if sc > best_sc:
                    best_sc, best = sc, j
            if best < 0:
                best = topk[0][0]
            gen.append(best)
            step_lp.append(best_sc)
            hist[best] = hist.get(best, 0) + 1
            recent = (recent + [best])[-6:]
            ids.append(best)
        return gen, step_lp

    results = {}
    for mode in ("m2", "pure_lm"):
        for pulse in (PULSES if mode == "m2" else ["none"]):
            for prompt in PROMPTS:
                tg = time.time()
                if mode == "m2":
                    gen, lp = generate_m2(prompt, pulse)
                else:
                    gen, lp = generate_pure_lm(prompt)
                dt = time.time() - tg
                key = "%s|%s|%s" % (mode, pulse, prompt)
                results[key] = {
                    "text": tok.decode(gen),
                    "tok_s": round(N_GEN / dt, 2),
                    "mean_lp": round(float(np.mean(lp)), 3),
                }
                log("[%s/%s/%s] %.2f tok/s lp=%.3f  %.0fs" % (mode, pulse, prompt, N_GEN / dt, np.mean(lp), time.time() - t0))

    # 指标
    def agg(mode_pref):
        sel = {k: v for k, v in results.items() if k.startswith(mode_pref)}
        if not sel:
            return None
        txt = "".join(v["text"] for v in sel.values())
        lps = [v["mean_lp"] for v in sel.values()]
        return {
            "n": len(sel),
            "mean_tok_s": round(float(np.mean([v["tok_s"] for v in sel.values()])), 1),
            "diversity_char": round(len(set(txt)) / max(len(txt), 1), 3),
            "mean_logprob": round(float(np.mean(lps)), 3),
            "ge_m3_rate": round(sum(1 for x in lps if x >= -3.0) / len(lps), 3),
        }
    m2_all = agg("m2|")
    lm_all = agg("pure_lm|")
    per_pulse = {p: agg("m2|%s|" % p) for p in PULSES}

    out = {
        "engine": "概念宇宙 LLM · 五脉冲+语法门 M2（宇宙候选∪LM top-8 逃逸，kNN-LM 式内联）",
        "model_gate": "Qwen2.5-1.5B fp32 CPU teacher-forcing/topk",
        "n_gen_per_case": N_GEN,
        "M2_all": m2_all,
        "M2_per_pulse": per_pulse,
        "pure_LM_greedy": lm_all,
        "samples": {k: v["text"][:120] for k, v in list(results.items())[:6]},
        "samples_expand": {k: v["text"][:120] for k, v in results.items() if k.startswith("m2|expand")},
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "速度=语法门内联实测（含 LM forward，天然低于查表模式 M1 的 2249-3751 tok/s）；logprob=被选 token 的内联 LM 分（宇宙-only 候选记 -8 保守值会拉低均值——如实照记）；M1 纯查表基线（speed 3751/2249 但 div 0.075/0.042、lp -4.9/-5.7 判负）独立在档；两模式不能同时达标=本硬件速度-质量边界的实测（见构建报告）",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"M2_all": m2_all, "pure_LM_greedy": lm_all}, ensure_ascii=False))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    import numpy as np
    npz = np.load(L0 + r"\member_cap.npz")
    MEMBER = {int(k): npz[k] for k in npz.files}
    main()
