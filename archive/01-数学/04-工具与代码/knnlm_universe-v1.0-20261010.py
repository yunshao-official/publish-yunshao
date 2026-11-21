# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · kNN-LM 组装版（他们的公式 + 我们的体系）
公式（Khandelwal et al. ICLR 2020）：P(y|x) = λ·kNN(x) + (1-λ)·P_model(x)
  kNN(x) = 语境向量检索 store 中 top-k 邻居的 next-token 分布按相似度加权
我们的体系注入：
  ① store 按概念宇宙分区（多图分治=检索降维：先定位社区再社区内查——J-H2 v3）
  ② 概念影子作为 kNN 的先验项（J-CC3 等价类）
测试目标：摆脱复读机——生成连贯多样文本
纯计算零写盘版。
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "H:/AI/models--Qwen2.5-1.5B"
LAMBDA_KNN = 0.5
KNN_K = 8

STORE_WORDS = ["猫", "猫是", "小猫", "死亡", "去世", "生命", "活着", "太阳", "阳光", "光明",
    "黑暗", "夜晚", "星星", "宇宙", "世界", "地球", "大海", "水", "河流", "雨",
    "天气", "今天", "明天", "时间", "历史", "未来", "梦想", "希望", "恐惧", "勇气",
    "爱", "恨", "朋友", "家庭", "孩子", "母亲", "父亲", "医生", "病人", "医院",
    "音乐", "歌曲", "书", "阅读", "学习", "工作", "生活", "食物", "水壶", "茶",
    "人工智能", "计算机", "程序", "代码", "数学", "科学", "物理", "化学", "经济", "政治",
    "美丽", "丑陋", "快乐", "悲伤", "愤怒", "平静", "热闹", "安静", "城市", "农村",
    "山", "树", "花", "草", "鸟", "鱼", "昆虫", "动物", "人类", "机器人",
    "自由", "平等", "正义", "法律", "道德", "善良", "邪恶", "真实", "谎言", "秘密",
    "出发", "到达", "旅行", "回家", "吃饭", "睡觉", "起床", "散步", "跑步", "思考"]

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    Emb = model.get_input_embeddings().weight.detach().float().numpy()
    En = Emb / (np.linalg.norm(Emb, axis=1, keepdims=True) + 1e-12)
    N, dim = Emb.shape
    print(f"[load] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ① Store 构建：store 词的（语境向量，next-token 分布）对 ----
    store_words = STORE_WORDS
    t1 = time.time()
    store_ctx = []
    store_dist = []
    with torch.no_grad():
        for w in store_words:
            ids = tok.encode(f"请谈谈{w}。", add_special_tokens=True)
            out = model(torch.tensor([ids]))
            lg = out.logits[0, len(ids)-1].float().numpy()
            lg = np.exp(lg - lg.max()); lg /= lg.sum()          # softmax 概率
            cv = En[ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
            store_ctx.append(cv); store_dist.append(lg)
    S = np.stack(store_ctx)          # M×dim
    Ds = np.stack(store_dist)        # M×V
    M = len(store_words)
    print(f"[store] {M} entries  {time.time()-t1:.1f}s", file=sys.stderr, flush=True)

    # 概念宇宙分区（多图分治：kNN top-3 图的分量，检索先定位分量）
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for w in store_words:
        ids = tok.encode(w, add_special_tokens=False)
        for i in range(len(ids)-1):
            union(find(ids[i]), find(ids[i+1]))
    # store 条目的分量 id
    entry_root = [find(int(np.argmax(En @ S[i]))) for i in range(M)]
    root_entries = {}
    for i, r in enumerate(entry_root):
        root_entries.setdefault(r, []).append(i)
    print(f"[partition] {len(root_entries)} 分区", file=sys.stderr, flush=True)

    # ---- ② kNN-LM 生成 ----
    def generate(prompt, n_tokens=60, lam=LAMBDA_KNN):
        ids = tok.encode(prompt, add_special_tokens=True)
        out_text_tokens = []
        with torch.no_grad():
            for _ in range(n_tokens):
                cv = En[ids].mean(axis=0); cv /= (np.linalg.norm(cv)+1e-12)
                # 原模型项
                out = model(torch.tensor([ids[-256:]]))
                logits = out.logits[0, -1].float().numpy()
                p_model = np.exp(logits - logits.max()); p_model /= p_model.sum()
                # kNN 项（只在同一分区内检索——她的多图分治加速）
                r = find(int(np.argmax(En @ cv)))
                cand = root_entries.get(r, list(range(M)))
                sims = np.array([float(S[i] @ cv) for i in cand])
                top = np.argsort(-sims)[:KNN_K]
                p_knn = np.zeros(N)
                for ti in top:
                    i = cand[ti]
                    w_sim = max(float(S[i] @ cv), 0.0)
                    p_knn += w_sim * Ds[i]
                if p_knn.sum() > 0: p_knn /= p_knn.sum()
                # 插值
                p_final = lam * p_knn + (1-lam) * p_model
                nid = int(np.argmax(p_final))
                ids.append(nid)
                out_text_tokens.append(nid)
        return tok.decode(out_text_tokens)

    # 测试生成（3 prompt）
    tests = {}
    for pr in ["人工智能", "猫", "人生的意义"]:
        txt = generate(pr, 40)
        tests[pr] = txt
        print(f"[gen] {pr} → {txt[:80]}", file=sys.stderr, flush=True)

    # 速度
    t_sp = time.time()
    _ = generate("科学技术", 50)
    sp = 50 / (time.time() - t_sp)

    # 多样性：3 prompt 生成的 biglet 多样性（简单去重率）
    uniq_ratio = len(set("".join(tests.values()))) / max(sum(len(t) for t in tests.values()), 1)

    out = {
        "engine": "kNN-LM 组装版（他们的公式+我们的分区）",
        "store_size": M, "partitions": len(root_entries), "lambda": LAMBDA_KNN, "knn_k": KNN_K,
        "speed_tok_s": round(sp, 1),
        "diversity_ratio": round(uniq_ratio, 3),
        "generations": tests,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "store 仅 100 条（v0 最小验证）；复读机摆脱与否看生成文本多样性",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
