# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · L0 语言分区重建（v2）
根因修复：v1 的 kmeans 把 129280 token 压成一锅，外语簇混入导致 v1.2 输出语种沙拉。
方法（知世"多张图"世界观的落地）：
  1. 按 Unicode 区段给每个 token 打语言标签（汉字/拉丁/西里尔/阿拉伯/CJK符号/其他）
  2. 每个语言岛内部各自 kmeans（汉字 K=1200、拉丁 K=400、其他各 50-100）
  3. 产出与 v1 同名资产（embed_fp16 复用不重跑），assign/centers/member_cap 换分区版
  4. 引擎跳转天然限制在同岛内（assign 隔离自动实现）
速度：kNN 边表复用（不重算）；kmeans 只在岛内跑，比 v1 的全局 2048 更快。
"""
import sys, os, json, time
import numpy as np
from tokenizers import Tokenizer

L0 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0"
L0V2 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l0_v2"
TOKJSON = r"H:\AI\DeepSeek-V4.1-Flash-IQ2XXS\tokenizer.json"

def log(m): print(m, file=sys.stderr, flush=True)

def lang_of(text):
    """按首字符 Unicode 区段打语言标签"""
    if not text: return "SYM"
    ch = text[0]
    o = ord(ch)
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF: return "CJK"      # 汉字
    if 0x3040 <= o <= 0x30FF or 0xAC00 <= o <= 0xD7AF: return "SYM"      # 日韩归符号岛
    if 0x0400 <= o <= 0x04FF: return "CYR"                              # 西里尔
    if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F: return "ARA"     # 阿拉伯
    if 0x0900 <= o <= 0x097F or 0x0B80 <= o <= 0x0BFF or 0x0E00 <= o <= 0x0E7F: return "SYM"  # 印度系归符号
    if ch.isascii() and (ch.isalpha()): return "LAT"                     # 拉丁字母
    if ch.isdigit(): return "NUM"                                        # 数字
    if ch.isspace(): return "SYM"
    return "SYM"                                                        # 标点/符号/其他

K_PLAN = {"CJK": 1200, "LAT": 400, "SYM": 300, "CYR": 50, "ARA": 50, "NUM": 48}

def main():
    t0 = time.time()
    os.makedirs(L0V2, exist_ok=True)
    tok = Tokenizer.from_file(TOKJSON)
    V = 129280

    # ---- ① 语言标签 ----
    labels = []
    tok_texts = []
    for i in range(V):
        try:
            text = tok.decode([i])
        except:
            text = ""
        tok_texts.append(text)
        labels.append(lang_of(text))
    labels = np.array(labels)
    from collections import Counter
    ctr = Counter(labels)
    log("[lang] %s" % dict(ctr))

    # ---- ② embed 复用 ----
    Em = np.load(L0 + r"\embed_fp16.npy").astype(np.float32)
    En = Em / (np.linalg.norm(Em, axis=1, keepdims=True) + 1e-12)
    D = Em.shape[1]
    assert Em.shape[0] == V

    # ---- ③ 岛内 kmeans ----
    all_assign = np.full(V, -1, dtype=np.int32)
    all_centers = []
    island_ranges = {}
    offset = 0
    rng = np.random.default_rng(7)
    for isl, K in K_PLAN.items():
        idx = np.nonzero(labels == isl)[0]
        n = len(idx)
        if n == 0:
            island_ranges[isl] = (offset, offset)
            continue
        K = min(K, n)  # 簇数不能超过成员数
        X = En[idx]
        C = X[rng.choice(n, K, replace=False)].copy()
        for it in range(10):
            sub = rng.choice(n, min(30000, n), replace=False)
            Xs = X[sub]
            lab = np.empty(len(sub), dtype=np.int32)
            for s in range(0, len(sub), 8192):
                lab[s:s+8192] = np.argmax(Xs[s:s+8192] @ C.T, axis=1)
            cnt = np.bincount(lab, minlength=K).astype(np.float64)
            sums = np.zeros((K, D), dtype=np.float64)
            np.add.at(sums, lab, Xs)
            nz = cnt > 0
            C[nz] = (sums[nz] / cnt[nz, None]).astype(np.float32)
        Cn = C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-12)
        # 全量 assign
        for s in range(0, n, 8192):
            ii = idx[s:s+8192]
            all_assign[ii] = offset + np.argmax(En[ii] @ Cn.T, axis=1)
        all_centers.append(Cn)
        island_ranges[isl] = (offset, offset + K)
        offset += K
        log("[%s] n=%d K=%d done %.0fs" % (isl, n, K, time.time() - t0))

    K_total = offset
    Centers = np.concatenate(all_centers, axis=0)
    log("[L0v2] total clusters=%d" % K_total)

    # ---- ④ kNN 边表（岛内边——复用 v1 的全局边，过滤跨岛） ----
    E = np.load(L0 + r"\edges.npy")
    mask = labels[E[:, 0]] == labels[E[:, 1]]
    E2 = E[mask]
    log("[edges] global=%d same-island=%d (dropped %d cross-island)" % (len(E), len(E2), len(E) - len(E2)))

    # ---- ⑤ member_cap ----
    sizes = np.bincount(all_assign[all_assign >= 0], minlength=K_total)
    member_cap = {}
    CAP = 300
    for c in range(K_total):
        m = np.nonzero(all_assign == c)[0]
        if len(m) == 0:
            member_cap[c] = np.zeros(0, dtype=np.int32)
            continue
        if len(m) > CAP:
            s = En[m] @ Centers[c]
            m = m[np.argsort(-s)[:CAP]]
        member_cap[c] = m.astype(np.int32)
    np.savez_compressed(L0V2 + r"\member_cap.npz", **{str(k): v for k, v in member_cap.items()})

    # ---- 保存 ----
    np.save(L0V2 + r"\assign.npy", all_assign)
    np.save(L0V2 + r"\centers.npy", Centers.astype(np.float16))
    np.save(L0V2 + r"\edges.npy", E2.astype(np.int32))
    np.save(L0V2 + r"\labels.npy", labels)
    # embed 直接软引用（不复制 1GB）
    if not os.path.exists(L0V2 + r"\embed_fp16.npy"):
        os.symlink(L0 + r"\embed_fp16.npy", L0V2 + r"\embed_fp16.npy")
    np.save(L0V2 + r"\cluster_sizes.npy", sizes)

    meta = {
        "engine": "L0 词面宇宙 v2（语言分区版）",
        "principle": "知世「你为什么非要把它看成一张图，而不是多张图呢」——按语言岛分治",
        "islands": {isl: {"n_tokens": int((labels == isl).sum()), "K": K_PLAN[isl], "range": island_ranges[isl]} for isl in K_PLAN},
        "total_clusters": K_total,
        "edges_global": int(len(E)),
        "edges_same_island": int(len(E2)),
        "edges_cross_island_dropped": int(len(E) - len(E2)),
        "root_cause_fixed": "v1 全局 kmeans 混入外语簇导致 v1.2 语种沙拉输出；v2 岛内分簇+跨岛边过滤",
        "elapsed_s": round(time.time() - t0, 1),
    }
    with open(L0V2 + r"\meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    log("[done] %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
