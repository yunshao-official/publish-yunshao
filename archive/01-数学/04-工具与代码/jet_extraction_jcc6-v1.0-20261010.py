# -*- coding: utf-8 -*-
"""
J-CC6 概念距离=权重本身？（预注册：J-CC6判据冻结书-预注册-20261010.md）
理论来源：知世口授猜想——"概念空间的距离就是权重本身"
三方对表：d_emb（embedding 权重行向量余弦距离）/ d_JSD（影子分布距离·沿用 J-CC4）/ d_fill（从属链·沿用 J-CC4）
embedding 直接读权重矩阵，无前向计算。纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "H:/AI/models--Qwen2.5-1.5B"
DTYPE = sys.argv[2] if len(sys.argv) > 2 else "fp32"

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

# d_fill/d_JSD 沿用 J-CC4 1.5B 结果（冻结书同源）
JCC4_REF = {
    "苹果|水果": (1, 0.4926), "猫|动物": (1, 0.4031), "钢琴|乐器": (1, 0.5455),
    "茶|饮料": (1, 0.3840), "北京|城市": (5, 0.4670), "玫瑰|花": (1, 0.4042),
    "狗|动物": (5, 0.3819), "汽车|交通工具": (1, 0.3761),
    "猫|狗": (5, 0.2303), "苹果|香蕉": (5, 0.5116), "北京|上海": (5, 0.4327),
    "猫|老虎": (5, 0.4340), "狗|狼": (5, 0.2909),
    "猫|汽车": (5, 0.4632), "苹果|民主": (5, 0.6412), "茶|钢琴": (5, 0.6048),
    "时间|石头": (5, 0.5704), "音乐|袜子": (5, 0.5618), "梦|发票": (5, 0.4425),
    "猫|民主": (5, 0.6215),
}

CONCEPTS = sorted({w for _, a, b in PAIRS for w in (a, b)})

def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx = (rx - rx.mean()) / (rx.std() + 1e-12)
    ry = (ry - ry.mean()) / (ry.std() + 1e-12)
    rho = float((rx * ry).mean())
    rng = np.random.default_rng(42)
    cnt = 0
    for _ in range(20000):
        r2 = float((rx * rng.permutation(ry)).mean())
        if abs(r2) >= abs(rho):
            cnt += 1
    return rho, float((cnt + 1) / 20001)

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    dt = torch.bfloat16 if DTYPE == "bf16" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=dt)
    model.eval()
    # embedding 矩阵 = 权重层（"字→向量"字典）
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    print(f"[load] {MODEL} vocab={Emb.shape[0]} dim={Emb.shape[1]}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 概念代表字的 embedding 行向量（多字词取各字行向量均值）
    vecs = {}
    for w in CONCEPTS:
        ids = tok.encode(w, add_special_tokens=False)
        vecs[w] = Emb[ids].mean(axis=0)
    # L2 归一化后余弦距离 = 1 - dot
    norms = {w: v / (np.linalg.norm(v) + 1e-12) for w, v in vecs.items()}

    d_emb = {}
    for kind, a, b in PAIRS:
        d_emb[f"{a}|{b}"] = float(1.0 - float(np.dot(norms[a], norms[b])))

    # 三方对表
    xs_fill = [JCC4_REF[f"{a}|{b}"][0] for _, a, b in PAIRS]
    xs_jsd = [JCC4_REF[f"{a}|{b}"][1] for _, a, b in PAIRS]
    xs_emb = [d_emb[f"{a}|{b}"] for _, a, b in PAIRS]

    r_emb_fill, p_emb_fill = spearman(xs_emb, xs_fill)
    r_jsd_fill = 0.4722  # J-CC4 1.5B 冻结结果
    r_emb_jsd, p_emb_jsd = spearman(xs_emb, xs_jsd)

    diff = r_emb_fill - r_jsd_fill
    if diff > 0.1:
        verdict = "PASS（分类结构住在权重·概念距离=权重本身实证）"
    elif diff < -0.1:
        verdict = "FAIL（判负照记）"
    else:
        verdict = "转续验（差值边缘）"

    killers = {}
    for a, b in [("猫", "狗"), ("苹果", "水果"), ("苹果", "民主")]:
        k = f"{a}|{b}"
        killers[k] = {"d_emb": round(d_emb[k], 4), "d_JSD": JCC4_REF[k][1], "d_fill": JCC4_REF[k][0]}

    out = {
        "model": MODEL,
        "d_emb_all": {k: round(v, 4) for k, v in d_emb.items()},
        "corr": {
            "emb_vs_fill": {"rho": r_emb_fill, "p": p_emb_fill},
            "jsd_vs_fill_ref": {"rho": r_jsd_fill, "source": "J-CC4 1.5B"},
            "emb_vs_jsd": {"rho": r_emb_jsd, "p": p_emb_jsd},
            "diff_emb_minus_jsd_vs_fill": round(diff, 4),
        },
        "killers": killers,
        "J-CC6": verdict,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC6判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；d_emb=embedding 行向量余弦（多字词取均值）；d_fill/d_JSD 沿用 J-CC4 1.5B 冻结结果",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
