# -*- coding: utf-8 -*-
"""
J-H1 语义哈密顿序验证（预注册：J-H1判据冻结书-预注册-20261010.md）
理论来源：知世口授三连问（哈密顿路径替代权重存储）
30 概念中性影子 → JSD 矩阵 → 贪心最近邻哈密顿路径
检验 A：路径相邻对 JSD 均值 vs 全体平均（置换）
检验 B：路径位置距离 vs JSD 的 Spearman
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

CONCEPTS = ["猫", "死亡", "愤怒", "快乐", "勇敢", "聪明", "大海", "花朵", "朋友", "时间",
            "家庭", "自由", "太阳", "山", "雨", "书", "道路", "梦", "爱", "恨",
            "勇气", "财富", "权力", "教育", "医生", "音乐", "战争", "和平", "孤独", "希望"]
NEUTRAL = "请谈谈{w}。"

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
            D[i, j] = D[j, i] = float(np.sqrt(max(0.5 * kl(Q[i]) + 0.5 * kl(Q[j]), 0.0)))
    return D

def greedy_hamiltonian(D):
    """贪心最近邻哈密顿路径（取全局最优起点）"""
    n = D.shape[0]
    best_path, best_len = None, float("inf")
    for start in range(n):
        visited = [start]
        used = {start}
        total = 0.0
        for _ in range(n - 1):
            cur = visited[-1]
            cand = [(D[cur, j], j) for j in range(n) if j not in used]
            d, nxt = min(cand)
            visited.append(nxt)
            used.add(nxt)
            total += d
        if total < best_len:
            best_len, best_path = total, visited
    pos = {v: i for i, v in enumerate(best_path)}
    return best_path, pos, best_len

def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx = (rx - rx.mean()) / (rx.std() + 1e-12)
    ry = (ry - ry.mean()) / (ry.std() + 1e-12)
    rho = float((rx * ry).mean())
    rng = np.random.default_rng(42)
    cnt = 0
    for _ in range(20000):
        if abs(float((rx * rng.permutation(ry)).mean())) >= abs(rho):
            cnt += 1
    return rho, float((cnt + 1) / 20001)

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    P = np.stack([next_token_probs(model, tok, NEUTRAL.replace("{w}", w)) for w in CONCEPTS])
    union = P.sum(axis=0).argsort()[::-1][:TOPK]
    D = jsd_matrix(P[:, union])
    n = len(CONCEPTS)
    print(f"[JSD] 30x30  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 路径构建
    path, pos, path_len = greedy_hamiltonian(D)
    path_names = [CONCEPTS[i] for i in path]

    # 检验 A：相邻对均值 vs 全体均值 + 置换
    adj = [D[path[i], path[i + 1]] for i in range(n - 1)]
    adj_mean = float(np.mean(adj))
    all_mean = float(D[np.triu_indices(n, 1)].mean())
    rng = np.random.default_rng(42)
    cnt_a = 0
    for _ in range(20000):
        rp = rng.permutation(n)
        rmean = float(np.mean([D[rp[i], rp[i + 1]] for i in range(n - 1)]))
        if rmean <= adj_mean:
            cnt_a += 1
    p_a = float((cnt_a + 1) / 20001)

    # 检验 B：路径位置距离 vs JSD
    pdist, jsds = [], []
    for i in range(n):
        for j in range(i + 1, n):
            pdist.append(abs(pos[CONCEPTS.index(CONCEPTS[i])] - pos[CONCEPTS.index(CONCEPTS[j])]))
            jsds.append(D[i, j])
    rho_b, p_b = spearman(pdist, jsds)

    ok_a = adj_mean < all_mean and p_a < 0.05
    ok_b = rho_b > 0.3 and p_b < 0.05
    if ok_a and ok_b:
        verdict = "PASS（语义哈密顿序成立·路径可作概念宇宙存储骨架）"
    elif ok_a or ok_b:
        verdict = f"转续验（仅{'A局部性' if ok_a else 'B路径编码'}成立）"
    else:
        verdict = "FAIL（判负照记）"

    out = {
        "model": MODEL,
        "path": path_names, "path_len": round(path_len, 4),
        "checkA": {"adjacent_mean_JSD": adj_mean, "all_mean_JSD": all_mean,
                   "ratio": round(adj_mean / all_mean, 4), "p_perm": p_a, "ok": ok_a},
        "checkB": {"spearman_posdist_vs_JSD": rho_b, "p": p_b, "ok": ok_b},
        "J-H1": verdict,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-H1判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；贪心最近邻哈密顿路径（30 起点 取全长最优）；A/B 双判据",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
