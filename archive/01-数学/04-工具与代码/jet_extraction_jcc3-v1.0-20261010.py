# -*- coding: utf-8 -*-
"""
J-CC3 概念聚类检验 + 填充观察（预注册：J-CC3判据冻结书-预注册-20261010.md）
理论来源：知世口授（字≠概念多对多；概念空间；填充性距离）
实验 A（判据）：同概念多字表达的影子（输出分布）聚类——概念内 JSD < 概念间 JSD？
实验 B（探索）：概念对中间填充形态观察——归纳"介于"定义
纯计算零写盘版：stdout JSON 输出，落盘由重定向完成。
"""
import os, sys, json, time
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1] if len(sys.argv) > 1 else "H:/AI/models--Qwen2.5-1.5B"
TOPK = 512

# 50 概念 × 4 同义字表达 + 8 干扰（v1.2 扩样版）
CONCEPTS = {
    "猫": ["猫", "猫咪", "小猫", "猫科"],
    "死亡": ["死亡", "去世", "逝世", "离世"],
    "愤怒": ["愤怒", "生气", "恼火", "暴怒"],
    "快乐": ["快乐", "高兴", "开心", "愉悦"],
    "勇敢": ["勇敢", "英勇", "无畏", "胆大"],
    "聪明": ["聪明", "机灵", "聪慧", "伶俐"],
    "海洋": ["大海", "海洋", "汪洋", "深蓝"],
    "花": ["花朵", "鲜花", "花卉", "花蕾"],
    "朋友": ["朋友", "好友", "挚友", "友人"],
    "时间": ["时间", "光阴", "岁月", "时光"],
    "家": ["家庭", "家", "家园", "港湾"],
    "自由": ["自由", "自在", "无拘", "随心"],
    "太阳": ["太阳", "烈日", "骄阳", "日头"],
    "山": ["山", "山峰", "山峦", "峻岭"],
    "雨": ["雨", "降雨", "雨水", "甘霖"],
    "书": ["书", "书籍", "书本", "典籍"],
    "路": ["路", "道路", "途径", "路径"],
    "梦": ["梦", "梦境", "幻梦", "梦乡"],
    "爱": ["爱", "爱恋", "深情", "挚爱"],
    "恨": ["恨", "憎恨", "仇恨", "怨恨"],
    "勇气": ["勇气", "胆量", "魄力", "气概"],
    "财富": ["财富", "钱财", "财产", "家产"],
    "权力": ["权力", "权势", "职权", "权柄"],
    "教育": ["教育", "教诲", "栽培", "教养"],
    "医生": ["医生", "大夫", "医师", "郎中"],
    "音乐": ["音乐", "乐曲", "乐章", "旋律"],
    "战争": ["战争", "战事", "烽火", "战火"],
    "和平": ["和平", "安宁", "太平", "祥和"],
    "孤独": ["孤独", "寂寞", "孤单", "孤寂"],
    "希望": ["希望", "期盼", "憧憬", "盼望"],
    "悲伤": ["悲伤", "难过", "哀伤", "忧伤"],
    "速度": ["速度", "疾速", "飞快", "迅速"],
    "寒冷": ["寒冷", "冰凉", "凛冽", "冰冷"],
    "炎热": ["炎热", "酷热", "滚烫", "灼热"],
    "红色": ["红", "赤红", "绯红", "艳红"],
    "森林": ["森林", "树林", "林海", "丛林"],
    "城市": ["城市", "都市", "城池", "都会"],
    "国家": ["国家", "国度", "邦国", "社稷"],
    "皇帝": ["皇帝", "帝王", "君主", "天子"],
    "战士": ["战士", "勇士", "士兵", "武者"],
    "鱼": ["鱼", "鱼类", "游鱼", "鲜鱼"],
    "鸟": ["鸟", "飞鸟", "禽鸟", "雀鸟"],
    "树": ["树", "大树", "树木", "林木"],
    "月亮": ["月亮", "明月", "月轮", "皓月"],
    "星星": ["星星", "星辰", "繁星", "星宿"],
    "河流": ["河流", "江河", "河川", "溪流"],
    "火焰": ["火焰", "烈焰", "火苗", "火舌"],
    "冰": ["冰", "寒冰", "冰块", "坚冰"],
    "风": ["风", "微风", "狂风", "清风"],
    "声音": ["声音", "声响", "音响", "音色"],
}
FILLERS = ["石头", "程序", "袜子", "发票", "牙刷", "地毯", "喇叭", "图钉"]

NEUTRAL_TPL = "请谈谈{w}。"

FAR_PAIRS = [("猫", "汽车"), ("苹果", "民主"), ("茶", "相对论")]
NEAR_PAIRS = [("猫", "小猫"), ("苹果", "水果"), ("北京", "上海")]

def next_token_probs(model, tok, sent):
    ids = tok.encode(sent, add_special_tokens=True)
    with torch.no_grad():
        out = model(torch.tensor([ids]))
    return torch.softmax(out.logits[0, -1].float(), dim=-1).numpy()

def shadow(model, tok, w, tpl=NEUTRAL_TPL):
    return next_token_probs(model, tok, tpl.replace("{w}", w))

