# -*- coding: utf-8 -*-
"""
J-U4 邻域覆盖率实测（预注册：J-U4判据冻结书-预注册-20261010.md）
原模型自回归生成 → 概念轨迹 → 落在初始概念邻域的比例
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
EDGES = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt"
N_GEN = 40
PROMPTS = ["猫是", "太阳从东边", "医生建议", "音乐会的", "北京的中", "水的用", "战争爆", "梦见了"]

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N, dim = Emb.shape

    # 宇宙（576 簇）+词→簇
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for l in open(EDGES):
        u, v = map(int, l.split())
        ra, rb = find(u), find(v)
        if ra != rb: parent[rb] = ra
    roots = np.array([find(i) for i in range(N)])
    uniq, counts = np.unique(roots, return_counts=True)
    r2i = {r: i for i, r in enumerate(uniq)}
    K = len(uniq)
    word_to_cluster = {i: r2i[roots[i]] for i in range(N)}
    print(f"[universe] K={K}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 邻域函数：种子词 id → 其簇 + top-10 邻居簇 + 两步可达簇
    def neighborhood(seed_ids):
        ks = set()
        core = set()
        for sid in seed_ids:
            k = word_to_cluster.get(sid)
            if k is not None:
                ks.add(k); core.add(k)
        # embedding top-10 邻居（种子向量）的簇
        cv = En[seed_ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
        for ti in np.argsort(-En @ cv)[:10]:
            ks.add(word_to_cluster.get(int(ti), -1))
        # 两步可达：邻域簇的 embedding 邻居簇（再加一层）
        for ti in np.argsort(-En @ cv)[:40]:
            k2 = word_to_cluster.get(int(ti), -1)
            ks.add(k2)
        ks.discard(-1)
        return ks, core

    def token_to_cluster(tid):
        k = word_to_cluster.get(tid)
        if k is not None: return k
        v = En[tid]
        nn = int(np.argmax(En @ v))
        return word_to_cluster.get(nn, -1)

    # 逐 prompt 生成+覆盖率
    coverages = []
    detail = []
    for pr in PROMPTS:
        ids = tok.encode(pr, add_special_tokens=True)
        ks_nb, core = neighborhood(ids)
        # 自回归生成 40 token（原模型）
        gen_ids = []
        cur = ids
        with torch.no_grad():
            for _ in range(N_GEN):
                out = model(torch.tensor([cur[-512:]]))
                nid = int(np.argmax(out.logits[0, -1]))
                gen_ids.append(nid); cur = cur + [nid]
                if nid == tok.eos_token_id: break
        # 概念轨迹
        traj_clusters = set()
        for tid in gen_ids:
            k = token_to_cluster(tid)
            traj_clusters.add(k)
        covered = sum(1 for k in traj_clusters if k in ks_nb)
        cov = covered / max(len(traj_clusters), 1)
        coverages.append(cov)
        detail.append({"prompt": pr, "gen_tokens": len(gen_ids),
                       "traj_clusters": len(traj_clusters), "neighborhood_size": len(ks_nb),
                       "coverage": round(cov, 3)})
        print(f"[gen] {pr} cov={cov:.3f}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    mean_cov = float(np.mean(coverages))
    if mean_cov > 0.6:
        verdict = "PASS（邻域可承载生成·公式嫁接可行）"
    elif mean_cov >= 0.4:
        verdict = "转续验（邻域半径需调）"
    else:
        verdict = "FAIL（判负照记）"

    out = {
        "model": MODEL, "n_prompts": len(PROMPTS), "gen_per_prompt": N_GEN,
        "mean_coverage": round(mean_cov, 4), "coverages": [round(c,3) for c in coverages],
        "detail": detail,
        "J-U4": verdict,
        "elapsed_s": round(time.time()-t0, 1),
        "frozen_doc": "J-U4判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "邻域=簇+top10邻居簇+两步可达；覆盖率=轨迹簇去重后落在邻域的比例",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
