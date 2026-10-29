# -*- coding: utf-8 -*-
"""
J-H1 v2：语义哈密顿序——按云韶哈密顿框架正本管线重做
（升维-辐射-降维：G1语义稀疏图 → G2两步可达升维 → 遍历 → 虫洞插公共邻居降维 → 广义哈密顿路径）
参照：迭代升维压缩边算法-20260726.md / BA图完整走通方法（正本）
检验同 J-H1 v1（A 局部性 / B 路径编码）+ 与贪心 v1 对比
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

def greedy_hp_on_graph(Dg):
    """在图距离矩阵 Dg 上贪心最近邻哈密顿（取最优起点）"""
    n = Dg.shape[0]
    best_path, best_len = None, float("inf")
    for start in range(n):
        visited = [start]
        used = {start}
        total = 0.0
        for _ in range(n - 1):
            cur = visited[-1]
            cand = [(Dg[cur, j], j) for j in range(n) if j not in used]
            d, nxt = min(cand)
            visited.append(nxt)
            used.add(nxt)
            total += d
        if total < best_len:
            best_len, best_path = total, list(visited)
    return best_path, best_len

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
    print(f"[JSD]  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- 云韶管线：G1 稀疏语义图（阈值=中位数）----
    T = float(np.median(D[np.triu_indices(n, 1)]))
    G1 = (D <= T)
    np.fill_diagonal(G1, False)

    # ---- 升维：G2 = G1 ∪ 两步可达（存在公共邻居）----
    reach2 = (G1.astype(int) @ G1.astype(int)) > 0
    G2 = G1 | reach2
    np.fill_diagonal(G2, False)
    # 图距离：G1 边=1，G2 虫洞边=2（两步）
    Dg = np.where(G2, np.where(G1, 1.0, 2.0), 1e6)
    np.fill_diagonal(Dg, 0)
    print(f"[G1边数]={G1.sum()//2}  [G2边数]={G2.sum()//2}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- 遍历：在 G2（稠密好遍历）上贪心哈密顿 ----
    path_g2, len_g2 = greedy_hp_on_graph(Dg)
    # ---- 降维：G2 边若非 G1 边（虫洞），插公共邻居 w（真实管线：full_real_descent 思想）----
    expanded = [path_g2[0]]
    wormholes = 0
    for i in range(len(path_g2) - 1):
        u, v = path_g2[i], path_g2[i + 1]
        if G1[u, v]:
            expanded.append(v)
        else:
            # 找公共语义邻居（JSD 最小的共同近邻）
            common = [w for w in range(n) if w != u and w != v and G1[u, w] and G1[v, w]]
            if common:
                w_best = min(common, key=lambda w: D[u, w] + D[w, v])
                expanded.append(w_best)
                expanded.append(v)
                wormholes += 1
            else:
                expanded.append(v)   # 无公共邻居，直跳（诚实记录）
    # 展开路径上相邻对的真实 JSD（walk 允许重复——广义哈密顿）
    adj = [D[expanded[i], expanded[i + 1]] for i in range(len(expanded) - 1)]
    adj_mean = float(np.mean(adj))
    all_mean = float(D[np.triu_indices(n, 1)].mean())

    # 检验 A：置换
    rng = np.random.default_rng(42)
    cnt_a = 0
    m = len(adj)
    for _ in range(20000):
        rp = rng.permutation(n)
        rmean = float(np.mean([D[rp[i], rp[i + 1]] for i in range(n - 1)]))
        if rmean <= adj_mean:
            cnt_a += 1
    p_a = float((cnt_a + 1) / 20001)
    ok_a = adj_mean < all_mean and p_a < 0.05

    # 检验 B：路径位置距离 vs JSD（用展开路径首次出现位置）
    pos = {}
    for i, v in enumerate(expanded):
        if v not in pos:
            pos[v] = i
    pdist, jsds = [], []
    for i in range(n):
        for j in range(i + 1, n):
            pi, pj = pos.get(i, 999), pos.get(j, 999)
            pdist.append(abs(pi - pj))
            jsds.append(D[i, j])
    rho_b, p_b = spearman(pdist, jsds)
    ok_b = rho_b > 0.3 and p_b < 0.05

    # v1 贪心对照（全连接 D 直接贪心）
    path_v1, len_v1 = greedy_hp_on_graph(D)
    adj_v1 = float(np.mean([D[path_v1[i], path_v1[i + 1]] for i in range(n - 1)]))

    ok1 = adj_mean < all_mean and p_a < 0.05
    ok2 = rho_b > 0.3 and p_b < 0.05
    if ok1 and ok2:
        verdict = "PASS（云韶管线语义哈密顿序成立）"
    elif ok1 or ok2:
        verdict = f"转续验（仅{'A局部性' if ok1 else 'B路径编码'}成立）"
    else:
        verdict = "FAIL（判负照记）"

    out = {
        "model": MODEL, "framework": "云韶哈密顿管线 v2（升维G2→遍历→虫洞降维）",
        "G1_edges": int(G1.sum() // 2), "G2_edges": int(G2.sum() // 2),
        "wormholes": wormholes,
        "expanded_len": len(expanded),
        "path_names": [CONCEPTS[i] for i in expanded],
        "checkA": {"adjacent_mean_JSD": adj_mean, "all_mean_JSD": all_mean,
                   "ratio": round(adj_mean / all_mean, 4), "p_perm": p_a, "ok": ok_a},
        "checkB": {"spearman": rho_b, "p": p_b, "ok": ok_b},
        "v1_greedy_baseline": {"adjacent_mean_JSD": adj_v1, "path": [CONCEPTS[i] for i in path_v1]},
        "J-H1v2": verdict,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-H1判据冻结书（v1）+框架正本=迭代升维压缩边算法-20260726.md",
        "honest_note": "纯计算零写盘；G2 边权=1/2（虫洞两步）；展开 walk 允许重复节点（广义哈密顿，正本口径）",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
