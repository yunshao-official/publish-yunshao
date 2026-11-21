# -*- coding: utf-8 -*-
# d=9 带深域外验证 + E_0 计数律完整定理化 + 单位词轨道谱 + 候补④特征函数反演层（R41）
# 判据书：代数册·d9带验证与E0计数律定理化预注册判据书-v1.0-20260925.md（冻结 2026-09-25T09:03:39）
# 用法: python d9_e0_band-v1.0-20260925.py all | part1 | part2 | ci | bands | band CS CE | merge
# part1: D-A0 锚 / D-A1 64档器 / D-A2 继承22档 / D-A3 段max=32 三态 / D-A5 分解律+C2+归因
# bands: D-A4 全部 78 段分段快扫（单进程共享 dp_full·逐段 JSON 落盘）
# band : D-A4 单段快扫 c=CS..CE
# merge: D-A4 全带统计（max 对表 32 三态+两抬升链五次验证+实质素数律+词数极值链第六点+相邻结构+直方图+分带统计+抽样3档枚举增信）
# part2: D-E0 计数律 E-1 / 显式闭式 E-2 / μ 分层 E-3 / 单位词轨道谱 / 递推层（L=1..12 逐层）
# ci   : D-CI 候补④ 六态矩阵特征函数层 + FFT 格点精确反演 + 一般 t 读法
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d9_e0_band-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T09:03:39"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R40P1 = "H:/理论存档/01-数学/02-实验与数据/results/d8_band_x0-part1-v1.0-20260925.json"
R40MG = "H:/理论存档/01-数学/02-实验与数据/results/d8_band_x0-merge-v1.0-20260925.json"
SEG64 = list(range(-19683, -19747, -1))        # 本轮段 64 档
INH22 = [c for c in SEG64 if c % 3 == 0]       # 继承 22 档（3|c 全集）
SRCS = sorted(set(c // 3 for c in INH22), reverse=True)   # 源档 -6561..-6582（R40 在档段）
PURE_CAND = [c for c in INH22 if (c // 3) % 2 == 1]       # 纯继承候选 11 档 -3(2j+6561) 型
# 快扫 78 段：段长 505·末段 417（i=0..76: cs=-19747-505i, ce=cs-504；i=77: cs=-58632, ce=-59048）
BAND_CHUNKS = [(-19747 - 505 * i, -19747 - 505 * i - 504) for i in range(77)] + [(-58632, -59048)]
PRED_MAX = 32                                  # 3*9+5

# ---------- 全域 DP（值索引口径·R34-R40 修正口径复用） ----------
def dp_full(L=12):
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for lay in range(L):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
    perm = np.argsort(ys, kind="stable")
    return ys[perm], Ds[perm], ts[perm], ms[perm]

def dp_layers(Lmax=12):
    """逐层 DP：返回 [(L, Ds_L, ms_L)]（值索引·每层独立落位）"""
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    layers = []
    for lay in range(1, Lmax + 1):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
        perm = np.argsort(ys, kind="stable")
        layers.append((lay, Ds[perm], ms[perm]))
    return layers

def rev_map():
    y = np.arange(N4, dtype=np.int64); rv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rv = rv * 4 + (y & 3); y >>= 2
    return rv

def sigma_map():
    y = np.arange(N4, dtype=np.int64); sv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        sv = sv * 4 + (3 - (y & 3)); y >>= 2
    return sv

def z03_masks(nmax=12):
    """masks[n] = bool 数组（长 4^n）：n 位词逐位∈{0,3}；masks[0]=[True]（空词值 0）"""
    masks = [np.ones(1, dtype=bool)]
    for n in range(1, nmax + 1):
        v = np.arange(4 ** n, dtype=np.int64)
        m = masks[n - 1][v >> 2] & np.isin(v & 3, (0, 3))
        masks.append(m)
    return masks

def step(state, rho):
    d, sg, mu = state
    return (3 * d + sg * G[rho][mu], sg * FAC[rho], (mu + rho) % 3)

def rev_closure(c):
    R = set((c, sg, m) for sg in (1, -1) for m in range(3))
    frontier = list(R)
    while frontier:
        cur = frontier.pop(); d = cur[0]
        if d == 0:
            continue
        for rho in range(4):
            for mu in range(3):
                for sg in (1, -1):
                    gamma = sg * G[rho][mu]
                    if (d - gamma) % 3 == 0:
                        p = ((d - gamma) // 3, sg, mu)
                        if p not in R:
                            R.add(p); frontier.append(p)
    return R

def build_dfa(c):
    START = (0, 1, 0)
    R = rev_closure(c); R.add(START)
    states = sorted(R); idx = {s: i for i, s in enumerate(states)}
    trans = np.full((len(states), 4), -1, dtype=np.int64)
    for i, s in enumerate(states):
        for rho in range(4):
            trans[i, rho] = idx.get(step(s, rho), -1)
    reach = {idx[START]}; stack = [idx[START]]
    while stack:
        u = stack.pop()
        for rho in range(4):
            v = int(trans[u, rho])
            if v >= 0 and v not in reach:
                reach.add(v); stack.append(v)
    keep = sorted(reach); kidx = {states[i]: i2 for i2, i in enumerate(keep)}
    tr2 = np.full((len(keep), 4), -1, dtype=np.int64)
    for i2, i in enumerate(keep):
        for rho in range(4):
            v = int(trans[i, rho])
            tr2[i2, rho] = kidx[states[v]] if v >= 0 else -1
    q0 = kidx[START]
    accept = [i2 for i2, i in enumerate(keep) if states[i][0] == c]
    return [states[i] for i in keep], tr2, q0, accept

def moore_min_vec(tr, accept_set):
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    lab = np.zeros(N, dtype=np.int64)
    for a in accept_set: lab[a] = 1
    while True:
        key = np.concatenate([lab[:, None], lab[TR]], axis=1)
        uni, newlab = np.unique(key, axis=0, return_inverse=True)
        if int(uni.shape[0]) == int(np.unique(lab).size):
            return int(uni.shape[0])
        lab = newlab.astype(np.int64)

def dfa_word_count(tr, q0, accept, L=12):
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    cnt = np.zeros(N, dtype=np.int64); cnt[q0] = 1
    for _ in range(L):
        new = np.zeros(N, dtype=np.int64)
        for s in range(N):
            c0 = int(cnt[s])
            if c0:
                for r in range(4):
                    new[int(TR[s, r])] += c0
        cnt = new
    return int(sum(int(cnt[a]) for a in accept))

def active_dead(keep_states, tr2, accept):
    n = len(keep_states)
    rev_adj = [[] for _ in range(n)]
    for u in range(n):
        for rho in range(4):
            v = int(tr2[u, rho])
            if v >= 0:
                rev_adj[v].append(u)
    act = set(int(a) for a in accept); st = list(act)
    while st:
        v = st.pop()
        for u in rev_adj[v]:
            if u not in act:
                act.add(u); st.append(u)
    return len(keep_states) - len(act)

def mint_layers(c):
    n = 0; L = 1
    while 3 ** L <= abs(c):
        if c % (3 ** L) == 0 and abs(c) // (3 ** L) >= 2:
            n += 1
        L += 1
    return n

def law_four(c, R_from=None):
    keep_states, tr, q0, acc = build_dfa(c)
    reach = len(keep_states); accn = len(acc)
    m_acc = accn - 1
    m_dead = active_dead(keep_states, tr, acc)
    Rm = int(moore_min_vec(tr, acc)) if R_from is None else int(R_from)
    m_int = reach + 1 - m_acc - m_dead - Rm
    return {"reach": reach, "acc": accn, "M_acc": m_acc, "M_dead": m_dead,
            "M_int": int(m_int), "R": int(Rm), "C2": mint_layers(c),
            "law_ok": bool(m_int >= 0 and Rm == reach + 1 - m_acc - m_dead - m_int)}

def inherit_check(cs, Ds, ms):
    dsub = Ds[:N11]; mu0 = (ms[:N11] == 0)
    recs = {}; bad = 0; pure_list = []
    for c in cs:
        s = c // 3
        zs = np.nonzero(dsub == s)[0]
        xsrc = zs[mu0[zs]]
        inherit = 4 * zs
        Xw = np.concatenate([4 * xsrc + 1, 4 * xsrc + 3])
        pred = np.sort(np.concatenate([inherit, Xw]))
        Ec = np.sort(np.nonzero(Ds == c)[0])
        eq = (pred.shape == Ec.shape) and bool((pred == Ec).all())
        tail_ok = bool(((Xw % 4 == 1).sum() + (Xw % 4 == 3).sum()) == len(Xw))
        src_ok = True
        if len(Xw):
            zback = Xw >> 2
            src_ok = bool((dsub[zback] == s).all() and mu0[zback].all())
        contain = True
        if zs.size:
            contain = bool((Ds[4 * zs] == c).all())
        pure = (len(Xw) == 0)
        if pure: pure_list.append(c)
        ok = bool(eq and tail_ok and src_ok and contain)
        if not ok: bad += 1
        recs[str(c)] = {"src": int(s), "n_Ec": int(len(Ec)), "n_4E": int(len(inherit)),
                        "n_X": int(len(Xw)), "pure": pure, "eq": eq, "tail_ok": tail_ok,
                        "src_ok": src_ok, "contain": contain, "ok": ok}
    return recs, bad, pure_list

# ---------- part1（㊹ d=9 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    # D-A0 回归锚（R40 在档只读）
    r40p1 = json.load(open(R40P1, encoding="utf-8"))
    r40mg = json.load(open(R40MG, encoding="utf-8"))
    anchor_bad = 0
    for c in (-6561, -6562, -6563, -6564):
        arch = r40p1["DB1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DA0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r40mg["fullband"]
    if not (fb["n"] == 13122 and fb["max"] == 29 and fb["at"] == -13123 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DA0 merge fullband mismatch %s" % json.dumps(fb))
    wm = r40mg["wordmax"]
    if not (wm["v"] == 7168 and wm["at"] == -13122):
        anchor_bad += 1; log.append("DA0 wordmax mismatch %s" % json.dumps(wm))
    log.append("DA0 anchor_bad=%d (fullband=%s wordmax=%s)" % (anchor_bad, json.dumps(fb), json.dumps(wm)))
    # D-A1 64 档器产出
    import time
    t0 = time.time()
    dm1 = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        dm1[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R_moore": Rm}
    seg_dt = time.time() - t0
    mutex = len(set(dm1[k]["c"] for k in dm1)) == 64
    seg_R = [dm1[str(c)]["R_moore"] for c in SEG64]
    seg_max = max(seg_R); seg_max_at = SEG64[seg_R.index(seg_max)]
    seg_reach = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        seg_reach[str(c)] = len(ks)
    import random
    rng = random.Random(20260925)
    samp = [seg_max_at] + rng.sample([c for c in SEG64 if c != seg_max_at], 2)
    enum3 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum3[str(c)] = {"dfa_paths": wc, "n_words": dm1[str(c)]["n_words"],
                         "eq": bool(wc == dm1[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum3.values())
    log.append("DA1 gear64 R=%s mutex=%s seg_max=%d@%d seg_dt=%.1fs enum3 bad=%d %s" %
               (str(seg_R), str(mutex), seg_max, seg_max_at, seg_dt, enum_bad, json.dumps(enum3)))
    # D-A2 继承律 22 档（源档重算+R40 在档双读）
    src_bad = 0
    src_re = {}
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r40p1["DB1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DA2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_re[str(c)] = {"recompute": Rm, "archive": arch}
    recs, inh_bad, pure_list = inherit_check(INH22, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dm1[str(c)]["R_moore"]
        Rs = src_re[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    pure_match = sorted(pure_list) == sorted(PURE_CAND)
    log.append("DA2 inherit22 bad=%d pure=%s pure_match_cand=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), str(pure_match), json.dumps(synth), str(synth_ok)))
    # D-A3 段 max=32 三态
    tri = "hit" if seg_max == PRED_MAX else ("fail" if seg_max > PRED_MAX else "unsupported")
    log.append("DA3 seg_max=%d@%d vs %d -> %s" % (seg_max, seg_max_at, PRED_MAX, tri))
    # D-A5 分解律+M_int C2+极值归因
    dm5 = {}; law_bad = 0; c2_bad = 0
    for c in SEG64:
        lw = law_four(c, R_from=dm1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dm5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"], "pure_inh": c in pure_list}
    reach_max_seg = max(seg_reach.values())
    seg_reach_at = [c for c in SEG64 if seg_reach[str(c)] == reach_max_seg]
    top = sorted(SEG64, key=lambda c: (-dm1[str(c)]["R_moore"], c))[:5]
    log.append("DA5 law_bad=%d c2_bad=%d reach_max_seg=%d@%s top5=%s" %
               (law_bad, c2_bad, reach_max_seg, str(seg_reach_at),
                json.dumps({str(c): dm5[str(c)] for c in top})))
    res = {"meta": {"script": "d9_e0_band-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DA0": {"anchor_bad": anchor_bad, "fullband": fb, "wordmax": wm},
           "DA1": {"gear64": dm1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad,
                    "seg_reach": seg_reach, "seg_dt_sec": round(seg_dt, 1)},
           "DA2": {"src_R": src_re, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "pure_cand": PURE_CAND, "pure_match": pure_match,
                    "synth": synth, "synth_ok": synth_ok},
           "DA3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DA5": {"records": dm5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "reach_max_seg": int(reach_max_seg), "reach_max_at": seg_reach_at,
                    "top5": {str(c): dm5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- band 快扫（共享 dp 口径·逐段 JSON 落盘） ----------
def _scan_chunk(cstart, cend, hist_all):
    log = []
    gear = {}
    for c in range(cstart, cend - 1, -1):
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        gear[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R": Rm, "reach": len(ks)}
    Rs = [gear[str(c)]["R"] for c in range(cstart, cend - 1, -1)]
    mx = max(Rs); mx_at = range(cstart, cend - 1, -1)[Rs.index(mx)]
    log.append("BAND [%d..%d] n=%d max=%d@%d" % (cstart, cend, len(Rs), mx, mx_at))
    res = {"meta": {"script": "d9_e0_band-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

def run_band(cstart, cend):
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts, ms
    aD = -Ds
    del Ds
    hist_all = np.bincount(aD)
    _scan_chunk(cstart, cend, hist_all)

def run_bands():
    import time
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts, ms
    aD = -Ds
    del Ds
    hist_all = np.bincount(aD)
    del aD
    t0 = time.time()
    for i, (cs, ce) in enumerate(BAND_CHUNKS):
        _scan_chunk(cs, ce, hist_all)
        print("CHUNK %d/%d done elapsed=%.1fs" % (i + 1, len(BAND_CHUNKS), time.time() - t0))

# ---------- merge（D-A4 全带统计+两抬升链五次验证+增信） ----------
def run_merge():
    log = []
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DA1"]["gear64"])
    for k in list(gear):
        gear[k] = {"c": gear[k]["c"], "n_words": gear[k]["n_words"],
                   "R": gear[k]["R_moore"], "reach": p1["DA1"]["seg_reach"][k]}
    for cs, ce in BAND_CHUNKS:
        bd = json.load(open(OUT % ("band%d" % abs(cs)), encoding="utf-8"))
        for k, v in bd["gear"].items():
            gear[k] = {"c": v["c"], "n_words": v["n_words"], "R": v["R"], "reach": v["reach"]}
    allc = sorted((int(k) for k in gear), reverse=True)
    Rs = [gear[str(c)]["R"] for c in allc]
    mx = max(Rs); mx_at = allc[Rs.index(mx)]
    tri = "hit" if mx == PRED_MAX else ("fail" if mx > PRED_MAX else "unsupported")
    Rdist = {}
    for r in Rs: Rdist[str(r)] = Rdist.get(str(r), 0) + 1
    nw = [(gear[str(c)]["n_words"], c) for c in allc]
    wmax, wmax_at = max(nw)
    # 两抬升链五次验证+max 档归因
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R"])
    lw["div3"] = bool((-mx_at) % 3 == 0)
    reach_all = [(gear[str(c)]["reach"], c) for c in allc]
    reach_max, reach_max_at = max(reach_all)
    lw["reach_is_band_max"] = bool(gear[str(mx_at)]["reach"] == reach_max)
    lw["reach_band_max_at"] = int(reach_max_at)
    # 相邻结构第四度候选：R 极值档与词数极值档
    adjacent = bool(abs(mx_at - wmax_at) == 1)
    # 继承压制
    inh_R = [gear[str(c)]["R"] for c in allc if c % 3 == 0]
    non_R = [gear[str(c)]["R"] for c in allc if c % 3 != 0]
    stat = {"n": len(allc), "all": {"min": min(Rs), "max": mx, "mean": round(sum(Rs) / len(Rs), 3)},
            "inherit": {"n": len(inh_R), "max": max(inh_R), "mean": round(sum(inh_R) / len(inh_R), 3)},
            "noninherit": {"n": len(non_R), "max": max(non_R), "mean": round(sum(non_R) / len(non_R), 3)}}
    # 抽样枚举增信
    import random
    rng = random.Random(20260925)
    samp = [mx_at] + rng.sample([c for c in allc if c != mx_at], 3)
    enum4 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum4[str(c)] = {"dfa_paths": wc, "n_words": gear[str(c)]["n_words"],
                         "eq": bool(wc == gear[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum4.values())
    # 词数极值链第六点：档位链 −2·3^9=−39366·值链 2^6·96=6144
    chain = {"at_pred": -2 * (3 ** 9), "at_actual": int(wmax_at),
             "at_hit": bool(wmax_at == -2 * 3 ** 9),
             "v_pred": 2 ** 6 * 96, "v_actual": int(wmax), "v_hit": bool(wmax == 2 ** 6 * 96),
             "record_8128": bool(wmax > 8128)}
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE wordmax=%d@%d chain6=%s (record 8128@-162) adjacent=%s (Rmax@%d)" %
               (wmax, wmax_at, json.dumps(chain), str(adjacent), int(mx_at)))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d9 %s" % json.dumps(stat))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    res = {"meta": {"script": "d9_e0_band-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "wordmax": {"v": int(wmax), "at": int(wmax_at), "chain6": chain, "adjacent": adjacent},
           "Rdist": Rdist, "band_d9_stat": stat, "max_law": lw,
           "enum4": enum4, "enum_bad": enum_bad, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㊺ E_0 计数律+闭式+μ 分层+单位词轨道谱） ----------
def run_part2():
    log = []
    layers = dp_layers(12)
    masks = z03_masks(12)
    z03vals = [np.nonzero(m)[0].astype(np.int64) for m in masks]   # z03vals[n]：n 位 {0,3}* 词值
    # D-E0 ①②③⑤：L=1..12 逐层
    e1_bad = 0; e2_bad = 0; e3_bad = 0; rec_bad = 0
    per_L = {}
    prev_n = None
    for (L, Ds, ms) in layers:
        zvals = np.nonzero(Ds == 0)[0]
        n_L = int(len(zvals))
        ok1 = bool(n_L == 2 ** (L + 1) - 1)
        if not ok1: e1_bad += 1
        # E-2 右端构造：{0,3}*^L ⊔ ⊔_{k=0}^{L−1}{z·1·0^k: z∈{0,3}*^{L−1−k}}
        parts = [z03vals[L]]
        for k in range(0, L):
            pre = z03vals[L - 1 - k]
            parts.append((pre * 4 + 1) << (2 * k))
        pred = np.unique(np.concatenate(parts))
        eq2 = bool(pred.shape == zvals.shape and (pred == zvals).all())
        if not eq2: e2_bad += 1
        # E-3 μ 分层
        mu0_layer = np.nonzero((Ds == 0) & (ms == 0))[0]
        eq3a = bool(mu0_layer.shape == z03vals[L].shape and (mu0_layer == z03vals[L]).all())
        n_mu_ne0 = int(n_L - len(mu0_layer))
        ok3 = bool(eq3a and n_mu_ne0 == 2 ** L - 1)
        if not ok3: e3_bad += 1
        # 递推层
        if prev_n is not None:
            if n_L != prev_n + 2 ** L: rec_bad += 1
        prev_n = n_L
        per_L[L] = {"n": n_L, "E1_ok": ok1, "E2_eq": eq2, "mu0_eq": eq3a,
                    "n_mu_ne0": n_mu_ne0, "E3_ok": ok3}
    log.append("DE0 e1_bad=%d e2_bad=%d e3_bad=%d rec_bad=%d per_L=%s" %
               (e1_bad, e2_bad, e3_bad, rec_bad, json.dumps(per_L)))
    # D-E0 ④ 单位词轨道谱（12 位全域）
    Ds12 = layers[-1][1]
    rv = rev_map()
    sv = sigma_map()
    unit = [4 ** j for j in range(12)]
    unit_D0 = bool(all(int(Ds12[v]) == 0 for v in unit))
    rev_ok = bool(all(int(rv[4 ** j]) == 4 ** (11 - j) for j in range(12)))
    # rep 格谱：rep=4^j (j=0..5)·格=(尾,首)
    rep_cells = {}
    for j in range(6):
        rep = 4 ** j
        t = rep % 4; h = (rep >> 22) & 3
        key = "%d%d" % (t, h)
        rep_cells[key] = rep_cells.get(key, 0) + 1
    cells_ok = bool(rep_cells == {"00": 5, "10": 1})
    # σ 像 rep 谱：min(σ(4^j), σ(4^{11−j})) == 数字串 3^j·2·3^{11−j}（j 个位3+位2+11−j 个位3）
    sig_ok = True; sig_reps = {}
    for j in range(6):
        s = "3" * j + "2" + "3" * (11 - j)
        expect = int(s, 4)
        img = int(min(int(sv[4 ** j]), int(sv[4 ** (11 - j)])))
        sig_reps["j%d" % j] = {"expect": expect, "img": img, "eq": bool(img == expect)}
        if img != expect: sig_ok = False
    log.append("DE0unit D0_all=%s rev_ok=%s rep_cells=%s cells_ok=%s sigma_ok=%s reps=%s" %
               (str(unit_D0), str(rev_ok), json.dumps(rep_cells), str(cells_ok),
                str(sig_ok), json.dumps(sig_reps)))
    res = {"meta": {"script": "d9_e0_band-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DE0": {"per_L": per_L, "e1_bad": e1_bad, "e2_bad": e2_bad, "e3_bad": e3_bad,
                    "rec_bad": rec_bad},
           "unit": {"D0_all": unit_D0, "rev_ok": rev_ok, "rep_cells": rep_cells,
                    "cells_ok": cells_ok, "sigma_ok": sig_ok, "sigma_reps": sig_reps},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- ci（候补④ 特征函数反演层·判定输出） ----------
TAU = np.array([1, 1, 1, -1, -1, -1], dtype=np.int64)   # 态 s=0..2: τ=1·s=3..5: τ=-1
MU = np.array([0, 1, 2, 0, 1, 2], dtype=np.int64)

def dest_state(rho):
    out = []
    for s in range(6):
        t2 = 1 if int(TAU[s]) * FAC[rho] == 1 else -1
        m2 = (int(MU[s]) + rho) % 3
        out.append((0 if t2 == 1 else 3) + m2)
    return out

def phi_mat(thetas, L=12, chunk=65536):
    """层频缩放六态矩阵层（修正机制）·φ(θ)=4^{-L}·1ᵀ B(3^{L−1}θ)B(3^{L−2}θ)…B(θ) e0
    （D 递推 D′=3D+τG ⟹ 第 j 位贡献相位 e^{iθ·3^{L−j}·τG}——逐层频率 3^{L−j} 缩放；
    冻结式单矩阵 (Σ_ρ M_ρ(θ))^{12} 缺 3 倍频结构·ci 首跑探针失配判负照记·本函数为修正机制）"""
    dests = [dest_state(rho) for rho in range(4)]
    gr = [np.array([int(TAU[s]) * G[rho][int(MU[s])] for s in range(6)], dtype=np.float64)
          for rho in range(4)]
    out = np.zeros(len(thetas), dtype=np.complex128)
    for i0 in range(0, len(thetas), chunk):
        th = thetas[i0:i0 + chunk]
        C = len(th)
        V = np.zeros((C, 6), dtype=np.complex128)
        V[:, 0] = 1.0
        for j in range(1, L + 1):
            f = 3 ** (L - j)                      # 本层频率乘子（首位 3^{L−1}·末位 1）
            A = np.zeros((C, 6, 6), dtype=np.complex128)
            for rho in range(4):
                w = np.exp(1j * f * np.outer(th, gr[rho]))          # (C,6)·e^{iφ·τG}
                for s in range(6):
                    A[:, dests[rho][s], s] += w[:, s]
            V = np.matmul(A, V[:, :, None])[:, :, 0]
        out[i0:i0 + chunk] = V.sum(axis=1)
    return out / (4 ** L)

def run_ci():
    log = []
    import time
    t0 = time.time()
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    h = np.bincount(aD).astype(np.float64)          # 支撑 d∈[0, 3^11]
    dmax = len(h) - 1
    N = 4 ** 12
    dv = np.arange(len(h), dtype=np.float64)
    # ① 探针对表：直方图存 aD=|D|=−D ⟹ φ_hist(θ)=(1/N)Σ_d h_d e^{−iθd}
    probes = [0.0, np.pi / 2, np.pi, 1.0 / 3.0, 2.5, np.pi / 7, 0.618, 5.0]
    phi_h = np.array([np.dot(h, np.exp(-1j * th * dv)) / N for th in probes])
    phi_m = phi_mat(np.array(probes))
    probe_err = np.abs(phi_m - phi_h)
    probe_ok = bool((probe_err <= 1e-7).all())
    log.append("DCI probes err=%s ok=%s dt=%.1fs" % (json.dumps([float(x) for x in probe_err]),
                                                     str(probe_ok), time.time() - t0))
    # ② FFT 格点精确反演（Nθ=2^19 ≥ 2·3^11+1）·矩阵层 Φ_k=Σ_d h_d e^{−iθ_k d} ⟹ h_rec=ifft(Φ)
    NTH = 2 ** 19
    thetas = 2 * np.pi * np.arange(NTH) / NTH
    phi_grid = phi_mat(thetas)
    h_rec = np.fft.ifft(phi_grid).real * N      # phi 已归一化 ⟹ ifft 还原 h/N·乘回 N 得计数
    hist_err = float(np.abs(h_rec[:len(h)] - h).max())
    tail_mass = float(np.abs(h_rec[len(h):]).max()) if NTH > len(h) else 0.0
    cdf_rec = np.cumsum(h_rec[:len(h)]) / N
    cdf_ref = np.cumsum(h) / N
    cdf_err = float(np.abs(cdf_rec - cdf_ref).max())
    hist_ok = bool(hist_err <= 1.0)
    cdf_ok = bool(cdf_err <= 1e-9)
    log.append("DCI fft hist_err=%.6g tail_mass=%.3g cdf_err=%.6g hist_ok=%s cdf_ok=%s" %
               (hist_err, tail_mass, cdf_err, str(hist_ok), str(cdf_ok)))
    ci_ok = bool(probe_ok and hist_ok and cdf_ok)
    log.append("DCI verdict ci_ok=%s" % str(ci_ok))
    res = {"meta": {"script": "d9_e0_band-v1.0-20260925.py", "frozen": FROZEN, "part": "ci",
                    "mechanism": "corrected layered-frequency B(3^(L-j)*theta) product; frozen single-matrix (sum M_rho)^12 failed probes (judge-negative recorded, see ci-singlematrix-slip JSON)"},
           "probes": {"theta": probes, "err": [float(x) for x in probe_err], "tol": 1e-7, "ok": probe_ok},
           "fft": {"NTH": NTH, "dmax": int(dmax), "hist_err": hist_err, "tail_mass": tail_mass,
                    "cdf_err": cdf_err, "tol_hist": 1.0, "tol_cdf": 1e-9,
                    "hist_ok": hist_ok, "cdf_ok": cdf_ok},
           "ci_ok": ci_ok, "log": log}
    json.dump(res, open(OUT % "ci", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "part1":
        run_part1()
    elif part == "part2":
        run_part2()
    elif part == "ci":
        run_ci()
    elif part == "bands":
        run_bands()
    elif part == "band":
        run_band(int(sys.argv[2]), int(sys.argv[3]))
    elif part == "merge":
        run_merge()
    else:
        run_part1()
        run_bands()
        run_merge()
        run_part2()
        run_ci()
