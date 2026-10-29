# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 合一引擎 v1.3（三源 rank 化融合 + 句结构 + 真知识亲和）
针对审计报告-终版-20261014 §三（质量-速度权衡）与 §四 P0 清单：
  三源 rank 化融合：bigram(语法先验·主导) + trigram(知世提示词步骤3) + output head 簇转移(v3 语义)
                   + L1 真知识亲和表(concept_tok 层21/42 替换前版簇号占位) + gateinp 簇关联(层21)
  句结构：标点驱动句尾 + 句首主题回拉（篇章主题锚/句级重定位，daily-10-12 两级展开实测口径）
  参与率计量：知识/转移源命中步占比（审计"图参与率未计量"修复）
验收五项：速度≥100 tok/s｜logprob≥-3.0(Qwen1.5B teacher-forcing)｜多样性≥0.6(字符)｜
  知识覆盖≥80%(L1 结构覆盖)｜语法正确率≥80%(logprob≥-3 样本比例代理)
本件为纯读+计算+stdout（无写盘语句）；运行：python 本件 > results/v4f_engine_v13-20261014.json
"""
import sys, os, json, time
import numpy as np

BASE = "H:/理论存档/01-数学/04-工具与代码/results"
L0, L1DIR = BASE + "/v4f_l0", BASE + "/v4f_l1"
TR, TF = BASE + "/v4f_transfer", BASE + "/v4f_transfer_v3_full"
TOKJSON = "H:/AI/DeepSeek-V4.1-Flash-IQ2XXS/tokenizer.json"
QMODEL = "H:/AI/models--Qwen2.5-1.5B"
V, K, N_GEN = 129280, 2048, 60
PROMPTS = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙"]
PULSES = ["sim", "tr", "mix", "conc", "expand"]

def log(m): print(m, file=sys.stderr, flush=True)

t00 = time.time()
from tokenizers import Tokenizer
tok = Tokenizer.from_file(TOKJSON)

punc_ids = {}
for s in ["。", "，", "！", "？", "；", "、", "…"]:
    ids2 = tok.encode(s, add_special_tokens=False).ids
    if ids2:
        punc_ids[ids2[0]] = s
END_P = {i for i, s in punc_ids.items() if s in "。！？"}
MID_P = {i for i, s in punc_ids.items() if s in "，、；…"}
log("[punc] " + str(punc_ids))

Em = np.load(L0 + "/embed_fp16.npy").astype(np.float32)
En = Em / (np.linalg.norm(Em, axis=1, keepdims=True) + 1e-12)
C = np.load(L0 + "/centers.npy").astype(np.float32)
Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
assign = np.load(L0 + "/assign.npy")
E = np.load(L0 + "/edges.npy")
src = np.concatenate([E[:, 0], E[:, 1]])
dst = np.concatenate([E[:, 1], E[:, 0]])
o = np.argsort(src, kind="stable")
src_s, dst_s = src[o], dst[o]
indptr = np.searchsorted(src_s, np.arange(V + 1))
npzm = np.load(L0 + "/member_cap.npz")
MEMBER = {int(k): npzm[k] for k in npzm.files}
del Em
log("[L0] edges=%d %.0fs" % (len(E), time.time() - t00))

nxt = np.load(TR + "/bigram_top5.npy")
tri = np.load(TR + "/trigram_top3.npz")
tri_keys, tri_top3 = tri["keys"], tri["top3"]

def tri_lookup(a, b):
    if a < 0 or b < 0:
        return []
    key = a * V + b
    i = int(np.searchsorted(tri_keys, key))
    if i < len(tri_keys) and tri_keys[i] == key:
        return [int(x) for x in tri_top3[i] if x >= 0]
    return []
log("[L2] tri=%d %.0fs" % (len(tri_keys), time.time() - t00))

sib = np.load(TF + "/sibling_tr.npy")
gz = np.load(TF + "/gateinp_assoc_full.npz")
_l, _i, _j = gz["layer"], gz["i"], gz["j"]
sel = _l == 21
gi21 = set(zip(_i[sel].tolist(), _j[sel].tolist()))
mt = np.load(BASE + "/v4f_transfer_v3/model_transfer.npy")
log("[v3] gi21=%d mt=%s %.0fs" % (len(gi21), mt.shape, time.time() - t00))

tok1 = np.load(L1DIR + "/concept_tok.npy", mmap_mode="r")
kfreq = {}
for L in (21, 42):
    blk = np.asarray(tok1[L]).reshape(-1)
    blk = blk[blk >= 0].astype(np.int64)
    kfreq[L] = np.bincount(blk, minlength=V).astype(np.int32)
    log("[L1] layer%d 亲和表非零=%d %.0fs" % (L, int((kfreq[L] > 0).sum()), time.time() - t00))

def locate(ids):
    ctx = En[ids].mean(axis=0)
    ctx /= (np.linalg.norm(ctx) + 1e-12)
    c = int(np.argmax(Cn @ ctx))
    return ctx, c

W_BG = [3.0, 2.2, 1.6, 1.1, 0.7]
W_TRI = [2.5, 1.8, 1.2]

def generate(prompt, pulse):
    ids = [i for i in tok.encode(prompt, add_special_tokens=False).ids if i < V]
    if not ids:
        ids = [3]
    ctx, cluster = locate(ids)
    theme = ctx.copy()
    gen = []
    cur, prev2 = ids[-1], (ids[-2] if len(ids) > 1 else -1)
    recent, hist = list(ids[-8:]), {}
    sent_start, n_kn_hit, n_tr_hit = 0, 0, 0
    for step in range(N_GEN):
        a, b = indptr[cur], indptr[cur + 1]
        sim_nb = dst_s[a:b]
        tr_valid = [int(x) for x in nxt[cur] if int(x) >= 0]
        tri_valid = tri_lookup(prev2, cur)
        c_cur = int(assign[cur])
        if pulse == "sim":
            pool = list(sim_nb[:10]) + tr_valid
        elif pulse == "tr":
            pool = tr_valid + list(sim_nb[:6])
        elif pulse == "mix":
            seed_nb = set()
            for s in ids[:4]:
                a2, b2 = indptr[s], indptr[s + 1]
                seed_nb.update(int(x) for x in dst_s[a2:b2])
            inter = [int(x) for x in sim_nb if int(x) in seed_nb]
            pool = (inter if inter else list(sim_nb[:6])) + tr_valid + tri_valid
        elif pulse == "conc":
            m = MEMBER[cluster]
            s = En[m] @ ctx
            pool = list(m[np.argsort(-s)[:20]]) + tr_valid
        else:
            other = [int(x) for x in sim_nb if int(assign[x]) != c_cur]
            if not other:
                m = MEMBER[cluster]
                s = En[m] @ ctx
                other = list(m[np.argsort(s)[:20]])
            pool = other + tr_valid
        cand = np.unique(np.array([c for c in pool if 0 <= c < V], dtype=np.int64))
        mt_row = {int(cc): r for r, cc in enumerate(mt[c_cur])}
        sib_row = {int(cc): r for r, cc in enumerate(sib[21, cluster])}
        in_window = (step - sent_start) >= 10
        w_punc = 1.2 + 0.15 * (step - sent_start - 10) if in_window else 0.0
        best, best_sc = -1, -1e18
        for t_ in cand:
            t_ = int(t_)
            if t_ in recent or hist.get(t_, 0) >= 3:
                continue
            sc = 0.0
            if t_ in tr_valid:
                sc += W_BG[tr_valid.index(t_)]
            if t_ in tri_valid:
                sc += W_TRI[tri_valid.index(t_)]
            rs = np.where(sim_nb == t_)[0]
            if len(rs):
                sc += max(0.0, 0.9 - 0.1 * int(rs[0]))
            sc += 0.35 * min(int(kfreq[21][t_]), 4) + 0.35 * min(int(kfreq[42][t_]), 4)
            if (c_cur, int(assign[t_])) in gi21:
                sc += 0.5
            if int(assign[t_]) in mt_row:
                sc += 0.3 * (8 - mt_row[int(assign[t_])]) / 8.0
            if int(assign[t_]) in sib_row:
                sc += 0.2 * (8 - sib_row[int(assign[t_])]) / 8.0
            if in_window and (t_ in END_P or t_ in MID_P):
                sc += w_punc
            sc -= 3.0 * hist.get(t_, 0)
            sc += 0.3 * float(En[t_] @ ctx)
            sc += 0.05 * float(np.random.default_rng((sum(ids) * 131 + step * 17 + t_) & 0x7FFFFFFF).random())
            if sc > best_sc:
                best_sc, best = sc, t_
        if best < 0:
            best = int(sim_nb[0]) if len(sim_nb) else 3
        gen.append(best)
        hist[best] = hist.get(best, 0) + 1
        recent = (recent + [best])[-8:]
        if best in tr_valid or best in tri_valid:
            n_tr_hit += 1
        if min(int(kfreq[21][best]), 4) + min(int(kfreq[42][best]), 4) >= 2:
            n_kn_hit += 1
        ctx = 0.92 * ctx + 0.08 * En[best]
        ctx /= (np.linalg.norm(ctx) + 1e-12)
        cur, prev2 = best, cur
        if best in END_P:
            sent_start = step + 1
            ctx = 0.7 * ctx + 0.3 * theme
            ctx /= (np.linalg.norm(ctx) + 1e-12)
        elif best in MID_P:
            ctx = 0.85 * ctx + 0.15 * theme
            ctx /= (np.linalg.norm(ctx) + 1e-12)
        cluster = int(assign[cur])
    return gen, n_kn_hit, n_tr_hit

texts_store, parts = {}, {}
for pulse in PULSES:
    for prompt in PROMPTS:
        tg = time.time()
        gen, n_kn, n_tr = generate(prompt, pulse)
        dt = time.time() - tg
        key = pulse + "|" + prompt
        texts_store[key] = tok.decode(gen)
        parts[key] = {"tok_s": round(N_GEN / dt, 1), "kn_hit": n_kn, "tr_hit": n_tr}
mean_ts = float(np.mean([p["tok_s"] for p in parts.values()]))
kn_rate = float(np.mean([p["kn_hit"] for p in parts.values()])) / N_GEN
tr_rate = float(np.mean([p["tr_hit"] for p in parts.values()])) / N_GEN
concat = "".join(texts_store.values())
diversity = len(set(concat)) / max(len(concat), 1)
log("[gen] %.1f tok/s div=%.3f kn=%.2f tr=%.2f %.0fs" % (mean_ts, diversity, kn_rate, tr_rate, time.time() - t00))

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
            out2 = qm(**enc).logits[0]
            logp = torch.log_softmax(out2[:-1].float(), dim=-1)
            tgt = enc["input_ids"][0][1:]
            sel2 = logp.gather(1, tgt.unsqueeze(1)).squeeze(1)
            lp[key] = float(sel2.mean())
    del qm
    log("[qwen] done %.0fs" % (time.time() - t00))
except Exception as ex:
    log("[qwen] FAIL: %r" % ex)
    lp = {k: None for k in texts_store}

lpm = None
vals = [v for v in lp.values() if v is not None]
if vals:
    lpm = float(np.mean(vals))
n_pass = sum(1 for v in vals if v >= -3.0)
grate = n_pass / max(len(lp), 1)
l1m = json.load(open(L1DIR + "/meta_final.json", encoding="utf-8"))
out = {
    "engine": "概念宇宙 LLM · 合一引擎 v1.3（三源rank化融合+句结构+真知识亲和）",
    "sources": {
        "语法": "bigram top5 + trigram top3（同语料同清洗）",
        "语义": "output head 簇转移(v3) + 兄弟簇(层21) + gateinp 关联",
        "知识": "L1 concept_tok 层21/42 真值亲和表（替换前版簇号占位）",
    },
    "mean_tok_s": round(mean_ts, 1),
    "speed_ge_100": mean_ts >= 100,
    "diversity_char": round(diversity, 3),
    "diversity_ge_0_6": diversity >= 0.6,
    "mean_logprob_qwen15b": None if lpm is None else round(lpm, 3),
    "logprob_ge_m3": None if lpm is None else bool(lpm >= -3.0),
    "grammar_rate": round(grate, 3),
    "grammar_ge_80pct": grate >= 0.8,
    "knowledge_coverage_l1": l1m.get("coverage"),
    "knowledge_ge_80pct": bool(l1m.get("coverage", 0) >= 0.8),
    "knowledge_participation_rate": round(kn_rate, 3),
    "transfer_participation_rate": round(tr_rate, 3),
    "per_part": parts,
    "logprobs": {k: (None if v is None else round(v, 3)) for k, v in lp.items()},
    "samples": {k: v[:200] for k, v in texts_store.items()},
    "elapsed_s": round(time.time() - t00, 1),
    "honest_note": "速度=纯图查表无LM内联；logprob=Qwen1.5B离线teacher-forcing代理；语法率代理=logprob≥-3样本比例；知识参与率=知识亲和命中步占比；句结构=标点驱动+句首主题回拉（三级展开的轻量实现，非完整篇章/句级宇宙）",
}
print(json.dumps(out, ensure_ascii=False))
log("[done] %.0fs" % (time.time() - t00))