def jsd(P):
    """P: n×V → n×n 对称 JSD 平方根距离"""
    n = P.shape[0]
    Q = P / np.maximum(P.sum(axis=1, keepdims=True), 1e-12)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            m = 0.5 * (Q[i] + Q[j])
            def kl(p):
                mask = p > 1e-12
                return float(np.sum(p[mask] * np.log2(p[mask] / m[mask])))
            d = 0.5 * kl(Q[i]) + 0.5 * kl(Q[j])
            D[i, j] = D[j, i] = float(np.sqrt(max(d, 0.0)))
    return D

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
    model.eval()
    print(f"[load] {MODEL}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- 实验 A：全部词的影子 ----
    words = []
    labels_concept = []
    for c, ws in CONCEPTS.items():
        for w in ws:
            words.append(w)
            labels_concept.append(c)
    for w in FILLERS:
        words.append(w)
        labels_concept.append("FILLER_" + w)

    P_list = []
    for w in words:
        P_list.append(shadow(model, tok, w))
    P = np.stack(P_list)
    union = P.sum(axis=0).argsort()[::-1][:TOPK]
    Ps = P[:, union]
    D = jsd(Ps)
    n = len(words)

    # 概念内 vs 概念间（干扰词排除在主统计外，单独记录）
    idx_real = [i for i, c in enumerate(labels_concept) if not c.startswith("FILLER_")]
    intra, inter = [], []
    for a in range(n):
        for b in range(a + 1, n):
            if a in idx_real and b in idx_real:
                if labels_concept[a] == labels_concept[b]:
                    intra.append(D[a, b])
                else:
                    inter.append(D[a, b])

    # 置换检验：打乱（排除干扰词的）概念标签
    rng = np.random.default_rng(42)
    obs_diff = float(np.mean(inter) - np.mean(intra))   # 预言方向 >0
    lab = [c for c in labels_concept if not c.startswith("FILLER_")]
    cnt = 0
    n_perm = 20000
    for _ in range(n_perm):
        shuffled = rng.permutation(lab)
        ia, ie = [], []
        k = len(shuffled)
        for a in range(k):
            for b in range(a + 1, k):
                if shuffled[a] == shuffled[b]:
                    ia.append(D[idx_real[a], idx_real[b]])
                else:
                    ie.append(D[idx_real[a], idx_real[b]])
        if float(np.mean(ie) - np.mean(ia)) >= obs_diff:
            cnt += 1
    p_val = float((cnt + 1) / (n_perm + 1))

    verdict_A = ("PASS（影子认概念·概念层实证）"
                 if obs_diff > 0 and p_val < 0.05 else
                 "FAIL（判负照记）")

    # 每词明细：概念内平均 JSD（到自己概念同伴）vs 到所有跨概念均值
    detail = {}
    for i, w in enumerate(words):
        same = [D[i, j] for j in idx_real if j != i and labels_concept[j] == labels_concept[i]]
        diff = [D[i, j] for j in idx_real if labels_concept[j] != labels_concept[i]]
        detail[w] = {
            "concept": labels_concept[i],
            "intra_mean": float(np.mean(same)) if same else None,
            "inter_mean": float(np.mean(diff)) if diff else None,
        }

    # ---- 实验 B：填充观察（探索性）----
    fill_obs = {}
    for kind, pairs in (("far", FAR_PAIRS), ("near", NEAR_PAIRS)):
        for (A, B) in pairs:
            PA = shadow(model, tok, A, "我们聊聊{w}。")
            PB = shadow(model, tok, B, "我们聊聊{w}。")
            mix = 0.5 * PA + 0.5 * PB
            top_mix = [tok.decode([i]) for i in mix.argsort()[::-1][:10]]
            # 从属链读数
            ids = tok.encode(f"{A}是一种", add_special_tokens=True)
            with torch.no_grad():
                out = model(torch.tensor([ids]))
            lg = out.logits[0, -1].float().numpy()
            top_hypo = [tok.decode([i]) for i in lg.argsort()[::-1][:5]]
            # 枚举 prompt
            ids2 = tok.encode(f"与{A}和{B}都有关的事物包括", add_special_tokens=True)
            with torch.no_grad():
                out2 = model(torch.tensor([ids2]))
            lg2 = out2.logits[0, -1].float().numpy()
            top_enum = [tok.decode([i]) for i in lg2.argsort()[::-1][:10]]
            fill_obs[f"{kind}:{A}-{B}"] = {
                "mix_top10": top_mix, "hypo_top5_after_isA": top_hypo, "enum_top10": top_enum,
            }
            print(f"[fill] {A}-{B}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    out = {
        "model": MODEL, "topk": TOPK,
        "words": words, "labels_concept": labels_concept,
        "expA": {
            "intra_mean_JSD": float(np.mean(intra)), "inter_mean_JSD": float(np.mean(inter)),
            "obs_diff_inter_minus_intra": obs_diff, "p_perm": p_val,
            "verdict": verdict_A, "detail": detail,
        },
        "expB_fill_observation": fill_obs,
        "elapsed_s": round(time.time() - t0, 1),
        "frozen_doc": "J-CC3判据冻结书-预注册-20261010.md（先于实算落盘）",
        "honest_note": "纯计算零写盘；实验B为探索性观察（归纳'介于'定义），无 PASS/FAIL",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
