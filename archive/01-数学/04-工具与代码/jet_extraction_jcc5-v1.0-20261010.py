# -*- coding: utf-8 -*-
"""
J-CC5 影子云维数谱（预注册：J-CC5判据冻结书-预注册-20261010.md）
理论来源：知世口授（概念=跨维度投影合成体——逐概念量化合成体维数）
30 概念 × 12 语境（句式6+任务6）→ 每概念影子云 JSD→MDS→ndim90/PR 维数谱
判定：维数谱非均匀（置换检验）→ PASS；方向性预言（抽象>具体）分开记
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "H:/AI/models--Qwen2.5-1.5B"
TOPK = 512

CONCEPTS = list({
    "猫": 0, "死亡": 0, "愤怒": 0, "快乐": 0, "勇敢": 0, "聪明": 0,
    "海洋": 0, "花": 0, "朋友": 0, "时间": 1, "家": 0, "自由": 1,
    "太阳": 0, "山": 0, "雨": 0, "书": 0, "路": 0, "梦": 0,
    "爱": 1, "恨": 1, "勇气": 1, "财富": 1, "权力": 1, "教育": 1,
    "医生": 0, "音乐": 0, "战争": 1, "和平": 1, "孤独": 1, "希望": 1,
}.keys())
ABSTRACT = {"时间", "自由", "爱", "恨", "勇气", "财富", "权力", "教育", "战争", "和平", "孤独", "希望"}

TEMPLATES = [
    "介绍一下{w}的相关知识。",
    "说实话，{w}给我的印象很深。",
    "{w}像一枚旧邮票，贴在时光的信封上。",
    "为什么{w}如此重要？",
    "什么是{w}？请给出定义。",
    "请以{w}为主题写一句诗。",
    "3个{w}加5个{w}是几个{w}？",
    "把{w}翻译成英文。",
    "{w}和其他同类事物比有什么不同？",
    "如果世界上没有{w}会怎样？",
    "我最近一直在想{w}这件事。",
    "{w}啊，说起来话就长了。",
]

def next_token_probs(model, tok, sent):
    ids = tok.encode(sent, add_special_tokens=True)
    with torch.no_grad():
        out = model(torch.tensor([ids]))
    return torch.softmax(out.logits[0, -1].float(), dim=-1).numpy()

def jsd_matrix(P):
    n = P.shape[0]
    Q = P / np.maximum(P.sum(axis=1, keepdims=True), 1e-12)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            m = 0.5 * (Q[i] + Q[j])
            def kl(p):
                mask = p > 1e-12
                return float(np.sum(p[mask] * np.log2(p[mask] / m[mask])))
            d = 0.5 * kl(Q[i]) + 0.5 * kl(Q[j])
            D[i, j] = D[j, i] = float(np.sqrt(max(d, 0.0)))
    return D

def mds_dims(D):
    n = D.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * (H @ (np.square(D)) @ H)
    vals = np.clip(np.linalg.eigvalsh(B)[::-1], 0, None)
    tot = vals.sum()
    if tot <= 0:
        return 0.0, 0.0
    cum = np.cumsum(vals) / tot
    nd90 = int(np.searchsorted(cum, 0.9) + 1)
    pr = float(np.square(vals.sum()) / np.square(vals).sum())
    return float(nd90), pr

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    spectra = {}
    for w in CONCEPTS:
        probs = [next_token_probs(model, tok, t.replace("{w}", w)) for t in TEMPLATES]
        P = np.stack(probs)
        union = P.sum(axis=0).argsort()[::-1][:TOPK]
        D = jsd_matrix(P[:, union])
        nd90, pr = mds_dims(D)
        spectra[w] = {"ndim90": nd90, "pr": pr, "abstract": 1 if w in ABSTRACT else 0}
        print(f"[spec] {w} nd90={nd90} pr={pr:.3f}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 判定：维数谱非均匀（预计算 360×360 JSD 大矩阵 + 子阵置换——秒级）
    obs_var = float(np.var([s["ndim90"] for s in spectra.values()]))
    rng = np.random.default_rng(42)
    n_tpl = len(TEMPLATES)
    all_probs = {}
    for w in CONCEPTS:
        all_probs[w] = np.stack([next_token_probs(model, tok, t.replace("{w}", w)) for t in TEMPLATES])
    flat = np.stack([all_probs[w][i] for w in CONCEPTS for i in range(n_tpl)])   # 360×V
    u_all = flat.sum(axis=0).argsort()[::-1][:TOPK]
    Flat = flat[:, u_all]
    N = Flat.shape[0]
    Qf = Flat / np.maximum(Flat.sum(axis=1, keepdims=True), 1e-12)
    Dbig = np.zeros((N, N))
    for i in range(N):
        m = 0.5 * (Qf[i][None, :] + Qf[i + 1:])
        kl_i = np.where(Qf[i][None, :] > 1e-12, Qf[i][None, :] * np.log2(np.maximum(Qf[i][None, :] / m, 1e-12)), 0).sum(axis=1)
        mask_j = Qf[i + 1:] > 1e-12
        kl_j = np.where(mask_j, Qf[i + 1:] * np.log2(np.maximum(Qf[i + 1:] / m, 1e-12)), 0).sum(axis=1)
        d = np.sqrt(np.maximum(0.5 * kl_i + 0.5 * kl_j, 0))
        Dbig[i, i + 1:] = d
        Dbig[i + 1:, i] = d
    Hm = np.eye(n_tpl) - np.ones((n_tpl, n_tpl)) / n_tpl

    def nd90_sub(idx):
        Ds = Dbig[np.ix_(idx, idx)]
        B = -0.5 * (Hm @ (np.square(Ds)) @ Hm)
        vals = np.clip(np.linalg.eigvalsh(B)[::-1], 0, None)
        tot = vals.sum()
        if tot <= 0:
            return 0.0
        return float(int(np.searchsorted(np.cumsum(vals) / tot, 0.9) + 1))

    cnt = 0
    n_perm = 5000
    for _ in range(n_perm):
        perm = rng.permutation(N)
        vars_perm = []
        for gi in range(0, N, n_tpl):
            vars_perm.append(nd90_sub(sorted(int(x) for x in perm[gi:gi + n_tpl])))
        if float(np.var(vars_perm)) >= obs_var:
            cnt += 1
    p_val = float((cnt + 1) / (n_perm + 1))
    verdict = ("PASS（合成体维数是概念的实在属性·维数谱非均匀）"
               if p_val < 0.05 else "FAIL（判负照记）")

    # 方向性预言（分开记）
    ab = [spectra[w]["ndim90"] for w in CONCEPTS if w in ABSTRACT]
    co = [spectra[w]["ndim90"] for w in CONCEPTS if w not in ABSTRACT]
    dir_note = {
        "abstract_mean_ndim90": float(np.mean(ab)), "concrete_mean_ndim90": float(np.mean(co)),
        "direction": "抽象>具体" if np.mean(ab) > np.mean(co) else "具体>=抽象",
    }

    out = {
        "model": MODEL, "topk": TOPK, "n_templates": len(TEMPLATES),
        "spectra": spectra,
        "obs_var_ndim90": obs_var, "p_perm": p_val, "J-CC5": verdict,
        "direction_check": dir_note,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC5判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；置换=跨概念重分组 5000 次；方向性预言不进判定",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
