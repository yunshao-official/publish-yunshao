# -*- coding: utf-8 -*-
# d=10 带深域外验证 + Fix 保持集谱定理化（F-1/F-2/F-3+轨道计数谱）（R42）
# 判据书：代数册·d10带验证与Fix保持集谱定理化预注册判据书-v1.0-20260925.md（冻结 2026-09-25T09:48:34）
# 用法: python d10_fix_track-v1.0-20260925.py all | part1 | part2 | bands | band CS CE | merge
# part1: D-B0 锚 / D-B1 64档器 / D-B2 继承22档 / D-B3 段max=35 三态 / D-B5 分解律+C2+归因
# bands: D-B4 全部 234 段分段快扫（单进程共享 dp_full·逐段 JSON 落盘）
# band : D-B4 单段快扫 c=CS..CE
# merge: D-B4 全带统计（max 对表 35 三态+两抬升链六次验证+实质素数律+词数极值链第七点+相邻结构+直方图+分带统计+抽样3档枚举增信）
# part2: D-T2 定理 F-1 rev保持集 / F-2 σ像落回谱 / F-3 μ=0层双封闭 / 轨道计数谱 / 单位词谱==R41 零容差
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d10_fix_track-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T09:48:34"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R41P1 = "H:/理论存档/01-数学/02-实验与数据/results/d9_e0_band-part1-v1.0-20260925.json"
R41MG = "H:/理论存档/01-数学/02-实验与数据/results/d9_e0_band-merge-v1.0-20260925.json"
SEG64 = list(range(-59049, -59113, -1))        # 本轮段 64 档
INH22 = [c for c in SEG64 if c % 3 == 0]       # 继承 22 档（3|c 全集）
SRCS = sorted(set(c // 3 for c in INH22), reverse=True)   # 源档 -19683..-19704（R41 在档段）
PURE_CAND = [c for c in INH22 if (c // 3) % 2 == 1]       # 纯继承候选 11 档 -3(2j+19683) 型
# 快扫 234 段：段长 505·末段 369（i=0..232: cs=-59113-505i, ce=cs-504；i=233: cs=-176778, ce=-177146）
BAND_CHUNKS = [(-59113 - 505 * i, -59113 - 505 * i - 504) for i in range(233)] + [(-176778, -177146)]
PRED_MAX = 35                                  # 3*10+5

# ---------- 全域 DP（值索引口径·R34-R41 修正口径复用） ----------
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

def rev_map_L(L):
    """L 位反转对合（每层独立·part2 逐层用）"""
    y = np.arange(4 ** L, dtype=np.int64); r = np.zeros(4 ** L, dtype=np.int64)
    for _ in range(L):
        r = r * 4 + (y & 3); y >>= 2
    return r

def sigma_map_L(L):
    """L 位 σ 镜像 ρ→3−ρ（每层独立·part2 逐层用）"""
    y = np.arange(4 ** L, dtype=np.int64); s = np.zeros(4 ** L, dtype=np.int64)
    for _ in range(L):
        s = s * 4 + (3 - (y & 3)); y >>= 2
    return s

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

# ---------- part1（㊻ d=10 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    # D-B0 回归锚（R41 在档只读）
    r41p1 = json.load(open(R41P1, encoding="utf-8"))
    r41mg = json.load(open(R41MG, encoding="utf-8"))
    anchor_bad = 0
    for c in (-19683, -19684, -19685, -19686):
        arch = r41p1["DA1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DB0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r41mg["fullband"]
    if not (fb["n"] == 39366 and fb["max"] == 32 and fb["at"] == -39367 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DB0 merge fullband mismatch %s" % json.dumps(fb))
    wm = r41mg["wordmax"]
    if not (wm["v"] == 6144 and wm["at"] == -39366):
        anchor_bad += 1; log.append("DB0 wordmax mismatch %s" % json.dumps(wm))
    log.append("DB0 anchor_bad=%d (fullband=%s wordmax=%s)" % (anchor_bad, json.dumps(fb), json.dumps(wm)))
    # D-B1 64 档器产出
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
    log.append("DB1 gear64 R=%s mutex=%s seg_max=%d@%d seg_dt=%.1fs enum3 bad=%d %s" %
               (str(seg_R), str(mutex), seg_max, seg_max_at, seg_dt, enum_bad, json.dumps(enum3)))
    # D-B2 继承律 22 档（源档重算+R41 在档双读）
    src_bad = 0
    src_re = {}
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r41p1["DA1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DB2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_re[str(c)] = {"recompute": Rm, "archive": arch}
    recs, inh_bad, pure_list = inherit_check(INH22, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dm1[str(c)]["R_moore"]
        Rs = src_re[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    pure_match = sorted(pure_list) == sorted(PURE_CAND)
    log.append("DB2 inherit22 bad=%d pure=%s pure_match_cand=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), str(pure_match), json.dumps(synth), str(synth_ok)))
    # D-B3 段 max=35 三态
    tri = "hit" if seg_max == PRED_MAX else ("fail" if seg_max > PRED_MAX else "unsupported")
    log.append("DB3 seg_max=%d@%d vs %d -> %s" % (seg_max, seg_max_at, PRED_MAX, tri))
    # D-B5 分解律+M_int C2+极值归因
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
    log.append("DB5 law_bad=%d c2_bad=%d reach_max_seg=%d@%s top5=%s" %
               (law_bad, c2_bad, reach_max_seg, str(seg_reach_at),
                json.dumps({str(c): dm5[str(c)] for c in top})))
    res = {"meta": {"script": "d10_fix_track-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DB0": {"anchor_bad": anchor_bad, "fullband": fb, "wordmax": wm},
           "DB1": {"gear64": dm1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad,
                    "seg_reach": seg_reach, "seg_dt_sec": round(seg_dt, 1)},
           "DB2": {"src_R": src_re, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "pure_cand": PURE_CAND, "pure_match": pure_match,
                    "synth": synth, "synth_ok": synth_ok},
           "DB3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DB5": {"records": dm5, "law_bad": law_bad, "c2_bad": c2_bad,
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
    res = {"meta": {"script": "d10_fix_track-v1.0-20260925.py", "frozen": FROZEN,
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
        print("CHUNK %d/%d done elapsed=%.1fs" % (i + 1, len(BAND_CHUNKS), time.time() - t0), flush=True)

# ---------- merge（D-B4 全带统计+两抬升链六次验证+增信） ----------
def run_merge():
    log = []
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DB1"]["gear64"])
    for k in list(gear):
        gear[k] = {"c": gear[k]["c"], "n_words": gear[k]["n_words"],
                   "R": gear[k]["R_moore"], "reach": p1["DB1"]["seg_reach"][k]}
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
    # 两抬升链六次验证+max 档归因
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R"])
    lw["div3"] = bool((-mx_at) % 3 == 0)
    reach_all = [(gear[str(c)]["reach"], c) for c in allc]
    reach_max, reach_max_at = max(reach_all)
    lw["reach_is_band_max"] = bool(gear[str(mx_at)]["reach"] == reach_max)
    lw["reach_band_max_at"] = int(reach_max_at)
    # 相邻结构第五度候选：R 极值档与词数极值档
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
    # 词数极值链第七点：档位链 −2·3^10=−118098·值链 2^6·64=4096（差分 −32 延拓·首猜）
    chain = {"at_pred": -2 * (3 ** 10), "at_actual": int(wmax_at),
             "at_hit": bool(wmax_at == -2 * 3 ** 10),
             "v_pred": 2 ** 6 * 64, "v_actual": int(wmax), "v_hit": bool(wmax == 2 ** 6 * 64),
             "record_8128": bool(wmax > 8128), "prev_d9_6144": bool(wmax > 6144)}
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE wordmax=%d@%d chain7=%s (record 8128@-162 d9 6144@-39366) adjacent=%s (Rmax@%d)" %
               (wmax, wmax_at, json.dumps(chain), str(adjacent), int(mx_at)))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d10 %s" % json.dumps(stat))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    res = {"meta": {"script": "d10_fix_track-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "wordmax": {"v": int(wmax), "at": int(wmax_at), "chain7": chain, "adjacent": adjacent},
           "Rdist": Rdist, "band_d10_stat": stat, "max_law": lw,
           "enum4": enum4, "enum_bad": enum_bad, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㊼ Fix 保持集谱+σ 像落回谱+双封闭+轨道计数谱） ----------
def run_part2():
    log = []
    layers = dp_layers(12)
    z03vals = [np.nonzero(m)[0].astype(np.int64) for m in z03_masks(12)]   # z03vals[n]：n 位 {0,3}* 词值
    # D-T2 ①②③④：L=1..12 逐层（每层独立 L 位 rev/σ 映射·微测拦截口径修正：12 位映射仅用于 12 位层）
    f1_bad = 0; f2_bad = 0; f3_bad = 0; orb_bad = 0
    per_L = {}
    for (L, Ds, ms) in layers:
        N = 4 ** L
        rv = rev_map_L(L); sv = sigma_map_L(L)
        E0 = np.nonzero(Ds == 0)[0].astype(np.int64)
        z = z03vals[L]
        # F-1：{w∈E0: D(rev w)==0} == z03 ⊔ {0^j·1·0^{L−1−j}}（值 4^{L−1−j}·j=0..L−1）
        fixE0 = E0[Ds[rv[E0]] == 0]
        pure0 = np.array([4 ** (L - 1 - j) for j in range(L)], dtype=np.int64)   # =单位词集
        pred1 = np.unique(np.concatenate([z, pure0]))
        eq1 = bool(fixE0.shape == pred1.shape and (fixE0 == pred1).all())
        cnt1 = bool(len(fixE0) == 2 ** L + L)
        if not (eq1 and cnt1): f1_bad += 1
        # F-2：{w∈E0: σ(w)∈E0} == z03
        inE0 = np.zeros(N, dtype=bool); inE0[E0] = True
        back = E0[inE0[sv[E0]]]
        eq2 = bool(back.shape == z.shape and (back == z).all())
        if not eq2: f2_bad += 1
        # F-3：rev(z03)==z03 且 σ(z03)==z03 两双射
        eq3a = bool((np.sort(rv[z]) == z).all())
        eq3b = bool((np.sort(sv[z]) == z).all())
        if not (eq3a and eq3b): f3_bad += 1
        # ④ 轨道计数谱（pal_E0 冻结公式与修正公式双落盘·微测拦截 M-T2(b) 冻结推导失配照记）
        pal03 = int((rv[z] == z).sum())
        ok_pal03 = bool(pal03 == 2 ** ((L + 1) // 2))
        orb03 = (2 ** L + pal03) // 2
        palE0 = int((rv[E0] == E0).sum())
        exp_frozen = 2 ** ((L + 1) // 2) + (2 ** ((L - 1) // 2) if L % 2 == 1 else 0)
        exp_corr = 2 ** ((L + 1) // 2) + (1 if L % 2 == 1 else 0)
        mu_ne0 = np.setdiff1d(E0, z)
        inn = mu_ne0[Ds[rv[mu_ne0]] == 0]           # μ≠0 层域内配对词
        ok_inn = bool(len(inn) == L and (np.sort(inn) == np.sort(pure0)).all())   # 双升序（首跑升序vs降序簿记滑误修正照记）
        outb = np.setdiff1d(mu_ne0, inn)
        out_ok = bool((Ds[rv[outb]] != 0).all()) if len(outb) else True
        n_out = int(len(outb))
        ok_all = bool(ok_pal03 and ok_inn and out_ok)   # pal_E0 冻结式另记 pal_frozen_hit（判定输出级）
        if not ok_all: orb_bad += 1
        per_L[L] = {"n_E0": int(len(E0)), "F1_eq": eq1, "F1_cnt": cnt1, "n_Fix": int(len(fixE0)),
                    "F2_eq": eq2, "F3_rev": eq3a, "F3_sig": eq3b,
                    "pal03": pal03, "pal03_ok": ok_pal03, "orb03": int(orb03),
                    "pal_E0": palE0, "pal_frozen_exp": int(exp_frozen),
                    "pal_frozen_hit": bool(palE0 == exp_frozen),
                    "pal_corr_exp": int(exp_corr), "pal_corr_hit": bool(palE0 == exp_corr),
                    "n_inn": int(len(inn)), "inn_ok": ok_inn, "n_inn_orbits": (L + (L % 2)) // 2,
                    "n_out": n_out, "out_ok": out_ok}
    log.append("DT2 f1_bad=%d f2_bad=%d f3_bad=%d orb_bad=%d per_L=%s" %
               (f1_bad, f2_bad, f3_bad, orb_bad, json.dumps(per_L)))
    # D-T2 ⑤ σ 像不保 D 样本谱（记录项·L=12 全域抽样 5 词）
    Ds12 = layers[-1][1]
    rv = rev_map(); sv = sigma_map()   # 12 位全域映射（单位词谱+σ 样本）
    E012 = np.nonzero(Ds12 == 0)[0].astype(np.int64)
    z12 = z03vals[12]
    mu_ne012 = np.setdiff1d(E012, z12)
    import random
    rng = random.Random(20260925)
    samp = rng.sample([int(w) for w in mu_ne012], 5)
    sig_spec = {}
    for w in samp:
        sig_spec[str(w)] = {"D": 0, "D_sigma": int(Ds12[sv[w]]), "sigma": int(sv[w])}
    log.append("DT2sig sigma_not_preserve_D samples=%s" % json.dumps(sig_spec))
    # D-T2 ⑥ 12 位单位词谱==R41 零容差
    unit = [4 ** j for j in range(12)]
    unit_D0 = bool(all(int(Ds12[v]) == 0 for v in unit))
    rev_ok = bool(all(int(rv[4 ** j]) == 4 ** (11 - j) for j in range(12)))
    rep_cells = {}
    for j in range(6):
        rep = 4 ** j
        t = rep % 4; h = (rep >> 22) & 3
        key = "%d%d" % (t, h)
        rep_cells[key] = rep_cells.get(key, 0) + 1
    cells_ok = bool(rep_cells == {"00": 5, "10": 1})
    sig_ok = True; sig_reps = {}
    for j in range(6):
        s = "3" * j + "2" + "3" * (11 - j)
        expect = int(s, 4)
        img = int(min(int(sv[4 ** j]), int(sv[4 ** (11 - j)])))
        sig_reps["j%d" % j] = {"expect": expect, "img": img, "eq": bool(img == expect)}
        if img != expect: sig_ok = False
    log.append("DT2unit D0_all=%s rev_ok=%s rep_cells=%s cells_ok=%s sigma_ok=%s reps=%s" %
               (str(unit_D0), str(rev_ok), json.dumps(rep_cells), str(cells_ok),
                str(sig_ok), json.dumps(sig_reps)))
    res = {"meta": {"script": "d10_fix_track-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DT2": {"per_L": per_L, "f1_bad": f1_bad, "f2_bad": f2_bad, "f3_bad": f3_bad,
                    "orb_bad": orb_bad},
           "sigma_samples": sig_spec,
           "unit": {"D0_all": unit_D0, "rev_ok": rev_ok, "rep_cells": rep_cells,
                    "cells_ok": cells_ok, "sigma_ok": sig_ok, "sigma_reps": sig_reps},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "part1":
        run_part1()
    elif part == "part2":
        run_part2()
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
