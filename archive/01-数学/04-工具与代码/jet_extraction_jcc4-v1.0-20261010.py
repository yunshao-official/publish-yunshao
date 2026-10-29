# -*- coding: utf-8 -*-
"""
J-CC4 两种距离体系对表（预注册：J-CC4判据冻结书-预注册-20261010.md）
理论来源：知世口授（"概念的距离跟Token的距离是不一样的"+填充性距离）
d_fill = 模型自建从属链步数（"{A}是一种"BFS 深度4，B 在链=链长，不在=5）
d_JSD  = 两概念中性影子分布的对称 JSD
判定 H1：Spearman 弱相关 → PASS（两距离体系分离）
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

PAIRS = [
    ("从属", "苹果", "水果"), ("从属", "猫", "动物"), ("从属", "钢琴", "乐器"),
    ("从属", "茶", "饮料"), ("从属", "北京", "城市"), ("从属", "玫瑰", "花"),
    ("从属", "狗", "动物"), ("从属", "汽车", "交通工具"),
    ("同层", "猫", "狗"), ("同层", "苹果", "香蕉"), ("同层", "北京", "上海"),
    ("同层", "猫", "老虎"), ("同层", "狗", "狼"),
    ("无关", "猫", "汽车"), ("无关", "苹果", "民主"), ("无关", "茶", "钢琴"),
    ("无关", "时间", "石头"), ("无关", "音乐", "袜子"), ("无关", "梦", "发票"),
    ("无关", "猫", "民主"),
]

CONCEPTS = sorted({w for _, a, b in PAIRS for w in (a, b)})
NEUTRAL = "请谈谈{w}。"

def next_token_probs(model, tok, sent):
    ids = tok.encode(sent, add_special_tokens=True)
    with torch.no_grad():
        out = model(torch.tensor([ids]))
    return torch.softmax(out.logits[0, -1].float(), dim=-1).numpy()

def jsd_pair(p, q):
    p = p / max(p.sum(), 1e-12)
    q = q / max(q.sum(), 1e-12)
    m = 0.5 * (p + q)
    def kl(x):
        mask = x > 1e-12
        return float(np.sum(x[mask] * np.log2(x[mask] / m[mask])))
    return float(np.sqrt(max(0.5 * kl(p) + 0.5 * kl(q), 0.0)))

def spearman(x, y):
    """秩相关 + 置换 p（双侧）"""
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx = (rx - rx.mean()) / (rx.std() + 1e-12)
    ry = (ry - ry.mean()) / (ry.std() + 1e-12)
    rho = float((rx * ry).mean())
    rng = np.random.default_rng(42)
    cnt = 0
    n_perm = 20000
    for _ in range(n_perm):
        ry2 = rng.permutation(ry)
        r2 = float((rx * ry2).mean())
        if abs(r2) >= abs(rho):
            cnt += 1
    return rho, float((cnt + 1) / (n_perm + 1))

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 1. 每概念中性影子
    P = {}
    for w in CONCEPTS:
        P[w] = next_token_probs(model, tok, NEUTRAL.replace("{w}", w))
    print(f"[shadow] {len(P)} concepts  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 统一掩码（全局 top-512）
    Pall = np.stack(list(P.values()))
    union = Pall.sum(axis=0).argsort()[::-1][:TOPK]
    Pu = {w: P[w][union] for w in CONCEPTS}

    # 2. d_JSD
    d_jsd = {}
    for kind, a, b in PAIRS:
        d_jsd[f"{a}|{b}"] = jsd_pair(Pu[a], Pu[b])

    # 3. d_fill："{A}是一种" BFS 深度 4
    def top_successors(w, k=5):
        probs = next_token_probs(model, tok, f"{w}是一种")
        ids = probs.argsort()[::-1][:k]
        out = []
        for i in ids:
            t = tok.decode([int(i)]).strip()
            if t and t not in ("的", "，", "。", "是", "一", "种") and len(t) <= 6:
                out.append(t)
        return out

    d_fill = {}
    paths = {}
    for kind, a, b in PAIRS:
        frontier = {a}
        visited = {a}
        found_depth = None
        path_log = {}
        for depth in range(1, 5):
            nxt = set()
            for u in frontier:
                succ = top_successors(u)
                path_log[u] = succ
                for s in succ:
                    if s == b:
                        found_depth = depth
                        frontier = set()
                        break
                    if s not in visited:
                        nxt.add(s)
                        visited.add(s)
                if found_depth:
                    break
            if found_depth:
                break
            frontier = nxt - visited
            if not frontier:
                break
        d_fill[f"{a}|{b}"] = found_depth if found_depth else 5
        paths[f"{a}|{b}"] = path_log

    # 4. H1：Spearman（d_fill 封顶 5 的对保留原值——主分析；敏感性：仅用未封顶对）
    xs = [d_fill[f"{a}|{b}"] for _, a, b in PAIRS]
    ys = [d_jsd[f"{a}|{b}"] for _, a, b in PAIRS]
    rho_all, p_all = spearman(xs, ys)
    mask_uncapped = [i for i, x in enumerate(xs) if x < 5]
    if len(mask_uncapped) >= 8:
        rho_u, p_u = spearman([xs[i] for i in mask_uncapped], [ys[i] for i in mask_uncapped])
    else:
        rho_u, p_u = None, None

    # H1 判定
    if rho_all < 0.5 or p_all > 0.05:
        h1 = "PASS（两距离体系分离·知世直觉实证）"
    elif rho_all >= 0.7 and p_all < 0.05:
        h1 = "FAIL（两距离同步·知世直觉判负照记）"
    else:
        h1 = "转续验（中间带）"

    # H2：三组 JSD 均值
    grp = {}
    for kind, a, b in PAIRS:
        grp.setdefault(kind, []).append(d_jsd[f"{a}|{b}"])
    grp_mean = {k: float(np.mean(v)) for k, v in grp.items()}

    out = {
        "model": MODEL,
        "pairs": [{"kind": k, "a": a, "b": b, "d_fill": d_fill[f"{a}|{b}"], "d_JSD": round(d_jsd[f"{a}|{b}"], 4)} for k, a, b in PAIRS],
        "chain_paths": paths,
        "spearman_all": {"rho": rho_all, "p": p_all},
        "spearman_uncapped": {"rho": rho_u, "p": p_u, "n": len(mask_uncapped)},
        "H1": h1,
        "group_mean_JSD": grp_mean,
        "H2_note": "同层组 d_fill 封顶但 JSD 与从属组对比=分离实例记录",
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC4判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；d_fill=模型自证从属链（top5/BFS4）；封顶值 5",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
