# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · L2 转移宇宙 + 关联宇宙（V4-Flash 词表自洽线）
输入：语料 = zcode DeepSeek 对话 blob（清洗后长回答段）+ L0 assign（簇共现）
产出（results/v4f_transfer/）：
  bigram_top5.npy   (129280,5) int32 —— 每 token 的 top-5 后继（转移脉冲）
  bigram_top5_sc.npy (129280,5) fp16 —— 归一化打分（log 归一）
  cooc_cluster.npz  概念簇级共现 top 表（关联脉冲：什么和什么常一起出现）
  meta.json
纪律（历史判负教训继承）：语料清洗三件套（只留长回答段/去 UI 题目碎片/去英文块）；
  转移宇宙角色定谳 = 知识候选源 + 语法先验，非生成器（bigram 天花板判负照记在案）。
"""
import sys, os, json, time, re
import numpy as np

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
OUT = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer"
CORPUS = r"C:\Users\Administrator\.zcode\workspace\default\_deepseek_all_blob.txt"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"
V = 129280
K_CLU = 2048
TOP5 = 5

def log(m): print(m, file=sys.stderr, flush=True)

# 清洗规则（判负教训固化）：正/负特征
NEG_PATS = [
    "用户可能需要", "翻译成英文", "____", "-10分", "Butler", "http://", "https://",
    "请输入", "点击", "关注", "转载", "版权声明", "扫码",
]
EN_LINE = re.compile(r"[A-Za-z]{3,}.*[A-Za-z]{3,}.*[A-Za-z]{3,}")
LIST_ITEM = re.compile(r"^\s*([A-D][\.、)]|\d+[\.、)]|①|②|③|④)")

def clean_paragraph(p):
    p = p.strip()
    if len(p) < 80:                       # 只留长段（回答主体）
        return None
    if any(x in p for x in NEG_PATS):     # UI/模板碎片
        return None
    ascii_ratio = sum(1 for ch in p if ord(ch) < 128) / max(len(p), 1)
    if ascii_ratio > 0.6:                 # 英文块
        return None
    return p

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKJSON)
    V_actual = tok.get_vocab_size()
    log("tokenizer vocab=%d" % V_actual)

    assign = np.load(L0 + r"\assign.npy")
    assert len(assign) == V

    # ---- ① 语料清洗 + 分词 ----
    big = {}
    cooc = np.zeros((K_CLU, K_CLU), dtype=np.uint32)
    n_para = n_tok = 0
    buf = []
    io_open = open(CORPUS, "r", encoding="utf-8", errors="replace")

    def flush(buf):
        para = clean_paragraph("".join(buf))
        nonlocal_ok = para is not None
        if not para:
            return 0, 0
        ids = [i for i in tok.encode(para, add_special_tokens=False).ids if i < V]
        if len(ids) < 2:
            return 0, 0
        for a, b in zip(ids, ids[1:]):
            big[(a, b)] = big.get((a, b), 0) + 1
            cooc[assign[a], assign[b]] += 1
        return 1, len(ids)

    np_para = np_tok = 0
    for line in io_open:
        if line.strip() == "" or line.startswith("{") or line.startswith("=" * 10):
            if buf:
                a, b = flush(buf)
                np_para += a; np_tok += b
                buf = []
            continue
        buf.append(line)
        if len("".join(buf)) > 4000:
            a, b = flush(buf)
            np_para += a; np_tok += b
            buf = []
    if buf:
        a, b = flush(buf)
        np_para += a; np_tok += b
    io_open.close()
    n_para, n_tok = np_para, np_tok
    log("[corpus] 段=%d token=%d bigram 类=%d  %.0fs" % (n_para, n_tok, len(big), time.time() - t0))

    # ---- ② top-5 后继表 ----
    best = {}
    for (a, b), c in big.items():
        if a not in best:
            best[a] = []
        best[a].append((b, c))
    nxt = np.full((V, TOP5), -1, dtype=np.int32)
    sc = np.zeros((V, TOP5), dtype=np.float16)
    for a, lst in best.items():
        if len(lst) < 2:                    # 频次<2 的不进表（噪声控制）
            continue
        lst.sort(key=lambda x: -x[1])
        for k, (b, c) in enumerate(lst[:TOP5]):
            nxt[a, k] = b
            sc[a, k] = np.float16(np.log1p(c))
    n_defined = int((nxt[:, 0] >= 0).sum())
    log("[transfer] 有后继的 token=%d (%.1f%%)" % (n_defined, 100.0 * n_defined / V))
    np.save(OUT + r"\bigram_top5.npy", nxt)
    np.save(OUT + r"\bigram_top5_sc.npy", sc)

    # ---- ③ 关联宇宙：簇共现 top-5（非对称→对称化取强边）----
    cooc_t = cooc + cooc.T
    iou = np.zeros((K_CLU, K_CLU), dtype=np.float32)
    # 用点互信息近似权重太大——直接取共现计数 top：按簇行 top5（对角线置 0）
    np.fill_diagonal(cooc_t, 0)
    rows = np.argsort(-cooc_t.astype(np.int64), axis=1)[:, :5]
    counts = np.take_along_axis(cooc_t, rows, axis=1)
    mask = counts > 0
    idx_i = np.repeat(np.arange(K_CLU), 5)
    idx_j = rows.reshape(-1)
    cnt = counts.reshape(-1)
    keep = mask.reshape(-1)
    np.savez_compressed(OUT + r"\cooc_cluster.npz",
                        i=idx_i[keep].astype(np.int32), j=idx_j[keep].astype(np.int32),
                        c=cnt[keep].astype(np.uint32))
    log("[assoc] 簇关联边=%d  %.0fs" % (int(keep.sum()), time.time() - t0))

    meta = {
        "engine": "概念宇宙 LLM · L2 转移宇宙 + 关联宇宙",
        "corpus": "zcode DeepSeek 对话 blob（清洗：>80字段落/去UI模板/去英文块）",
        "cleaned_paragraphs": n_para, "cleaned_tokens": n_tok,
        "bigram_types": len(big),
        "tokens_with_successor": n_defined,
        "cooc_edges": int(keep.sum()),
        "elapsed_s": round(time.time() - t0, 1),
        "honest_note": "历史判负继承：bigram 转移宇宙给不了句子级生成（多样性 0.70 天花板、判负在案）——本表角色=语法先验+知识候选源，生成主力在引擎侧；语料=她的对话记录（助手腔/题目碎片风险，清洗三件套已应用但残余风险照记）",
    }
    with open(OUT + r"\meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
