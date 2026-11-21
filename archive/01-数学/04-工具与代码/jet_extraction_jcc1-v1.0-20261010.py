# -*- coding: utf-8 -*-
"""
J-CC1 概念度量收缩指纹首测（预注册判据已冻结：J-CC1判据冻结书-预注册-20261010.md）
纯计算零写盘版 v1.1：全部结果经 stdout JSON 输出；span 定位改用字符区间+offsets 映射（修 BPE 合并 bug）。
模型：Qwen2.5-0.5B（本地 HF 缓存，CPU，fp32）
判据：实体点云 participation ratio（PR）vs 功能词+低频词对照组，置换检验单侧
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-0.5B"
DTYPE = sys.argv[2] if len(sys.argv) > 2 else "fp32"   # fp32 | bf16（3B+ 内存折衷）
LAYERS = [6, 12, 18]
K_TEMPLATES = 12

WORDS = {
    "E": ["牛顿", "北京", "苹果", "钢琴", "相对论", "熊猫", "光", "茶"],
    "C1": ["的", "了", "是", "这"],
    "C2": ["玄武岩", "三弦", "苔藓", "晷"],
}

TEMPLATES = [
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

def pr_ratio(mat):
    """participation ratio = (Σλ)²/Σλ²，mat: K×d（v1.0 口径·已判负照记：被各向异性饱和）"""
    X = mat - mat.mean(axis=0, keepdims=True)
    s = np.linalg.svd(X, compute_uv=False)
    lam = np.square(s)
    denom = float(np.square(lam).sum())
    if denom <= 0:
        return float("inf")
    return float(np.square(lam.sum()) / denom)

def lam2_ratio(mat):
    """v1.1 口径：λ₂/λ₁（词内中心化谱前两特征值之比=第二方向相对强度）"""
    X = mat - mat.mean(axis=0, keepdims=True)
    s = np.linalg.svd(X, compute_uv=False)
    l1 = float(s[0])
    if l1 <= 0:
        return float("nan")
    return float(s[1] / l1)

def span_token_indices(tok, tpl, w):
    """返回 (sent, [token indices])：w 的字符区间经 offsets 映射定位（修 BPE 合并）"""
    i = tpl.index("{w}")
    sent = tpl.replace("{w}", w)
    char_s, char_e = i, i + len(w)
    enc = tok(sent, return_offsets_mapping=True, add_special_tokens=True)
    offsets = enc["offset_mapping"]
    idxs = []
    for idx, pair in enumerate(offsets):
        a, b = int(pair[0]), int(pair[1])
        if b > a and a < char_e and b > char_s:   # 与 w 区间重叠
            idxs.append(idx)
    if not idxs:
        raise RuntimeError(f"span empty: {w} in {sent}")
    return sent, idxs

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    dt = torch.bfloat16 if DTYPE == "bf16" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=dt)
    model.eval()
    n_layers = model.config.num_hidden_layers
    print(f"[load] {MODEL} layers={n_layers} cpu/{DTYPE}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    data = {}
    with torch.no_grad():
        for g, words in WORDS.items():
            for w in words:
                mats = {L: [] for L in LAYERS}
                for tpl in TEMPLATES:
                    sent, idxs = span_token_indices(tok, tpl, w)
                    ids = tok.encode(sent, add_special_tokens=True)
                    assert len(ids) == len(tok(sent, add_special_tokens=True)["input_ids"])
                    out = model(torch.tensor([ids]), output_hidden_states=True)
                    hs = out.hidden_states
                    for L in LAYERS:
                        mats[L].append(hs[L][0, idxs].mean(dim=0).float().numpy().astype(np.float32))
                data[(g, w)] = {L: np.stack(v) for L, v in mats.items()}
                print(f"[extract] {g}/{w}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    pr = {}
    rat = {}
    jet_summary = {}
    for (g, w), mats in data.items():
        pr[(g, w)] = {L: pr_ratio(m) for L, m in mats.items()}
        rat[(g, w)] = {L: lam2_ratio(m) for L, m in mats.items()}
        m12 = mats[12]
        X = m12 - m12.mean(0, keepdims=True)
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        jet_summary[g + "__" + w] = {
            "x_L12_norm": float(np.linalg.norm(m12.mean(axis=0))),
            "J_top3_sv": [float(x) for x in S[:3]],
        }

    def perm_test(e_vals, c_vals, n_perm=20000, seed=42):
        rng = np.random.default_rng(seed)
        e, c = np.array(e_vals), np.array(c_vals)
        obs = float(np.median(e) - np.median(c))
        pool = np.concatenate([e, c])
        ne = len(e)
        cnt = 0
        for _ in range(n_perm):
            rng.shuffle(pool)
            d = np.median(pool[:ne]) - np.median(pool[ne:])
            if d <= obs:
                cnt += 1
        return obs, float((cnt + 1) / (n_perm + 1))

    verdict = {}
    # v1.0 绝对 PR 口径（FAIL 照记）
    for L in LAYERS:
        e = [pr[(g, w)][L] for (g, w) in pr if g == "E"]
        c = [pr[(g, w)][L] for (g, w) in pr if g in ("C1", "C2")]
        obs, p = perm_test(e, c)
        verdict[str(L)] = {
            "E_median_PR": float(np.median(e)), "E_PRs": e,
            "C_median_PR": float(np.median(c)), "C_PRs": c,
            "obs_diff_E_minus_C": obs, "p_one_sided": p,
        }
    passed = sum(1 for L in LAYERS if verdict[str(L)]["obs_diff_E_minus_C"] < 0 and verdict[str(L)]["p_one_sided"] < 0.05)
    if passed >= 2:
        jc = "PASS（实体点云谱塌缩成立·概念度量收缩指纹）"
    elif passed == 1:
        jc = "转续验（仅一层成立）"
    else:
        rev = sum(1 for L in LAYERS if verdict[str(L)]["obs_diff_E_minus_C"] > 0 and verdict[str(L)]["p_one_sided"] < 0.05)
        jc = ("FAIL（判负照记）" if rev == 0 else
              f"反向显著候选读法：概念=高维发散点（{rev}层反向显著·如实标注）")

    # ---- v1.1 谱比口径（λ₂/λ₁·冻结书 v1.1）----
    verdict_v11 = {}
    for L in LAYERS:
        e = [rat[(g, w)][L] for (g, w) in rat if g == "E"]
        c = [rat[(g, w)][L] for (g, w) in rat if g in ("C1", "C2")]
        obs, p = perm_test(e, c)
        verdict_v11[str(L)] = {
            "E_median_ratio": float(np.median(e)), "E_ratios": e,
            "C_median_ratio": float(np.median(c)), "C_ratios": c,
            "obs_diff_E_minus_C": obs, "p_one_sided": p,
        }
    passed11 = sum(1 for L in LAYERS if verdict_v11[str(L)]["obs_diff_E_minus_C"] < 0 and verdict_v11[str(L)]["p_one_sided"] < 0.05)
    if passed11 >= 2:
        jc11 = "PASS（实体点云谱塌缩成立·概念度量收缩指纹·谱比口径）"
    elif passed11 == 1:
        jc11 = "转续验（仅一层成立）"
    else:
        rev11 = sum(1 for L in LAYERS if verdict_v11[str(L)]["obs_diff_E_minus_C"] > 0 and verdict_v11[str(L)]["p_one_sided"] < 0.05)
        jc11 = ("FAIL（判负照记）" if rev11 == 0 else
               f"反向显著候选读法：概念=高维发散点（{rev11}层反向显著·如实标注）")

    out = {
        "model": MODEL, "device": "cpu/fp32",
        "layers": LAYERS, "k_templates": K_TEMPLATES,
        "words": WORDS, "templates": TEMPLATES,
        "PR": {g + "__" + w: {str(L): pr[(g, w)][L] for L in LAYERS} for (g, w) in pr},
        "RATIO": {g + "__" + w: {str(L): rat[(g, w)][L] for L in LAYERS} for (g, w) in rat},
        "jet_summary_L12": jet_summary,
        "verdict_by_layer": verdict,
        "J-CC1": jc,
        "verdict_v11_by_layer": verdict_v11,
        "J-CC1_v11": jc11,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC1判据冻结书-预注册-20261010.md（v1.0）+J-CC1判据冻结书-v1.1-预注册-20261010.md（先于重跑落盘）",
        "honest_note": "纯计算零写盘：原始激活矩阵未落盘（复跑可再现）；v1.0 绝对 PR 口径首跑 FAIL 照记（各向异性饱和）；v1.1 谱比口径 λ₂/λ₁",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
