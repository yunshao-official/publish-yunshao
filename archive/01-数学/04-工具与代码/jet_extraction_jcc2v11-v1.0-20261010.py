# -*- coding: utf-8 -*-
"""
J-CC2 v1.1 跨维度概念合成体（影子=输出分布版）
预注册判据已冻结：J-CC2判据冻结书-v1.1-预注册-20261010.md
理论来源：知世口授命题（概念=跨维度投影合成体；语境=维度选择器）
纯计算零写盘版：全部结果经 stdout JSON 输出，文件落盘由运行方重定向完成。
影子：每模板句末位置的 next-token 分布（top-512 并集掩码）；距离=对称 JSD；有效维数=MDS 谱 ndim90
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "H:/AI/models--Qwen2.5-1.5B"
TOPK = 512

WORDS = {
    "E": ["牛顿", "北京", "苹果", "钢琴", "相对论", "熊猫", "光", "茶"],
    "F": ["的", "了", "是", "这"],
}

STYLE_TEMPLATES = [
    "介绍一下{w}的相关知识。",
    "{w}的基本概念是什么？",
    "请说明{w}的定义和来源。",
    "我最近一直在想{w}这件事。",
    "{w}啊，说起来话就长了。",
    "说实话，{w}给我的印象很深。",
    "夜色中，{w}静静地躺在记忆的角落里。",
    "他梦见了{w}，那是故乡最初的模样。",
    "{w}像一枚旧邮票，贴在时光的信封上。",
    "为什么{w}如此重要？",
    "{w}和我们的生活有什么关系？",
    "到底是谁第一个发现了{w}？",
]

TASK_TEMPLATES = [
    "什么是{w}？请给出定义。",
    "{w}的定义是什么？",
    "请以{w}为主题写一句诗。",
    "用{w}写一句浪漫的话。",
    "3个{w}加5个{w}是几个{w}？",
    "如果每个{w}值2元，7个{w}值多少钱？",
    "把{w}翻译成英文。",
    "{w}的英文怎么说？",
    "{w}和其他同类事物比有什么不同？",
    "{w}最独特的地方是什么？",
    "如果世界上没有{w}会怎样？",
    "假如{w}突然消失了，会发生什么？",
]

def next_token_probs(model, tok, sent):
    """句末位置 next-token 概率分布（fp32 numpy）"""
    ids = tok.encode(sent, add_special_tokens=True)
    with torch.no_grad():
        out = model(torch.tensor([ids]))
    logits = out.logits[0, -1].float()
    probs = torch.softmax(logits, dim=-1).numpy()
    return probs

def shadow_cloud(model, tok, templates, w):
    """12 条模板 → 12 个影子（top-512 并集掩码上的概率向量，未归一化原始概率保留）"""
    probs_list = []
    for tpl in templates:
        sent = tpl.replace("{w}", w)
        probs_list.append(next_token_probs(model, tok, sent))
    P = np.stack(probs_list)
    union = P.sum(axis=0).argsort()[::-1][:TOPK]
    return P[:, union]   # 12 × 512（每行未重新归一——JSD 用相对比例，行内归一在 jsd 内做）

def jsd_matrix(P):
    """对称 JSD 平方根距离矩阵；P: n×V（行=分布）"""
    n = P.shape[0]
    Q = P / np.maximum(P.sum(axis=1, keepdims=True), 1e-12)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            m = 0.5 * (Q[i] + Q[j])
            def kl(p, m_):
                mask = p > 1e-12
                return float(np.sum(p[mask] * np.log2(p[mask] / m_[mask])))
            d = 0.5 * kl(Q[i], m) + 0.5 * kl(Q[j], m)
            D[i, j] = D[j, i] = float(np.sqrt(max(d, 0.0)))
    return D

def mds_ndim90(D):
    """经典 MDS → 特征谱 → 保留90%方差所需维数 + participation ratio"""
    n = D.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * (H @ (D ** 2) @ H)
    vals = np.linalg.eigvalsh(B)[::-1]
    vals = np.clip(vals, 0, None)
    tot = vals.sum()
    if tot <= 0:
        return 0.0, 0.0
    cum = np.cumsum(vals) / tot
    ndim90 = int(np.searchsorted(cum, 0.9) + 1)
    pr = float(np.square(vals.sum()) / np.square(vals).sum())
    return float(ndim90), pr

def perm_paired(diffs, n_perm=20000, seed=42):
    rng = np.random.default_rng(seed)
    d = np.array(diffs)
    obs = float(np.median(d))
    cnt = 0
    for _ in range(n_perm):
        signs = rng.choice([-1.0, 1.0], size=len(d))
        if float(np.median(d * signs)) <= obs:
            cnt += 1
    return obs, float((cnt + 1) / (n_perm + 1))

def perm_test(a_vals, b_vals, n_perm=20000, seed=42):
    rng = np.random.default_rng(seed)
    a, b = np.array(a_vals), np.array(b_vals)
    obs = float(np.median(a) - np.median(b))
    pool = np.concatenate([a, b])
    na = len(a)
    cnt = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        d = np.median(pool[:na]) - np.median(pool[na:])
        if d <= obs:
            cnt += 1
    return obs, float((cnt + 1) / (n_perm + 1))

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    shadows = {}   # word -> {"style": (P12, D12, ndim90, pr, meanJSD), "task": ...}
    for g, words in WORDS.items():
        for w in words:
            entry = {}
            for kind, tpls in (("style", STYLE_TEMPLATES), ("task", TASK_TEMPLATES)):
                P = shadow_cloud(model, tok, tpls, w)
                D = jsd_matrix(P)
                nd, pr = mds_ndim90(D)
                mean_jsd = float(D[np.triu_indices(len(D), 1)].mean())
                entry[kind] = {"P": P, "D": D, "ndim90": nd, "pr": pr, "meanJSD": mean_jsd}
            shadows[w] = entry
            print(f"[shadow] {g}/{w}  style_nd={entry['style']['ndim90']} task_nd={entry['task']['ndim90']}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 判据①：配对（任务 ndim90 > 句式 ndim90，实体词）
    diffs = [shadows[w]["task"]["ndim90"] - shadows[w]["style"]["ndim90"] for w, g in [(w, gg) for gg, ws in WORDS.items() for w in ws] if True and word_group_of(w, WORDS) == "E"]
    obs1, p1 = perm_paired(diffs)

    # 判据②：组间（实体任务 ndim90 > 功能词任务 ndim90）
    e = [shadows[w]["task"]["ndim90"] for gg, ws in WORDS.items() if gg == "E" for w in ws]
    f = [shadows[w]["task"]["ndim90"] for gg, ws in WORDS.items() if gg == "F" for w in ws]
    obs2, p2 = perm_test(e, f)

    ok1 = obs1 > 0 and p1 < 0.05
    ok2 = obs2 > 0 and p2 < 0.05
    if ok1 and ok2:
        verdict = "PASS（跨维度合成体·分布读出实证·双条件全过）"
    elif ok1 or ok2:
        verdict = f"转续验（仅{'配对' if ok1 else '组间'}条件成立）"
    else:
        verdict = "FAIL（判负照记）"

    detail = {}
    for gg, ws in WORDS.items():
        for w in ws:
            detail[gg + "__" + w] = {
                "style_ndim90": shadows[w]["style"]["ndim90"], "task_ndim90": shadows[w]["task"]["ndim90"],
                "style_pr": shadows[w]["style"]["pr"], "task_pr": shadows[w]["task"]["pr"],
                "style_meanJSD": shadows[w]["style"]["meanJSD"], "task_meanJSD": shadows[w]["task"]["meanJSD"],
            }

    out = {
        "model": MODEL, "device": "cpu/fp32", "topk": TOPK,
        "words": WORDS, "style_templates": STYLE_TEMPLATES, "task_templates": TASK_TEMPLATES,
        "detail": detail,
        "c1_paired": {"n": len(diffs), "median_diff_task_minus_style": obs1, "p_one_sided": p1, "diffs": diffs},
        "c2_between": {"E_ndims": e, "F_ndims": f, "obs_diff_E_minus_F": obs2, "p_one_sided": p2},
        "J-CC2_v11": verdict,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC2判据冻结书-v1.1-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；影子=句末 next-token 分布 top-512 并集；距离=√JSD；维数=MDS 谱 ndim90",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

def word_group_of(w, WORDS):
    for g, ws in WORDS.items():
        if w in ws:
            return g
    return None

if __name__ == "__main__":
    main()
