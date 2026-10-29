# -*- coding: utf-8 -*-
"""
J-U4b 主大陆切分（标签传播社区发现）+ 细粒度覆盖率重测
预注册：J-U4b判据冻结书-预注册-20261010.md
纯计算零写盘版（社区谱+8 prompt 覆盖率重测）。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
import networkx as nx
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

    # 语义图（top-3）
    G = nx.Graph()
    with open(EDGES) as f:
        for l in f:
            u, v = map(int, l.split())
            G.add_edge(u, v)
    print(f"[graph] {G.number_of_nodes()} nodes {G.number_of_edges()} edges  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 标签传播社区发现（线性时间）
    t1 = time.time()
    comms = nx.community.asyn_lpa_communities(G, seed=42)
    comm_list = sorted((set(c) for c in comms), key=len, reverse=True)
    word_to_comm = {}
    for ci, c in enumerate(comm_list):
        for w in c:
            word_to_comm[w] = ci
    sizes = sorted((len(c) for c in comm_list), reverse=True)
    print(f"[communities] {len(comm_list)} communities  top10={sizes[:10]}  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # 细粒度覆盖率重测（8 prompt×40 token 自回归）
    coverages = []
    detail = []
    for pr in PROMPTS:
        ids = tok.encode(pr, add_special_tokens=True)
        # 邻域（社区粒度）：种子 token 的社区 + embedding top-10 邻居的社区 + 两步
        cv = En[ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
        nb = set()
        for ti in np.argsort(-En @ cv)[:40]:
            w = word_to_comm.get(int(ti))
            if w is not None: nb.add(w)
        # 种子 token 的社区
        for sid in ids:
            w = word_to_comm.get(sid)
            if w is not None: nb.add(w)
        # 自回归 40 token
        gen_ids = []
        cur = list(ids)
        with torch.no_grad():
            for _ in range(N_GEN):
                out = model(torch.tensor([cur[-512:]]))
                nid = int(np.argmax(out.logits[0, -1]))
                gen_ids.append(nid); cur.append(nid)
                if nid == tok.eos_token_id: break
        traj = set()
        for tid in gen_ids:
            w = word_to_comm.get(tid)
            if w is None:
                v = En[tid]
                w = word_to_comm.get(int(np.argmax(En @ v)), -1)
            traj.add(w)
        covered = sum(1 for c in traj if c in nb)
        cov = covered / max(len(traj), 1)
        coverages.append(cov)
        detail.append({"prompt": pr, "traj_communities": len(traj), "neighborhood": len(nb), "coverage": round(cov, 3)})
        print(f"[gen] {pr} cov={cov:.3f}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    mean_cov = float(np.mean(coverages))
    if mean_cov > 0.6:
        verdict = "PASS（细粒度邻域可承载生成·真检验通过）"
    elif mean_cov >= 0.4:
        verdict = "转续验（粒度或深度需调）"
    else:
        verdict = "FAIL（判负照记）"

    out = {
        "model": MODEL,
        "community_spectrum": {"n_communities": len(comm_list), "top20_sizes": sizes[:20],
                                "median": int(np.median(sizes)), "singletons": sum(1 for s in sizes if s == 1)},
        "mean_coverage": round(mean_cov, 4), "coverages": [round(c, 3) for c in coverages],
        "detail": detail,
        "J-U4b": verdict,
        "elapsed_s": round(time.time()-t0, 1),
        "frozen_doc": "J-U4b判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "切分=LPA 标签传播（语义图 455808 边）；覆盖率=轨迹社区落在种子邻域（top40+种子社区）的比例",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
