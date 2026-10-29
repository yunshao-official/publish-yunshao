# -*- coding: utf-8 -*-
"""
J-CC2 跨维度概念合成体首测（预注册判据已冻结：J-CC2判据冻结书-预注册-20261010.md）
理论来源：知世口授命题（语境=维度选择器；概念=跨维度投影合成体）
纯计算零写盘版：全部结果经 stdout JSON 输出，文件落盘由运行方重定向完成。
模型：Qwen2.5-1.5B（本地路径，CPU，fp32）
判据：①配对（任务点云PR>句式点云PR，同词自配）②组间（实体任务PR>功能词任务PR）——去全局公共均值后 PR
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "H:/AI/models--Qwen2.5-1.5B"
LAYERS = [6, 12, 18]

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

def pr_debias(mat, global_mean):
    """去全局公共均值后的 participation ratio（J-CC1 饱和教训：必须去公共方向）"""
    X = mat - global_mean[None, :]
    X = X - X.mean(axis=0, keepdims=True)
    s = np.linalg.svd(X, compute_uv=False)
    lam = np.square(s)
    denom = float(np.square(lam).sum())
    if denom <= 0:
        return float("inf")
    return float(np.square(lam.sum()) / denom)

def lam2_ratio(mat, global_mean):
    X = mat - global_mean[None, :]
    X = X - X.mean(axis=0, keepdims=True)
    s = np.linalg.svd(X, compute_uv=False)
    if float(s[0]) <= 0:
        return float("nan")
    return float(s[1] / s[0])

def span_token_indices(tok, tpl, w):
    i = tpl.index("{w}")
    sent = tpl.replace("{w}", w)
    char_s, char_e = i, i + len(w)
    enc = tok(sent, return_offsets_mapping=True, add_special_tokens=True)
    offsets = enc["offset_mapping"]
    idxs = []
    for idx, pair in enumerate(offsets):
        a, b = int(pair[0]), int(pair[1])
        if b > a and a < char_e and b > char_s:
            idxs.append(idx)
    if not idxs:
        raise RuntimeError(f"span empty: {w} in {sent}")
    return sent, idxs

def perm_test(a_vals, b_vals, n_perm=20000, seed=42):
    """单侧：obs = median(A)-median(B)，p = P(perm diff <= obs)"""
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

def perm_paired(diffs, n_perm=20000, seed=42):
    """配对单侧：obs = median(diffs)，零假设=对称翻转，p = P(median(flip) <= obs)"""
    rng = np.random.default_rng(seed)
    d = np.array(diffs)
    obs = float(np.median(d))
    cnt = 0
    for _ in range(n_perm):
        signs = rng.choice([-1.0, 1.0], size=len(d))
        if float(np.median(d * signs)) <= obs:
            cnt += 1
    return obs, float((cnt + 1) / (n_perm + 1))

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL} cpu/fp32  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 收集：每词两类点云（style/task），层 6/12/18
    clouds = {}  # (word) -> {"style": {L: 12xd}, "task": {L: 12xd}}
    word_group = {}
    with torch.no_grad():
        for g, words in WORDS.items():
            for w in words:
                entry = {"style": {L: [] for L in LAYERS}, "task": {L: [] for L in LAYERS}}
                for kind, templates in (("style", STYLE_TEMPLATES), ("task", TASK_TEMPLATES)):
                    for tpl in templates:
                        sent, idxs = span_token_indices(tok, tpl, w)
                        ids = tok.encode(sent, add_special_tokens=True)
                        out = model(torch.tensor([ids]), output_hidden_states=True)
                        hs = out.hidden_states
                        for L in LAYERS:
                            entry[kind][L].append(hs[L][0, idxs].mean(dim=0).numpy().astype(np.float32))
                for L in LAYERS:
                    entry["style"][L] = np.stack(entry["style"][L])
                    entry["task"][L] = np.stack(entry["task"][L])
                clouds[w] = entry
                word_group[w] = g
                print(f"[extract] {g}/{w}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 全局公共均值（每层）：全部词全部语境的全部激活点均值
    global_mean = {}
    for L in LAYERS:
        allpts = []
        for w, entry in clouds.items():
            allpts.append(entry["style"][L])
            allpts.append(entry["task"][L])
        global_mean[L] = np.concatenate(allpts, axis=0).mean(axis=0)

    # PR（去公共均值）
    pr = {}   # word -> {"style": {L: pr}, "task": {L: pr}}
    ratio = {}
    for w, entry in clouds.items():
        pr[w] = {}
        ratio[w] = {}
        for kind in ("style", "task"):
            pr[w][kind] = {L: pr_debias(entry[kind][L], global_mean[L]) for L in LAYERS}
            ratio[w][kind] = {L: lam2_ratio(entry[kind][L], global_mean[L]) for L in LAYERS}

    # ---- 判据①：配对（任务>句式）——实体词内配对 ----
    paired = {}
    for L in LAYERS:
        diffs = [pr[w]["task"][L] - pr[w]["style"][L] for w, g in word_group.items() if g == "E"]
        obs, p = perm_paired(diffs)
        paired[str(L)] = {"n": len(diffs), "median_diff_task_minus_style": obs, "p_one_sided": p,
                          "diffs": [float(x) for x in diffs]}
    ok1 = sum(1 for L in LAYERS if paired[str(L)]["median_diff_task_minus_style"] > 0 and paired[str(L)]["p_one_sided"] < 0.05)

    # ---- 判据②：组间（实体任务PR > 功能词任务PR）----
    between = {}
    for L in LAYERS:
        e = [pr[w]["task"][L] for w, g in word_group.items() if g == "E"]
        f = [pr[w]["task"][L] for w, g in word_group.items() if g == "F"]
        obs, p = perm_test(e, f)
        between[str(L)] = {"E_median_PR_task": float(np.median(e)), "E_PRs": e,
                           "F_median_PR_task": float(np.median(f)), "F_PRs": f,
                           "obs_diff_E_minus_F": obs, "p_one_sided": p}
    ok2 = sum(1 for L in LAYERS if between[str(L)]["obs_diff_E_minus_F"] > 0 and between[str(L)]["p_one_sided"] < 0.05)

    if ok1 >= 2 and ok2 >= 2:
        verdict = "PASS（语境=维度选择器·跨维度合成体实证·双条件全过）"
    elif ok1 >= 2 or ok2 >= 2:
        which = "配对条件" if ok1 >= 2 else "组间条件"
        verdict = f"转续验（仅{which}成立）"
    else:
        verdict = "FAIL（判负照记）"

    # 附带：类内中心距离谱（任务骨架描述统计，层12）
    task_class_centers = {}
    for w, g in word_group.items():
        if g != "E":
            continue
        entry = clouds[w]
        centers = []
        for ci in range(6):
            pts = entry["task"][12][ci * 2:(ci + 1) * 2]
            centers.append(pts.mean(axis=0))
        centers = np.stack(centers)
        C = centers - centers.mean(0, keepdims=True)
        s = np.linalg.svd(C, compute_uv=False)
        task_class_centers[w] = {"top6_sv": [float(x) for x in s[:6]]}

    out = {
        "model": MODEL, "device": "cpu/fp32", "layers": LAYERS,
        "words": WORDS,
        "style_templates": STYLE_TEMPLATES, "task_templates": TASK_TEMPLATES,
        "PR_debiased": {w: {k: {str(L): pr[w][k][L] for L in LAYERS} for k in ("style", "task")} for w in pr},
        "RATIO": {w: {k: {str(L): ratio[w][k][L] for L in LAYERS} for k in ("style", "task")} for w in ratio},
        "c1_paired": paired, "c2_between": between,
        "task_class_centers_L12": task_class_centers,
        "verdict_c1_layers_ok": ok1, "verdict_c2_layers_ok": ok2,
        "J-CC2": verdict,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC2判据冻结书-预注册-20261010.md（先于实算落盘·理论来源=知世口授）",
        "honest_note": "纯计算零写盘；PR 去全局公共均值（J-CC1 饱和教训修正）；配对=同词自配对置换",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
